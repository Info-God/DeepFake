from web3 import Web3
import json
from solcx import compile_standard, install_solc
from utils import file_sha256
import sys, os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Install Solidity compiler if not already
install_solc("0.8.0")

GANACHE_URL = os.getenv("GANACHE_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
assert w3.is_connected(), "❌ Ganache not connected"

with open("contract/MediaRegistry.sol", "r") as f:
    source = f.read()

compiled_sol = compile_standard({
    "language": "Solidity",
    "sources": {"MediaRegistry.sol": {"content": source}},
    "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}}
}, solc_version="0.8.0")

# Extract ABI and bytecode
abi = compiled_sol["contracts"]["MediaRegistry.sol"]["MediaRegistry"]["abi"]
bytecode = compiled_sol["contracts"]["MediaRegistry.sol"]["MediaRegistry"]["evm"]["bytecode"]["object"]

MediaRegistry = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)

tx = MediaRegistry.constructor().build_transaction({
    "chainId": 1337,
    "from": ACCOUNT_ADDRESS,
    "nonce": nonce,
    "gas": 3000000,
    "gasPrice": w3.to_wei("20", "gwei")
})

signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"✅ Deployed contract address: {tx_receipt.contractAddress}")

# Save ABI + address
os.makedirs("contract", exist_ok=True)
with open("contract/MediaRegistry.json", "w") as f:
    json.dump({
        "address": tx_receipt.contractAddress,
        "abi": abi
    }, f, indent=2)

# --- Register video ---
if len(sys.argv) < 3:
    print("Usage: python deploy_and_register.py video.mp4 'Description'")
    sys.exit(1)

video_path = sys.argv[1]
desc = sys.argv[2]
video_hash = file_sha256(video_path)
print("Video sha256:", video_hash)

contract_instance = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)

tx = contract_instance.functions.registerMedia(video_hash, desc).build_transaction({
    "chainId": 1337,
    "from": ACCOUNT_ADDRESS,
    "nonce": nonce,
    "gas": 300000,
    "gasPrice": w3.to_wei("20", "gwei")
})
signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print("✅ Registered on chain. Tx:", tx_receipt.transactionHash.hex())
