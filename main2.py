from fastapi import FastAPI, status, Cookie, Header, Request, Form, HTTPException
from pydantic import BaseModel
from typing import Annotated

from admin.routers import router as admin_routers

app = FastAPI()

app.include_router(admin_routers, prefix="/admin", tags=["Admin"])


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


# how to access cookie from client & make it optional
@app.get("/users")
async def get_info(info: Annotated[str | None, Cookie()] = None):
    if info:
        return info + " cookie send from server"
    return "no cookie found"


# access custom req header


@app.get("/headers")
async def get_info(info: Annotated[str | None, Header()] = None):
    if info:
        return info + " header send from server"
    return "no header found"


@app.get("/allHeaders")
async def get_all_headers(req: Request):
    return req.headers


# handle formdata
# @app.post("/login")
# async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
#     return f"hi {username} welcome!! your password started with {password[0]}****"


@app.get("/allHeaders")
async def get_all_headers(req: Request):
    return req.headers


## middleware
@app.middleware("http")
async def validator(req: Request, call_next):
    print("middleware executing before req")
    res = await call_next(req)
    print("after req, middleware execution")
    return res


@app.get("/testing")
async def testing():
    print("inside testing")
    return "tested tested"


@app.get("/user/{user_id}")
async def get_user(user_id: int):
    if user_id >= 5:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found"
        )
    return {"user": f"hi {user_id}, how are you?"}


@app.get("/players/{id}", tags=["players"])
def get_player(id: int):
    return {"player_id": id}


@app.get("/players/special", tags=["players"])
def special_player():
    return {"message": "hi player"}
