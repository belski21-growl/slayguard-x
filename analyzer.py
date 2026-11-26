"""SlayGuard AI — on-chain contract analyzer (read-only, no keys, no gas).

Reads live state from public RPC endpoints and scans deployed bytecode for
known function selectors, then scores the contract and returns findings.
Selector values are well-known 4-byte constants (keccak of the signature);
see SELECTORS. No web3 dependency — raw JSON-RPC via `requests`.
"""
import os
import re

import requests

RPCS = {
    "bsc": [
        "https://bsc-dataseed2.binance.org",
        "https://bsc-dataseed.binance.org",
        "https://bsc-dataseed1.defibit.io",
    ],
    "eth": [
        "https://eth.llamarpc.com",
        "https://cloudflare-eth.com",
        "https://ethereum.publicnode.com",
    ],
    # X Layer (OKX, OP Stack, EVM-equivalent, gas OKB)
    # Mainnet chain 196, testnet chain 1952 — RPC resmi OKX.
    "xlayer": [
        "https://rpc.xlayer.tech",
    ],
    "xlayer-testnet": [
        "https://testrpc.xlayer.tech/terigon",
    ],
}

# Override RPC via env (dipakai tes lokal lawan anvil):
#   SLAY_RPC_XLAYER_TESTNET=http://127.0.0.1:8545
_RPC_ENV = {
    "xlayer": "SLAY_RPC_XLAYER",
    "xlayer-testnet": "SLAY_RPC_XLAYER_TESTNET",
}

# --- TapeOut on X Layer (mainnet, chain 196) ---
# Alamat factory + market dikonfirmasi dua sumber independen (dev.to snapshot
# 23 Okt 2026 + docs ViperX: "factory exists only on mainnet").
# BUKAN ditebak. Verifikasi live (eth_getCode) ada di tapeout_status().
TAPEOUT_FACTORY = "0x1f09daefa827f02cbb40967cc91b259763760761"
TAPEOUT_MARKET = "0xd89f358c48a7B632c9845af2a02A32eB90DD75DB"
# Slot EIP-1967 implementation (factory adalah proxy — baca di tapeout_status).
_EIP1967_IMPL_SLOT = (
    "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
)

# 4-byte selectors (keccak256(signature)[:4]) — standard, verifiable on 4byte.directory
SELECTORS = {
    "owner()": "8da5cb5b",
    "totalSupply()": "18160ddd",
    "name()": "06fdde03",
    "symbol()": "95d89b41",
    "balanceOf(address)": "70a08231",
    "mint(address,uint256)": "40c10f19",
    "mint(uint256)": "a0712d68",
    "safeMint(address,uint256)": "a1448194",
    "pause()": "8456cb59",
    "unpause()": "3f4ba83a",
    "setBaseURI(string)": "55f804b3",
    "withdraw()": "3ccfd60b",
    "renounceOwnership()": "715018a6",
    "transferOwnership(address)": "f2fde38b",
    "setApprovalForAll(address,bool)": "a22cb465",
    "approve(address,uint256)": "095ea7b3",
    "maxSupply()": "d5abeb01",
    "MAX_SUPPLY()": "0d0e4b70",
    "tokenURI(uint256)": "c87b56dd",
    "implementation()": "5c60da1b",  # EIP-1967 proxy
    "upgradeTo(address)": "3659cfe6",
}

# Risky / owner-power selectors: (key, label, severity, points)
RISKY_FUNCS = [
    ("pause()", "Owner can pause the contract (trading/minting can be frozen)", "medium", 10),
    ("setBaseURI(string)", "Owner can change the metadata/URI of all tokens", "medium", 10),
    ("withdraw()", "Owner can withdraw funds from the contract", "medium", 10),
    ("upgradeTo(address)", "Proxy can be upgraded — logic can be replaced entirely", "high", 25),
    ("mint(address,uint256)", "Owner can mint new tokens with no visible cap", "low", 5),
    ("mint(uint256)", "Public/open mint function", "low", 5),
]

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def rpc_call(chain, method, params, timeout=15):
    """Try each public RPC for the chain until one answers."""
    last_err = None
    urls = list(RPCS[chain])
    env_url = os.environ.get(_RPC_ENV.get(chain, ""), "")
    if env_url:
        urls = [env_url]  # override (tes lokal lawan anvil)
    for url in urls:
        try:
            r = requests.post(url, json={"jsonrpc": "2.0", "id": 1,
                                         "method": method, "params": params},
                              timeout=timeout)
            data = r.json()
            if "result" in data:
                return data["result"]
            last_err = data.get("error", data)
        except Exception as e:  # noqa: BLE001 - try next endpoint
            last_err = str(e)
    raise RuntimeError(f"RPC {chain} failed on all endpoints: {last_err}")


def _decode_string(hexdata):
    """Decode ABI-encoded string return (0x + offset + len + bytes)."""
    try:
        raw = bytes.fromhex(hexdata[2:])
        if len(raw) < 96:
            return None
        ln = int.from_bytes(raw[64:96], "big")
        return raw[96:96 + ln].decode("utf-8", "replace")
    except Exception:
        return None


def _decode_address(hexdata):
    try:
        raw = bytes.fromhex(hexdata[2:])
        if len(raw) < 32:
            return None
        return "0x" + raw[12:32].hex()
    except Exception:
        return None


def _decode_uint(hexdata):
    try:
        return int(hexdata, 16)
    except Exception:
        return None


def eth_call(chain, to_addr, data):
    return rpc_call(chain, "eth_call",
                    [{"to": to_addr, "data": "0x" + data}, "latest"])


def tapeout_status(chain="xlayer"):
    """Baca status on-chain TapeOut di X Layer (READ-ONLY, tanpa gas).

    Mengembalikan: chainId, nomor blok, ada/tidaknya bytecode factory &
    market, panjang bytecode, alamat implementasi proxy factory.
    Dipakai UI sebagai bukti integrasi "onchain data" (syarat OKX: pakai
    TapeOut circuits, contracts, ATAU onchain data di X Layer).
    """
    if chain not in ("xlayer", "xlayer-testnet"):
        raise ValueError("tapeout_status only supports xlayer / xlayer-testnet")
    out = {"chain": chain}
    try:
        out["chain_id"] = int(rpc_call(chain, "eth_chainId", []), 16)
    except Exception as e:  # noqa: BLE001
        out["chain_id_error"] = str(e)
    try:
        out["block_number"] = int(rpc_call(chain, "eth_blockNumber", []), 16)
    except Exception as e:  # noqa: BLE001
        out["block_number_error"] = str(e)
    for label, addr in (("factory", TAPEOUT_FACTORY),
                        ("market", TAPEOUT_MARKET)):
        try:
            code = rpc_call(chain, "eth_getCode", [addr, "latest"])
            nbytes = max(0, (len(code) - 2) // 2) if code else 0
            out[f"{label}_address"] = addr
            out[f"{label}_live"] = nbytes > 0
            out[f"{label}_code_bytes"] = nbytes
        except Exception as e:  # noqa: BLE001
            out[f"{label}_live"] = False
            out[f"{label}_error"] = str(e)
    # Factory adalah proxy EIP-1967 — baca implementation slot-nya.
    try:
        slot = rpc_call(chain, "eth_getStorageAt",
                        [TAPEOUT_FACTORY, _EIP1967_IMPL_SLOT, "latest"])
        if slot and int(slot, 16) != 0:
            out["factory_implementation"] = "0x" + slot[-40:]
    except Exception:
        pass
    return out


def gas_price_gwei(chain):
    """Harga gas live (gwei) di chain — dipakai estimasi biaya OKB."""
    raw = rpc_call(chain, "eth_gasPrice", [])
    return int(raw, 16) / 1e9


def analyze(address, chain="bsc"):
    """Full audit. Returns dict with verdict, score (0-100, higher = safer), findings."""
    if chain not in RPCS:
        raise ValueError(f"Unsupported chain: {chain} "
                         "(choose bsc / eth / xlayer / xlayer-testnet)")
    if not ADDRESS_RE.match(address):
        raise ValueError("Invalid address (must be 0x + 40 hex)")

    addr = address.lower()
    findings = []
    score = 100

    def add(sev, pts, title, detail):
        nonlocal score
        score = max(0, score - pts)
        findings.append({"severity": sev, "points": pts,
                         "title": title, "detail": detail})

    # 1. Bytecode ada atau tidak
    code = rpc_call(chain, "eth_getCode", [addr, "latest"])
    if code in ("0x", "0x0", None):
        return {"address": address, "chain": chain, "score": 0,
                "verdict": "HOLD",
                "findings": [{"severity": "high", "points": 100,
                              "title": "Not a contract — this is a wallet address (EOA)",
                              "detail": "No bytecode at this address. "
                                        "Do not send funds/mint here."}],
                "meta": {}}
    code_len = (len(code) - 2) // 2
    meta = {"bytecode_bytes": code_len}

    # 2. Proxy? (EIP-1967 implementation slot)
    impl_slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
    try:
        slot = rpc_call(chain, "eth_getStorageAt", [addr, impl_slot, "latest"])
        if slot and int(slot, 16) != 0:
            impl = "0x" + slot[-40:]
            meta["proxy_implementation"] = impl
            add("medium", 15, "Proxy contract (EIP-1967)",
                f"Logic lives in the implementation {impl}. "
                "The proxy admin can change the logic — check who the admin is.")
    except Exception:
        pass

    # 3. Metadata ERC20/721: name / symbol / totalSupply / owner
    for fn, key in [("name()", "name"), ("symbol()", "symbol")]:
        try:
            out = eth_call(chain, addr, SELECTORS[fn])
            val = _decode_string(out)
            if val:
                meta[key] = val
        except Exception:
            pass
    try:
        out = eth_call(chain, addr, SELECTORS["totalSupply()"])
        ts = _decode_uint(out)
        if ts is not None:
            meta["total_supply"] = ts
    except Exception:
        pass

    owner = None
    if SELECTORS["owner()"] in code[2:]:
        try:
            out = eth_call(chain, addr, SELECTORS["owner()"])
            owner = _decode_address(out)
            if owner:
                meta["owner"] = owner
                if owner == "0x0000000000000000000000000000000000000000":
                    add("low", 0, "Ownership already renounced",
                        "owner() = zero address — nobody can change the contract. Good.")
                    meta["renounced"] = True
                else:
                    add("info", 0, "Owner detected",
                        f"Owner: {owner}. Check whether this owner is an EOA / multisig / known team.")
        except Exception:
            pass
    else:
        meta["owner"] = None

    # 4. Scan bytecode untuk fungsi berisiko
    code_body = code[2:].lower()
    for fn, label, sev, pts in RISKY_FUNCS:
        sel = SELECTORS[fn]
        if sel in code_body:
            # mint tanpa owner() terdeteksi = lebih berisiko (publik)
            if fn in ("mint(address,uint256)", "mint(uint256)") and not meta.get("owner"):
                add("medium", 10, label + " (no owner detected)",
                    "Mint function exists but there is no owner() — mint may be open to everyone.")
            else:
                add(sev, pts, label, f"Selector 0x{sel} found in bytecode.")

    # 5. maxSupply
    for fn in ("maxSupply()", "MAX_SUPPLY()"):
        if SELECTORS[fn] in code_body:
            try:
                out = eth_call(chain, addr, SELECTORS[fn])
                ms = _decode_uint(out)
                if ms is not None:
                    meta["max_supply"] = ms
                    if meta.get("total_supply") is not None and ms > 0:
                        pct = meta["total_supply"] / ms * 100
                        meta["minted_pct"] = round(pct, 1)
                        if pct >= 99:
                            add("high", 20, "Supply almost exhausted",
                                f"{pct:.1f}% of max supply already minted.")
            except Exception:
                pass
            break

    if score >= 80:
        verdict = "GO"
    elif score >= 55:
        verdict = "CAUTION"
    else:
        verdict = "HOLD"

    return {"address": address, "chain": chain, "score": score,
            "verdict": verdict, "findings": findings, "meta": meta}
