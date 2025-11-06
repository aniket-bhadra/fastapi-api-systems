from fastapi import FastAPI, Depends
from models import Product
from database import sessionLocal, engine
import database_models
from sqlalchemy.orm import Session

app = FastAPI()

# create_all() is smart — it checks if the table already exists in the database. If the table exists, it does nothing. If the table doesn't exist, it creates it. So restarting the server won't duplicate tables.

database_models.Base.metadata.create_all(bind=engine)
# This is a structural operation — it creates the table structure itself
# Uses engine directly, NO session needed


@app.get("/")
def greet():
    return "welcome to new learning!!"


products = [
    Product(id=1, name="Phone", description="A smartphone", price=699.99, quantity=50),
    Product(
        id=2, name="Laptop", description="A powerful laptop", price=999.99, quantity=30
    ),
    Product(id=3, name="Pen", description="A blue ink pen", price=1.99, quantity=100),
    Product(
        id=4, name="Table", description="A wooden table", price=199.99, quantity=20
    ),
]


def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


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


@app.get("/products")
def get_all_products(db: Session = Depends(get_db)):
    db_products = db.query(database_models.Product).all()
    return db_products


@app.get("/product/{id}")
def get_product_by_id(id: int, db: Session = Depends(get_db)):
    db_product = (
        db.query(database_models.Product)
        .filter(database_models.Product.id == id)
        .first()
    )
    if db_product:
        return db_product
    else:
        return "Product not found!!"


@app.post("/product")
def add_product(product: Product, db: Session = Depends(get_db)):
    db.add(database_models.Product(**product.model_dump()))
    db.commit()
    return "added successfully!!"


@app.put("/product")
def update_product(id: int, product: Product, db: Session = Depends(get_db)):
    db_product = (
        db.query(database_models.Product)
        .filter(database_models.Product.id == id)
        .first()
    )
    if db_product:
        db_product.name = product.name
        db_product.description = product.description
        db_product.price = product.price
        db_product.quantity = product.quantity
        db.commit()
        return "Product updated"
    else:
        return "no product found to update"


@app.delete("/product/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    db_product = (
        db.query(database_models.Product)
        .filter(database_models.Product.id == id)
        .first()
    )
    if db_product:
        db.delete(db_product)
        db.commit()
        return "product deletion completed!"
    else:
        "Product not found to delete!!"
