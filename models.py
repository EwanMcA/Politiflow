from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, create_engine

class Poll(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    poll_type: str  # e.g., "Pres. Approval", "Generic Congressional Vote"
    source: str
    source_url: Optional[str] = None
    date_range: str
    positive_result: float
    negative_result: float
    sample_size: str
    margin_of_error: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PollAverage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    poll_type: str
    positive_avg: float
    negative_avg: float
    date_updated: datetime = Field(default_factory=datetime.utcnow)

sqlite_url = "sqlite:///politiflow.db"
engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
