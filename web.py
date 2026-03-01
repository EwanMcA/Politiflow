from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from models import Poll, PollAverage, engine, create_db_and_tables
from scraper import scrape_ballotpedia
from typing import List

app = FastAPI(title="PolitiFlow")
templates = Jinja2Templates(directory="templates")

def get_session():
    with Session(engine) as session:
        yield session

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, session: Session = Depends(get_session)):
    # Fetch latest averages (one of each type)
    averages_raw = session.exec(select(PollAverage).order_by(PollAverage.date_updated.desc())).all()
    
    averages = {}
    for a in averages_raw:
        if a.poll_type not in averages:
            averages[a.poll_type] = a
            
    # Fetch latest 20 polls
    polls = session.exec(select(Poll).order_by(Poll.created_at.desc()).limit(20)).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "averages": averages.values(),
        "polls": polls
    })

@app.post("/sync")
async def sync_data():
    scrape_ballotpedia()
    return {"status": "success", "message": "Data synchronized from Ballotpedia."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
