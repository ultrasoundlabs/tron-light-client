import grpc
from api import api_pb2, api_pb2_grpc
from eth_account import Account
from hashlib import sha256

grpc_server = "grpc.trongrid.io:50051"
channel = grpc.insecure_channel(grpc_server)
stub = api_pb2_grpc.WalletStub(channel)

def get_block_by_number(block_number):
    request = api_pb2.NumberMessage()
    request.num = block_number
    
    block = stub.GetBlockByNum2(request)
    
    return block

if __name__ == "__main__":
    block = get_block_by_number(62913164)
    for tx in block.transactions:
        print(tx)
        address = b"\x41" + bytes.fromhex(Account._recover_hash(sha256(tx.transaction.SerializeToString()).digest(), signature=tx.transaction.signature[0][:65])[2:])
        print(address)