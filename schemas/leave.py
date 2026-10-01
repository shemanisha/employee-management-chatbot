from datetime import date

from pydantic import BaseModel, Field


class LeaveRequestCreate(BaseModel):
    leave_type: str = Field(min_length=2, max_length=10)
    start_date: date
    end_date: date
    reason: str | None = Field(default=None, max_length=500)