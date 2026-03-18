from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class WeddingProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, unique=True)

    wedding_date: Optional[str] = None  # YYYY-MM-DD
    budget_total: Optional[float] = None
    location: Optional[str] = None
    vibe: Optional[str] = None

    onboarding_step: int = 0  # 0..4
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChecklistItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    title: str
    due_date: str  # YYYY-MM-DD
    priority: str  # "Emergency" | "High" | "Normal"

class BudgetLine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    category: str
    percent: float
    amount: float
    is_add_on: bool = False
    note: str = ""
    
class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
from datetime import datetime

class ContractDoc(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    contract_id: str = Field(index=True)
    filename: str
    summary_json: str  # store JSON as string for MVP
    created_at: datetime = Field(default_factory=datetime.utcnow)