import requests, base58

proposers = []

response = requests.get("https://apilist.tronscanapi.com/api/pagewitness?witnesstype=0").json()
for account in response["data"][:128]:
    print(account["address"])
    data = requests.get("https://apilist.tronscanapi.com/api/accountv2?address=" + account["address"]).json()
    if permissions := data.get("witnessPermission"):
        proposers.extend([base58.b58decode(x["address"])[:21].hex() for x in permissions["keys"]])
    proposers.append(base58.b58decode(account["address"])[:21].hex())

open("srs.txt", "w").write("\n".join(proposers))