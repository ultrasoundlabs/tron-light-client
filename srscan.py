import grpc
from api import api_pb2, api_pb2_grpc
from core import Tron_pb2

grpc_server = "grpc.trongrid.io:50051"
channel = grpc.insecure_channel(grpc_server)
stub = api_pb2_grpc.WalletStub(channel)

def get_block_by_number(block_number):
    request = api_pb2.NumberMessage()
    request.num = block_number
    
    block = stub.GetBlockByNum2(request)
    
    return block

def get_latest_block_number():
    request = api_pb2.EmptyMessage()
    
    block = stub.GetNowBlock2(request)
    
    # it seems to be protobuf but there's no such structure in protos and we only need i64 at the start
    return int.from_bytes(block.blockid[:8])

if __name__ == "__main__":
    latest = get_latest_block_number()
    depth = 1000

    srs = []
    
    for block_number in range(latest-depth, latest):
        print(block_number)
        block = get_block_by_number(block_number)
        proposer = block.block_header.raw_data.witness_address
        if proposer not in srs:
            srs.append(proposer)
    
    print("\n".join([x.hex() for x in srs]))
    print("total %d unique SRs" % len(srs))