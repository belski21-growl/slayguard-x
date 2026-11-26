#!/usr/bin/env python3
"""show_registry.py — read-back bukti on-chain SlayGuardRegistry (read-only).

No key, no signing, no tx. Calls eth_call getAudit(factory) on the public
X Layer RPC and prints a short human-readable summary. Short addresses only
(full values live in the build log / status file, never on video frames).
"""
import datetime
import json
import urllib.request

REGISTRY = "0x55b9460db2a22a9fA70A8cBe2c665804167A42e5"
FACTORY = "0x1f09daefa827f02cbb40967cc91b259763760761"
RPC = "https://rpc.xlayer.tech"


def short(addr):
    return addr[:6] + "…" + addr[-4:]


def main():
    # getAudit(address) selector 0x6670c4bf (keccak, verified via ethers).
    data = "0x6670c4bf" + FACTORY[2:].rjust(64, "0")
    body = {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
            "params": [{"to": REGISTRY, "data": data}, "latest"]}
    req = urllib.request.Request(
        RPC, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    res = json.loads(urllib.request.urlopen(req, timeout=30).read())
    raw = res["result"][2:]
    verdict = int(raw[0:64], 16)
    score = int(raw[64:128], 16)
    fhash = "0x" + raw[128:192]
    ts = int(raw[192:256], 16)
    auditor = "0x" + raw[256:320][-40:]
    names = ["GO", "CAUTION", "HOLD"]
    when = datetime.datetime.fromtimestamp(
        ts, datetime.timezone.utc).strftime("%d %b %Y")
    print("SlayGuardRegistry — X Layer mainnet (chain 196)")
    print(f"registry : {short(REGISTRY)}")
    print(f"getAudit(factory {short(FACTORY)}):")
    print(f"  verdict  : {names[verdict]} ({verdict})")
    print(f"  score    : {score} / 100")
    print(f"  findings : {fhash[:10]}…")
    print(f"  auditor  : {short(auditor)}")
    print(f"  recorded : {when}")
    print("deploy tx: 0xcd3a…f969f  ·  record tx: 0xa9f9…26d4d")
    print("total mainnet cost: ~$0.0013  ·  verify: okx.com/web3/explorer/xlayer")


if __name__ == "__main__":
    main()
