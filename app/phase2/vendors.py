import os
import pandas as pd
from typing import List, Dict, Optional

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_chroma import Chroma


VENDOR_CSV_PATH = "app/data/vendors/vendors.csv"
CHROMA_DIR = "app/data/chroma/vendors"
COLLECTION_NAME = "vendors"

embeddings = OpenAIEmbeddings()
rank_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)


def _vendor_row_to_text(row: dict) -> str:
    # This is what gets embedded for semantic search
    return (
        f"Vendor Name: {row.get('name','')}\n"
        f"Category: {row.get('category','')}\n"
        f"Location: {row.get('location','')}\n"
        f"Price Range: {row.get('price_min','')} - {row.get('price_max','')}\n"
        f"Styles: {row.get('styles','')}\n"
        f"Description: {row.get('description','')}\n"
        f"Contact: {row.get('contact','')}\n"
    )


def load_and_index_vendors_if_needed(force_rebuild: bool = False) -> int:
    """
    Loads vendors.csv and indexes into Chroma.
    Call this once on startup.
    """
    os.makedirs(CHROMA_DIR, exist_ok=True)

    # If already exists, skip unless force_rebuild
    if (not force_rebuild) and os.path.exists(os.path.join(CHROMA_DIR, "chroma.sqlite3")):
        return 0

    if not os.path.exists(VENDOR_CSV_PATH):
        raise FileNotFoundError(f"Vendor CSV not found: {VENDOR_CSV_PATH}")

    df = pd.read_csv(VENDOR_CSV_PATH)
    docs: List[Document] = []

    for i, row in df.iterrows():
        r = row.fillna("").to_dict()
        text = _vendor_row_to_text(r)
        meta = {
            "name": str(r.get("name", "")),
            "category": str(r.get("category", "")),
            "location": str(r.get("location", "")),
            "price_min": float(r.get("price_min", 0) or 0),
            "price_max": float(r.get("price_max", 0) or 0),
            "styles": str(r.get("styles", "")),
            "contact": str(r.get("contact", "")),
        }
        docs.append(Document(page_content=text, metadata=meta))

    # Build / persist Chroma
    Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
    )
    return len(docs)


def _get_vectorstore() -> Chroma:
    return Chroma(
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )


async def vendor_search(query: str, profile: dict, k: int = 5) -> List[Dict]:
    """
    Returns vendor 'cards' for UI/chat:
    [{name, category, location, price_range, styles, contact, reason}]
    """
    vs = _get_vectorstore()

    # Make the retrieval query stronger using wedding profile context
    enriched_query = (
        f"User is planning a wedding.\n"
        f"Location: {profile.get('location','')}\n"
        f"Vibe: {profile.get('vibe','')}\n"
        f"Budget: {profile.get('budget_total','')}\n"
        f"User request: {query}\n"
        f"Find best matching wedding vendors."
    )

    docs = vs.similarity_search(enriched_query, k=k)

    # Ask LLM to rank + explain based on retrieved docs
    joined = "\n\n---\n\n".join([d.page_content for d in docs])

    prompt = (
        "You are a wedding vendor matchmaker.\n"
        "Given the wedding profile and user request, rank the vendors.\n"
        "Return ONLY JSON array with fields:\n"
        "name, category, location, price_range, styles, contact, reason\n\n"
        f"Wedding Profile:\n{profile}\n\n"
        f"User Request:\n{query}\n\n"
        f"Vendor Candidates:\n{joined}\n"
    )

    resp = await rank_llm.ainvoke(prompt)

    # Safe parse
    import json
    text = resp.content.strip()
    if text.startswith("```"):
        text = text.strip("`").replace("json", "", 1).strip()
    return json.loads(text)