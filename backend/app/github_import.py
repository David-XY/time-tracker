import os, httpx, traceback
from sqlmodel import select
from .database import get_session
from .models import Project, Issue

GITHUB_PAT = os.getenv("GITHUB_PAT")
DEFAULT_REPOS = ["domi413/vhdl-fmt", "domi413/vhdl-fmt-doc"]

async def import_repo(repo: str):
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_PAT:
        headers["Authorization"] = f"token {GITHUB_PAT}"

    print(f"[import_repo] Starting import for {repo}")

    try:
        async with httpx.AsyncClient() as client:
            page = 1
            items = []
            while True:
                url = f"https://api.github.com/repos/{repo}/issues?state=all&per_page=100&page={page}"
                print(f"[import_repo] Fetching {url}")
                r = await client.get(url, headers=headers)
                if r.status_code != 200:
                    print(f"[import_repo] ERROR {r.status_code}: {r.text}")
                    r.raise_for_status()
                batch = r.json()
                if not batch:
                    break
                items.extend(batch)
                print(f"[import_repo] Got {len(batch)} issues on page {page}")
                page += 1

        session = next(get_session())
        project = session.exec(select(Project).where(Project.github_repo == repo)).first()
        if not project:
            project = Project(name=repo.split('/')[-1], github_repo=repo)
            session.add(project)
            session.commit()
            session.refresh(project)
            print(f"[import_repo] Created new project {project.name}")

        for it in items:
            if "pull_request" in it:
                continue
            labels = [l.get("name") for l in it.get("labels", [])]
            assignee = (it.get("assignee") or {}).get("login")
            existing = session.exec(
                select(Issue).where(Issue.project_id == project.id).where(Issue.github_number == it["number"])
            ).first()
            if existing:
                existing.title = it["title"]
                existing.body = it.get("body")
                existing.url = it["html_url"]
                existing.state = it.get("state", "open")
                existing.labels = labels
                existing.assignee = assignee
                print(f"[import_repo] Updated issue #{it['number']}: {it['title']}")
            else:
                session.add(Issue(
                    project_id=project.id,
                    github_number=it["number"],
                    title=it["title"],
                    body=it.get("body"),
                    url=it["html_url"],
                    state=it.get("state", "open"),
                    labels=labels,
                    assignee=assignee
                ))
                print(f"[import_repo] Added new issue #{it['number']}: {it['title']}")
        session.commit()
        print(f"[import_repo] Finished import for {repo}, total {len(items)} issues processed")

    except Exception as e:
        print(f"[import_repo] FAILED for {repo}: {e}")
        traceback.print_exc()

async def import_all(repos=None):
    repos = repos or DEFAULT_REPOS
    for r in repos:
        await import_repo(r)
