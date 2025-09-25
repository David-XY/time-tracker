from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, List
from datetime import datetime, date

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    github_id: Optional[str] = None
    role: str = "user"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    github_repo: Optional[str] = None

class Issue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    github_number: Optional[int] = None
    title: str
    body: Optional[str] = None
    url: Optional[str] = None
    state: str = "open"
    assignee: Optional[str] = None
    labels: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))

class TimeEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    project_id: int = Field(foreign_key="project.id")
    issue_id: int = Field(foreign_key="issue.id")
    date: date
    duration_minutes: int
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Timer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    project_id: int = Field(foreign_key="project.id")
    issue_id: int = Field(foreign_key="issue.id")
    start_ts: datetime = Field(default_factory=datetime.utcnow)
    running: bool = True
