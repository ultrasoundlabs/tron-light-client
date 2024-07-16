import grpc, ecdsa, sys, json
from api import api_pb2, api_pb2_grpc
from core.contract import smart_contract_pb2
from pymerkle import verify_inclusion, InmemoryTree as MerkleTree
from hashlib import sha256
from trontrie import *
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

def is_usdt_transfer(tx):
    if tx.transaction.ret[0].contractRet != 1: return False

    tx_data = tx.transaction.raw_data.contract[0]

    if tx_data.type != 31: return False # 31 = TriggerSmartContract

    call = smart_contract_pb2.TriggerSmartContract()
    call.ParseFromString(tx_data.parameter.value)
    
    if call.contract_address != bytes.fromhex("41a614f803b6fd780986a42c78ec9c7f77e6ded13c"): return False # USDT contract TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t

    calldata = call.data

    if calldata[:4] != bytes.fromhex("a9059cbb"): return False # transfer(address,uint256)

    return True

def parse_usdt_transfer(tx):

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

    assert call_type == 31 # TriggerSmart Contract

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

    assert tx[offset:offset+length] == b"type.googleapis.com/protocol.TriggerSmartContract" # this is unnecessary because we verified the type == 31
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

    sender = tx[offset:offset+length][1:] # strip 0x41
    offset += length

    assert tx[offset] & 7 == 2 # LEN
    assert tx[offset] >> 3 == 2 # 2:
    offset += 1
    length, v = read_varint(tx[offset:]) # contract_address length
    offset += v

    assert tx[offset:offset+length] == bytes.fromhex("41a614f803b6fd780986a42c78ec9c7f77e6ded13c") # USDT contract TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t
    offset += length

    assert tx[offset] & 7 == 2 # LEN
    assert tx[offset] >> 3 == 4 # 4: (we skip 3 because no call_value)
    offset += 1
    length, v = read_varint(tx[offset:]) # data length
    offset += v

    data = tx[offset:offset+length]
    assert data[:4] == bytes.fromhex("a9059cbb") # transfer(address,uint256)
    to = data[16:36]
    amount = int.from_bytes(data[36:68])

    return sender, to, amount

if __name__ == "__main__":
    start_block = int(sys.argv[1])

    blocks = []
            
    for offset in range(18):
        prev_block_hash = get_block_by_number(start_block+offset-1).blockid
        block = get_block_by_number(start_block+offset)

        print("dumping block %d..." % (start_block+offset))
        
        tree = MerkleTree(algorithm="sha256", disable_security=True)
        for tx in block.transactions:
            tree.append_entry(tx.transaction.SerializeToString())

        tx_root = tree.root.digest
        assert tx_root == block.block_header.raw_data.txTrieRoot

        txs = []
        for i, tx in enumerate(block.transactions):
            if is_usdt_transfer(tx):
                raw_tx = tx.transaction.SerializeToString()
                sender, to, amount = parse_usdt_transfer(raw_tx)

                merkle_proof = tree.prove_inclusion(i+1) # counting from 1
                proof, leaf, index = soliditify(merkle_proof)
                assert verify_proof(proof, tx_root, leaf, index)
                txs.append({
                    "from": sender.hex(),
                    "to": to.hex(),
                    "amount": amount,
                    "tx_index": i,
                    "inclusion_proof": b"".join(proof).hex(), # bytes32[]
                    "tx": raw_tx.hex()
                })
        print("total %d USDT transfers" % len(txs))

        raw_data = block.block_header.raw_data.SerializeToString()
        public_key = verify_block_header(prev_block_hash, block.block_header.SerializeToString())
        signature = block.block_header.witness_signature[:64]

        blocks.append({
            "new_block_id": block.blockid.hex(),
            "prev_block_id": prev_block_hash.hex(),
            "public_key": public_key.hex(),
            "raw_data": raw_data.hex(),
            "signature": signature.hex(),
            "tx_root": tx_root.hex(),
            "txs": txs
        })
    
    open("input.json", "w").write(json.dumps(blocks))