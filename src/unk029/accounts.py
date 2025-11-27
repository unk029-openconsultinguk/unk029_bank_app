import oracledb
import os
from dotenv import load_dotenv
from contextlib import contextmanager
from pydantic import BaseModel
from fastapi import HTTPException

load_dotenv()

ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")
ORACLE_DSN = os.getenv("ORACLE_DSN")

def get_connection():
    return oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)

@contextmanager
def get_cursor():
    conn = get_connection()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    finally:
        cur.close()
        conn.close()

class AccountCreate(BaseModel):
    name: str
    balance: float

class TopUp(BaseModel):
    amount: float

class WithDraw(BaseModel):
    amount: float


def get_account(account_no: int):
    with get_cursor() as cur:
        cur.execute("SELECT account_no, name, balance FROM accounts WHERE account_no = :id", {"id": account_no})
        row = cur.fetchone()
        if row:
            return {"account_no": row[0], "name": row[1], "balance": row[2]}
        raise HTTPException(status_code=404, detail="Account not found")



def create_account(account: AccountCreate):
    with get_cursor() as cur:
        acc_no_var = cur.var(int)
        cur.execute(
            "INSERT INTO accounts (name, balance) VALUES (:name, :balance) RETURNING account_no INTO :acc_no",
            {"name": account.name, "balance": account.balance, "acc_no": acc_no_var}
        )
        account_no = acc_no_var.getvalue()
        return {"account_no": account_no, "name": account.name, "balance": account.balance}




def topup_account(account_no: int, topup: TopUp):
    with get_cursor() as cur:
        cur.execute("SELECT name, balance FROM accounts WHERE account_no = :id", {"id": account_no})
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        name, balance = row
        new_balance = balance + topup.amount
        cur.execute("UPDATE accounts SET balance = :balance WHERE account_no = :id", {"balance": new_balance, "id": account_no})
        return {"account_no": account_no, "name": name, "new_balance": new_balance}

def withdraw_account(account_no: int, withdraw: WithDraw):
    with get_cursor() as cur:
        cur.execute("SELECT name, balance FROM accounts WHERE account_no = :id", {"id": account_no})
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        name, balance = row
        if withdraw.amount > balance:
            raise HTTPException(status_code=400, detail="Insufficient funds")
        new_balance = balance - withdraw.amount
        cur.execute("UPDATE accounts SET balance = :balance WHERE account_no = :id", {"balance": new_balance, "id": account_no})
        return {"account_no": account_no, "name": name, "new_balance": new_balance}
