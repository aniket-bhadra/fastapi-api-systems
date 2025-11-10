from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class UserINDB(BaseModel):
    id: int
    name: str
    email: str
    password: str


user1 = UserINDB(
    id=1, name="robin pandey", email="robin@gmail.com", password="1245hin575#&"
)

print(user1)
