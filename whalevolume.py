import grpc
from core import Tron_pb2, Tron_pb2_grpc
from core.contract import smart_contract_pb2
from api import api_pb2, api_pb2_grpc
from eth_account import Account
from hashlib import sha256
from base58 import b58decode_check, b58encode_check
import requests
import matplotlib.pyplot as plt

grpc_server = "grpc.trongrid.io:50051"
channel = grpc.insecure_channel(grpc_server)
stub = api_pb2_grpc.WalletStub(channel)

def get_account_resource(address):
    request = Tron_pb2.Account()
    request.address = address
    
    account = stub.GetAccountResource(request)
    
    return account

def get_block_by_number(block_number):
    request = api_pb2.NumberMessage()
    request.num = block_number
    
    block = stub.GetBlockByNum2(request)
    
    return block

def get_now_block():
    request = api_pb2.EmptyMessage()
    block = stub.GetNowBlock2(request)
    return block

def get_public_tag(address):
    return requests.get(f"https://apilist.tronscanapi.com/api/accountv2?address={address}", headers={"TRON-PRO-API-KEY": "5b9e3a55-3956-47ba-93b3-c523cc3d527c"}).json().get("publicTag")

if __name__ == "__main__":
    usdt_holders = [x.split(",")[1] for x in open("usdtholders.csv").readlines()[1:]]
    
    total_txs = 0
    total_whale_txs = 0
    transfers = {}
    
    latest_block = get_now_block().block_header.raw_data.number
    limit = 1000
    for i in range(limit):
        block = get_block_by_number(latest_block - i)
        print("checking block %d (%d/%d)" % (latest_block - i, i, limit))

        for tx in block.transactions:
            if tx.transaction.raw_data.contract[0].type != 31: continue
            
            call = smart_contract_pb2.TriggerSmartContract()
            call.ParseFromString(tx.transaction.raw_data.contract[0].parameter.value)

            if call.contract_address != b58decode_check("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"): continue

            _from = b58encode_check(call.owner_address).decode()
            to = b58encode_check(call.data[15:36]).decode()

            total_txs += 1

            if to in usdt_holders:
                print("found CEX receiver's transfer to", to)
                transfers["CEX receiver"] = transfers.get("CEX receiver", 0) + 1
                continue

            if _from in usdt_holders:
                print("found USDT transfer from", _from)
                transfers[_from] = transfers.get(_from, 0) + 1
                total_whale_txs += 1
    
    print("total %d USDT transfers" % total_txs)

    transfers = dict(sorted(transfers.items(), key=lambda item: item[1], reverse=True))

    for address in list(transfers.keys())[:20]:
        tag = get_public_tag(address)
        if tag is not None:
            transfers[tag] = transfers[address]
            del transfers[address]
    
    transfers = dict(sorted(transfers.items(), key=lambda item: item[1], reverse=True))
    
    transfers["Others"] = total_txs - total_whale_txs

    print(transfers)

    # Generate pie chart
    labels = []
    sizes = []
    for tag, txs in transfers.items():
        labels.append(f"{tag}\n{txs} ({txs/total_txs:.1%})")
        sizes.append(txs)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    plt.title(f"Whale Transactions Volume\n(exluding transfers from CEX receivers)\nTotal Transfers: {total_txs}")
    plt.tight_layout()
    plt.savefig('whale_transfer_distribution.png')
    plt.show()