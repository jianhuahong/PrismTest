from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    key: str = Field(pattern=r"^[a-z][a-z0-9-]{1,31}$")


class ProjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class MemberCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    role: str


class ProjectOut(BaseModel):
    id: int
    name: str
    key: str
    owner_id: int
    my_role: str
    can_write: bool


class MemberOut(BaseModel):
    user_id: int
    username: str
    role: str
