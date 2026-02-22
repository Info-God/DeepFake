# save this as check_address.py
from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

private_key = os.getenv("PRIVATE_KEY")
account_address = os.getenv("ACCOUNT_ADDRESS")

w3 = Web3()

# Derive address from private key
account = w3.eth.account.from_key(private_key)
derived_address = account.address

print("=" * 50)
print("Address Check")
print("=" * 50)
print(f"Private key from .env: {private_key[:20]}...")
print(f"ACCOUNT_ADDRESS from .env: {account_address}")
print(f"Address derived from private key: {derived_address}")
print(f"Do they match? {account_address.lower() == derived_address.lower()}")