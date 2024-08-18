import grpc
from api import api_pb2, api_pb2_grpc

grpc_server = "grpc.trongrid.io:50051"
channel = grpc.insecure_channel(grpc_server)
stub = api_pb2_grpc.WalletStub(channel)

def get_block_by_number(block_number):
    request = api_pb2.NumberMessage()
    request.num = block_number
    
    block = stub.GetBlockByNum2(request)
    
    return block

if __name__ == "__main__":
    start_block = 62913164
    for i in range(1000):
        block = get_block_by_number(start_block+i)
        for tx in block.transactions:
            if tx.transaction.raw_data.contract[0].type == 4:
                print(tx.transaction.SerializeToString().hex())