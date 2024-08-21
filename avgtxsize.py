import grpc
from api import api_pb2, api_pb2_grpc
from core.contract import smart_contract_pb2
from base58 import b58decode_check
from random import randint

grpc_server = "grpc.trongrid.io:50051"
channel = grpc.insecure_channel(grpc_server)
stub = api_pb2_grpc.WalletStub(channel)

def get_block_by_number(block_number):
    request = api_pb2.NumberMessage()
    request.num = block_number
    
    block = stub.GetBlockByNum2(request)
    
    return block

def get_latest_block():
    block = stub.GetNowBlock2(api_pb2.EmptyMessage())
    
    return block

if __name__ == "__main__":
    start_block = 60000000
    end_block = int.from_bytes(get_latest_block().blockid[:8])

    _from = b58decode_check("TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf")
    transfers = []
    limit = 10000
    f = open("dump.txt", "w")

    for i in range(limit):
        block_number = randint(start_block, end_block)
        block = get_block_by_number(block_number)
        print("checking block %d (%d/%d)" % (block_number, i, limit))

        for tx in block.transactions:
            if tx.transaction.raw_data.contract[0].type != 31: continue
            
            call = smart_contract_pb2.TriggerSmartContract()
            call.ParseFromString(tx.transaction.raw_data.contract[0].parameter.value)

            if call.contract_address != b58decode_check("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"): continue

            if call.owner_address != _from: continue

            amount = int.from_bytes(call.data[36:]) / 1e6
            print("%d USDT out" % amount)
            if amount < 1000000: # otherwise it's probably an internal cross-wallet tranfer
                transfers.append(amount)
                f.write(str(amount) + "\n")
    
    transfers.sort()
    print("total %d transfers" % len(transfers))
    print("avg transfer amount: %d" % (sum(transfers) / len(transfers)))
    print("median transfer amount: %d" % (transfers[len(transfers) // 2]))