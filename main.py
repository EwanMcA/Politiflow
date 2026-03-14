import uvicorn

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from models import Poll, PollAverage, engine, create_db_and_tables
from scraper import scrape_ballotpedia
from typing import Optional

app = FastAPI(title="PolitiFlow")
templates = Jinja2Templates(directory="templates")

def get_session():
    with Session(engine) as session:
        yield session

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, poll_type: Optional[str] = None, session: Session = Depends(get_session)):
    averages_raw = session.exec(select(PollAverage).order_by(PollAverage.id.desc())).all()
    
    latest_averages = {}
    for a in averages_raw:
        if a.poll_type not in latest_averages:
            latest_averages[a.poll_type] = a
            
    highlighted_types = ["Pres. Approval", "Generic Congressional Vote"]
    
    averages = []
    for t in highlighted_types:
        if t in latest_averages:
            averages.append(latest_averages[t])
            
    poll_types = session.exec(select(Poll.poll_type).distinct()).all()

    query = select(Poll).order_by(Poll.id.desc())
    if poll_type:
        query = query.where(Poll.poll_type == poll_type)
    
    polls = session.exec(query.limit(20)).all()
    
    # Fetch history for charts (last 100 data points per type)
    history_data = {}
    for t in highlighted_types:
        h = session.exec(
            select(PollAverage)
            .where(PollAverage.poll_type == t)
            .order_by(PollAverage.date_updated.asc())
            .limit(100)
        ).all()
        # Convert to serializable format for JS
        history_data[t] = [
            {
                "date_label": d.date_updated.strftime('%b %d'),
                "positive_avg": d.positive_avg,
                "negative_avg": d.negative_avg
            }
            for d in h
        ]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "averages": averages,
        "polls": polls,
        "poll_types": poll_types,
        "current_filter": poll_type,
        "history": history_data
    })

@app.post("/sync")
async def sync_data():
    scrape_ballotpedia()
    return {"status": "success", "message": "Data synchronized from Ballotpedia."}

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
