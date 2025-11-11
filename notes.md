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

## Visual Example

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

## Without FastAPI (Manual Work)

In Node.js or plain Python, you'd do:

```python
def create_user(scope, receive):
    body_bytes = await receive()  # Manual receive
    body = json.loads(body_bytes['body'])  # Manual parse
    email = body['email']
    age = int(body['age'])  # Manual conversion
    # Manual validation...
```

## With FastAPI (Automatic)

```python
async def create_user(user: User):
    # FastAPI already did all the work!
    # user.email is str, user.age is int - guaranteed
```

---

**Summary:** ASGI gives raw scope dictionary and a receive() callable that returns body bytes. FastAPI reads your type hints and Pydantic models, extracts data from scope and body, validates, converts types, and hands you clean, typed Python objects in your function parameters.

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
# Total: 5 seconds, BUT event loop handles many other requests during waits
```

**Difference:**

- **Sync:** Each worker thread handles 1 request at a time, thread blocked during I/O waits
- **Async:** Event loop handles many requests concurrently, no thread blocking during I/O waits

**Why FastAPI is faster for I/O-heavy apps:** Built for async from day one (optimized for I/O-heavy operations like database, API calls, file operations). Django added async support later as a retrofit. FastAPI's async design allows a single event loop to handle thousands of concurrent I/O-bound requests efficiently. Additionally, FastAPI uses Pydantic V2 for validation, which has its core written in Rust (a compiled language), making data validation significantly faster than pure Python implementations.

Django = Built sync-first (2005), async retrofitted later - async/await works but not as optimized as FastAPI which was designed async-first.

ASGI allows async (event loop, concurrent), WSGI forces sync (thread-per-request, blocking).

---
if ASGI/WSGI are just specifications, how can one be "faster" than the other?
 ASGI itself isn't faster than WSGI. The speed difference comes from whether your application code runs synchronously or asynchronously.

 WSGI specification says:

"Application must be a synchronous callable"
"Handle one request, return one response, then move to next"
Forces servers to use thread-based or process-based concurrency

ASGI specification says:

"Application can be an asynchronous callable"
"Can handle multiple requests concurrently in single thread using event loop"
Allows servers to use async/await and event loop

ASGI isn't "faster" as a specification. It's that ASGI permits async code, which allows servers like Uvicorn to handle I/O-bound requests more efficiently than thread-based WSGI servers like Gunicorn.

## Request Flow: ASGI vs WSGI

### ASGI (Async) Flow:

**Request 1 arrives:**

1. Server (Uvicorn) receives HTTP request
2. Server converts to Python dict (scope)
3. Server calls FastAPI application as a function with that dict
4. FastAPI performs validation and conversion
5. FastAPI executes the route callback function
6. Inside callback: `await db.add()` — Python sees this `await`
7. Python asks the event loop to handle it
8. Event loop delegates the I/O operation to the OS
9. Event loop signals to server: "I'm free, bring more requests if they come"
10. **Main thread is now free** while OS handles the database operation

**Request 2 arrives (while Request 1's DB call is still processing):**

1. Server receives the new HTTP request
2. Server converts to Python dict
3. Server calls FastAPI application again (same process)
4. FastAPI handles Request 2 on the same thread
5. **Both requests are being handled concurrently** — Request 1 waiting for DB, Request 2 being processed

This way, one thread handles multiple requests without blocking.

---

### WSGI (Sync) Flow:

**Request 1 arrives:**

1. Server (Gunicorn) receives HTTP request
2. Server converts to Python dict (environ)
3. Server calls Django/Flask application
4. Application executes route callback
5. Inside callback: `db.add()` (blocking call)
6. **Thread is blocked** — sits idle waiting for database
7. Thread cannot handle anything else until DB responds

**Request 2 arrives (while Request 1's DB call is still processing):**

1. Server receives the new request
2. **Cannot forward to the same worker** — it's blocked
3. Server either:
   - Queues the request (waits for worker to be free)
   - Uses another worker thread/process (if available)
   - Rejects the request (if no workers available and queue is full)

To handle concurrent requests, WSGI servers need **multiple worker threads/processes** running simultaneously, each handling one request at a time.

---

### Key Differences:

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
- ✅ Better for CPU-bound operations

---

### Why ASGI is "Faster":

ASGI isn't just fast because it handles more requests simultaneously — it's **optimized for I/O-bound workloads**:

1. **Less memory overhead:** 1 thread vs. 100 threads for 100 concurrent requests
2. **No context switching:** OS doesn't switch between threads constantly
3. **Better resource utilization:** Thread doesn't sit idle during I/O waits
4. **Higher throughput:** Can handle thousands of concurrent connections on single process

**Important:** For CPU-bound tasks (heavy computation), async provides no benefit since the thread is actually working, not waiting for I/O. WSGI with multiple processes can be better for CPU-intensive work.

---

### Visual Comparison:

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

If we don't use async/await, even if we use ASGI, the concurrent request handling won't work efficiently. Without async/await, you'll fall back to traditional threaded/process-based concurrency, losing the main advantage of ASGI. so without async await You're basically using ASGI like WSGI.

WSGI/ASGI is NOT middleware. It's a specification (just rules/contract) that is built into the server.
There is no separate middleware layer. The server itself does the conversion (HTTP request → Python dict, Python response → HTTP response) following the WSGI/ASGI specification rules. No middleware, Server directly converts and calls your app

so 
When you use an ASGI server like Uvicorn with FastAPI and use async/await in your route handlers, concurrent requests are handled automatically. You don't need to do anything extra - Uvicorn handles multiple requests concurrently using async I/O under the hood.
Just make sure your route handler is defined as async def and you use await for I/O operations (like database calls, HTTP requests, etc.).

so,
In FastAPI, it only works with ASGI servers which support asynchronous request-response, and FastAPI also supports asynchronous request-response - this is why it's faster.

In Django, it supports both ASGI and WSGI. So in Django, if we use async/await but use a WSGI server, then nothing will happen since WSGI servers do not support asynchronous request-response - the WSGI server will just block and wait, turning your async code back into synchronous execution, so you won't get any async benefits.

But if we use an ASGI server, even in that case it will not be as fast as FastAPI because Django is built for synchronous request-response - async was added later so it is not as optimized as FastAPI.

So for asynchronous request-response to work, both the server and application layer must support it. If one supports it but the other does not, then it will not work.

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

### ORM

When we define a class in JS/Python that maps to a table/collection:

- Class name maps to table/collection name
- The type of each field inside the class maps to each column type of that table (or field type in a document)
- Each instance (object) of that class maps to each row of that table (or document in a collection)

So we're connecting objects and relations (tables) by mapping everything in that class to that table/collection — that's why it's called Object-Relational Mapper (ORM) for SQL databases, or Object-Document Mapper (ODM) for NoSQL document databases like MongoDB.

We need this because when working with Python/JS, we'd have to manually convert class objects to SQL queries (or MongoDB queries), which is cumbersome, very error-prone, complex, and difficult to maintain since two different languages exist in one file. That's why these tools exist — they give us functions we can call, and behind the scenes those queries are generated and executed. We just write code in Python/JS. This is why ORMs and ODMs exist.

So these ODM/ORM tools let us:

- Define models (classes) for collections/tables
- Validate data automatically
- Query and update documents/rows using Python/JS syntax instead of raw MongoDB/SQL queries

To work with FastAPI and PostgreSQL, we need a PostgreSQL driver and optionally SQLAlchemy. SQLAlchemy is an ORM, which is optional — we can communicate with PostgreSQL directly using Python and the driver alone, but it becomes complex, cumbersome, and harder to manage. The driver, however, is mandatory. It functions as the communication layer through which we send SQL queries to the actual PostgreSQL server — similar to how pgAdmin or the psql CLI communicates with PostgreSQL.

The driver itself isn't the DBMS; the PostgreSQL server is the DBMS that stores, manages, and processes data.

- **psycopg2** (sync) / **asyncpg** (async) → drivers that communicate with the PostgreSQL server
- **SQLAlchemy** → ORM layer built on top of the driver. Since the driver is the only medium to communicate with the server, SQLAlchemy (or any ORM/ODM) is built on top of these drivers so that communication happens successfully
- **pgAdmin** / **psql** → client tools that also communicate with the PostgreSQL server using a driver

psql and pgAdmin are tools that provide a command-line or graphical interface for interacting with PostgreSQL server. Behind the scenes, they use database drivers (such as libpq for psql) to handle the actual communication with the PostgreSQL database server.

Mongoose (NoSQL - MongoDB ODM) → works only with JavaScript/TypeScript (Node.js).
Mongoengine or Motor (NoSQL - MongoDB ODM) → works only with Python.
Prisma (SQL/NoSQL ORM) → works only with JavaScript/TypeScript.
SQLAlchemy (SQL ORM) → works only with Python.

### autocommit && autoflush

session = sessionLocal()

user1 = User(name="Alice")
user2 = User(name="Bob")
user3 = User(name="Charlie")

session.add(user1)
session.add(user2)
session.add(user3)

### NOW you want to query: How many users are in the database?

**autocommit=False && autoflush=True:** Changes are temporarily sent to DB during queries (visible only in this session, count=110), but not permanent until `commit()` — other sessions see count=100.

**autocommit=False && autoflush=False:** Changes stay in Python memory, never touch DB until `commit()` (even this session sees count=100) — gives full control, fewer DB calls, better performance.

**autocommit=True && autoflush=True:** Changes are immediately flushed and permanently committed to DB automatically (all sessions see count=110) — no control, no rollback, everything saves instantly.

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

---

### **Case 1: autocommit=False, autoflush=True**

```python
What happens:
1. session.add(user1) → Stays in memory
2. session.add(user2) → Stays in memory
3. session.add(user3) → Stays in memory
4. session.query(User).count() → ⚠️ AUTOFLUSH triggers!
   - SQLAlchemy sends INSERT for Alice, Bob, Charlie to database (temporary, in transaction)
   - Then runs the COUNT query
   - Count includes Alice, Bob, Charlie
5. No commit() yet → Changes are NOT permanent, other sessions can't see them

Result: Count = (original users + 3)
Database calls: 3 INSERT queries + 1 COUNT query = 4 database operations
```

---

### **Case 2: autocommit=False, autoflush=False**

```python
What happens:
1. session.add(user1) → Stays in memory
2. session.add(user2) → Stays in memory
3. session.add(user3) → Stays in memory
4. session.query(User).count() → No autoflush!
   - Runs COUNT query directly without sending Alice, Bob, Charlie
   - Count does NOT include Alice, Bob, Charlie (they're still only in Python memory)
5. No commit() yet → Changes are NOT in database at all

Result: Count = (original users only, NO new users counted)
Database calls: 1 COUNT query = 1 database operation
```

## sessionmaker

sessionmaker is a class
sessionLocal = sessionmaker(...) creates an instance of sessionmaker, BUT this instance itself is also a callable class.
db = sessionLocal() calls that callable session class to create an actual session instance which we use to interact with the database.

### database_models.Base.metadata.create_all(bind=engine)

create_all() is smart — it checks if the table already exists in the database. If the table exists, it does nothing. If the table doesn't exist, it creates it. So restarting the server won't duplicate tables.

Base is a base class provided by SQLAlchemy. When you create your model classes (like Product) and inherit from Base, SQLAlchemy automatically tracks all the metadata about that class — table name, column names, column types, primary keys, etc.

so,
Here's what's happening:

Base.metadata contains all the information about ALL the tables (models) you defined that inherit from Base
create_all(bind=engine) takes all that metadata and generates the SQL CREATE TABLE statements
It executes those statements on the database (using the engine) to create the actual tables
But it only creates tables that don't already exist

### db

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

### yield in python

We need an extra method like `next()` to work with `yield`. It's like a `return` statement, but instead of returning and exiting the function, it returns a value and pauses the function execution. The catch is, after returning, the function call is paused. When we call `next()` one more time, the function resumes execution until the next `yield`. If there is no more `yield` and we hit the end of the function (closing `}`) or a `return` statement, then the function execution is permanently finished. Now calling `next()` will raise a `StopIteration` exception.


### Dependency Injection
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
FastAPI calls `get_db()`, which runs until `yield db` and pauses. FastAPI injects that `db` object into `get_all_products()` parameter, so `get_all_products()` continues its execution. FastAPI does NOT go back to `get_db()` immediately after injecting `db`. It waits until `get_all_products()` completely finishes, THEN it goes back to `get_db()` and runs the rest of the code (the `finally` block) automatically.

**Why use dependency injection over manual function calls?**
If we manually call `get_db()`, we'd have to remember to use `next()` since the function execution is paused after `yield`. But with dependency injection, all of this is handled automatically by FastAPI — no extra code, no manual `next()` calls, nothing. We just declare the dependency and FastAPI handles everything on behalf of us. This way we can reuse the same session management multiple times, and managing sessions becomes easy and consistent across all routes.


### If the client is sending JSON (which is already key-value pairs like a dictionary), why can't we directly unpack that JSON response? Why do we need the conversion using model_dump()? Because model_dump() converts to a dictionary, but we're already getting a dictionary as JSON, right?

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

**Will it work?** No, because SQLAlchemy models cannot be used to validate request/response data. When a request comes in as JSON, FastAPI sees it doesn't match the data type and tries to convert it, but it cannot convert it because FastAPI only converts Pydantic data types — it doesn't know about SQLAlchemy models. So it will throw an error.

---

**Why we need both models:**

- **Pydantic models** (`Product` from `models.py`) → for FastAPI request/response validation and conversion
- **SQLAlchemy models** (`database_models.Product`) → for database operations

---

**Remember:**

If there are predefined types like `int`, `float`, `str`, then FastAPI can validate the request and try to convert it automatically if the request data type doesn't match. But if there is a custom type, we must define types with Pydantic, because for custom type checking, validation, and conversion, FastAPI only supports Pydantic. So we must define a Pydantic model and use it as the parameter type so that FastAPI can validate and convert the incoming JSON.

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

### FastAPI's Parameter Detection
- If a parameter name appears in the route path with {}, it's a path parameter.

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

- If a parameter is a Pydantic model or marked with Body(), it comes from the request body.
```python
@app.put("/product")
def update_product(id: int, product: Product, ...):
    # FastAPI knows:
    # - product = request body (Pydantic model)
```

- If a parameter has = Depends(...), it's a dependency injection.
```python
def update_product(id: int, product: Product, db: Session = Depends(get_db)):
    # FastAPI knows:
    # - db = dependency (injected by FastAPI)
```
### now what if we wanted make sure this parameter must come from body?
method 1: Use Body() for simple types
```python
@app.put("/product")
def update_product(id: int = Body(), product: Product)
```

```js
fetch(`/product`, {
    method: 'PUT',
    body: JSON.stringify({
        id: 5,  // ← id in body now
        name: "Phone", 
        price: 699.99
    })
})
```
If we send both id and product data in one request body, but the controller expects two separate parameters, does FastAPI automatically extract and map them, or do we need to do it manually?

FastAPI receives the entire JSON body, then automatically extracts and maps each field to the corresponding parameter:

id: 5 → goes to id parameter
name, price, etc. → goes to product parameter (remaining fields form the Pydantic model)

FastAPI is smart enough to separate the JSON body into multiple parameters based on their names and types. No manual extraction needed!


Method 2: Include it in your Pydantic model (Best Practice)
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
    method: 'PUT',
    body: JSON.stringify({
        id: 5,
        name: "Phone",
        price: 699.99,
        // ... all fields
    })
})
```

method 3 wrapper
```python
@app.put("/product")
def update_product(product: Product = Body(embed=True))
```

```js
fetch(`/product`, {
    method: 'PUT',
    body: JSON.stringify({
        product: {  // ← Notice the wrapper
            id: 5,
            name: "Phone",
            price: 699.99
        }
    })
})
```
If we use Body(embed=True), Pydantic model comes from body with a wrapper key (the wrapper key name = parameter name)

FastAPI is smart — it looks at the route definition and parameter types to automatically figure out where each parameter should come from. No manual configuration needed!


### response model
In FastAPI, Pydantic models are required to validate and convert request/response data types. For database operations with an ORM, we need separate SQLAlchemy models since Pydantic models cannot be understood by the ORM — the ORM needs its own model types.

Even though APIs return JSON, Pydantic models are also needed to validate the response so that we can ensure the route function returns the correct structure. This prevents accidentally returning wrong fields or types and exposing sensitive fields (like passwords). It also ensures that the function returns correct types so that JSON conversion by FastAPI is error-free, since certain types cannot be converted to JSON easily by FastAPI (for example, `datetime` objects, `Decimal`, `set`, or custom classes need proper serialization).

**Example:** Suppose the return type must have `userId` which is type `int`, and we return `{"user_id": "abc"}`. Without response validation, this will be converted to JSON by FastAPI automatically and sent to the user with no error. But if we validate the response with a Pydantic model:

```python
@app.get("/user", response_model=UserResponse)
def get_user():
    return {"user_id": "abc"}  # FastAPI catches this type error before sending!
```

FastAPI will raise a validation error because `"abc"` is a string, not an integer, preventing the incorrect response from reaching the client.

**So response validation = catches bugs before they reach clients, ensures API contract consistency, and handles proper JSON serialization of complex types.**


When does FastAPI start the event loop - at server start or when it sees async keyword?
At server start!
When you run uvicorn main:app, FastAPI (through Uvicorn) starts the event loop immediately and keeps it running. Then:


If route is async def → FastAPI runs it in the event loop (non-blocking)
If route is regular def → FastAPI runs it in a thread pool (to avoid blocking the event loop)

## What is Annotated?
Annotated is just a wrapper that lets you add extra instructions to a variable's type
Think of it like putting a sticky note on a variable that says "hey, this variable needs special handling!"

```python
def get_info(info: Annotated[str, Header()]):
    pass
```
str = the type (it's a string)
Header() = extra instruction (get this from HTTP headers)

Typing means telling Python what type of data a variable should be. A typing feature is just a tool Python gives you to describe types better. Annotated is one such tool - it lets you say "this is a string, AND here's extra info about it."

it's just extra information that tools like FastAPI can read and use.

## middleware
Once you define a middleware with @app.middleware("http"), it applies to ALL endpoints in your FastAPI app, regardless of whether the endpoints are defined before or after the middleware,it applied to all endpoints.

## Can you exclude specific endpoints from middleware?
yes but manually, 

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
## can we apply middleware to only specific paths?
yes there few options to achieve that 

### **Option 1: Middleware with Path Check**

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

## **Option 2: Dependency (Recommended)**

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

---

## **Option 3: Sub-Application**

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
,
ALL routes under /about/* are automatically protected! That's the power of sub-applications,
 /about, /about/name, /about/details

in real life we use this
`app.mount("/admin", admin_app)`

this way 

http://localhost:8000/ → Public, no auth middleware
http://localhost:8000/products → Public, no auth middleware
http://localhost:8000/admin/dashboard → Auth middleware runs
http://localhost:8000/admin/settings → Auth middleware runs

Define two FastAPI apps: public routes go in the main app, protected routes go in the sub-app. Mount the sub-app at a specific path (like /admin), and all its routes automatically become protected under that prefix. This also keeps protected and public routes clearly separated in your code.
---

## Which One to Use?

- **Option 1** (Middleware): Simple, but messy if you have many protected routes
- **Option 2** (Dependency): **BEST** - Clean, reusable, FastAPI way
- **Option 3** (Sub-app): Good when you have many protected routes grouped together

## templates
FastAPI only comes with the integration layer (Jinja2Templates class) built-in. But the actual Jinja2 templating engine itself is NOT included - you have to install it separately

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()
templates = Jinja2Templates(directory="template")

data = ["rohit", "virat", "Hardik"]


@app.get("/", response_class=HTMLResponse)
async def home(req: Request):
    return templates.TemplateResponse("index.html", {"request": req, "data": data})
```
now we can access this data and request inside the index.html