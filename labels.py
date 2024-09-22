import requests

def get_public_tag(address):
    return requests.get(f"https://apilist.tronscanapi.com/api/accountv2?address={address}", headers={"TRON-PRO-API-KEY": "5b9e3a55-3956-47ba-93b3-c523cc3d527c"}).json().get("publicTag")

f = open("labeled_usdt_volume.csv", "w")
f.write("sender,volume,transfers,avg_value\n")
for line in open("usdt_volume.csv").readlines()[1:]:
    address, volume, transfers, avg_value = line.split(",")
    public_tag = get_public_tag(address) or address
    f.write(f"{public_tag},{volume},{transfers},{avg_value}")
f.close()