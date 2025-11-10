from fastapi import FastAPI, status, Cookie, Header, Request
from pydantic import BaseModel
from typing import Annotated

app = FastAPI()


class UserINDB(BaseModel):
    id: int
    name: str
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str


user1 = UserINDB(
    id=1, name="robin pandey", email="robin@gmail.com", password="1245hin575#&"
)


@app.get("/user", response_model=UserOut)
async def get_user():
    return user1


# status code
@app.post("/user", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserOut):
    return {"msg": "created successfully", "user": user}


# optional query parameter
@app.get("/get")
async def get_id(id: int = None):
    return id
