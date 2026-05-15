# FastAPI Setup & Concepts Guide

## Table of Contents

1. [Why FastAPI Needs a Separate Server](#why-fastapi-needs-a-separate-server)
   - [Web Server Architecture: 3-Layer System](#web-server-architecture-3-layer-system)
   - [What Actually Happens (ASGI Flow)](#what-actually-happens-asgi-flow)
   - [Visual Example](#visual-example)
   - [Without FastAPI (Manual Work)](#without-fastapi-manual-work)
   - [With FastAPI (Automatic)](#with-fastapi-automatic)
   - [Framework Comparison](#framework-comparison)
2. [Synchronous vs Asynchronous](#synchronous-vs-asynchronous)
   - [Blocking vs Non-Blocking Code](#blocking-vs-non-blocking-code)
   - [Is ASGI Faster as a Specification?](#is-asgi-faster-as-a-specification)
   - [ASGI Request Flow: Uvicorn and FastAPI](#asgi-request-flow-uvicorn-and-fastapi)
   - [How FastAPI Validates Parameters](#how-fastapi-validates-parameters)
   - [Concurrent Request Handling in ASGI](#concurrent-request-handling-in-asgi)
   - [When Does the Event Loop Start?](#when-does-the-event-loop-start)
   - [WSGI Request Flow: Gunicorn and Django](#wsgi-request-flow-gunicorn-and-django)
   - [Concurrent Request Handling in WSGI](#concurrent-request-handling-in-wsgi)
   - [ASGI vs WSGI: Key Differences](#asgi-vs-wsgi-key-differences)
   - [Visual Comparison](#visual-comparison)
   - [Why ASGI Is Faster](#why-asgi-is-faster)
   - [async and await Gotchas](#async-and-await-gotchas)
   - [Server and Application Must Both Support Async](#server-and-application-must-both-support-async)
3. [Virtual Environments: Isolating Dependencies](#virtual-environments-isolating-dependencies)
   - [Creating & Activating a Virtual Environment](#creating--activating-a-virtual-environment)
4. [Managing Dependencies with requirements.txt](#managing-dependencies-with-requirementstxt)
   - [For Others to Replicate Your Environment](#for-others-to-replicate-your-environment)
5. [Client-Server Communication: The Basics](#client-server-communication-the-basics)
   - [Server Types](#server-types)
   - [Language-Independent Communication](#language-independent-communication)
6. [REST APIs: How Data Flows](#rest-apis-how-data-flows)
7. [Running FastAPI with Uvicorn](#running-fastapi-with-uvicorn)
8. [Pydantic: Data Validation & Conversion](#pydantic-data-validation--conversion)
9. [Swagger: Built-in API Documentation](#swagger-built-in-api-documentation)
   - [Why Does the 5th Product Show Up in Swagger but Not in My Python File?](#why-does-the-5th-product-show-up-in-swagger-but-not-in-my-python-file)
10. [Type Hints in FastAPI](#type-hints-in-fastapi)
11. [ORM & ODM](#orm--odm)
    - [Working with FastAPI and PostgreSQL: Driver and SQLAlchemy](#working-with-fastapi-and-postgresql-driver-and-sqlalchemy)
    - [autocommit and autoflush](#autocommit-and-autoflush)
    - [sessionmaker](#sessionmaker)
    - [Base.metadata.create_all(bind=engine)](#basemetadatacreate_allbindengine)
    - [model_dump() and db.add()](#model_dump-and-dbadd)
12. [Yield in Python](#yield-in-python)
13. [Dependency Injection](#dependency-injection)
    - [Why Use Dependency Injection Over Manual Function Calls](#why-use-dependency-injection-over-manual-function-calls)
    - [Pydantic vs SQLAlchemy Models](#pydantic-vs-sqlalchemy-models)
14. [FastAPI's Parameter Detection](#fastapis-parameter-detection)
    - [Now, What If We Want a Parameter to Come from the Body?](#now-what-if-we-want-a-parameter-to-come-from-the-body)
15. [Response Model](#response-model)
16. [What Is Annotated?](#what-is-annotated)
17. [Middleware](#middleware)
    - [Excluding Specific Endpoints from Middleware](#excluding-specific-endpoints-from-middleware)
    - [Applying Middleware to Only Specific Paths](#applying-middleware-to-only-specific-paths)
      - [Option 1: Middleware with Path Check](#option-1-middleware-with-path-check)
      - [Option 2: Dependency (Recommended)](#option-2-dependency-recommended)
      - [Option 3: Sub-Application](#option-3-sub-application)
      - [Which One to Use?](#which-one-to-use)
18. [Templates](#templates)
19. [Route Order in FastAPI](#route-order-in-fastapi)
20. [CORS in FastAPI](#cors-in-fastapi)
    - [Why Does the Browser Block the Request?](#why-does-the-browser-block-the-request)
    - [Adding CORSMiddleware](#adding-corsmiddleware)
    - [Things to Remember](#things-to-remember)

---

## Why FastAPI Needs a Separate Server

### Web Server Architecture: 3-Layer System

**Layer 1: Server (Network/HTTP Handler)**

- Handles raw HTTP connections, manages TCP/IP, parses HTTP protocol
- Examples: Uvicorn, Hypercorn (ASGI), Gunicorn (WSGI)
- Nginx is usually placed **in front** of these as a reverse proxy (it forwards requests to them); it is not a WSGI/ASGI server itself

**Layer 2: Interface/Gateway (Converter)**

- Converts between HTTP and Python objects (standardized format)
- Standards: WSGI (sync) or ASGI (async) — just specifications, not software you install
- Both server and framework follow this standard to communicate

**Layer 3: Application (Your Code)**

- Business logic, routing, database, validation
- Examples: Django, FastAPI

**How it works:**

1. Server (like Uvicorn, Gunicorn) receives HTTP request
2. Server's built-in ASGI/WSGI implementation converts HTTP to Python dict following the specification rules
3. Server calls your Application (FastAPI/Flask) as a function with that dict
4. Application returns response to Server
5. Server's ASGI/WSGI implementation converts response back to HTTP following the specification rules
6. Server sends HTTP response to user

So:

- WSGI/ASGI specification = The contract/rules (documentation)
- ASGI/WSGI implementation = Code built INTO the server that does the conversion following those rules
- Server = Handles network connections AND does the conversion (via its built-in ASGI/WSGI implementation)

**Why separate layers?**

- Swap servers without changing code
- Use same server for different frameworks
- Scale and optimize each layer independently

_but_

- **Server** = Physical software ✅ Ex: Uvicorn, Gunicorn
- **Application** = Physical software ✅ Ex: FastAPI, Django
- **ASGI/WSGI** = Just a standard/protocol (like HTTP, USB-C) — NOT separate software you install, it's a contract that both parties follow

**Analogy:** Phone and charger both follow USB-C standard — rules about pin size, voltage, data transfer. USB-C itself isn't a physical thing; it's a specification that phone manufacturers and charger manufacturers implement.

**Similarly, ASGI/WSGI is a specification:**

- **Uvicorn** has ASGI implementation built-in → knows how to create `scope` dictionary and call app
- **FastAPI** (through Starlette, the toolkit it is built on) has ASGI implementation built-in → knows how to receive `scope` dictionary and respond

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
- Function returns Python objects - FastAPI automatically serializes to JSON (using Pydantic / `jsonable_encoder`)

So no manual conversion like `req.json()` in Node.js or `JsonResponse` in Django. Just return Python object from each function → FastAPI automatically converts to JSON & hands over this JSON to ASGI → ASGI converts to HTTP response and hands over to server → server sends to user

But ASGI gives a Python dictionary, so why does FastAPI need to "convert request data to Python types"?

### What Actually Happens (ASGI Flow)

**Step 1: ASGI hands over dictionary**

```python
# ASGI gives FastAPI something like this:
scope = {
    "type": "http",
    "method": "POST",
    "path": "/users",
    "query_string": b"age=25&name=John",
    "headers": [...],
}
# Body comes separately through receive() callable, not in scope
# receive() returns: {"type": "http.request", "body": b'{"email": "test@example.com", "age": "25"}'}
```

**Step 2: FastAPI converts using type hints**

When you write:

```python
from pydantic import BaseModel

class User(BaseModel):
    email: str
    age: int

@app.post("/users")
async def create_user(user: User):  # Pydantic model with type hints
    return {"email": user.email, "age": user.age}
```

FastAPI looks at your type hints and Pydantic models and:

1. **Extracts data** from the ASGI scope and body (from body, query params, path, etc.)
2. **Validates types** - checks if `age` can be converted to `int`
3. **Converts** - turns `"25"` (string) into `25` (integer)
4. **Passes clean data** to your function

### Visual Example

```python
# What ASGI gives (raw):
# Body from receive(): b'{"email": "test@example.com", "age": "25"}'  # Bytes, and age is STRING in JSON

# What FastAPI does with Pydantic models:
from pydantic import BaseModel

class User(BaseModel):
    email: str
    age: int  # You specify: age should be INT

@app.post("/users")
async def create_user(user: User):
    # FastAPI + Pydantic automatically:
    # 1. Reads body bytes from ASGI
    # 2. Parses JSON from bytes
    # 3. Sees age: int in your Pydantic model
    # 4. Converts "25" (string) → 25 (integer)
    # 5. Validates it's a valid integer
    # 6. Creates User object and passes to your function

    print(type(user.age))  # <class 'int'> - already converted!
    return {"email": user.email, "age": user.age}
```

### Without FastAPI (Manual Work)

In Node.js or plain Python (raw ASGI), you'd do:

```python
import json

async def create_user(scope, receive, send):
    event = await receive()  # Manual receive
    body = json.loads(event["body"])  # Manual parse
    email = body["email"]
    age = int(body["age"])  # Manual conversion
    # Manual validation...
```

### With FastAPI (Automatic)

```python
async def create_user(user: User):
    # FastAPI already did all the work!
    # user.email is str, user.age is int - guaranteed
```

**Summary:** ASGI gives raw scope dictionary and a receive() callable that returns body bytes. FastAPI reads your type hints and Pydantic models, extracts data from scope and body, validates, converts types, and hands you clean, typed Python objects in your function parameters.

---

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
- Supports both sync (default) and async (ASGI support since v3.0, async views since v3.1)

**FastAPI:**

- Lightweight, no built-in server
- Development & Production: Install ASGI server (Uvicorn, Hypercorn)
- **Uses separate server layer** (ASGI architecture)
- Async-first (designed for async from ground up)

**Key takeaway:**

- Node.js/Express/Next.js have **integrated server** (no separate layer)
- Django and FastAPI use **separate server layer** architecture (WSGI/ASGI). Django includes a convenience development server; FastAPI requires you to choose your own ASGI server from the start. Both need production servers installed separately.

---

## Synchronous vs Asynchronous

### Blocking vs Non-Blocking Code

**Synchronous (Blocking):**

```python
def get_data(request):
    user = fetch_from_database()     # Waits 2 sec - blocks the thread
    weather = fetch_from_api()       # Waits 3 sec - blocks the thread
    return JsonResponse({"user": user, "weather": weather})
# Total: 5 seconds, thread is blocked so worker cannot handle other requests while waiting
```

**Asynchronous (Non-blocking):**

```python
async def get_data(request):
    user = await fetch_from_database()     # Waits 2 sec - event loop handles other requests
    weather = await fetch_from_api()       # Waits 3 sec - event loop handles other requests
    return {"user": user, "weather": weather}
# Total: 5 seconds for THIS request, BUT event loop handles many other requests during waits
```

(If the two calls don't depend on each other, `await asyncio.gather(fetch_from_database(), fetch_from_api())` runs them together and this request takes only ~3 seconds.)

**Difference:**

- **Sync:** Each worker thread handles 1 request at a time, thread blocked during I/O waits
- **Async:** Event loop handles many requests concurrently, no thread blocking during I/O waits

**Why FastAPI is faster for I/O-heavy apps:** Built for async from day one (optimized for I/O-heavy operations like database, API calls, file operations). Django added async support later as a retrofit. FastAPI's async design allows a single event loop to handle thousands of concurrent I/O-bound requests efficiently. Additionally, FastAPI uses Pydantic V2 for validation, which has its core written in Rust (a compiled language), making data validation significantly faster than pure Python implementations.

Django = Built sync-first (2005), async retrofitted later - async/await works but not as optimized as FastAPI which was designed async-first.

ASGI allows async (event loop, concurrent), WSGI forces sync (thread-per-request, blocking).

---

### Is ASGI Faster as a Specification?

If ASGI/WSGI are just specifications, how can one be "faster" than the other?

ASGI itself isn't faster than WSGI. The speed difference comes from whether your application code runs synchronously or asynchronously.

**WSGI specification says:**

- "Application must be a synchronous callable"
- "Handle one request, return one response, then move to next"
- Forces servers to use thread-based or process-based concurrency

**ASGI specification says:**

- "Application can be an asynchronous callable"
- "Can handle multiple requests concurrently in single thread using event loop"
- Allows servers to use async/await and event loop

ASGI isn't "faster" as a specification. It's that ASGI permits async code, which allows servers like Uvicorn to handle I/O-bound requests more efficiently than thread-based WSGI servers like Gunicorn.

---

### ASGI Request Flow: Uvicorn and FastAPI

**Uvicorn (ASGI server) →** Accepts HTTP connection → Builds `scope` dict + `receive`/`send` callables

- Calls `await app(scope, receive, send)` → this `app` is FastAPI
- `scope` → dict of request metadata (method, path, headers, query string)
- `receive` → async fn to **get the body** (in chunks)
- `send` → async callable to **send the response**

**FastAPI (built on Starlette):**

- Reads `scope` (method, path, headers, query)
- Calls `await receive()` to collect body bytes

```python
event = await receive()  # you call this to pull the body
# event = {"type": "http.request", "body": b"...", "more_body": False}
```

- Wraps everything into a `Request` object
- From this request object, FastAPI **finds the path's controller fn**, and looks at its **type hints + Pydantic models**
- When it needs the body, FastAPI reads it (internally `await request.body()`, which triggers `receive()` under the hood), gets the raw bytes, and parses them to a dict/JSON
- Then it checks types, required fields and constraints for each parameter of that controller fn against that dict. Converts `"25"` → `25`, etc. If it's not able to convert, it raises `RequestValidationError` → **422 response**
- On success of validation + conversion, FastAPI **calls your controller fn with clean Python objects** as arguments (e.g. `age: int = 25`)
- Your controller fn runs → returns a Python object
- FastAPI serializes the return value → JSON, and calls `await send({...})` → Uvicorn receives this response → converts it to HTTP bytes → sends to client

### How FastAPI Validates Parameters

When a request comes in, FastAPI finds the corresponding controller and checks its parameters:

- For simple types like `int` or `str`, FastAPI itself handles parameter validation and conversion using the type information provided. It checks whether the incoming values match the expected types, tries to convert them when possible, and returns a validation error if conversion is not possible.
- For Pydantic models, FastAPI uses Pydantic to perform the same validation on the incoming data against the model's field definitions, converts compatible values to the expected types whenever possible, and raises a validation error if the data cannot be validated or converted.

**Short version:**

- For simple types like `int` or `str`, FastAPI handles parameter validation and conversion.
- For Pydantic models, FastAPI uses Pydantic to validate and convert the incoming data against the model's field definitions.
- In both cases, if validation or conversion fails, FastAPI returns a validation error, typically **HTTP 422**.

### Concurrent Request Handling in ASGI

**Request 1 arrives:**

1. Server (Uvicorn) receives HTTP request
2. Server converts to Python dict (scope) and builds `receive`/`send`
3. Server calls the FastAPI application as a function
4. FastAPI performs validation and conversion
5. FastAPI executes the route callback function
6. Inside the callback: `await db.execute(query)` — Python hits this `await` and **pauses this coroutine right there**, it doesn't block the thread waiting for the DB
7. Control goes back to the **event loop** (which is just part of Uvicorn, running via asyncio/uvloop — not some separate process)
8. The event loop parks the paused coroutine aside, marks "wake it up when the DB responds" (the waiting is handed to the OS), and moves on to whatever else needs running
9. **The main thread is now free** while the database operation is in progress
10. Once the result's ready, the event loop gets notified and resumes the coroutine from where it paused

**Request 2 arrives (while Request 1's DB call is still processing):**

1. Server receives the new HTTP request, calls `await app(scope, receive, send)` again (same process)
2. FastAPI handles Request 2 on the same thread, same way
3. **Both requests are being handled concurrently** — Request 1 waiting on DB, Request 2 being processed

So the thread is never sitting idle waiting — it is free to pick up other work the moment it hits an `await`. This way, one thread handles multiple requests without blocking.

### When Does the Event Loop Start?

**At server start!** When you run `uvicorn main:app`, Uvicorn starts the event loop immediately and keeps it running. Then:

- If a route is `async def` → FastAPI runs it **in the event loop** (non-blocking, as long as you `await` things)
- If a route is regular `def` → FastAPI runs it **in a thread pool** (to avoid blocking the event loop)

### WSGI Request Flow: Gunicorn and Django

**Gunicorn (WSGI server) →** Accepts HTTP connection → Builds `environ` dict (WSGI equivalent of ASGI `scope`) & provides `start_response` callable (like ASGI `send`) → calls `app(environ, start_response)` → this `app` is Django.

Django wraps `environ` into a `Request` object where:

- `request.GET` ← from `QUERY_STRING`
- `request.headers` ← from `HTTP_*` keys in environ
- `request.body` ← from `environ["wsgi.input"].read()`, but Django hasn't called this method yet at this point — it's **lazy**. This method is synchronous, so when it _does_ get called, the main thread is occupied while the body is being read; once read, it's put into `request.body`.

Then Django:

1. Checks `ROOT_URLCONF` in `settings.py`, which points to `ProjectFolder.urls`
2. Opens the project's root `urls.py` and looks for a matching pattern (`food/`)
3. If `food/` matches, it moves to `food/urls.py` and looks for the next part (`hello`)
4. If a match is found, Django executes the corresponding view function (e.g. `index`) with that request

**No automatic validation or type conversion — that's on you.** Django calls your view function with this request object as-is — body still unread at that point. Inside the view, you do `json.loads(request.body)` yourself. On first access, `request.body` triggers the synchronous `environ["wsgi.input"].read()` to get the raw binary bytes, then you parse that into JSON — and it's cached on the `request` instance after that first access.

For form data, you just do `request.POST` — Django internally calls that same `read()`, parses the binary bytes, and returns the parsed object directly, no manual parsing needed on your end.

Then the view fn returns an HTTP response, like `"Hello, User!"`. It must return an `HttpResponse` (or `JsonResponse`, `render`, etc.), so inside this view you manually serialize the data (`JsonResponse({"ok": True})`).

So when the view returns `HttpResponse("hi", status=200, headers={...})`, Django splits this and first calls `start_response("200 OK", [("Content-Type","text/html")])` ← status + headers, then sends the body to Gunicorn. Gunicorn combines both into the raw HTTP response sent to the client. That's the WSGI contract.

### Concurrent Request Handling in WSGI

**Request 1 arrives:**

1. Server (Gunicorn) receives HTTP request
2. Server converts to Python dict (`environ`)
3. Server calls the Django/Flask application
4. Application executes the route callback / view
5. Inside it: `db.execute()` (blocking call)
6. **Thread is blocked** — sits idle waiting for the database
7. Thread cannot handle anything else until DB responds

**Request 2 arrives (while Request 1's DB call is still processing):**

1. Server receives the new request
2. **Cannot forward it to the same worker** — it's blocked
3. Server either:
   - Queues the request (waits for a worker to be free)
   - Uses another worker thread/process (if available)
   - Rejects the request (if no workers are available and the queue is full)

To handle concurrent requests, WSGI servers need **multiple worker threads/processes** running simultaneously, each handling one request at a time ("handle one request, return one response, then move to next").

However, Django can be used with `async`/`await` too, but async support was added later, so it's not as optimized as FastAPI (Django added async support from 3.0/3.1 onward, and a lot of the ORM is still sync under the hood unless you use the newer async ORM methods).

So Django/FastAPI's application layer and server layer are two different layers, whereas in Node there is no separate server layer — server and application run together (Express wraps the built-in server, Next.js inherits Node's HTTP server capabilities).

### ASGI vs WSGI: Key Differences

**ASGI (Async):**

- ✅ One thread handles many concurrent requests
- ✅ No blocking during I/O waits
- ✅ Event loop efficiently switches between requests
- ✅ Lower memory usage (fewer threads)
- ✅ Better for I/O-bound operations (DB, APIs, file operations)

**WSGI (Sync):**

- ❌ Each worker thread handles one request at a time
- ❌ Thread blocks during I/O waits
- ❌ Needs many worker threads/processes for concurrency
- ❌ Higher memory usage (more threads)
- ✅ Simpler mental model, easier to debug
- ➖ CPU-bound work blocks a worker either way (see the gotchas below)

### Visual Comparison

**WSGI (Sync):**

```
Worker 1: [Request A ████████████████] (blocked, waiting)
Worker 2: [Request B ████████████████] (blocked, waiting)
Worker 3: [Request C ████████████████] (blocked, waiting)
Worker 4: [idle]
```

Needs 4 workers for 4 concurrent requests

**ASGI (Async):**

```
Single Event Loop: [Req A █ Req B █ Req C █ Req D █ Req A █ Req B ...]
```

One event loop handles all 4+ requests, switching between them during I/O waits

### Why ASGI Is Faster

ASGI isn't just fast because it handles more requests simultaneously — it's **optimized for I/O-bound workloads**:

1. **Less memory overhead:** 1 thread vs. 100 threads for 100 concurrent requests
2. **No context switching:** OS doesn't switch between threads constantly
3. **Better resource utilization:** Thread doesn't sit idle during I/O waits
4. **Higher throughput:** Can handle thousands of concurrent connections on a single process

**Important:** For CPU-bound tasks (heavy computation), async provides no benefit since the thread is actually working, not waiting for I/O. For CPU-heavy work, you scale with **multiple processes** (e.g. `uvicorn --workers 4`, or Gunicorn managing Uvicorn workers), which works for ASGI and WSGI alike.

### async and await Gotchas

- If you don't use `async`/`await`, even with ASGI, concurrent request handling won't work efficiently — without `async`/`await` you're basically using ASGI like WSGI (FastAPI runs plain `def` routes in a thread pool).
- When you use an ASGI server like Uvicorn with FastAPI and use `async def` + `await` for I/O (database calls, HTTP requests, etc.), concurrent requests are handled automatically. You don't need to do anything extra.
- ⚠️ **Never put blocking code inside `async def`** (like `time.sleep()`, `requests.get()`, or a sync DB driver). It blocks the **whole event loop**, so every other request waits too. Use `await asyncio.sleep()`, async libraries, or define that route as a plain `def`.
- WSGI/ASGI is NOT middleware. It's a specification (just rules/contract) that is built into the server and framework. There is no separate layer in between: the server itself does the conversion (HTTP request → Python dict, Python response → HTTP response).

### Server and Application Must Both Support Async

- In FastAPI, it only works with ASGI servers, which support asynchronous request-response, and FastAPI also supports asynchronous request-response — this is why it's faster.
- In Django, it supports both ASGI and WSGI. If we use `async`/`await` but use a WSGI server, nothing will happen, since WSGI servers do not support asynchronous request-response — the WSGI server will just block and wait, turning your async code back into synchronous execution, so you won't get any async benefits.
- If we use an ASGI server with Django, even then it will not be as fast as FastAPI, because Django is built for synchronous request-response — async was added later, so it is not as optimized.

**So for asynchronous request-response to work, both the server and application layer must support it. If one supports it but the other does not, it will not work.**

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

# Activate (macOS / Linux)
source myenv/bin/activate

# Deactivate
deactivate
```

**Analogy:**

- `myenv/` or `env/` → like `node_modules` (stores packages locally)
- `requirements.txt` → like `package.json` (lists dependencies)

---

## Managing Dependencies with requirements.txt

Instead of writing `requirements.txt` manually, generate it automatically:

```bash
pip freeze > requirements.txt
```

This captures **exact versions** of all installed packages (including the dependencies of your packages). Run this after finishing or updating your project.

### For Others to Replicate Your Environment

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

This standardization ensures **unified communication** regardless of language or version. Ex: GET → Read, POST → Create, PUT/PATCH → Update, DELETE → Delete.

---

## Running FastAPI with Uvicorn

```bash
uvicorn main:app --reload
```

- `main` = your Python file (main.py)
- `app` = FastAPI instance variable
- `--reload` = auto-restart on code changes (for development only)

---

## Pydantic: Data Validation & Conversion

**Pydantic** is a Python package for data validation and conversion.

When you call `Product(...)`, Pydantic's **auto-generated `__init__`** runs:

1. Validates input data using type hints
2. Converts data to correct types
3. Creates an instance if valid, otherwise raises `ValidationError`

---

## Swagger: Built-in API Documentation

**Swagger (Swagger UI)** is a tool that shows your API documentation (generated from an OpenAPI schema) as a page where you can also test the endpoints.

- Provides a **clean UI to test REST APIs**
- Works with REST APIs (OpenAPI). GraphQL has its own tools like GraphiQL / Playground for this
- In frameworks like Node.js, Django, or Next.js, you must configure Swagger manually (add paths, etc.)
- **FastAPI comes with Swagger built-in** — it generates the OpenAPI schema (`/openapi.json`) automatically and serves Swagger UI at `/docs` (and ReDoc at `/redoc`). No configuration needed!

**Why use Swagger alongside Postman?**

- Swagger provides **interactive documentation** — anyone can test the API directly from the docs without installing anything
- Postman requires installation and manual request setup (but it is better for saved collections, environments, and team workflows)

### Why Does the 5th Product Show Up in Swagger but Not in My Python File?

When you POST a new product → it goes into RAM (memory)
When you GET all products → you see it (it's in RAM)
When you look at this file → no change (RAM ≠ File)

The file is NOT the database! The file is just the code. It ran once when the server started.

Why it works in Swagger but not in file:

- Swagger talks to the running server (RAM)
- The file is just source code (not connected to RAM)
- You need to explicitly save RAM → File

To save RAM state to file so that it's stored permanently we use `.json` files

```python
import json

def add_product(product: Product):
    products.append(product)        # Step 1: Add to RAM

    # Step 2: Save RAM → File
    with open("products.json", "w") as f:  # Open file for Writing
        # Pydantic objects are not JSON serializable, so convert them to dicts first
        json.dump([p.model_dump() for p in products], f)  # Dump (write) RAM data into file

    return products
```

To save to file: You MUST explicitly write it using `open()` and `json.dump()`

What `json.dump()` does:

- Takes data from RAM (products list)
- Converts it to JSON text format
- Writes it to the file (products.json)

So in JSON it works because after the products got added to RAM, we take that updated list from RAM and overwrite the existing content in the .json file with this list - this is why it works.

Normally with a list in a .py file it won't work because there's no simple way to modify just the list variable in the Python source file. Even if we tried, we'd have to put the list in a completely separate file so that when we overwrite it with the new updated list from RAM, the other code doesn't get lost. So we'd have to put that in a separate file, but still this is complex and not a good approach.

For this use JSON since it's lightweight, performs better, and is widely used so it's trustworthy.

In case of `json-server` in npm/JS, that package does the same thing - it syncs the file that we watch with the package with RAM state. Whenever that RAM state gets updated, it updates that watched file - this is how we see the updated file.

So anyway, if we want to see the updated state from RAM reflected in a file also, we must explicitly read the RAM state and sync it with the file. If we don't do that, this won't automatically happen. This is why normally we don't see the products array get automatically populated with new products in the source file like it does in RAM.

When we restart the server, the RAM state gets cleared and initialized again, so that data will be gone. So we must sync that RAM state with a file so that the data persists. We have to do it manually and explicitly.

So,
The reason we don't see the updated list in the source code is because the source code runs once when the server starts. After that, the source code and the running entity (process) created from it are two completely different things.

The running process exists in RAM with its own state. If we want to see changes reflected in the source code file itself, we have to explicitly write to that file while the process is running. It's not automatic — just because the running entity came from the source code doesn't mean it will update the source file. The source code and the running process are completely separate. Only if the running process explicitly writes to the source code file will we see changes there.

---

## Type Hints in FastAPI

In case of Python, type hints are **not enforced** by the interpreter — they're used to tell what developers expect and for IDE support. But they are stored on the function (in `__annotations__`), so libraries **can read them at runtime**. In case of TypeScript, types are enforced at compile time (and erased at runtime).

In case of FastAPI, it uses Pydantic, which reads type hints and enforces validation at runtime, so in that case it strictly checks and throws error if it gets something which is not defined.

---

## ORM & ODM

When we define a class in JS/Python that maps to a table/collection:

- Class name maps to table/collection name (in SQLAlchemy usually set with `__tablename__`)
- The type of each field inside the class maps to each column type of that table (or field type in a document)
- Each instance (object) of that class maps to each row of that table (or document in a collection)

So we're connecting objects and relations (tables) by mapping everything in that class to that table/collection — that's why it's called Object-Relational Mapper (ORM) for SQL databases, or Object-Document Mapper (ODM) for NoSQL document databases like MongoDB.

We need this because when working with Python/JS, we'd have to manually convert class objects to SQL queries (or MongoDB queries), which is cumbersome, very error-prone, complex, and difficult to maintain since two different languages exist in one file. That's why these tools exist — they give us functions we can call, and behind the scenes those queries are generated and executed. We just write code in Python/JS. This is why ORMs and ODMs exist.

So these ODM/ORM tools let us:

- Define models (classes) for collections/tables
- Validate data automatically
- Query and update documents/rows using Python/JS syntax instead of raw MongoDB/SQL queries

### Working with FastAPI and PostgreSQL: Driver and SQLAlchemy

To work with FastAPI and PostgreSQL, we need a PostgreSQL driver and optionally SQLAlchemy. SQLAlchemy is an ORM, which is optional — we can communicate with PostgreSQL directly using Python and the driver alone, but it becomes complex, cumbersome, and harder to manage. The driver, however, is mandatory. It functions as the communication layer through which we send SQL queries to the actual PostgreSQL server — similar to how pgAdmin or the psql CLI communicates with PostgreSQL.

The driver itself isn't the DBMS; the PostgreSQL server is the DBMS that stores, manages, and processes data.

- **psycopg2** (sync) / **asyncpg** (async) → drivers that communicate with the PostgreSQL server
- **SQLAlchemy** → ORM layer built on top of the driver. Since the driver is the only medium to communicate with the server, SQLAlchemy (or any ORM/ODM) is built on top of these drivers so that communication happens successfully
- **pgAdmin** / **psql** → client tools that also communicate with the PostgreSQL server using a driver

psql and pgAdmin are tools that provide a command-line or graphical interface for interacting with PostgreSQL server. Behind the scenes, they use database drivers (such as libpq for psql) to handle the actual communication with the PostgreSQL database server.

- **Mongoose** (NoSQL - MongoDB ODM) → JavaScript/TypeScript (Node.js)
- **Mongoengine / Beanie** (NoSQL - MongoDB ODMs) → Python. (**Motor** is the async MongoDB _driver_ for Python, like asyncpg is for PostgreSQL, not an ODM)
- **Prisma** (ORM for SQL databases and MongoDB) → JavaScript/TypeScript
- **SQLAlchemy** (SQL ORM) → Python

### autocommit and autoflush

Suppose the database already has **100 users**, and we do:

```python
session = sessionLocal()

user1 = User(name="Alice")
user2 = User(name="Bob")
user3 = User(name="Charlie")

session.add(user1)
session.add(user2)
session.add(user3)

# NOW you want to query: How many users are in the database?
count = session.query(User).count()
print(f"Count: {count}")
```

**autocommit=False && autoflush=True (default):** Before running the query, SQLAlchemy **flushes** the pending changes (sends the INSERTs to the DB inside the transaction), so this session sees count=103. But nothing is permanent until `commit()` — other sessions still see count=100.

**autocommit=False && autoflush=False:** Changes stay in Python memory, never touch the DB until `commit()` (even this session sees count=100) — gives full control, fewer DB calls, better performance.

**autocommit=True && autoflush=True (legacy):** Changes are immediately flushed and permanently committed to DB automatically (all sessions see count=103) — no control, no rollback, everything saves instantly. In SQLAlchemy 2.0, `autocommit=True` is no longer supported, so you always call `commit()` yourself.

**Case 1: autocommit=False, autoflush=True**

```text
What happens:
1. session.add(user1) → Stays in memory
2. session.add(user2) → Stays in memory
3. session.add(user3) → Stays in memory
4. session.query(User).count() → ⚠️ AUTOFLUSH triggers!
   - SQLAlchemy sends INSERT for Alice, Bob, Charlie to database (temporary, in transaction)
   - Then runs the COUNT query
   - Count includes Alice, Bob, Charlie
5. No commit() yet → Changes are NOT permanent, other sessions can't see them

Result: Count = 103 (original users + 3)
Database calls: 3 INSERT queries + 1 COUNT query = 4 database operations
```

**Case 2: autocommit=False, autoflush=False**

```text
What happens:
1. session.add(user1) → Stays in memory
2. session.add(user2) → Stays in memory
3. session.add(user3) → Stays in memory
4. session.query(User).count() → No autoflush!
   - Runs COUNT query directly without sending Alice, Bob, Charlie
   - Count does NOT include Alice, Bob, Charlie (they're still only in Python memory)
5. No commit() yet → Changes are NOT in database at all

Result: Count = 100 (original users only, NO new users counted)
Database calls: 1 COUNT query = 1 database operation
```

### sessionmaker

`sessionmaker` is a class.
`sessionLocal = sessionmaker(...)` creates an instance of sessionmaker, BUT this instance itself is also a callable.
`db = sessionLocal()` calls that callable to create an actual session instance which we use to interact with the database.

### Base.metadata.create_all(bind=engine)

`create_all()` is smart — it checks if the table already exists in the database. If the table exists, it does nothing. If the table doesn't exist, it creates it. So restarting the server won't duplicate tables.

`Base` is a base class provided by SQLAlchemy. When you create your model classes (like Product) and inherit from Base, SQLAlchemy automatically tracks all the metadata about that class — table name, column names, column types, primary keys, etc.

So,
Here's what's happening:

- `Base.metadata` contains all the information about ALL the tables (models) you defined that inherit from Base
- `create_all(bind=engine)` takes all that metadata and generates the SQL CREATE TABLE statements
- It executes those statements on the database (using the engine) to create the actual tables
- But it only creates tables that don't already exist. It does **not** update existing tables (if you add a column later, you need a migration tool like Alembic)

### model_dump() and db.add()

```python
def init_db():
    db = sessionLocal()

    # Count existing products in the database
    count = db.query(database_models.Product).count()

    if count == 0:
        for product in products:
            # Convert Pydantic model to SQLAlchemy model and add to session
            db.add(database_models.Product(**product.model_dump()))

        # Commit all changes to the database permanently
        db.commit()

    db.close()


# product.model_dump() => converts Pydantic model object to dictionary
# ** unpacks the dictionary into keyword arguments (key=value pairs)
# database_models.Product(**dict) => creates SQLAlchemy Product object from those key-value pairs
init_db()

# ** spreads out a dictionary into function/constructor arguments, so you don't have to manually type each key=value pair.

# product.model_dump()  # Returns: {"id": 1, "name": "Phone", "price": 699.99, ...}

# database_models.Product(**product.model_dump())
# # Becomes:
# database_models.Product(id=1, name="Phone", price=699.99, ...)
```

---

## Yield in Python

We need an extra method like `next()` to work with `yield`. It's like a `return` statement, but instead of returning and exiting the function, it returns a value and pauses the function execution. The catch is, after returning, the function call is paused. When we call `next()` one more time, the function resumes execution until the next `yield`. If there is no more `yield` and we reach the end of the function or a `return` statement, then the function execution is permanently finished. Now calling `next()` will raise a `StopIteration` exception.

```python
def numbers():
    print("start")
    yield 1          # pauses here and gives 1
    print("resume")
    yield 2          # pauses here and gives 2
    print("end")     # no more yield → function finishes

gen = numbers()
next(gen)   # prints "start", returns 1
next(gen)   # prints "resume", returns 2
next(gen)   # prints "end", then raises StopIteration
```

---

## Dependency Injection

If any route function needs a value (like a database session), instead of creating it directly inside the function or manually calling a function to get it, we can ask FastAPI to provide it for us. FastAPI will automatically call the dependency function, get the value, and pass it as a parameter to our route function.

Ex:

```python
def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/products")
def get_all_products(db: Session = Depends(get_db)):
    db_products = db.query(database_models.Product).all()
    return db_products
```

Here `db: Session` is the normal type annotation — whatever parameter we pass in a controller, we give its type so FastAPI can validate it at runtime. But `= Depends(get_db)` tells FastAPI: "Listen, I depend on this function for this object." So FastAPI calls `get_db()` and injects the returned object as `db` whenever this controller is requested.

**How it works:**
FastAPI calls `get_db()`, which runs until `yield db` and pauses. FastAPI injects that `db` object into the `get_all_products()` parameter, so `get_all_products()` runs. FastAPI does NOT go back to `get_db()` immediately after injecting `db`. It waits until `get_all_products()` completely finishes, THEN it goes back to `get_db()` and runs the rest of the code (the `finally` block) automatically.

### Why Use Dependency Injection Over Manual Function Calls

If we manually call `get_db()`, we'd have to remember to use `next()` since the function execution is paused after `yield`. But with dependency injection, all of this is handled automatically by FastAPI — no extra code, no manual `next()` calls, nothing. We just declare the dependency and FastAPI handles everything on behalf of us. This way we can reuse the same session management multiple times, and managing sessions becomes easy and consistent across all routes.

### Pydantic vs SQLAlchemy Models

If the client is sending JSON (which is already key-value pairs like a dictionary), why can't we directly unpack that JSON response? Why do we need the conversion using `model_dump()`? Because `model_dump()` converts to a dictionary, but we're already getting a dictionary as JSON, right?

**Answer:**

Whatever parameter type we provide, FastAPI checks if the incoming request has the same data type. If yes, it allows it; if not, it tries to convert it to whichever type is mentioned.

When we add a product, the client sends JSON: `{"id": 1, "name": "Phone", "price": 699.99, ...}`. FastAPI sees that the parameter type is a Pydantic model, so FastAPI converts this JSON to a Pydantic object: `Product(id=1, name="Phone", price=699.99, ...)` — NOT a dictionary. We cannot unpack an object directly, so `model_dump()` converts this Pydantic object → dictionary, then `**` unpacks the dictionary into `key=value` arguments. After that, SQLAlchemy's `Product()` constructor accepts those keyword arguments like this:

```python
database_models.Product(id=1, name="Phone", price=699.99, ...)
```

This creates a SQLAlchemy model instance that `db.add()` can store in the database.

---

**What if we use SQLAlchemy model as the parameter type?**

```python
@app.post("/product")
def add_product(product: database_models.Product, db: Session = Depends(get_db)):
    db.add(product)
```

**Will it work?** No, because SQLAlchemy models cannot be used to validate request/response data. When a request comes in as JSON, FastAPI sees it doesn't match the data type and tries to convert it, but it cannot convert it because FastAPI doesn't know how to validate SQLAlchemy models. So it will throw an error.

---

**Why we need both models:**

- **Pydantic models** (`Product` from `models.py`) → for FastAPI request/response validation and conversion
- **SQLAlchemy models** (`database_models.Product`) → for database operations

---

**Remember:**

If there are predefined types like `int`, `float`, `str`, then FastAPI can validate the request and try to convert it automatically if the request data type doesn't match. But if there is a custom type, we must define types with Pydantic (FastAPI's custom type checking, validation and conversion is built around Pydantic). So we must define a Pydantic model and use it as the parameter type so that FastAPI can validate and convert the incoming JSON.

Then we have to convert the Pydantic type to SQLAlchemy model type because the Pydantic type cannot be stored in the database directly. SQLAlchemy, which is the ORM used to store data, doesn't understand Pydantic types — it only understands its own types. So we have to convert that Pydantic type to SQLAlchemy model type:

```python
db.add(database_models.Product(**product.model_dump()))
```

Here:

- `product.model_dump()` converts the Pydantic object to a dictionary
- `**` unpacks those key-value pairs and passes them to `database_models.Product()` as arguments
- `database_models.Product()` creates a SQLAlchemy model instance that we can add to the database

So we need both:

- **Pydantic models** → for FastAPI request/response validation
- **SQLAlchemy models** → for database operations

---

## FastAPI's Parameter Detection

- If a parameter name appears in the route path with `{}`, it's a path parameter.

```python
@app.put("/product/{id}")  # ← id is in the path
def update_product(id: int, ...):
    # FastAPI knows: id comes from URL path
```

- If a parameter is NOT in the path and has a simple type (int, str, float, bool), it's a query parameter.

```python
@app.put("/product")  # ← id is NOT in the path
def update_product(id: int, ...):
    # FastAPI knows: id comes from query string
```

- If a parameter is a Pydantic model or marked with `Body()`, it comes from the request body.

```python
@app.put("/product")
def update_product(id: int, product: Product, ...):
    # FastAPI knows:
    # - product = request body (Pydantic model)
```

- If a parameter has `= Depends(...)`, it's a dependency injection.

```python
def update_product(id: int, product: Product, db: Session = Depends(get_db)):
    # FastAPI knows:
    # - db = dependency (injected by FastAPI)
```

### Now, What If We Want a Parameter to Come from the Body?

**Method 1: Use `Body()` for simple types**

```python
@app.put("/product")
def update_product(product: Product, id: int = Body()):  # params without defaults must come first
    ...
```

When a route has **more than one body parameter**, FastAPI expects each one under its **parameter name**, so the JSON looks like this:

```js
fetch(`/product`, {
  method: "PUT",
  body: JSON.stringify({
    id: 5, // ← the `id` body parameter
    product: {
      // ← the `product` body parameter (wrapped by its name)
      name: "Phone",
      price: 699.99,
    },
  }),
});
```

FastAPI receives the entire JSON body, then automatically extracts and maps each key to the parameter with the same name — no manual extraction needed. (Note: the fields of `product` are **not** flattened next to `id`.)

**Method 2: Include it in your Pydantic model (Best Practice)**

```python
class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    quantity: int

def update_product(product_data: Product)
```

```js
fetch(`/product`, {
  method: "PUT",
  body: JSON.stringify({
    id: 5,
    name: "Phone",
    price: 699.99,
    // ... all fields
  }),
});
```

(In REST style, it is also common to put the id in the path: `PUT /product/{id}`.)

**Method 3: Wrapper**

```python
@app.put("/product")
def update_product(product: Product = Body(embed=True))
```

```js
fetch(`/product`, {
  method: "PUT",
  body: JSON.stringify({
    product: {
      // ← Notice the wrapper
      id: 5,
      name: "Phone",
      price: 699.99,
    },
  }),
});
```

If we use `Body(embed=True)`, the Pydantic model comes from the body with a wrapper key (the wrapper key name = parameter name).

FastAPI is smart — it looks at the route definition and parameter types to automatically figure out where each parameter should come from. No manual configuration needed!

---

## Response Model

In FastAPI, Pydantic models are required to validate and convert request/response data types. For database operations with an ORM, we need separate SQLAlchemy models since Pydantic models cannot be understood by the ORM — the ORM needs its own model types.

Even though APIs return JSON, Pydantic models are also needed to validate the response so that we can ensure the route function returns the correct structure. This prevents accidentally returning wrong fields or types and exposing sensitive fields (like passwords). It also ensures that the function returns correct types so that JSON conversion by FastAPI is error-free, since certain types cannot be converted to JSON easily (for example, `datetime` objects, `Decimal`, `set`, or custom classes need proper serialization).

**Example:** Suppose the response must have `user_id` which is type `int`, and we return `{"user_id": "abc"}`. Without response validation, this will be converted to JSON by FastAPI automatically and sent to the user with no error. But if we validate the response with a Pydantic model:

```python
class UserResponse(BaseModel):
    user_id: int

@app.get("/user", response_model=UserResponse)
def get_user():
    return {"user_id": "abc"}  # FastAPI catches this type error before sending!
```

FastAPI will raise a `ResponseValidationError` (the client gets a 500, because it's a bug on the server side) because `"abc"` is a string, not an integer, preventing the incorrect response from reaching the client.

**Extra benefits of `response_model`:**

- It **filters the output**: any field that is not declared in the response model (like `password`) is dropped from the response, even if your function returned it.
- If you return SQLAlchemy objects with a response model, enable `model_config = ConfigDict(from_attributes=True)` in the Pydantic model so it can read attributes from the ORM object.

**So response validation = catches bugs before they reach clients, ensures API contract consistency, and handles proper JSON serialization of complex types.**

---

## What Is Annotated?

`Annotated` is just a wrapper that lets you add extra instructions to a variable's type.
Think of it like putting a sticky note on a variable that says "hey, this variable needs special handling!"

```python
from typing import Annotated
from fastapi import Header

def get_info(info: Annotated[str, Header()]):
    pass
```

- `str` = the type (it's a string)
- `Header()` = extra instruction (get this from HTTP headers)

Typing means telling Python what type of data a variable should be. A typing feature is just a tool Python gives you to describe types better. `Annotated` is one such tool - it lets you say "this is a string, AND here's extra info about it."

It's just extra information that tools like FastAPI can read and use. FastAPI's docs now recommend this style for dependencies too:

```python
def get_all_products(db: Annotated[Session, Depends(get_db)]):
    ...
```

---

## Middleware

Once you define a middleware with `@app.middleware("http")`, it applies to ALL endpoints in your FastAPI app, regardless of whether the endpoints are defined before or after the middleware, it's applied to all endpoints.

### Excluding Specific Endpoints from Middleware

Yes, but manually:

```python
@app.middleware("http")
async def validator(req: Request, call_next):
    # Skip middleware for specific endpoints
    if req.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(req)

    print("middleware executing before req")
    res = await call_next(req)
    print("after req, middleware execution")
    return res
```

### Applying Middleware to Only Specific Paths

Yes, there are a few options to achieve that.

#### Option 1: Middleware with Path Check

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.middleware("http")
async def auth_middleware(req: Request, call_next):
    # Only check authentication for /about route
    if req.url.path == "/about":
        username = req.headers.get("username")

        if not username:
            return JSONResponse(
                {"error": "You are not authenticated to access this route"},
                status_code=401
            )

    res = await call_next(req)
    return res

@app.get("/")
async def home():
    return {"message": "Home - Public route"}

@app.get("/about")
async def about(req: Request):
    username = req.headers.get("username")
    return {"message": f"About - Protected route. Welcome {username}!"}
```

**Test:**

- `GET http://localhost:8000/` → ✅ Works (public)
- `GET http://localhost:8000/about` → ❌ "You are not authenticated..."
- `GET http://localhost:8000/about` with header `username: John` → ✅ "Welcome John!"

---

#### Option 2: Dependency (Recommended)

```python
from fastapi import FastAPI, Request, Depends, HTTPException

app = FastAPI()

# Dependency function
async def check_auth(req: Request):
    username = req.headers.get("username")

    if not username:
        raise HTTPException(
            status_code=401,
            detail="You are not authenticated to access this route"
        )

    return username

@app.get("/")
async def home():
    return {"message": "Home - Public route"}

@app.get("/about")
async def about(username: str = Depends(check_auth)):
    return {"message": f"About - Protected route. Welcome {username}!"}
```

**Test:**

- `GET http://localhost:8000/` → ✅ Works (public)
- `GET http://localhost:8000/about` → ❌ "You are not authenticated..."
- `GET http://localhost:8000/about` with header `username: John` → ✅ "Welcome John!"

To protect a whole group of routes, put them in an `APIRouter` with `dependencies=[Depends(check_auth)]`, and then every route in that router runs the check.

---

#### Option 3: Sub-Application

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# Sub-app for protected routes
protected_app = FastAPI()

# Middleware only for protected_app
@protected_app.middleware("http")
async def auth_middleware(req: Request, call_next):
    username = req.headers.get("username")

    if not username:
        return JSONResponse(
            {"error": "You are not authenticated to access this route"},
            status_code=401
        )

    res = await call_next(req)
    return res

# Public route in main app
@app.get("/")
async def home():
    return {"message": "Home - Public route"}

# Protected route in sub-app
@protected_app.get("/about")
async def about(req: Request):
    username = req.headers.get("username")
    return {"message": f"About - Protected route. Welcome {username}!"}

# Mount protected_app to main app
app.mount("", protected_app)
```

**Test:**

- `GET http://localhost:8000/` → ✅ Works (public)
- `GET http://localhost:8000/about` → ❌ "You are not authenticated..."
- `GET http://localhost:8000/about` with header `username: John` → ✅ "Welcome John!"

Here the sub-app is mounted at the root, so everything inside `protected_app` is protected. In real life we mount it under a prefix:

`app.mount("/admin", admin_app)`

This way:

- `http://localhost:8000/` → Public, no auth middleware
- `http://localhost:8000/products` → Public, no auth middleware
- `http://localhost:8000/admin/dashboard` → Auth middleware runs
- `http://localhost:8000/admin/settings` → Auth middleware runs

Define two FastAPI apps: public routes go in the main app, protected routes go in the sub-app. Mount the sub-app at a specific path (like `/admin`), and all its routes automatically become protected under that prefix. This also keeps protected and public routes clearly separated in your code.

Remember: a mounted sub-app is a separate app, so its endpoints do **not** show up in the main app's Swagger docs (it has its own `/admin/docs`).

---

#### Which One to Use?

- **Option 1** (Middleware): Simple, but messy if you have many protected routes
- **Option 2** (Dependency): **BEST** - Clean, reusable, FastAPI way
- **Option 3** (Sub-app): Good when you have many protected routes grouped together

---

## Templates

FastAPI only comes with the integration layer (`Jinja2Templates` class) built-in. But the actual Jinja2 templating engine itself is NOT included in plain `fastapi` - you have to install it separately (`pip install jinja2`, or use `fastapi[standard]` which includes it).

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()
templates = Jinja2Templates(directory="template")

data = ["rohit", "virat", "Hardik"]


@app.get("/", response_class=HTMLResponse)
async def home(req: Request):
    return templates.TemplateResponse(
        request=req, name="index.html", context={"data": data}
    )
```

Now we can access this `data` (and `request`) inside the `index.html` (for example `{{ data }}`). In older code you will see the old style `templates.TemplateResponse("index.html", {"request": req, "data": data})`; it still works in many versions but the newer style above is preferred.

---

## Route Order in FastAPI

When you have both static and dynamic routes with the same prefix (like `/players/special` and `/players/{id}`), always declare the static route first in FastAPI.

```python
@app.get("/players/special")   # ✅ declared first
async def special_player():
    return {"player": "special"}

@app.get("/players/{id}")      # declared after
async def get_player(id: str):
    return {"player": id}
```

If the dynamic one is above, FastAPI will match `/players/special` as `{id="special"}`, skipping the static route.

---

## CORS in FastAPI

**CORS (Cross-Origin Resource Sharing)** is a **browser** security rule that decides whether a web page from one origin can read responses from another origin. An **origin** = scheme + host + port. So `http://localhost:5173` (your React app) and `http://localhost:8000` (your FastAPI app) are **different origins**, even on the same machine.

### Why Does the Browser Block the Request?

- By default, browsers follow the **Same-Origin Policy**: JavaScript from origin A cannot read the response from origin B.
- The server has to explicitly allow it by sending headers like `Access-Control-Allow-Origin: http://localhost:5173`.
- For requests with JSON bodies, custom headers, or methods like `PUT`/`DELETE`, the browser first sends a **preflight** `OPTIONS` request to ask "is this allowed?". If the server doesn't answer correctly, the real request is never sent.
- This is why the same API works fine in **Postman, curl, and Swagger** (Swagger UI is served from the same origin) but fails from your frontend with a "blocked by CORS policy" error. CORS is enforced by the **browser**, not by the server or Postman.

### Adding `CORSMiddleware`

FastAPI has it built in (it comes from Starlette):

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # frontend origins that are allowed
    allow_credentials=True,                   # allow cookies / Authorization header
    allow_methods=["*"],                      # GET, POST, PUT, DELETE, ...
    allow_headers=["*"],                      # Content-Type, Authorization, ...
)
```

### Things to Remember

- `allow_origins` needs the **exact origin** (`http://localhost:5173`), with scheme and port, and **no trailing slash**.
- `allow_origins=["*"]` allows everyone, but it **can't be combined with credentials** (cookies / auth headers). If you use credentials, list the exact origins.
- Don't use `"*"` in production for private APIs; list your real frontend domains.
- If your server crashes with a 500 error, the browser may show it as a CORS error because the error response has no CORS headers. Check the server logs first.
- CORS doesn't protect your API from non-browser clients (curl, scripts). You still need real authentication.
