from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import select
from datetime import date, datetime, timedelta
from typing import Optional, Dict
import os
import tempfile

from .database import get_session
from .models import Project, Issue, TimeEntry, Timer, User
from .reports import weekly_aggregate, weekly_pdf
from .github_import import import_all

api = APIRouter(prefix="/api")


def current_user(request: Request) -> User:
    uid = request.cookies.get("user_id")
    if not uid:
        raise HTTPException(status_code=401, detail="not authenticated")
    with get_session() as session:
        user = session.get(User, int(uid))
        if not user:
            raise HTTPException(status_code=401, detail="user not found")
        return user


@api.get("/users")
def list_users():
    with get_session() as session:
        return session.exec(select(User)).all()


@api.get("/projects")
def list_projects():
    with get_session() as session:
        return session.exec(select(Project)).all()


@api.get("/issues")
def list_issues(
    project_id: Optional[int] = None,
    state: Optional[str] = None,
    label: Optional[str] = None,
    assignee: Optional[str] = None,
):
    with get_session() as session:
        stmt = select(Issue)
        if project_id is not None:
            stmt = stmt.where(Issue.project_id == project_id)
        if state:
            stmt = stmt.where(Issue.state == state)
        issues = session.exec(stmt).all()
        if label:
            issues = [i for i in issues if i.labels and label in i.labels]
        if assignee:
            issues = [i for i in issues if i.assignee == assignee]
        return issues


@api.get("/issues/{issue_id}")
def get_issue(issue_id: int):
    with get_session() as session:
        it = session.get(Issue, issue_id)
        if not it:
            raise HTTPException(404, "Issue not found")
        return it


@api.get("/issues/by-gh/{owner}/{repo}/{number}")
def get_issue_by_github(owner: str, repo: str, number: int):
    with get_session() as session:
        project = session.exec(
            select(Project).where(Project.github_repo == f"{owner}/{repo}")
        ).first()
        if not project:
            raise HTTPException(404, "Project not found")
        issue = session.exec(
            select(Issue).where(
                Issue.project_id == project.id, Issue.github_number == number
            )
        ).first()
        if not issue:
            raise HTTPException(404, "Issue not found")
        return issue


@api.post("/issues/{issue_id}/time-entries")
def add_time_entry(issue_id: int, payload: Dict, request: Request):
    user = current_user(request)
    with get_session() as session:
        issue = session.get(Issue, issue_id)
        if not issue:
            raise HTTPException(404, "Issue not found")
        minutes = int(payload.get("duration_minutes", 0))
        if minutes <= 0:
            raise HTTPException(400, "duration_minutes must be > 0")
        d = (
            date.fromisoformat(payload.get("date"))
            if payload.get("date")
            else date.today()
        )
        entry = TimeEntry(
            user_id=user.id,
            project_id=issue.project_id,
            issue_id=issue.id,
            date=d,
            duration_minutes=minutes,
            notes=payload.get("notes"),
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry


@api.get("/time-entries")
def list_time_entries(
    week_start: Optional[str] = None,
    project_id: Optional[int] = None,
    user_id: Optional[int] = None,
    label: Optional[str] = None,
    assignee: Optional[str] = None,
):
    with get_session() as session:
        stmt = (
            select(TimeEntry, Issue.title, User.username, Project.name)
            .where(TimeEntry.issue_id == Issue.id)
            .where(TimeEntry.user_id == User.id)
            .where(TimeEntry.project_id == Project.id)
        )
        if project_id:
            stmt = stmt.where(TimeEntry.project_id == project_id)
        if user_id:
            stmt = stmt.where(TimeEntry.user_id == user_id)
        if week_start:
            ws = date.fromisoformat(week_start)
            we = ws + timedelta(days=7)
            stmt = stmt.where(TimeEntry.date >= ws).where(TimeEntry.date < we)

        rows = session.exec(stmt).all()

        # apply label/assignee filtering
        if label or assignee:
            filtered = []
            for te, title, username, project_name in rows:
                issue = session.get(Issue, te.issue_id)
                if label and (not issue.labels or label not in issue.labels):
                    continue
                if assignee and issue.assignee != assignee:
                    continue
                filtered.append((te, title, username, project_name))
            rows = filtered

        return [
            {
                "id": te.id,
                "date": te.date.isoformat(),
                "duration_minutes": te.duration_minutes,
                "notes": te.notes,
                "issue_id": te.issue_id,
                "issue_title": title,
                "user": username,
                "project": project_name,
            }
            for (te, title, username, project_name) in rows
        ]


@api.delete("/time-entries/{entry_id}")
def delete_time_entry(entry_id: int, request: Request):
    user = current_user(request)
    with get_session() as session:
        entry = session.get(TimeEntry, entry_id)
        if not entry:
            raise HTTPException(404, "Time entry not found")
        if entry.user_id != user.id:
            raise HTTPException(403, "Not allowed")
        session.delete(entry)
        session.commit()
    return {"ok": True}


@api.post("/issues/{issue_id}/timer/start")
def start_timer(issue_id: int, request: Request):
    user = current_user(request)
    with get_session() as session:
        issue = session.get(Issue, issue_id)
        if not issue:
            raise HTTPException(404, "Issue not found")
        running = session.exec(
            select(Timer).where(Timer.user_id == user.id, Timer.running)
        ).all()
        for t in running:
            t.running = False
        timer = Timer(
            user_id=user.id,
            project_id=issue.project_id,
            issue_id=issue.id,
            running=True,
        )
        session.add(timer)
        session.commit()
        session.refresh(timer)
        return {"timer_id": timer.id, "started": timer.start_ts.isoformat()}


@api.post("/timer/stop")
def stop_timer(request: Request, payload: Dict = {}):
    user = current_user(request)
    with get_session() as session:
        timer = session.exec(
            select(Timer).where(Timer.user_id == user.id, Timer.running)
        ).first()
        if not timer:
            raise HTTPException(400, "No running timer")
        timer.running = False
        delta = datetime.utcnow() - timer.start_ts
        minutes = max(1, int(delta.total_seconds() // 60))
        entry = TimeEntry(
            user_id=user.id,
            project_id=timer.project_id,
            issue_id=timer.issue_id,
            date=date.today(),
            duration_minutes=minutes,
            notes=payload.get("notes"),
        )
        session.add(entry)
        session.commit()
        return {"stopped": True, "duration_minutes": minutes, "entry_id": entry.id}


@api.get("/timer/status")
def timer_status(request: Request):
    user = current_user(request)
    with get_session() as session:
        timer = session.exec(
            select(Timer).where(Timer.user_id == user.id, Timer.running)
        ).first()
        if not timer:
            return {"running": False}
        issue = session.get(Issue, timer.issue_id)
        elapsed = int((datetime.utcnow() - timer.start_ts).total_seconds())
        return {
            "running": True,
            "issue_id": issue.id,
            "issue_title": issue.title,
            "elapsed_seconds": elapsed,
        }


@api.get("/reports/week")
def weekly_report(
    week_start: Optional[str] = None,
    project_id: Optional[int] = None,
    user_id: Optional[int] = None,
    label: Optional[str] = None,
    assignee: Optional[str] = None,
):
    ws = (
        date.fromisoformat(week_start)
        if week_start
        else (date.today() - timedelta(days=date.today().weekday()))
    )
    return weekly_aggregate(ws, project_id, user_id, label, assignee)


@api.get("/reports/week.pdf")
def weekly_report_pdf(
    week_start: Optional[str] = None,
    project_id: Optional[int] = None,
    user_id: Optional[int] = None,
    label: Optional[str] = None,
    assignee: Optional[str] = None,
):
    ws = (
        date.fromisoformat(week_start)
        if week_start
        else (date.today() - timedelta(days=date.today().weekday()))
    )
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    weekly_pdf(path, ws, project_id, user_id, label, assignee)
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"weekly-{ws.isoformat()}.pdf",
    )


@api.post("/github/refresh")
async def github_refresh(request: Request):
    user = request.cookies.get("user_id")
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")
    # Run the import asynchronously
    await import_all()
    return {"ok": True, "message": "GitHub issues refreshed"}
