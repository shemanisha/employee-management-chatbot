from pydantic import BaseModel, ConfigDict, EmailStr


class EmployeeCreateRequest(BaseModel):
    employee_code: str
    firstname: str
    lastname: str
    email: EmailStr
    department_id: int
    designation: str
    manager_id: int | None = None


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

class EmployeeUpdateRequest(BaseModel):

    first_name: str | None = None

    last_name: str | None = None

    department_id: int | None = None

    designation: str | None = None

    manager_id: int | None = None