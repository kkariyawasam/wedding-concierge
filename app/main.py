# app/main.py
import uuid
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlmodel import Session, select, delete

from .db import init_db, get_session
from .models import WeddingProfile, ChecklistItem, BudgetLine, ChatMessage
from .ai import (
    concierge_answer,
    summarize_chat_preferences,
    generate_checklist_v2,
    generate_budget_lines_v2,
)
from fastapi.responses import FileResponse
from fastapi import UploadFile, File
import os

from fastapi import UploadFile, File
from .phase2.vendors import load_and_index_vendors_if_needed, vendor_search
from .phase2.contracts import save_contract_pdf, extract_pdf_text, summarize_contract
from .models import ContractDoc
import json

from .models import ChatMessage  # you already have this
from sqlmodel import select
#from .phase2.vendors import ingest_vendors_if_needed
from .phase2.moodboard import generate_moodboard

load_dotenv()

app = FastAPI(title="Wedding Concierge (Phase 1)")
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

    
@app.on_event("startup")
def on_startup():
    init_db()
    load_and_index_vendors_if_needed(force_rebuild=False)
    
from fastapi import UploadFile, File
from .phase2.vendors import load_and_index_vendors_if_needed, vendor_search
from .phase2.contracts import save_contract_pdf, extract_pdf_text, summarize_contract
from .models import ContractDoc
import json


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def get_or_create_profile(db: Session, session_id: str) -> WeddingProfile:
    prof = db.exec(select(WeddingProfile).where(WeddingProfile.session_id == session_id)).first()
    if prof:
        return prof
    prof = WeddingProfile(session_id=session_id, onboarding_step=0)
    db.add(prof)
    db.commit()
    db.refresh(prof)
    return prof


def onboarding_next_question(step: int) -> str:
    return [
        "What’s your wedding date? (YYYY-MM-DD)",
        "What’s your total budget number (example: 20000)?",
        "Where is the wedding happening? (City + country)",
        "What’s the vibe? (example: modern minimalist, garden party, disco glam)",
    ][step]


@app.post("/api/session")
def create_session():
    return {"session_id": str(uuid.uuid4())}


@app.get("/api/state/{session_id}")
def get_state(session_id: str, db: Session = Depends(get_session)):
    prof = get_or_create_profile(db, session_id)

    checklist = db.exec(
        select(ChecklistItem).where(ChecklistItem.session_id == session_id)
    ).all()
    budget = db.exec(
        select(BudgetLine).where(BudgetLine.session_id == session_id)
    ).all()

    return {
        "profile": prof.model_dump(),
        "checklist": [c.model_dump() for c in checklist],
        "budget": [b.model_dump() for b in budget],
    }


@app.post("/api/chat")
async def chat(payload: dict, db: Session = Depends(get_session)):
    """
    payload: { session_id: str, message: str }
    """
    session_id = payload["session_id"]
    msg = (payload.get("message") or "").strip()

    prof = get_or_create_profile(db, session_id)

    # Save user message
    db.add(ChatMessage(session_id=session_id, role="user", content=msg))
    db.commit()

    # ---------------------------
    # 1) Onboarding flow (4 steps)
    # ---------------------------
    if prof.onboarding_step < 4:
        step = prof.onboarding_step

        if step == 0:
            if len(msg) != 10 or msg[4] != "-" or msg[7] != "-":
                assistant_text = "Please enter the date as YYYY-MM-DD (example: 2026-08-15)."
                db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_text))
                db.commit()
                return {"role": "assistant", "text": assistant_text}

            prof.wedding_date = msg
            prof.onboarding_step = 1

        elif step == 1:
            try:
                prof.budget_total = float(msg.replace(",", "").replace("$", ""))
            except Exception:
                assistant_text = "Please enter just a number for budget (example: 20000)."
                db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_text))
                db.commit()
                return {"role": "assistant", "text": assistant_text}

            prof.onboarding_step = 2

        elif step == 2:
            prof.location = msg
            prof.onboarding_step = 3

        elif step == 3:
            prof.vibe = msg
            prof.onboarding_step = 4

        db.add(prof)
        db.commit()
        db.refresh(prof)

        if prof.onboarding_step < 4:
            assistant_text = onboarding_next_question(prof.onboarding_step)
            db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_text))
            db.commit()
            return {"role": "assistant", "text": assistant_text}

        assistant_text = (
            "✅ Profile created! You can now chat freely about your wedding. "
            "When you’re ready, click “Generate Checklist” or “Generate Budget” to create/update them from your chat."
        )
        db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_text))
        db.commit()
        return {"role": "assistant", "text": assistant_text}

    # ---------------------------------------
    # 2) Phase 2: Contract question handling
    # ---------------------------------------
    contract_keywords = [
        "contract", "agreement", "clause", "deposit",
        "cancellation", "refund", "legal", "sign",
        "safe", "risk", "penalty", "terms"
    ]

    if any(k in msg.lower() for k in contract_keywords):
        last_contract = db.exec(
            select(ContractDoc)
            .where(ContractDoc.session_id == session_id)
            .order_by(ContractDoc.created_at.desc())
        ).first()

        if last_contract:
            data = json.loads(last_contract.summary_json)

            # Use the concierge model to answer based on stored contract summary
            prompt = (
                "You are helping analyze a wedding vendor contract.\n\n"
                f"Contract summary JSON:\n{json.dumps(data, indent=2)}\n\n"
                f"User question:\n{msg}\n\n"
                "Answer clearly, mention risks, and suggest what to ask the vendor."
            )

            assistant_text = await concierge_answer(prof.model_dump(), prompt)

            db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_text))
            db.commit()
            return {"role": "assistant", "text": assistant_text}

        # If user asks about contract but none uploaded yet
        assistant_text = "I can help with that—please upload the contract PDF using the upload button first."
        db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_text))
        db.commit()
        return {"role": "assistant", "text": assistant_text}

    # ---------------------------------------
    # 3) Phase 2: Vendor search command
    # ---------------------------------------
    if msg.lower().startswith("/vendor"):
        query = msg[len("/vendor"):].strip()
        if not query:
            assistant_text = "Please type like: /vendor florist in Berlin modern"
            db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_text))
            db.commit()
            return {"role": "assistant", "text": assistant_text}

        results = await vendor_search(query=query, profile=prof.model_dump(), k=5)

        lines = ["Here are the best vendor matches I found:"]
        for v in results:
            lines.append(
                f"\n**{v.get('name','')}** ({v.get('category','')}, {v.get('location','')})\n"
                f"- Price: {v.get('price_range','')}\n"
                f"- Styles: {v.get('styles','')}\n"
                f"- Why: {v.get('reason','')}\n"
                f"- Contact: {v.get('contact','')}"
            )

        assistant_text = "\n".join(lines)
        db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_text))
        db.commit()
        return {"role": "assistant", "text": assistant_text}

    # ---------------------------------------
    # 4) Phase 2: Auto-detect vendor questions
    # ---------------------------------------
    vendor_keywords = [
        "vendor", "vendors", "florist", "photographer", "videographer",
        "dj", "band", "music", "catering", "caterer", "venue", "planner",
        "makeup", "hair", "decor", "decoration"
    ]

    if any(k in msg.lower() for k in vendor_keywords):
        results = await vendor_search(query=msg, profile=prof.model_dump(), k=5)
        if results:
            lines = ["Here are vendor matches from my local vendor list:"]
            for v in results:
                lines.append(
                    f"\n**{v.get('name','')}** ({v.get('category','')}, {v.get('location','')})\n"
                    f"- Price: {v.get('price_range','')}\n"
                    f"- Styles: {v.get('styles','')}\n"
                    f"- Why: {v.get('reason','')}\n"
                    f"- Contact: {v.get('contact','')}"
                )
            assistant_text = "\n".join(lines)
            db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_text))
            db.commit()
            return {"role": "assistant", "text": assistant_text}

    # ---------------------------------------
    # 5) Phase 2: Image generation in chat
    # ---------------------------------------
    if ("image" in msg.lower()) or ("moodboard" in msg.lower()):
        prompt = (
            f"Wedding inspiration image. "
            f"Location: {prof.location}. "
            f"Vibe: {prof.vibe}. "
            f"User request: {msg}"
        )

        images = generate_moodboard(prompt)

        assistant_text = "Here are some inspiration images:"
        db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_text))
        db.commit()
        return {"role": "assistant", "text": assistant_text, "images": images}

    # ---------------------------
    # 6) Concierge mode (default)
    # ---------------------------
    assistant_text = await concierge_answer(prof.model_dump(), msg)
    db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_text))
    db.commit()
    return {"role": "assistant", "text": assistant_text}


@app.post("/api/generate/checklist")
async def generate_checklist_endpoint(payload: dict, db: Session = Depends(get_session)):
    """
    payload: { session_id: str }
    """
    session_id = payload["session_id"]
    prof = get_or_create_profile(db, session_id)

    if prof.onboarding_step < 4:
        return JSONResponse({"error": "Finish onboarding first."}, status_code=400)
    if not prof.wedding_date:
        return JSONResponse({"error": "Wedding date missing in profile."}, status_code=400)

    chats = db.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()
    chat_messages = [{"role": c.role, "content": c.content} for c in chats]

    prefs = await summarize_chat_preferences(chat_messages)

    # Clear old checklist
    db.exec(delete(ChecklistItem).where(ChecklistItem.session_id == session_id))
    db.commit()

    # Generate new checklist based on profile + chat-derived prefs
    profile_dict = {
    "wedding_date": prof.wedding_date,
    "budget_total": prof.budget_total,
    "location": prof.location,
    "vibe": prof.vibe,
}
    items = await generate_checklist_v2(profile_dict, prefs)

    for item in items:
        db.add(
            ChecklistItem(
                session_id=session_id,
                title=item["title"],
                due_date=item["due_date"],
                priority=item["priority"],
            )
        )

    db.commit()
    return {"ok": True}


@app.post("/api/generate/budget")
async def generate_budget_endpoint(payload: dict, db: Session = Depends(get_session)):
    """
    payload: { session_id: str }
    """
    session_id = payload["session_id"]
    prof = get_or_create_profile(db, session_id)

    if prof.onboarding_step < 4:
        return JSONResponse({"error": "Finish onboarding first."}, status_code=400)
    if not prof.budget_total:
        return JSONResponse({"error": "Budget missing in profile."}, status_code=400)

    chats = db.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()
    chat_messages = [{"role": c.role, "content": c.content} for c in chats]

    prefs = await summarize_chat_preferences(chat_messages)

    # Clear old budget
    db.exec(delete(BudgetLine).where(BudgetLine.session_id == session_id))
    db.commit()

    # Generate new budget based on profile + chat-derived prefs
    result = await generate_budget_lines_v2(prof.budget_total, prefs)

# Clear old budget
    db.exec(delete(BudgetLine).where(BudgetLine.session_id == session_id))
    db.commit()

# Save core
    for line in result["core"]:
        db.add(BudgetLine(
            session_id=session_id,
            category=line["category"],
            percent=line["percent"],
            amount=line["amount"],
            is_add_on=False,
            note=""
        ))

# Save add-ons
    for a in result["add_ons"]:
        db.add(BudgetLine(
            session_id=session_id,
            category=a["name"],     # store name in category field
            percent=0.0,
            amount=a["amount"],
            is_add_on=True,
            note=a.get("note","")
        ))

    db.commit()
    return {"ok": True}

@app.post("/api/vendors/upload")
async def upload_vendors(file: UploadFile = File(...)):
    os.makedirs("app/data/vendors", exist_ok=True)
    path = f"app/data/vendors/{file.filename}"
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    count = ingest_vendors_csv(path)
    return {"ok": True, "ingested": count}

@app.post("/api/vendors/search")
async def vendors_search(payload: dict, db: Session = Depends(get_session)):
    session_id = payload["session_id"]
    query = payload["query"]

    prof = get_or_create_profile(db, session_id)
    if prof.onboarding_step < 4:
        return JSONResponse({"error": "Finish onboarding first."}, status_code=400)

    cards = await search_vendors(prof.model_dump(), query, k=5)
    return {"ok": True, "results": cards}


@app.post("/api/chat/upload-contract")
async def upload_contract(session_id: str, file: UploadFile = File(...), db: Session = Depends(get_session)):
    prof = get_or_create_profile(db, session_id)
    if prof.onboarding_step < 4:
        return JSONResponse({"error": "Finish onboarding first."}, status_code=400)

    data = await file.read()
    saved = save_contract_pdf(data, file.filename)
    text = extract_pdf_text(saved["path"])

    if not text:
        return {"role": "assistant", "text": "I couldn’t extract text from this PDF. If it’s a scanned image, I’ll need OCR later. Try a text-based PDF if possible."}

    analysis = await summarize_contract(text)

    # store in DB
    db.add(ContractDoc(
        session_id=session_id,
        contract_id=saved["contract_id"],
        filename=saved["filename"],
        summary_json=json.dumps(analysis),
    ))
    db.commit()

    # Return a chat-style reply
    risks = analysis.get("risk_flags", [])
    risk_lines = []
    for r in risks[:6]:
        risk_lines.append(f"- ({r.get('severity','')}) {r.get('type','')}: {r.get('detail','')}")
    risk_text = "\n".join(risk_lines) if risk_lines else "- No major red flags detected (based on extracted text)."

    text_reply = (
        f"📄 **Contract Summary for:** {saved['filename']}\n\n"
        f"{analysis.get('summary','(No summary)')}\n\n"
        f"⚠️ **Risk flags:**\n{risk_text}\n\n"
        f"Want me to explain any clause in simpler terms? Paste the clause text or ask what to watch out for."
    )
    return {"role": "assistant", "text": text_reply}


@app.get("/api/moodboard/image")
def moodboard_image(path: str):
    # simple local-file serving for demo
    if not path.startswith("app/data/moodboards/") or not os.path.exists(path):
        return JSONResponse({"error": "Not found"}, status_code=404)
    return FileResponse(path, media_type="image/png")



