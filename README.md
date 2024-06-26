# tron-light-client
Tron Network light client PoC for my future project

## Usage

`python3 main.py <tron-block>` - connects to TronGrid gRPC API, fetches the block, verifies its signature, prevblockhash, and checks if the proposer is in allowlist

`python3 main.py` - same but fetches 1000 random blocks. this is needed for tests, make sure it works if you PR something

`python3 getsrs.py` - fetches top 128 Tron validators and their witness authorities using TronScan API and saves them into `srs.txt` (allowlist)

`python3 srscan.py <epochs-depth>` - scans SRs of the last epochs and shows how many unique there were *(e.g., shows 28 for the last 7 200 000 blocks)*