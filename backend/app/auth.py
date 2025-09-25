from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import select
import os, httpx
from .database import get_session
from .models import User

router = APIRouter()
CLIENT_ID = os.getenv('GITHUB_OAUTH_CLIENT_ID')
CLIENT_SECRET = os.getenv('GITHUB_OAUTH_CLIENT_SECRET')
DOMAIN = os.getenv('DOMAIN')

# Only these GitHub usernames are allowed to log in
ALLOWED_USERS = {"David-XY", "domi413"}

@router.get("/auth/me")
def me(request: Request):
    uid = request.cookies.get("user_id")
    if not uid:
        return {"user": None}
    session = next(get_session())
    user = session.get(User, int(uid))
    if not user or user.username not in ALLOWED_USERS:
        return {"user": None}
    return {"user": {"id": user.id, "username": user.username, "email": user.email}}

@router.get("/auth/github/login")
def github_login():
    redirect_uri = f"https://{DOMAIN}/auth/github/callback"
    url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={redirect_uri}&scope=read:user"
    return RedirectResponse(url)

@router.get("/auth/github/callback")
async def github_callback(code: str, request: Request):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://github.com/login/oauth/access_token",
            data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code},
            headers={"Accept": "application/json"}
        )
        data = r.json()

    token = data.get("access_token")
    if not token:
        raise HTTPException(status_code=400, detail="OAuth failed")

    async with httpx.AsyncClient() as client:
        u = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"}
        )
        ud = u.json()

    github_id = str(ud["id"])
    username = ud.get("login")
    email = ud.get("email") or f"{username}@users.noreply.github.com"

    # enforce whitelist before creating/allowing user
    if username not in ALLOWED_USERS:
        raise HTTPException(status_code=403, detail="Not authorized")

    session = next(get_session())
    user = session.exec(select(User).where(User.github_id == github_id)).first()
    if not user:
        user = User(username=username, email=email, github_id=github_id)
        session.add(user)
        session.commit()
        session.refresh(user)

    resp = RedirectResponse(url=f"https://app.{DOMAIN}/")
    resp.set_cookie("user_id", str(user.id), httponly=True, secure=True, samesite="lax")
    return resp
