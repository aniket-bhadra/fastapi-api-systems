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