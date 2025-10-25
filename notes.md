# FastAPI Setup & Concepts Guide

## Why FastAPI Needs a Separate Server

**Node.js** and **Django** come with built-in web servers, so you just code and start the server. But **FastAPI** (like PHP with XAMPP) requires installing a separate server — here we use **Uvicorn**.

---

## Virtual Environments: Isolating Dependencies

If you run `pip install fastapi` directly, it installs **globally** — meaning every project on your PC gets that version. This creates conflicts.

**Solution:** Use **virtual environments** to isolate dependencies per project.

### Creating & Activating a Virtual Environment

```bash
# Create virtual environment
python -m venv myenv

# Activate (Windows)
myenv\Scripts\activate.bat

# Deactivate
deactivate
```

**Analogy:**
- `myenv/` or `env/` → like `node_modules` (stores packages locally)
- `requirements.txt` → like `package.json` (lists dependencies)

---

## Managing Dependencies with requirements.txt

**Don't write `requirements.txt` manually.** Generate it automatically:

```bash
pip freeze > requirements.txt
```

This captures **exact versions** of all installed packages. Run this after finishing or updating your project.

### For others to replicate your environment:

```bash
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
```

---

## Client-Server Communication: The Basics

### Server Types
- **File Server** → sends files via FTP/SFTP
- **Web Server** → sends data in HTML/JSON via HTTP/HTTPS
- **Mail Server** → handles emails

### Language-Independent Communication

It doesn't matter if the client is built in JavaScript and the server in Python — they can still communicate because they share data through a **common format: JSON**.

**JS ↔ Python** works because they talk over **JSON**.

---

## REST APIs: How Data Flows

We send the **current state of data** between client and server in a **representational format** (JSON). This happens through **endpoints**.

- **Client hits an endpoint** to get or send data
- We need a **protocol** (HTTP/HTTPS) for standardized communication
- HTTP provides **clear direction** on how to perform CRUD operations

### HTTP Methods (Standard CRUD)
- **GET** → Read
- **POST** → Create
- **PUT** → Update
- **DELETE** → Delete

This standardization ensures **unified communication** regardless of language or version.

---

## Running FastAPI with Uvicorn

```bash
uvicorn main:app --reload
```

- `main` = your Python file (main.py)
- `app` = FastAPI instance variable
- `--reload` = auto-restart on code changes

---

## Pydantic: Data Validation & Conversion

**Pydantic** is a Python package for data validation and conversion.

When you call `Product(...)`, Pydantic's **auto-generated `__init__`** runs:
1. Validates input data using type hints
2. Converts data to correct types
3. Creates an instance if valid, otherwise raises `ValidationError`

---

## Swagger: Built-in API Documentation

**Swagger** is an API documentation tool — like GraphQL's built-in UI for testing.

- Provides a **clean UI to test REST APIs**
- Works with both REST and GraphQL
- In frameworks like Node.js, Django, or Next.js, you must configure Swagger manually (add paths, etc.)
- **FastAPI comes with Swagger built-in** — no configuration needed!

**Why use Swagger over Postman?**
- Swagger provides **interactive documentation** — anyone can test the API directly from the docs without installing anything
- Postman requires installation and manual request setup