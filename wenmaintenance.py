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

def get_now_block():
    request = api_pb2.EmptyMessage()
    block = stub.GetNowBlock2(request)
    return block

if __name__ == "__main__":
    block = get_now_block()
    print("latest block:", block.block_header.raw_data.number)
    latest_number = block.block_header.raw_data.number
    latest_timestamp = block.block_header.raw_data.timestamp

    for i in range(1, 10000):
        block = get_block_by_number(latest_number - i)
        block_timestamp = block.block_header.raw_data.timestamp
        print("block %d timestamp: %d" % (latest_number - i, block_timestamp))
        if latest_timestamp - block_timestamp != 3000:
            print("block %d timestamp was made after %d seconds" % (latest_number - i +1, (latest_timestamp - block_timestamp) / 1000))
            break
        latest_timestamp = block_timestamp