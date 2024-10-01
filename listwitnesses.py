import grpc
from core import Tron_pb2
from api import api_pb2, api_pb2_grpc

grpc_server = "grpc.trongrid.io:50051"
channel = grpc.insecure_channel(grpc_server)
stub = api_pb2_grpc.WalletStub(channel)

def list_witnesses():
    request = api_pb2.EmptyMessage()
    
    witnesses = stub.ListWitnesses(request)
    
    return witnesses

def get_account_by_address(address):
    request = Tron_pb2.Account()
    request.address = address
    
    account = stub.GetAccount(request)
    
    return account

def get_all_witness_delegatees():
    witnesses = list_witnesses()

    witness_delegatees = {}

    for witness in witnesses.witnesses:
        witness_address = witness.address
        account = get_account_by_address(witness_address)
        
        for key in account.witness_permission.keys:
            witness_delegatees[key.address] = witness_address

    return witness_delegatees

if __name__ == "__main__":
    print(get_all_witness_delegatees())