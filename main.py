import grpc, ecdsa, sys, random
from api import api_pb2, api_pb2_grpc
from core.contract import smart_contract_pb2
from hashlib import sha256
from trontrie import create_tree
from base58 import b58encode_check

# list of all SRs and SR partners as of block 62913164
# the assumption is that there were no new SRs not from partner list
# for the last 7 200 000 blocks, so we can skip votes calculation
# and assume all block producers in this list are eligible
srs = [bytes.fromhex(x) for x in open("srs.txt").read().split("\n")]

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

def verify_block_header(prev_block_hash, block_header) -> bool:
    # noir doesn't have IO wrappers so i don't use them here for simpler rewrite
    assert block_header[0] & 7 == 2 # LEN
    assert block_header[0] >> 3 == 1 # 1:
    raw_data_length, offset = read_varint(block_header[1:])
    offset += 1

    raw_data = block_header[offset:offset+raw_data_length]
    assert block_header[offset] & 7 == 0 # VARINT
    assert block_header[offset] >> 3 == 1 # 1:
    offset += 1
    offset += read_varint(block_header[offset:])[1] # we don't need timestamp
    assert block_header[offset] & 7 == 2 # LEN
    assert block_header[offset] >> 3 == 2 # 2:
    offset += 1
    offset += 33 # txroot (offset + length); it's always 33 bytes total but we'll need txroot later
    assert block_header[offset] & 7 == 2 # LEN
    assert block_header[offset] >> 3 == 3 # 3:
    offset += 1
    offset += 1 # prevblockhash length, always 32
    assert block_header[offset:offset+32] == prev_block_hash
    offset += 32
    assert block_header[offset] & 7 == 0 # VARINT
    assert block_header[offset] >> 3 == 7 # 7: idk why
    offset += 1
    block_number, nl = read_varint(block_header[offset:])
    offset += nl
    assert block_header[offset] & 7 == 2 # LEN
    assert block_header[offset] >> 3 == 9 # 9: idk why
    offset += 1
    offset += 1 # witness_address length, always 21
    # witness_address = block_header[offset:offset+21]
    offset += 21
    assert block_header[offset] & 7 == 0 # VARINT
    assert block_header[offset] >> 3 == 10 # 9: idk why
    offset += 1
    offset += 1 # version, always 30

    assert block_header[offset] & 7 == 2 # LEN
    assert block_header[offset] >> 3 == 2 # 2:
    offset += 1
    assert block_header[offset] == 65 # signature is always 65 bytes
    offset += 1
    signature_bytes = block_header[offset:]

    message_hash = sha256(raw_data).digest()
    # for solidity tests
    # print(message_hash.hex() + signature_bytes[64].to_bytes(32).hex() + signature_bytes[:32].hex() + signature_bytes[32:64].hex())

    r = int.from_bytes(signature_bytes[:32])
    s = int.from_bytes(signature_bytes[32:64])
    v = signature_bytes[64]
    
    if v >= 27:
        v -= 27

    sig = ecdsa.util.sigencode_string(r, s, 2**256-1)
    vk = ecdsa.VerifyingKey.from_public_key_recovery_with_digest(
        sig,
        message_hash,
        curve=ecdsa.SECP256k1,
        hashfunc=sha256
    )[v].to_string()

    assert vk in srs

    return vk

def parse_usdt_transfer(tx):
    tx_data = tx.transaction.raw_data.contract[0]

    if tx_data.type != 31: return None # 31 = TriggerSmartContract

    call = smart_contract_pb2.TriggerSmartContract()
    call.ParseFromString(tx_data.parameter.value)
    
    if call.contract_address != bytes.fromhex("41a614f803b6fd780986a42c78ec9c7f77e6ded13c"): return None # USDT contract TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t

    calldata = call.data

    if calldata[:4] != bytes.fromhex("a9059cbb"): return None # transfer(address,uint256)

    sender = b58encode_check(call.owner_address).decode()

    to = b58encode_check(b"\x41" + calldata[16:36]).decode()

    amount = int.from_bytes(calldata[36:68])/10**6
    return sender, to, amount

if __name__ == "__main__":
    blocks = []
    if len(sys.argv) > 1:
        blocks.append(int(sys.argv[1]))
    else:
        for i in range(1000):
            blocks.append(62913164-random.randint(0, 10000))
            
    for block_number in blocks:
        prev_block_hash = get_block_by_number(block_number-1).blockid
        block = get_block_by_number(block_number)

        print("checking block %d..." % block_number)

        tx_root = create_tree([sha256(x.transaction.SerializeToString()).digest() for x in block.transactions]).hash
        assert tx_root == block.block_header.raw_data.txTrieRoot

        print(prev_block_hash.hex())
        print(block.blockid.hex())
        print(block.block_header.raw_data.txTrieRoot.hex())
        print(verify_block_header(prev_block_hash, block.block_header.SerializeToString()).hex())
        print(block.block_header.SerializeToString().hex())

        print("\nlooking for USDT transfers...")

        for tx in block.transactions:
            if not tx.result.result: continue # result is a bool (executed/failed)

            if transfer := parse_usdt_transfer(tx):
                print("{} -> {} ({} USDT)".format(*transfer))