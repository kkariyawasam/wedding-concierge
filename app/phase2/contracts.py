import os
import uuid
from typing import Dict, List

from pypdf import PdfReader
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

CONTRACT_DIR = "app/data/contracts"


def save_contract_pdf(file_bytes: bytes, original_filename: str) -> Dict:
    os.makedirs(CONTRACT_DIR, exist_ok=True)
    contract_id = str(uuid.uuid4())
    safe_name = original_filename.replace("/", "_").replace("\\", "_")
    path = os.path.join(CONTRACT_DIR, f"{contract_id}_{safe_name}")
    with open(path, "wb") as f:
        f.write(file_bytes)
    return {"contract_id": contract_id, "path": path, "filename": safe_name}


def extract_pdf_text(path: str) -> str:
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def chunk_text(text: str) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150
    )
    return splitter.split_text(text)


async def summarize_contract(text: str) -> Dict:
    """
    Returns:
      {summary: str, risk_flags: [...], key_terms: {...}}
    """
    chunks = chunk_text(text)
    # Map step: summarize chunks
    chunk_summaries = []
    for c in chunks[:12]:  # keep it bounded for MVP
        prompt = (
            "Summarize this contract chunk in 3-6 bullet points. "
            "Focus on money, dates, cancellation, obligations.\n\n"
            f"CHUNK:\n{c}"
        )
        r = await llm.ainvoke(prompt)
        chunk_summaries.append(r.content.strip())

    # Reduce step: combine
    reduce_prompt = (
        "You are a contract analyzer for wedding vendor contracts.\n"
        "Combine the chunk summaries into a clear contract overview.\n"
        "Return ONLY JSON with keys:\n"
        "- summary (short paragraph + bullets)\n"
        "- risk_flags (array of {type, detail, severity})\n"
        "- key_terms (object with: deposit, cancellation, payment_schedule, deadlines, overtime_fees, hidden_fees)\n\n"
        f"CHUNK SUMMARIES:\n{chr(10).join(chunk_summaries)}"
    )
    resp = await llm.ainvoke(reduce_prompt)

    import json
    out = resp.content.strip()
    if out.startswith("```"):
        out = out.strip("`").replace("json", "", 1).strip()
    return json.loads(out)