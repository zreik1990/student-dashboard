from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from database import SessionLocal, engine
import models
from auth import verify_password, create_token, hash_password

# ======================================================
# APP INIT
# ======================================================

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Student Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# DB DEPENDENCY
# ======================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ======================================================
# AUDIT LOGGER
# ======================================================

def audit(db: Session, username: str, action: str):
    log = models.AuditLog(
        username=username,
        action=action,
        timestamp=datetime.now().strftime("%d/%m/%Y %I:%M %p")
    )
    db.add(log)
    db.commit()

# ======================================================
# AUTO CREATE ADMIN
# ======================================================

@app.on_event("startup")
def create_admin():
    db = SessionLocal()

    if not db.query(models.User).filter_by(username="admin").first():
        admin = models.User(
            username="admin",
            password=hash_password("Admin@12345"),
            first_name="System",
            last_name="Administrator",
            role="admin",
            group_name="Administration",
            is_active=1
        )
        db.add(admin)
        db.commit()

    db.close()

# ======================================================
# AUTH
# ======================================================

@app.post("/login")
def login(data: dict, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(
        username=data.get("username")
    ).first()

    if not user or not verify_password(data.get("password"), user.password):
        raise HTTPException(401, "Invalid credentials")

    if not user.is_active:
        raise HTTPException(403, "Account disabled")

    audit(db, user.username, "Logged in")

    return {
        "token": create_token(user.username),
        "username": user.username,
        "role": user.role,
        "group": user.group_name
    }

@app.post("/logout")
def logout(data: dict, db: Session = Depends(get_db)):
    audit(db, data.get("username"), "Logged out")
    return {"status": "ok"}

# ======================================================
# AUDIT
# ======================================================

@app.post("/audit")
def audit_event(data: dict, db: Session = Depends(get_db)):
    audit(db, data.get("username"), data.get("action"))
    return {"status": "logged"}

@app.get("/audit")
def get_audit(db: Session = Depends(get_db)):
    return db.query(models.AuditLog).order_by(
        models.AuditLog.id.desc()
    ).all()

# ======================================================
# FEEDBACK
# ======================================================

@app.post("/feedback")
def submit_feedback(data: dict, db: Session = Depends(get_db)):
    timestamp = datetime.now().strftime("%d/%m/%Y %I:%M %p")

    fb = models.Feedback(
        username=data["username"],
        group_name=data["group"],
        subject=data["subject"],
        level=data["level"],
        problems=data["problems"],
        notes=data["notes"],
        created_at=timestamp
    )
    db.add(fb)
    db.commit()

    audit(db, data["username"], "Submitted feedback")
    return {"status": "success"}

# ======================================================
# USERS
# ======================================================

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.post("/users/create")
def create_user(data: dict, db: Session = Depends(get_db)):
    if db.query(models.User).filter_by(username=data["username"]).first():
        raise HTTPException(400, "User already exists")

    user = models.User(
        username=data["username"],
        password=hash_password(data["password"]),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        role=data.get("role"),
        group_name=data.get("group"),
        is_active=1
    )

    db.add(user)
    db.commit()

    audit(db, "admin", f'Created user "{data["username"]}"')
    return {"status": "created"}

@app.post("/users/update")
def update_user(data: dict, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(
        username=data.get("username")
    ).first()

    if not user:
        raise HTTPException(404, "User not found")

    if data.get("first_name") is not None:
        user.first_name = data.get("first_name")

    if data.get("last_name") is not None:
        user.last_name = data.get("last_name")

    if data.get("role") is not None:
        user.role = data.get("role")

    if data.get("group") is not None:
        user.group_name = data.get("group")

    if data.get("password"):
        user.password = hash_password(data.get("password"))

    db.commit()

    audit(db, "admin", f'Updated user "{user.username}"')
    return {"status": "updated"}

@app.post("/users/toggle")
def toggle_user(data: dict, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(
        username=data["username"]
    ).first()

    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = 0 if user.is_active else 1
    db.commit()

    audit(db, "admin", f'Toggled user "{user.username}"')
    return {"status": "updated"}

@app.post("/users/delete")
def delete_user(data: dict, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(
        username=data["username"]
    ).first()

    if not user:
        raise HTTPException(404, "User not found")

    db.delete(user)
    db.commit()

    audit(db, "admin", f'Deleted user "{data["username"]}"')
    return {"status": "deleted"}

# ======================================================
# GROUPS
# ======================================================

@app.get("/groups")
def get_groups(db: Session = Depends(get_db)):
    return db.query(models.Group).all()

@app.get("/groups/active")
def get_active_groups(db: Session = Depends(get_db)):
    return db.query(models.Group).filter(
        models.Group.is_active == 1
    ).all()

@app.post("/groups/create")
def create_group(data: dict, db: Session = Depends(get_db)):
    name = data.get("group", "").strip()

    if not name:
        raise HTTPException(400, "Group name required")

    if db.query(models.Group).filter_by(group_name=name).first():
        raise HTTPException(400, "Group already exists")

    group = models.Group(group_name=name, is_active=1)
    db.add(group)
    db.commit()

    audit(db, "admin", f'Created group "{name}"')
    return {"status": "created"}

@app.post("/groups/toggle")
def toggle_group(data: dict, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter_by(
        group_name=data["group"]
    ).first()

    if not group:
        raise HTTPException(404, "Group not found")

    group.is_active = 0 if group.is_active else 1
    db.commit()

    audit(db, "admin", f'Toggled group "{group.group_name}"')
    return {"status": "updated"}

@app.post("/groups/delete")
def delete_group(data: dict, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter_by(
        group_name=data["group"]
    ).first()

    if not group:
        raise HTTPException(404, "Group not found")

    db.delete(group)
    db.commit()

    audit(db, "admin", f'Deleted group "{data["group"]}"')
    return {"status": "deleted"}

# ======================================================
# REPORTS (DATE & TIME SPLIT)
# ======================================================

@app.get("/reports")
def get_reports(db: Session = Depends(get_db)):
    results = (
        db.query(
            models.Feedback.created_at,
            models.Feedback.username,
            models.User.first_name,
            models.User.last_name,
            models.Feedback.group_name,
            models.Feedback.subject,
            models.Feedback.level,
            models.Feedback.problems,
            models.Feedback.notes
        )
        .join(models.User, models.User.username == models.Feedback.username)
        .order_by(models.Feedback.id.desc())
        .all()
    )

    output = []

    for r in results:
        date_part, time_part = r.created_at.split(" ", 1)

        output.append({
            "date": date_part,
            "time": time_part,
            "username": r.username,
            "first_name": r.first_name,
            "last_name": r.last_name,
            "group_name": r.group_name,
            "subject": r.subject,
            "level": r.level,
            "problems": r.problems,
            "notes": r.notes
        })

    return output

# ======================================================
# HEALTH CHECK
# ======================================================

@app.get("/")
def root():
    return {"status": "Backend running"}
