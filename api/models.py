from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from api.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    reports = relationship("Report", back_populates="user")
    search_history = relationship("SearchHistory", back_populates="user")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    drug = Column(String)
    reaction = Column(String)
    age = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    timestamp = Column(String, default=lambda: datetime.now().isoformat())

    user = relationship("User", back_populates="reports")

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    drug = Column(String)
    timestamp = Column(String, default=lambda: datetime.now().isoformat())

    user = relationship("User", back_populates="search_history")
