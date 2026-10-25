from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    field_validator,
    model_validator,
)


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

    @field_validator(
        "first_name",
        "last_name",
        "department_id",
        "designation",
        mode="before",
    )
    @classmethod
    def reject_null_required_fields(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self
