"""
Request/response schemas. Validation lives here so bad input is rejected
before it ever touches the email or database layer.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator


class ContactFormRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=10, max_length=2000)

    # Honeypot field: invisible to real users via CSS, but bots that
    # auto-fill every input will populate it. Any non-empty value = spam.
    website: str = Field(default="", max_length=200)

    @field_validator("name", "message")
    @classmethod
    def strip_and_check_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field cannot be blank.")
        return v


class ContactFormResponse(BaseModel):
    success: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    environment: str
