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
    recipients = {}
    
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

            to = b58encode_check(call.data[15:36]).decode()
            if to in usdt_holders: continue

            total_txs += 1

            recipients[to] = recipients.get(to, 0) + 1
    
    print("in all %d USDT transfers:" % total_txs)
    print("total %d unique tx recipients" % len(recipients))
    recipients = dict(sorted(recipients.items(), key=lambda item: item[1], reverse=True))

    f = open("usdt_recipients.txt", "w")
    for address, txs in recipients.items():
        f.write(f"{address} {txs}\n")
    f.close()

    # Generate pie chart
    labels = []
    sizes = []
    for tag, txs in recipients.items():
        labels.append(f"{tag}\n{txs} ({txs/total_txs:.1%})")
        sizes.append(txs)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    plt.title(f"USDT Recipients Share\nTotal Recipients: {total_txs}")
    plt.tight_layout()
    plt.savefig('usdt_recipient_distribution.png')
    plt.show()