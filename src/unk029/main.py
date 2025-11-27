from fastapi import FastAPI
from unk029 import accounts

app = FastAPI()



@app.get("/account/{account_no}")
def get_account(account_no: int):
    return accounts.get_account(account_no)

@app.post("/account")
def create_account(account: accounts.AccountCreate):
    return accounts.create_account(account)

@app.patch("/account/{account_no}/topup")
def topup_account(account_no: int, topup: accounts.TopUp):
    return accounts.topup_account(account_no, topup)

@app.patch("/account/{account_no}/withdraw")
def withdraw_account(account_no: int, withdraw: accounts.WithDraw):
    return accounts.withdraw_account(account_no, withdraw)