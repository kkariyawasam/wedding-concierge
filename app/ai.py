import json
import re
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from dateutil import relativedelta

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from .prompts import CHECKLIST_PROMPT, BUDGET_PROMPT, CONCIERGE_PROMPT

from .prompts import (
    CHECKLIST_PROMPT_V2,
    BUDGET_PROMPT_V2,
    CONCIERGE_PROMPT,
    CHAT_MEMORY_SUMMARY_PROMPT
)

CORE_BUDGET_CATEGORIES = [
    {"category": "Venue", "percent": 25},
    {"category": "Catering", "percent": 35},
    {"category": "Photography", "percent": 12},
    {"category": "Attire", "percent": 8},
    {"category": "Flowers", "percent": 7},
    {"category": "Music", "percent": 5},
    {"category": "Decor/Rentals", "percent": 4},
    {"category": "Stationery", "percent": 2},
    {"category": "Transportation", "percent": 1},
    {"category": "Misc/Buffer", "percent": 1},
]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)


def months_until(wedding_date_str: str) -> int:
    y, m, d = [int(x) for x in wedding_date_str.split("-")]
    wd = date(y, m, d)
    today = date.today()
    if wd <= today:
        return 0
    rd = relativedelta.relativedelta(wd, today)
    return rd.years * 12 + rd.months + (1 if rd.days > 0 else 0)


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    return text


def _parse_json_or_raise(text: str):
    """
    Extracts the first JSON array/object found in the text and parses it.
    Handles ```json fences and extra commentary.
    """
    text = _strip_code_fences(text)

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Non-greedy extraction of first JSON array
    m = re.search(r"(\[[\s\S]*?\])", text)
    if m:
        return json.loads(m.group(1))

    # Non-greedy extraction of first JSON object
    m = re.search(r"(\{[\s\S]*?\})", text)
    if m:
        return json.loads(m.group(1))

    raise ValueError("Could not parse JSON from model output.")


async def generate_checklist(profile: dict) -> list[dict]:
    months_left = months_until(profile["wedding_date"])
    prompt = CHECKLIST_PROMPT.format(
        wedding_date=profile["wedding_date"],
        months_left=months_left,
        location=profile.get("location", ""),
        vibe=profile.get("vibe", ""),
    )

    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    data = _parse_json_or_raise(resp.content)

    # Accept either a list OR {"items": [...]}
    if isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            data = data["items"]

    if not isinstance(data, list):
        raise ValueError(f"Checklist JSON must be a list, got: {type(data)}")

    # Light validation
    cleaned = []
    for item in data:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        due_date = item.get("due_date")
        priority = item.get("priority", "Normal")
        if title and due_date:
            cleaned.append(
                {"title": str(title), "due_date": str(due_date), "priority": str(priority)}
            )

    return cleaned


async def generate_budget_lines(budget_total: float) -> list[dict]:
    prompt = BUDGET_PROMPT.format(budget_total=budget_total)

    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    data = _parse_json_or_raise(resp.content)

    # Accept list OR {"lines":[...]} OR {"items":[...]}
    if isinstance(data, dict):
        if "lines" in data and isinstance(data["lines"], list):
            data = data["lines"]
        elif "items" in data and isinstance(data["items"], list):
            data = data["items"]

    if not isinstance(data, list):
        raise ValueError(f"Budget JSON must be a list, got: {type(data)}")

    # Clean rows, ignore broken ones
    rows = []
    for line in data:
        if not isinstance(line, dict):
            continue
        cat = line.get("category")
        pct = line.get("percent")
        if cat is None or pct is None:
            continue
        try:
            pct_f = float(pct)
        except Exception:
            continue
        rows.append({"category": str(cat), "percent": pct_f})

    if not rows:
        raise ValueError("Budget JSON had no valid lines.")

    # Ensure percents add to ~100 (normalize if needed)
    pct_sum = sum(r["percent"] for r in rows)
    if pct_sum <= 0:
        raise ValueError("Budget percent sum <= 0.")

    if abs(pct_sum - 100.0) > 0.5:
        # Normalize to 100
        for r in rows:
            r["percent"] = (r["percent"] / pct_sum) * 100.0

    total = Decimal(str(budget_total))
    out = []
    running = Decimal("0.00")

    # Calculate amounts with proper rounding
    for i, r in enumerate(rows):
        pct = Decimal(str(r["percent"])) / Decimal("100")

        if i < len(rows) - 1:
            amt = (total * pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            running += amt
        else:
            # Last line gets remainder to ensure totals match exactly
            amt = (total - running).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        out.append(
            {
                "category": r["category"],
                "percent": float(Decimal(str(r["percent"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "amount": float(amt),
            }
        )

    return out


async def concierge_answer(profile: dict, question: str) -> str:
    prompt = CONCIERGE_PROMPT.format(
        wedding_date=profile.get("wedding_date"),
        budget_total=profile.get("budget_total"),
        location=profile.get("location"),
        vibe=profile.get("vibe"),
        question=question,
    )
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return resp.content.strip()

async def summarize_chat_preferences(chat_messages: list[dict]) -> dict:
    # chat_messages: [{"role":"user","content":"..."}, ...]
    chat_text = "\n".join([f'{m["role"]}: {m["content"]}' for m in chat_messages][-30:])  # last 30
    prompt = CHAT_MEMORY_SUMMARY_PROMPT.format(chat=chat_text)
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return _parse_json_or_raise(resp.content)

async def generate_checklist_v2(profile: dict, prefs: dict) -> list[dict]:
    months_left = months_until(profile["wedding_date"])
    prompt = CHECKLIST_PROMPT_V2.format(
        wedding_date=profile["wedding_date"],
        months_left=months_left,
        location=profile.get("location", ""),
        vibe=profile.get("vibe", ""),
        prefs_json=json.dumps(prefs),
    )
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return _parse_json_or_raise(resp.content)

async def generate_budget_lines_v2(budget_total: float, prefs: dict) -> dict:
    prompt = BUDGET_PROMPT_V2.format(
        budget_total=budget_total,
        core_json=json.dumps(CORE_BUDGET_CATEGORIES),
        prefs_json=json.dumps(prefs),
    )
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    data = _parse_json_or_raise(resp.content)

    core_lines = data.get("core", [])
    add_ons = data.get("add_ons", [])

    total = Decimal(str(budget_total))

    # Convert core % into exact amounts (your fixed “core” stays intact)
    core_out = []
    for line in core_lines:
        pct = Decimal(str(line["percent"])) / Decimal("100")
        amt = (total * pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        core_out.append({
            "category": line["category"],
            "percent": float(line["percent"]),
            "amount": float(amt),
        })

    # Add-ons are already amounts; just normalize format
    add_on_out = []
    for a in add_ons:
        try:
            amt = Decimal(str(a["suggested_amount"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except:
            continue
        add_on_out.append({
            "name": a.get("name", "Add-on"),
            "amount": float(amt),
            "note": a.get("note", ""),
        })

    return {"core": core_out, "add_ons": add_on_out}