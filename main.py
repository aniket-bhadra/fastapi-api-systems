from fastapi import FastAPI
from models import Product
app = FastAPI()

@app.get("/")
def greet():
   return "welcome to new learning!!"

products = [
    Product(id=1, name="Phone", description="A smartphone", price=699.99, quantity=50),
    Product(id=2, 
]

@app.get("/products")
def get_all_products():
   return products