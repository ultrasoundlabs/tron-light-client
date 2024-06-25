import grpc, sys
from api import api_pb2, api_pb2_grpc
from time import time

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
    depth = int(sys.argv[1])

    srs = {}
    
    start = time()
    for epoch in range(depth):
        epoch_block = latest-(epoch*7200)
        for block_number in range(epoch_block, epoch_block+27):
            print(block_number)
            block = get_block_by_number(block_number)
            proposer = block.block_header.raw_data.witness_address
            srs[proposer] = srs.get(proposer, 0)+1
    
    elapsed = time()-start
    print("\n".join([x.hex() for x in srs.keys()]))
    print("total %d unique SRs" % len(srs))
    print("scraped in %f sec, avg %fepochs/s" % (elapsed, depth/elapsed))