from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from auth import auth_router
from users import users_router
from groups import groups_router
from feedback import feedback_router
from reports import reports_router
from audit import audit_router

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# ✅ CORS FIX (THIS IS THE IMPORTANT PART)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Backend running"}

# Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(groups_router)
app.include_router(feedback_router)
app.include_router(reports_router)
app.include_router(audit_router)
