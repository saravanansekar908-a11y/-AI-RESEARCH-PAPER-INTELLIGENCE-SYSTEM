from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class PaperOut(BaseModel):
    id: int
    title: str
    authors: str | None = None
    publication_year: int | None = None
    topic: str | None = None
    filename: str
    file_size: int
    page_count: int
    status: str
    extraction_error: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SummaryRequest(BaseModel):
    detail_level: str = Field(default="medium", pattern="^(short|medium|detailed)$")


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    session_id: int | None = None


class CompareRequest(BaseModel):
    paper_ids: list[int] = Field(min_length=2, max_length=6)


class LiteratureRequest(BaseModel):
    paper_ids: list[int] = Field(min_length=1, max_length=10)
    title: str = Field(min_length=3, max_length=500)

