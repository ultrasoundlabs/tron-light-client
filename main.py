import grpc
from api import api_pb2, api_pb2_grpc
import ecdsa
from hashlib import sha256
from eth_utils import keccak

grpc_server = "grpc.trongrid.io:50051"
channel = grpc.insecure_channel(grpc_server)
stub = api_pb2_grpc.WalletStub(channel)

def get_block_by_number(block_number):
    request = api_pb2.NumberMessage()
    request.num = block_number
    
    block = stub.GetBlockByNum2(request)
    
    return block

def verify_block_header(block_header) -> bool:
    message_hash = sha256(block_header.raw_data.SerializeToString()).digest()
    witness_address = block_header.raw_data.witness_address
    signature_bytes = block_header.witness_signature

    r = int.from_bytes(signature_bytes[:32])
    s = int.from_bytes(signature_bytes[32:64])
    v = signature_bytes[64]
    
    if v >= 27:
        v -= 27

    sig = ecdsa.util.sigencode_string(r, s, 2**256-1)
    vk = ecdsa.VerifyingKey.from_public_key_recovery_with_digest(
        sig,
        message_hash,
        curve=ecdsa.SECP256k1,
        hashfunc=sha256
    )[v]

    recovered_address = b"\x41" + keccak(vk.to_string())[12:]

    return witness_address == recovered_address

if __name__ == "__main__":
    block_number = 1000000
    block = get_block_by_number(block_number)
    
    assert verify_block_header(block.block_header)