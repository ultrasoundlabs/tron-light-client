import grpc
from api import api_pb2, api_pb2_grpc
import sys
from hashlib import sha256

grpc_server = "grpc.trongrid.io:50051"
channel = grpc.insecure_channel(grpc_server)
stub = api_pb2_grpc.WalletStub(channel)

def get_tx_by_id(tx_id):
    request = api_pb2.BytesMessage()
    request.value = tx_id
    
    tx = stub.GetTransactionById(request)
    
    return tx

if __name__ == "__main__":
    tx = get_tx_by_id(bytes.fromhex(sys.argv[1]))
    print(tx)
    print("encoded:", tx.SerializeToString().hex())