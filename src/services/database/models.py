import json
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from src.config import DEFAULT_LANGUAGE


class User(BaseModel):
    """Defines User object from database"""
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    language: str = DEFAULT_LANGUAGE
    cv_file_id: Optional[str] = None
    cv_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class UserSkill(BaseModel):
    """Defines User Skill object from database"""
    name: str
    level: str = "Junior"
    experience_years: float = 0.0


class UserSettings(BaseModel):
    """Defines User Settings object from database"""
    id: int
    user_id: int
    skills: List[UserSkill] = []
    grade: Optional[str] = None  # Intern/Junior/Middle and etc
    job_type: Optional[str] = None  # Such as Remote, Full-time
    location: Optional[str] = None  # If specified - country/city
    updated_at: Optional[datetime] = None

    @field_validator('skills', mode='before')
    @classmethod
    def decode_json_skills(cls, v: Any) -> List[Dict[str, Any]]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v
