from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()
templates = Jinja2Templates(directory="template")

data = ["rohit", "virat", "Hardik"]


@app.get("/", response_class=HTMLResponse)
async def home(req: Request):
    return templates.TemplateResponse("index.html", {"request": req, "data": data})
