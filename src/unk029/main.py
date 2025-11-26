"""FastAPI application for Bank App."""

from fastapi import FastAPI
from unk029 import add

app = FastAPI(
    title="Bank App API",
    description="A simple bank app API with FastAPI",
    version="0.1.0",
)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to Bank App API"}


@app.get("/add")
def add_numbers(a: int, b: int):
    """Add two numbers together.
    
    Parameters:
    - a: First number
    - b: Second number
    
    Returns:
    - result: Sum of a and b
    """
    return {"result": add(a, b)}


@app.get("/balance/{account_id}")
def get_balance(account_id: int):
    """Get account balance (placeholder).
    
    Parameters:
    - account_id: The account ID
    
    Returns:
    - account_id: The requested account ID
    - balance: The account balance
    """
    return {"account_id": account_id, "balance": 1000.00}
