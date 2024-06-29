# tron-light-client
Tron Network light client PoC in Python. I use it as a testing ground for my [zktron project](https://github.com/alexhooketh/zktron)

## Usage

`python3 main.py <tron-block>` - connects to TronGrid gRPC API, fetches the block, verifies its signature, prevblockhash, checks if the proposer is in allowlist, validates tx root against the transactions, looks for USDT transfers in the block and displays them

`python3 main.py` - same but fetches 1000 random blocks. this is needed for tests, make sure it works if you PR something

`python3 srscan.py <epochs-depth>` - scans SRs of the last epochs and saves their public keys into srs.txt (allowlist)
