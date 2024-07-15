import hashlib

def compute_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(left + right).digest()

def verify_proof(proof, root, leaf, index):
    # path = list(zip(proof["rule"], [bytes.fromhex(x) for x in proof["path"]]))

    # if not path:
    #     return compute_hash(b"", b"")

    # bit, result = path[0]
    # index = 0
    # while index < len(path) - 1:
    #     next_bit, digest = path[index + 1]

    #     if bit == 0:
    #         result = compute_hash(result, digest)
    #     elif bit == 1:
    #         result = compute_hash(digest, result)
    #     else:
    #         raise ValueError('Invalid bit found')

    #     bit = next_bit
    #     index += 1

    # return result

    hash = leaf

    for i in range(len(proof)):
        proof_element = proof[i]

        if index % 2 == 0:
            hash = compute_hash(hash, proof_element)
        else:
            hash = compute_hash(proof_element, hash)

        index = index // 2
    
    return hash == root

def soliditify(merkle):
    proof = merkle.path[1:]
    leaf = merkle.path[0]
    index = int("".join([str(x) for x in merkle.rule][::-1]), 2)

    return proof, leaf, index