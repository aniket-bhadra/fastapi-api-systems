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

*but*

- **Server** = Physical software ✅ Ex: Uvicorn, Gunicorn
- **Application** = Physical software ✅ Ex: FastAPI, Django
- **ASGI/WSGI** = Just a standard/protocol (like HTTP, USB-C) — NOT separate software you install, it's a contract that both parties follow

**Analogy:** Phone and charger both follow USB-C standard — rules about pin size, voltage, data transfer. USB-C itself isn't a physical thing; it's a specification that phone manufacturers and charger manufacturers implement.

**Similarly, ASGI/WSGI is a specification:**
- **Uvicorn** has ASGI implementation built-in → knows how to create `scope` dictionary and call app
- **FastAPI** has ASGI implementation built-in → knows how to receive `scope` dictionary and respond

**Result:** ASGI/WSGI rules are built INTO both server and framework, allowing them to communicate in a standardized format.

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

but ASGI gives a Python dictionary, so why does FastAPI need to "convert request data to Python types"?

## What Actually Happens

**Step 1: ASGI hands over dictionary**
```python
# ASGI gives FastAPI something like this:
scope = {
    "type": "http",
    "method": "POST",
    "path": "/users",
    "query_string": b"age=25&name=John",
    "headers": [...],
    "body": b'{"email": "test@example.com", "age": "25"}'  # Raw bytes/strings
}
```

**Step 2: FastAPI converts using type hints**

When you write:
```python
@app.post("/users")
async def create_user(email: str, age: int):  # Type hints here
    return {"email": email, "age": age}
```

FastAPI looks at your type hints (`email: str, age: int`) and:

1. **Extracts data** from the ASGI dictionary (from body, query params, path, etc.)
2. **Validates types** - checks if `age` can be converted to `int`
3. **Converts** - turns `"25"` (string) into `25` (integer)
4. **Passes clean data** to your function

## Visual Example

```python
# What ASGI gives (raw):
body = '{"email": "test@example.com", "age": "25"}'  # Everything is STRING

# What FastAPI does with type hints:
@app.post("/users")
async def create_user(email: str, age: int):  # You specify: age should be INT
    # FastAPI automatically:
    # 1. Parses JSON from body
    # 2. Sees age: int in your function
    # 3. Converts "25" (string) → 25 (integer)
    # 4. Validates it's a valid integer
    # 5. Passes to your function
    
    print(type(age))  # <class 'int'> - already converted!
    return {"email": email, "age": age}
```

## Without FastAPI (Manual Work)

In Node.js or plain Python, you'd do:
```python
def create_user(request_dict):
    body = json.loads(request_dict['body'])  # Manual parse
    email = body['email']
    age = int(body['age'])  # Manual conversion
    # Manual validation...
```

## With FastAPI (Automatic)

```python
async def create_user(email: str, age: int):
    # FastAPI already did all the work!
    # email is str, age is int - guaranteed
```

---

**Summary:** ASGI gives raw dictionary with bytes/strings. FastAPI reads your type hints, extracts data from that dictionary, validates, converts types, and hands you clean, typed Python objects in your function parameters.

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

## "Why does the 5th product show up in Swagger after POST but not in my Python file, and how does using JSON solve this problem?"

When you POST a new product → it goes into RAM (memory)
When you GET all products → you see it (it's in RAM)
When you look at this file → no change (RAM ≠ File)

The file is NOT the database! The file is just the code. It ran once when the server started.

Why it works in Swagger but not in file:

Swagger talks to the running server (RAM)
The file is just source code (not connected to RAM)
You need to explicitly save RAM → File

To save RAM state to file so that it's stored permanently we use .json files
```python
def add_product(product: Product):
    products.append(product)        # Step 1: Add to RAM
    
    # Step 2: Save RAM → File
    with open("products.json", "w") as f:  # Open file for Writing
        json.dump(products, f)              # Dump (write) RAM data into file
    
    return products
```

To save to file: You MUST explicitly write it using open() and json.dump()

What json.dump() does:
- Takes data from RAM (products list)
- Converts it to JSON text format
- Writes it to the file (products.json)

So in JSON it works because after the products got added to RAM, we take that updated list from RAM and overwrite the existing content in the .json file with this list - this is why it works.

Normally with a list in a .py file it won't work because there's no simple way to modify just the list variable in the Python source file. Even if we tried, we'd have to put the list in a completely separate file so that when we overwrite it with the new updated list from RAM, the other code doesn't get lost. So we'd have to put that in a separate file, but still this is complex and not a good approach.

For this use JSON since it's lightweight, performs better, and is widely used so it's trustworthy.

In case of json-server in npm/JS, that package does the same thing - it syncs the file that we watch with the package with RAM state. Whenever that RAM state gets updated, it updates that watched file - this is how we see the updated file.

So anyway, if we want to see the updated state from RAM reflected in a file also, we must explicitly read the RAM state and sync it with the file. If we don't do that, this won't automatically happen. This is why normally we don't see the products array get automatically populated with new products in the source file like it does in RAM.

When we restart the server, the RAM state gets cleared and initialized again, so that data will be gone. So we must sync that RAM state with a file so that the data persists. We have to do it manually and explicitly.

so,
The reason we don't see the updated list in the source code is because the source code runs once when the server starts. After that, the source code and the running entity (process) created from it are two completely different things.

The running process exists in RAM with its own state. If we want to see changes reflected in the source code file itself, we have to explicitly write to that file while the process is running. It's not automatic — just because the running entity came from the source code doesn't mean it will update the source file. The source code and the running process are completely separate. Only if the running process explicitly writes to the source code file will we see changes there.

### type hints
So in case of Python, type hints are ignored at compile and runtime — they're used to tell what developers expect and for IDE support, but not enforced. In case of TypeScript, it enforces at compile time.
But in case of FastAPI, it uses Pydantic which reads type hints and enforces validation at runtime, so in that case it strictly checks and throws error if it gets something which is not defined.