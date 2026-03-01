import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session, select
from models import Poll, PollAverage, engine, create_db_and_tables
from datetime import datetime

URL = "https://ballotpedia.org/Ballotpedia%27s_Polling_Indexes"

def parse_percentage(value: str) -> float:
    try:
        return float(value.strip('%'))
    except ValueError:
        return 0.0

def parse_date(date_str: str) -> datetime:
    try:
        # Expected format: "MM/DD-MM/DD" or "MM/DD"
        end_part = date_str.split('-')[-1].strip()
        current_year = datetime.utcnow().year
        dt = datetime.strptime(f"{end_part}/{current_year}", "%m/%d/%Y")
        
        # If the parsed date is in the future, it likely belongs to previous year
        if dt > datetime.utcnow():
            dt = dt.replace(year=current_year - 1)
        return dt
    except Exception:
        return datetime.utcnow()

def scrape_ballotpedia():
    create_db_and_tables()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = httpx.get(URL, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching {URL}: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', class_='current-polls-table')
    
    if not table:
        print("Could not find the polling table on the page.")
        return

    rows = table.find_all('tr')
    
    with Session(engine) as session:
        for row in reversed(rows):
            if row.find('th'):
                continue

            cells = row.find_all('td')
            if not cells:
                continue

            if 'poll-average-row' in row.get('class', []):
                if len(cells) >= 3:
                    text = cells[0].get_text(strip=True)
                    poll_type = text.replace('(average):', '').strip()
                    pos = parse_percentage(cells[1].get_text(strip=True))
                    neg = parse_percentage(cells[2].get_text(strip=True))
                    
                    avg = PollAverage(
                        poll_type=poll_type,
                        positive_avg=pos,
                        negative_avg=neg,
                        net_avg=round(pos - neg, 1)
                    )
                    session.add(avg)
                continue

            if len(cells) == 7:
                poll_type = cells[0].get_text(strip=True)
                source_cell = cells[1]
                source_text = source_cell.get_text(strip=True)
                source_link = source_cell.find('a')
                source_url = source_link['href'] if source_link and source_link.has_attr('href') else None
                
                if source_url and source_url.startswith('/'):
                    source_url = f"https://ballotpedia.org{source_url}"
                
                date_range = cells[2].get_text(strip=True)
                pos = parse_percentage(cells[3].get_text(strip=True))
                neg = parse_percentage(cells[4].get_text(strip=True))
                sample = cells[5].get_text(strip=True)
                moe = cells[6].get_text(strip=True)
                
                statement = select(Poll).where(
                    Poll.poll_type == poll_type,
                    Poll.source == source_text,
                    Poll.date_range == date_range
                )
                existing = session.exec(statement).first()
                
                if not existing:
                    poll = Poll(
                        poll_type=poll_type,
                        source=source_text,
                        source_url=source_url,
                        date_range=date_range,
                        positive_result=pos,
                        negative_result=neg,
                        sample_size=sample,
                        margin_of_error=moe
                    )
                    session.add(poll)
        
        session.commit()

        # Recalculate historical averages based on parsed dates
        all_types = session.exec(select(Poll.poll_type).distinct()).all()
        for t in all_types:
            polls = session.exec(
                select(Poll).where(Poll.poll_type == t).order_by(Poll.id.asc())
            ).all()
            
            if len(polls) >= 5:
                for i in range(4, len(polls)):
                    window = polls[i-4:i+1]
                    avg_pos = round(sum(p.positive_result for p in window) / 5, 1)
                    avg_neg = round(sum(p.negative_result for p in window) / 5, 1)
                    
                    poll_date = parse_date(polls[i].date_range)
                    
                    avg = PollAverage(
                        poll_type=t,
                        positive_avg=avg_pos,
                        negative_avg=avg_neg,
                        net_avg=round(avg_pos - avg_neg, 1),
                        date_updated=poll_date
                    )
                    session.add(avg)
        
        session.commit()

if __name__ == "__main__":
    scrape_ballotpedia()
