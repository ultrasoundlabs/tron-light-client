import grpc
from core import Tron_pb2, Tron_pb2_grpc
from core.contract import smart_contract_pb2
from api import api_pb2, api_pb2_grpc
from eth_account import Account
from hashlib import sha256
from base58 import b58decode_check, b58encode_check
import requests
import matplotlib.pyplot as plt

import json
import os

grpc_server = "grpc.trongrid.io:50051"
channel = grpc.insecure_channel(grpc_server)
stub = api_pb2_grpc.WalletStub(channel)

def get_now_block():
    request = api_pb2.EmptyMessage()
    block = stub.GetNowBlock2(request)
    return block

# Function to load or create config file
def load_or_create_config():
    config_file = 'config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    else:
        # Default configuration
        config = {
            "latest_block": get_now_block().block_header.raw_data.number,
            "block_limit": 1000
        }
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        return config

# Load configuration
config = load_or_create_config()

def get_account_resource(address):
    request = Tron_pb2.Account()
    request.address = address
    
    account = stub.GetAccountResource(request)
    
    return account

def get_block_by_number(block_number):
    cache_path = f"cache/{block_number}.bin"
    
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            block = api_pb2.BlockExtention()
            block.ParseFromString(f.read())
            return block
    
    request = api_pb2.NumberMessage()
    request.num = block_number
    
    block = stub.GetBlockByNum2(request)
    
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as f:
        f.write(block.SerializeToString())
    
    return block

def get_public_tag(address):
    cache_path = f"cache/tags/{address}"
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return f.read().strip()
    
    tag = requests.get(f"https://apilist.tronscanapi.com/api/accountv2?address={address}", headers={"TRON-PRO-API-KEY": "5b9e3a55-3956-47ba-93b3-c523cc3d527c"}).json().get("publicTag")
    
    if tag is not None and tag != "":
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w') as f:
            f.write(tag)
    
    return tag

if __name__ == "__main__":
    usdt_holders = [x.split(",")[1] for x in open("usdtholders.csv").readlines()[1:]]
    
    total_volume = 0
    total_transfers = 0
    tx_volume = {}
    tx_count = {}
    
    latest_block = config['latest_block']
    limit = config['block_limit']
    
    for i in range(limit):
        block = get_block_by_number(latest_block - i)
        print("checking block %d (%d/%d)" % (latest_block - i, i, limit))

        for tx in block.transactions:
            if tx.transaction.ret[0].contractRet != 1: continue # SUCCESS

            if tx.transaction.raw_data.contract[0].type != 31: continue
            
            call = smart_contract_pb2.TriggerSmartContract()
            call.ParseFromString(tx.transaction.raw_data.contract[0].parameter.value)

            if call.contract_address != b58decode_check("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"): continue

            if call.data[:4] != b"\xa9\x05\x9c\xbb": continue # transfer(address, uint256)

            _from = b58encode_check(call.owner_address).decode()
            to = b58encode_check(b"\x41" + call.data[16:36]).decode()
            value = int.from_bytes(call.data[60:68], "big") / 1000000

            if value < 1: continue # spam

            total_volume += value
            total_transfers += 1
            if _from in usdt_holders and to in usdt_holders:
                tx_volume["Internal CEX transfers"] = tx_volume.get("Internal CEX transfers", 0) + value
                tx_count["Internal CEX transfers"] = tx_count.get("Internal CEX transfers", 0) + 1
            elif _from in usdt_holders:
                tx_volume["CEX vaults (top 1000 USDT holders)"] = tx_volume.get("CEX vaults (top 1000 USDT holders)", 0) + value
                tx_count["CEX vaults (top 1000 USDT holders)"] = tx_count.get("CEX vaults (top 1000 USDT holders)", 0) + 1
            elif to in usdt_holders:
                tx_volume["CEX deposit addresses"] = tx_volume.get("CEX deposit addresses", 0) + value
                tx_count["CEX deposit addresses"] = tx_count.get("CEX deposit addresses", 0) + 1
            else:
                tx_volume[_from] = tx_volume.get(_from, 0) + value
                tx_count[_from] = tx_count.get(_from, 0) + 1
    
    print("total volume: %f USDT" % total_volume)
    print("total transfers: %d" % total_transfers)
    
    tx_volume = dict(sorted(tx_volume.items(), key=lambda item: item[1], reverse=True))
    tx_count = dict(sorted(tx_count.items(), key=lambda item: item[1], reverse=True))

    for address in list(tx_volume.keys())[:20]:
        tag = get_public_tag(address)
        if tag is not None:
            tx_volume[tag] = tx_volume[address]
            tx_count[tag] = tx_count[address]
            del tx_volume[address]
            del tx_count[address]
    
    # Write to CSV file after fetching labels
    with open("usdt_volume.csv", "w") as f:
        f.write("sender,volume,transfers,avg_value\n")
        for sender, volume in tx_volume.items():
            transfers = tx_count[sender]
            avg_value = volume / transfers
            f.write(f"{sender},{volume},{transfers},{avg_value}\n")
    
    # Combine addresses lower than top 20 in volume and transfer count into "Others"
    others_volume = sum([v for k, v in list(tx_volume.items())[20:]])
    others_count = sum([v for k, v in list(tx_count.items())[20:]])
    
    tx_volume = dict(list(tx_volume.items())[:20])
    tx_count = dict(list(tx_count.items())[:20])
    
    tx_volume["Others"] = others_volume
    tx_count["Others"] = others_count
    
    print("Volume distribution:", tx_volume)
    print("Transfer count distribution:", tx_count)

    # Generate pie charts
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

    # Volume pie chart
    labels_volume = []
    sizes_volume = []
    for tag, volume in tx_volume.items():
        labels_volume.append(f"{tag}\n{volume:.2f} ({volume/total_volume:.1%})")
        sizes_volume.append(volume)

    ax1.pie(sizes_volume, labels=labels_volume, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    ax1.set_title(f"USDT Volume Share\nTotal Volume: {total_volume:.2f}")

    # Transfer count pie chart
    labels_count = []
    sizes_count = []
    for tag, count in tx_count.items():
        labels_count.append(f"{tag}\n{count} ({count/total_transfers:.1%})")
        sizes_count.append(count)

    ax2.pie(sizes_count, labels=labels_count, autopct='%1.1f%%', startangle=90)
    ax2.axis('equal')
    ax2.set_title(f"USDT Transfer Count Share\nTotal Transfers: {total_transfers}")

    plt.tight_layout()
    plt.savefig('usdt_volume_and_count_share.png')
    plt.show()

    # Calculate and print average transfer value for each group
    print("\nAverage transfer value for each group:")
    for tag in tx_volume.keys():
        avg_value = tx_volume[tag] / tx_count[tag]
        print(f"{tag}: {avg_value:.2f} USDT")