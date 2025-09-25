from typing import Optional
from datetime import date, timedelta
from sqlmodel import select
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from .database import get_session
from .models import TimeEntry, Issue, User

def weekly_aggregate(week_start: date, project_id: Optional[int] = None,
                     user_id: Optional[int] = None, label: Optional[str] = None,
                     assignee: Optional[str] = None):
    session = next(get_session())
    we = week_start + timedelta(days=7)

    stmt = select(TimeEntry, Issue.title, Issue.labels, Issue.assignee, User.username)        .where(TimeEntry.issue_id == Issue.id)        .where(TimeEntry.user_id == User.id)        .where(TimeEntry.date >= week_start, TimeEntry.date < we)
    if project_id:
        stmt = stmt.where(TimeEntry.project_id == project_id)
    if user_id:
        stmt = stmt.where(TimeEntry.user_id == user_id)
    rows = session.exec(stmt).all()

    # Filter label/assignee after join
    filtered = []
    for (te, title, labels, iss_assignee, username) in rows:
        if label and (not labels or label not in labels):
            continue
        if assignee and iss_assignee != assignee:
            continue
        filtered.append((te, title, labels or [], iss_assignee, username))

    days = [ (week_start + timedelta(days=i)) for i in range(7) ]
    labels_days = [d.isoformat() for d in days]
    by_issue = {}
    for (te, title, _labels, _assignee, username) in filtered:
        arr = by_issue.setdefault(title, [0]*7)
        idx = (te.date - week_start).days
        if 0 <= idx < 7:
            arr[idx] += te.duration_minutes
    datasets = [{"label": k, "data": v, "stack": "time"} for k, v in by_issue.items()]
    return {"labels": labels_days, "datasets": datasets}

def weekly_pdf(path: str, week_start: date, project_id: Optional[int] = None,
               user_id: Optional[int] = None, label: Optional[str] = None,
               assignee: Optional[str] = None):
    session = next(get_session())
    we = week_start + timedelta(days=7)

    stmt = select(TimeEntry, Issue.title, User.username)        .where(TimeEntry.issue_id == Issue.id)        .where(TimeEntry.user_id == User.id)        .where(TimeEntry.date >= week_start, TimeEntry.date < we)
    if project_id:
        stmt = stmt.where(TimeEntry.project_id == project_id)
    if user_id:
        stmt = stmt.where(TimeEntry.user_id == user_id)

    rows = session.exec(stmt).all()

    c = canvas.Canvas(path, pagesize=A4)
    W, H = A4
    y = H - 2*cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y, f"Weekly Report — {week_start.isoformat()} to {(we- timedelta(days=1)).isoformat()}")
    y -= 1*cm
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, f"Project: {project_id or 'All'}   User: {user_id or 'All'}")
    y -= 0.8*cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Date")
    c.drawString(5*cm, y, "User")
    c.drawString(9*cm, y, "Issue")
    c.drawString(15*cm, y, "Minutes")
    y -= 0.4*cm
    c.setFont("Helvetica", 10)
    total = 0
    for (te, title, username) in rows:
        if y < 2*cm:
            c.showPage()
            y = H - 2*cm
        c.drawString(2*cm, y, te.date.isoformat())
        c.drawString(5*cm, y, username[:20])
        c.drawString(9*cm, y, (title or '')[:40])
        c.drawRightString(19*cm, y, str(te.duration_minutes))
        y -= 0.3*cm
        total += te.duration_minutes
    y -= 0.5*cm
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(19*cm, y, f"Total minutes: {total}")
    c.save()
