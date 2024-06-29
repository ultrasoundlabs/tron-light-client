import hashlib
from typing import List, Optional

# rewritten line-by-line from here: https://github.com/tronprotocol/java-tron/blob/develop/chainbase/src/main/java/org/tron/core/capsule/utils/MerkleTree.java

class Leaf:
    hash: bytes
    left: Optional[super]
    right: Optional[super]

def create_tree(hashes: List[bytes]) -> bytes:
    
    leaves = create_leaves(hashes)
    while len(leaves) > 1:
        leaves = create_parent_leaves(leaves)

    return leaves[0]

def create_parent_leaves(leaves: List[Leaf]) -> List[Leaf]:
    length = len(leaves)
    parent = []
    for i in range(0, length, 2):
        if i >= length: break

        if i + 1 < length:
            right = leaves[i + 1]
        else:
            right = None
        
        parent.append(combine_into_leaf(leaves[i], right))
    
    return parent

def create_leaves(hashes: List[bytes]) -> List[Leaf]:
    length = len(hashes)
    leaves = []
    for i in range(0, length, 2):
        if i >= length: break

        if i + 1 < length:
            right = create_leaf(hashes[i + 1])
        else:
            right = None
        
        leaves.append(combine_into_leaf(create_leaf(hashes[i]), right))
    
    return leaves

def combine_into_leaf(left: Leaf, right: Leaf) -> Leaf:
    leaf = Leaf()
    if right is None:
        leaf.hash = left.hash
    else:
        leaf.hash = compute_hash(left.hash, right.hash)
    leaf.left = left
    leaf.right = right
    return leaf

def create_leaf(hash: bytes) -> Leaf:
    leaf = Leaf()
    leaf.hash = hash
    return leaf

def compute_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(left + right).digest()


if __name__ == "__main__":
    transactions = [b'tx1', b'tx2', b'tx3', b'tx4']

    root = create_tree(transactions)
    print("Transaction Root:", root.hex())