from pydantic import BaseModel, EmailStr


class EmployeeIn(BaseModel):
    name: str
    email: str
    department: str
    role: str = "Employee"


class EmployeeOut(BaseModel):
    id: int
    name: str
    email: str
    department: str
    role: str
    status: str

    model_config = {"from_attributes": True}
