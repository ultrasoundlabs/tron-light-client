import grpc, sys, ecdsa
from api import api_pb2, api_pb2_grpc
from time import time
from hashlib import sha256

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
    for epoch in range(1, depth):
        epoch_block = latest-(epoch*7200)
        for block_offset in range(27):
            print(epoch_block + block_offset)
            block = get_block_by_number(epoch_block + block_offset)
            
            signature = block.block_header.witness_signature
            sig = ecdsa.util.sigencode_string(int.from_bytes(signature[:32]), int.from_bytes(signature[32:64]), 2**256-1)
            proposer = ecdsa.VerifyingKey.from_public_key_recovery_with_digest(
                sig,
                sha256(block.block_header.raw_data.SerializeToString()).digest(),
                curve=ecdsa.SECP256k1
            )[signature[64]].to_string()

            srs[proposer] = srs.get(proposer, 0)+1
    
    elapsed = time()-start
    keys = "\n".join([x.hex() for x in srs.keys()])
    print(keys)
    print("total %d unique SRs" % len(srs))
    print("scraped in %f sec, avg %fepochs/s" % (elapsed, depth/elapsed))
    open("srs.txt", "w").write(keys)
    print("saved in srs.txt")