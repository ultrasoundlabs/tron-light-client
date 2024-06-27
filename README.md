# tron-light-client
Tron Network light client PoC for my future project

## Usage

`python3 main.py <tron-block>` - connects to TronGrid gRPC API, fetches the block, verifies its signature, prevblockhash, and checks if the proposer is in allowlist; returns input data for zktron

`python3 main.py` - same but fetches 1000 random blocks. this is needed for tests, make sure it works if you PR something

`python3 srscan.py <epochs-depth>` - scans SRs of the last epochs and saves their public keys into srs.txt (allowlist)