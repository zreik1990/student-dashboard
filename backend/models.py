from sqlalchemy import Column, Integer, String, Text
from database import Base


class User(Base):
    __tablename__ = "users"

    username = Column(String(50), primary_key=True)
    password = Column(String(255))
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(20))
    group_name = Column(String(100))
    is_active = Column(Integer, default=1)


class Group(Base):
    __tablename__ = "groups"

    group_name = Column(String(100), primary_key=True)
    is_active = Column(Integer, default=1)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    group_name = Column(String(100))
    subject = Column(String(100))
    level = Column(String(20))
    problems = Column(Text)
    notes = Column(Text)
    created_at = Column(String(30))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50))
    action = Column(Text)
    timestamp = Column(String(40))
