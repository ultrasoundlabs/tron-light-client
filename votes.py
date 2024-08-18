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

def read_varint(arr):
    shift = 0
    result = 0
    offset = 0
    while True:
        i = arr[offset]
        result |= (i & 0x7f) << shift
        shift += 7
        if not (i & 0x80):
            break
        offset += 1

    return result, offset + 1

def parse_vote_tx(tx):
    assert tx[-1] == 1 # ret.contractRet: SUCCESS (THIS THING IS CRITICAL!!!)

    assert tx[0] & 7 == 2 # LEN
    assert tx[0] >> 3 == 1 # 1:
    length, offset = read_varint(tx[1:]) # raw_data length
    offset += 1
    
    # skipping unnecessary protobuf elements
    while True:
        t = tx[offset]
        if t == 0x5a: # 11: LEN
            break
        offset += 1
        if t & 7 == 5:
            offset += 4
        else:
            length, v = read_varint(tx[offset:])
            offset += v + (length * (t & 7 == 2))

    assert tx[offset] & 7 == 2 # LEN
    assert tx[offset] >> 3 == 11 # 11:
    offset += 1
    length, v = read_varint(tx[offset:]) # contract length
    offset += v

    assert tx[offset] & 7 == 0 # VARINT
    assert tx[offset] >> 3 == 1 # 1: (we enter the contract protobuf)
    offset += 1
    call_type, v = read_varint(tx[offset:]) # contract call type
    offset += v

    assert call_type == 4 # VoteWitnessContract

    assert tx[offset] & 7 == 2 # LEN
    assert tx[offset] >> 3 == 2 # 2:
    offset += 1
    length, v = read_varint(tx[offset:]) # container length
    offset += v

    assert tx[offset] & 7 == 2 # LEN
    assert tx[offset] >> 3 == 1 # 1:
    offset += 1
    length, v = read_varint(tx[offset:]) # type_url length
    offset += v

    assert tx[offset:offset+length] == b"type.googleapis.com/protocol.VoteWitnessContract" # this is unnecessary because we verified the type == 31
    offset += length

    assert tx[offset] & 7 == 2 # LEN
    assert tx[offset] >> 3 == 2 # 2:
    offset += 1
    length, v = read_varint(tx[offset:]) # TriggerSmartContract length ?
    offset += v

    assert tx[offset] & 7 == 2 # LEN
    assert tx[offset] >> 3 == 1 # 1:
    offset += 1
    length, v = read_varint(tx[offset:]) # owner_address length
    offset += v

    voter = tx[offset:offset+length][1:] # strip 0x41
    offset += length

    votes = []

    while True:

        if tx[offset] & 7 != 2 or tx[offset] >> 3 != 2:
            break
        offset += 1
        length, v = read_varint(tx[offset:])
        offset += v

        assert tx[offset] & 7 == 2 # LEN
        assert tx[offset] >> 3 == 1 # 1:
        offset += 1
        length, v = read_varint(tx[offset:]) # witness_address length
        offset += v

        witness_address = tx[offset:offset+length][1:] # strip 0x41
        offset += length

        assert tx[offset] & 7 == 0 # VARINT
        assert tx[offset] >> 3 == 2 # 2: (we enter the contract protobuf)
        offset += 1
        votes_count, v = read_varint(tx[offset:]) # contract call type
        offset += v

        votes.append((witness_address, votes_count))
    
    return voter, votes

if __name__ == "__main__":
    start_block = 62913164
    for i in range(1000):
        block = get_block_by_number(start_block+i)
        for tx in block.transactions:
            if tx.transaction.raw_data.contract[0].type == 4:
                print(parse_vote_tx(tx.transaction.SerializeToString()))