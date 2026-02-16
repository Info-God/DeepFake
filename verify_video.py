from web3 import Web3
import json
from utils import file_sha256

GANACHE_URL = "http://127.0.0.1:7545"

# Connect to Ganache
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
assert w3.is_connected(), "❌ Ganache not connected"

# Load contract ABI + address
with open("contract/MediaRegistry.json", "r") as f:
    contract_data = json.load(f)

contract_address = contract_data["address"]
contract_abi = contract_data["abi"]

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Compute hash of the video
video_path = "sample_video.mp4"
video_hash = file_sha256(video_path)
print("Video hash:", video_hash)

# Call verifyMedia from contract
is_registered, desc, uploader, timestamp = contract.functions.verifyMedia(video_hash).call()

if is_registered:
    print("✅ Video is registered on blockchain.")
    print("Description:", desc)
    print("Uploader:", uploader)
    print("Timestamp:", timestamp)
else:
    print("❌ Video not found on blockchain.")
