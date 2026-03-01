import os
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, create_engine

class Poll(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    poll_type: str
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
    net_avg: float
    date_updated: datetime = Field(default_factory=datetime.utcnow)

sqlite_file_name = "politiflow.db"
base_dir = os.path.dirname(os.path.abspath(__file__))
sqlite_url = f"sqlite:///{os.path.join(base_dir, sqlite_file_name)}"
engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
