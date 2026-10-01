from pydantic import BaseModel, ConfigDict, EmailStr


class EmployeeResponse(BaseModel):
    id: int
    employee_code: str
    first_name: str
    last_name: str
    email: EmailStr
    department_id: int
    designation: str
    manager_id: int | None
    status: str

    model_config = ConfigDict(from_attributes=True)