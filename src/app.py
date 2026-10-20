"""
High School Management System API

A super simple FastAPI application that lets students view activities and
authorized staff manage extracurricular activity sign-ups.
"""

import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

SESSION_COOKIE = "teacher_session"
SESSION_DURATION = 8 * 60 * 60


class TeacherLogin(BaseModel):
    username: str
    password: str


def get_session_secret() -> str | None:
    return os.environ.get("SESSION_SECRET")


def get_teacher_credentials() -> dict[str, str] | None:
    configured_credentials = os.environ.get("TEACHER_CREDENTIALS")
    if configured_credentials is None:
        return None

    try:
        credentials = json.loads(configured_credentials)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail="Teacher credentials are not valid JSON",
        ) from exc

    if (
        not isinstance(credentials, dict)
        or not credentials
        or any(
            not isinstance(username, str)
            or not username
            or not isinstance(password, str)
            or not password
            for username, password in credentials.items()
        )
    ):
        raise HTTPException(
            status_code=500,
            detail="Teacher credentials must be a non-empty username/password object",
        )

    return credentials


def create_session_token(username: str, secret: str) -> str:
    payload = json.dumps(
        {"username": username, "expires": int(time.time()) + SESSION_DURATION},
        separators=(",", ":"),
    ).encode()
    encoded_payload = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    signature = hmac.new(
        secret.encode(), encoded_payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def get_session_username(token: str | None, secret: str | None) -> str | None:
    if not token or not secret:
        return None

    try:
        encoded_payload, signature = token.split(".", 1)
        expected_signature = hmac.new(
            secret.encode(), encoded_payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None

        payload = base64.urlsafe_b64decode(
            encoded_payload + "=" * (-len(encoded_payload) % 4)
        )
        session = json.loads(payload)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError, binascii.Error):
        return None

    if (
        not isinstance(session, dict)
        or not isinstance(session.get("username"), str)
        or not isinstance(session.get("expires"), int)
        or session["expires"] <= int(time.time())
    ):
        return None

    return session["username"]


def require_teacher(
    teacher_session: Annotated[str | None, Cookie()] = None,
) -> str:
    username = get_session_username(teacher_session, get_session_secret())
    if username is None:
        raise HTTPException(
            status_code=401,
            detail="Teacher login required",
        )
    return username


# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.get("/auth/status")
def get_auth_status(
    teacher_session: Annotated[str | None, Cookie()] = None,
):
    return {
        "authenticated": get_session_username(
            teacher_session, get_session_secret()
        ) is not None
    }


@app.post("/auth/login")
def login(credentials: TeacherLogin, response: Response):
    teacher_credentials = get_teacher_credentials()
    session_secret = get_session_secret()

    if teacher_credentials is None or session_secret is None:
        raise HTTPException(
            status_code=503,
            detail="Teacher login is not configured",
        )

    password = teacher_credentials.get(credentials.username)
    if password is None or not hmac.compare_digest(password, credentials.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(credentials.username, session_secret),
        max_age=SESSION_DURATION,
        httponly=True,
        secure=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
        samesite="strict",
        path="/",
    )
    return {"message": "Logged in successfully"}


@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
        samesite="strict",
        path="/",
    )
    return {"message": "Logged out successfully"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    _: Annotated[str, Depends(require_teacher)],
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    _: Annotated[str, Depends(require_teacher)],
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
