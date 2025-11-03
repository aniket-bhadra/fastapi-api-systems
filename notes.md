# FastAPI Setup & Concepts Guide

## Why FastAPI Needs a Separate Server

### Web Server Architecture: 3-Layer System

**Layer 1: Server (Network/HTTP Handler)**
- Handles raw HTTP connections, manages TCP/IP, parses HTTP protocol
- Examples: Uvicorn, Gunicorn, Nginx

**Layer 2: Interface/Gateway (Converter)**
- Converts between HTTP and Python objects (standardized format)
- Standards: WSGI (sync) or ASGI (async) — just specifications, not software you install
- Both server and framework follow this standard to communicate

**Layer 3: Application (Your Code)**
- Business logic, routing, database, validation
- Examples: Django, FastAPI

**How it works:**
When HTTP request comes → Server passes it to Interface → Interface converts HTTP to Python dict and calls Application as a function with that dict as argument → Application processes and returns response → Interface converts response back to HTTP → Server sends to user

**Why separate layers?**
- Swap servers without changing code
- Use same server for different frameworks
- Scale and optimize each layer independently


**Django:**
- WSGI/ASGI passes request to application as dictionary (environ for WSGI, scope for ASGI)
- URL routing directs to appropriate view function  
- View function processes and returns HttpResponse object
- WSGI/ASGI converts back to HTTP response

**FastAPI:**
- ASGI passes request to application as dictionary (scope)
- FastAPI converts request data to Python types using type hints
- Router calls the appropriate path operation function
- Function returns Python objects - FastAPI automatically serializes to JSON using Pydantic

So no manual conversion like `req.json()` in Node.js or `JsonResponse` in Django. Just return Python object from each function → FastAPI automatically converts to JSON & hands over this JSON to ASGI → ASGI converts to HTTP response and hands over to server → server sends to user

### Framework Comparison

**Node.js:**
- Runtime environment with built-in `http` module
- Creates server directly: `http.createServer(...).listen(3000)`
- **No separate server layer** — server and application run together
- Express.js wraps this built-in server
- Next.js inherits Node's HTTP server capabilities

**Django:**
- Comes with development server: `python manage.py runserver`
- Production: Install Gunicorn (WSGI) or Uvicorn/Daphne (ASGI)
- **Uses separate server layer** (WSGI/ASGI architecture)
- Supports both sync (default) and async (since v3.1)

**FastAPI:**
- Lightweight, no built-in server
- Development & Production: Install ASGI server (Uvicorn, Hypercorn)
- **Uses separate server layer** (ASGI architecture)
- Async-first (designed for async from ground up)

**Key takeaway:** 
- Node.js/Express/Next.js have **integrated server** (no separate layer)
- Django and FastAPI use **separate server layer** architecture (WSGI/ASGI). Django includes a convenience development server; FastAPI requires you to choose your own ASGI server from the start. Both need production servers installed separately.

---

### Synchronous vs Asynchronous

**Synchronous (Blocking):**
```python
def get_data(request):
    user = fetch_from_database()     # Waits 2 sec - does nothing
    weather = fetch_from_api()       # Waits 3 sec - does nothing
    return JsonResponse({"user": user, "weather": weather})
# Total: 5 seconds, cannot handle other requests while waiting
```

**Asynchronous (Non-blocking):**
```python
async def get_data(request):
    user = await fetch_from_database()     # Waits 2 sec - handles other requests
    weather = await fetch_from_api()       # Waits 3 sec - handles other requests
    return {"user": user, "weather": weather}
# Total: 5 seconds, BUT handles 100s of other requests during waits
```

**Difference:**
- **Sync:** 1 request at a time, waits idle
- **Async:** Many requests at once, no idle waiting

**Why FastAPI is faster:** Built for async from day one (optimized for I/O-heavy operations like database, API calls, file operations). Django added async support later as a retrofit. FastAPI handles thousands of requests without blocking.

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
- **File Server** → sends files in their original format (PDF, images, videos, etc.) via FTP/FTPS
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

This standardization ensures **unified communication** regardless of language or version. ex - GET → Read, POST → Create,PUT → Update

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
- Swagger provides **more interactive documentation** — anyone can test the API directly from the docs without installing anything
- Postman requires installation and manual request setup