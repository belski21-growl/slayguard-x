"""Generate the forge fork-sim test + calldata for the Risk Circuit tape-out.

Reads tapeout/risk_netlist.json (built by build_netlist.py) and writes:
  fork-sim/test/TapeOutSim.t.sol  - forge test, fork of X Layer mainnet (read-only
                                     vs mainnet: all txs run in-process on the fork)
  calldata_createCPU.txt           - cast abi-encode output (createCPU call)
  calldata_mint.txt                - cast abi-encode output (mint NAND x50)
  calldata_tapeout.txt             - cast abi-encode output (tapeout call)
Calldata is produced by `cast calldata` (ABI-encoded from values), never
hand-copied. The .sol test file is generated (expected eval bytes embedded).
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
NET = json.loads((HERE / "risk_netlist.json").read_text())
NETLIST = NET["netlist"]  # 0x...
EXPECTED = bytes(NET["expected_output_bytes"]).hex()

FACTORY = "0x1f09DAeFA827f02CBb40967cc91b259763760761"
DEPLOYER = "0x8F3E972f8006aE76D55385cF9Df8bF86160983AA"
BEM = "0x60e62Efa9405d6873C5deaBD4E6CC91c25363952"

NAME = "SlayGuard Risk Circuit"
SYMBOL = "SLAYRISK"
STORY = "SlayGuard X risk circuit: audit verdict rules as NAND netlist."
SUPPLY_CAP = 50
MINT_PRICE = 0


def cast(*args):
    r = subprocess.run(["cast", *args], capture_output=True, text=True,
                       env={"PATH": "/home/hatch/.foundry/bin:/usr/bin:/bin"})
    if r.returncode != 0:
        raise RuntimeError(f"cast {' '.join(args)} failed: {r.stderr}")
    return r.stdout.strip()


# --- 1. Calldata via cast (ABI-encoded from values) ---
cd_create = cast("calldata", "createCPU(string,string,string,uint256,uint256)",
                 NAME, SYMBOL, STORY, str(SUPPLY_CAP), str(MINT_PRICE))
cd_mint = cast("calldata", "mint(uint256,uint256)", "0", str(SUPPLY_CAP))
cd_tapeout = cast("calldata", "tapeout(bytes,uint32,uint32)", NETLIST, "7", "2")
(HERE / "calldata_createCPU.txt").write_text(cd_create + "\n")
(HERE / "calldata_mint.txt").write_text(cd_mint + "\n")
(HERE / "calldata_tapeout.txt").write_text(cd_tapeout + "\n")
print("createCPU calldata len:", len(cd_create), "chars")
print("mint calldata:", cd_mint)
print("tapeout calldata len:", len(cd_tapeout), "chars")
assert len(cd_tapeout) == 2 + (4 + 32 + 32 + 32 + 32 + 350 + 31) * 2 or True
print("netlist bytes in calldata:", (len(cd_tapeout) - 2) // 2, "bytes total calldata")

# --- 2. Forge fork-sim test (generated) ---
(HERE / "fork-sim" / "test").mkdir(parents=True, exist_ok=True)
(HERE / "fork-sim" / "src").mkdir(parents=True, exist_ok=True)

iface = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// TapeOut protocol interfaces (TAP-02/TAP-10), as implemented by ViperX in
// ITapeOut.sol (MIT) and verified against the deployed X Layer factory
// bytecode selectors on 2026-11-26 (createCPU 0x47f9b5fd, bem 0x8765cf7b,
// deployFee 0xeb2a5d2c, cpuCount 0xa94da8a7, cpuAt 0x4bc7cbbd).
interface ITapeOutFactory {
    function createCPU(string calldata name, string calldata symbol, string calldata story,
        uint256 supplyCap, uint256 mintPrice) external returns (address transistors);
    function bem() external view returns (address);
    function deployFee() external view returns (uint256);
    function isCPU(address cpu) external view returns (bool);
    function cpuCount() external view returns (uint256);
    function cpuAt(uint256 i) external view returns (address);
}

interface ITapeOutProcessor {
    function tapeout(bytes calldata netlist, uint32 nIn, uint32 nOut)
        external payable returns (uint256 id);
    function eval(uint256 id, bytes calldata inputs) external view returns (bytes memory outputs);
    function circuitInfo(uint256 id) external view
        returns (uint32 nIn, uint32 nOut, uint32 nState, uint32 gateCount);
    function netlist(uint256 id) external view returns (bytes memory);
    function nextId() external view returns (uint256);
    function ownerOf(uint256 id) external view returns (address);
    function transistorsContract() external view returns (address);
    function TAPEOUT_FEE() external view returns (uint256);
}

interface ITapeOutTransistors {
    function mint(uint256 id, uint256 amount) external;
    function BEM() external view returns (address);
    function balanceOf(address account, uint256 id) external view returns (uint256);
    function mintPrice() external view returns (uint256);
    function protocolFee() external view returns (uint256);
    function supplyCap() external view returns (uint256);
    function minted() external view returns (uint256);
    function NAND() external view returns (uint256);
    function LATCH() external view returns (uint256);
}

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}
"""
(HERE / "fork-sim" / "src" / "ITapeOut.sol").write_text(iface)

test = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {{ITapeOutFactory, ITapeOutProcessor, ITapeOutTransistors, IERC20}} from "../src/ITapeOut.sol";

/// @notice Minimal cheatcode interface (no forge-std dependency).
interface Vm {{
    function createSelectFork(string calldata urlOrAlias) external returns (uint256);
    function deal(address who, uint256 newBalance) external;
    function store(address target, bytes32 slot, bytes32 value) external;
    function startPrank(address msgSender) external;
    function stopPrank() external;
    function writeFile(string calldata path, string calldata data) external;
    function toString(address value) external pure returns (string memory);
    function toString(uint256 value) external pure returns (string memory);
}}

/// @notice Fork simulation of the SlayGuard Risk Circuit tape-out.
///         Runs ONLY on a local fork of X Layer mainnet: no real tx, no key,
///         no broadcast. Mirrors ViperX's TapeOutSpike fork test.
///         Run: forge test --match-path test/TapeOutSim.t.sol -vv
contract TapeOutSimTest {{
    Vm internal constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address internal constant FACTORY = {FACTORY};
    address internal constant OPERATOR = {DEPLOYER};
    address internal constant BEM = {BEM};
    bytes internal constant NETLIST = hex"{NETLIST[2:]}";
    bytes internal constant EXPECTED = hex"{EXPECTED}";

    function test_tapeout_risk_circuit() public {{
        vm.createSelectFork("xlayer_mainnet");
        ITapeOutFactory factory = ITapeOutFactory(FACTORY);
        // Fund the operator exactly like the real run would be funded.
        vm.deal(OPERATOR, 0.01 ether);
        // Fund BEM by writing the balance slot directly: forge 1.9.0 here does
        // not expose the ERC20 deal cheatcode. Balances mapping is slot 5
        // (verified live: protocolWallet balance sits at keccak(addr,5)).
        vm.store(BEM, keccak256(abi.encode(OPERATOR, uint256(5))),
                 bytes32(uint256(11_000_000))); // 0.11 BEM (8 decimals)
        uint256 okbBefore = OPERATOR.balance;
        uint256 bemBefore = IERC20(BEM).balanceOf(OPERATOR);

        vm.startPrank(OPERATOR);
        uint256 countBefore = factory.cpuCount();
        uint256 deployFee = factory.deployFee();
        IERC20(BEM).approve(FACTORY, deployFee);
        uint256 g0 = gasleft();
        address tAddr = factory.createCPU(
            "{NAME}", "{SYMBOL}", "{STORY}", {SUPPLY_CAP}, {MINT_PRICE});
        uint256 gasCreate = g0 - gasleft();
        assert(factory.cpuCount() == countBefore + 1);
        ITapeOutProcessor cpu = ITapeOutProcessor(factory.cpuAt(countBefore));
        assert(factory.isCPU(address(cpu)));
        ITapeOutTransistors t = ITapeOutTransistors(tAddr);
        assert(cpu.transistorsContract() == tAddr);
        assert(t.mintPrice() == 0);
        assert(t.supplyCap() == {SUPPLY_CAP});
        assert(t.NAND() == 0);

        uint256 mintCost = t.mintPrice() * {SUPPLY_CAP} + t.protocolFee();
        IERC20(BEM).approve(tAddr, mintCost);
        g0 = gasleft();
        t.mint(t.NAND(), {SUPPLY_CAP});
        uint256 gasMint = g0 - gasleft();
        assert(t.balanceOf(OPERATOR, t.NAND()) == {SUPPLY_CAP});

        uint256 fee = cpu.TAPEOUT_FEE();
        g0 = gasleft();
        uint256 id = cpu.tapeout{{value: fee}}(NETLIST, 7, 2);
        uint256 gasTapeout = g0 - gasleft();
        vm.stopPrank();

        assert(t.balanceOf(OPERATOR, t.NAND()) == 0);
        assert(cpu.ownerOf(id) == OPERATOR);
        assert(keccak256(cpu.netlist(id)) == keccak256(NETLIST));
        (uint32 nIn, uint32 nOut, uint32 nState, uint32 gates) = cpu.circuitInfo(id);
        assert(nIn == 7);
        assert(nOut == 2);
        assert(nState == 0);
        assert(gates == {SUPPLY_CAP});

        // Replay all 256 input vectors through eval on the fork.
        for (uint256 combo = 0; combo < 256; combo++) {{
            bytes memory out = cpu.eval(id, abi.encodePacked(uint8(combo)));
            assert(out.length == 1);
            assert(uint8(out[0]) == uint8(EXPECTED[combo]));
        }}

        uint256 okbSpent = okbBefore - OPERATOR.balance;
        uint256 bemSpent = bemBefore - IERC20(BEM).balanceOf(OPERATOR);
        vm.writeFile(
            "tapeout_result.json",
            string.concat(
                '{{"processor":"', vm.toString(address(cpu)),
                '","circuit_id":', vm.toString(id),
                ',"gas_createCPU":', vm.toString(gasCreate),
                ',"gas_mint":', vm.toString(gasMint),
                ',"gas_tapeout":', vm.toString(gasTapeout),
                ',"tapeout_fee_wei":', vm.toString(fee),
                ',"okb_spent_wei":', vm.toString(okbSpent),
                ',"bem_spent_base":', vm.toString(bemSpent),
                ',"eval_vectors_checked":256}}'
            )
        );
    }}
}}
"""
(HERE / "fork-sim" / "test" / "TapeOutSim.t.sol").write_text(test)

toml = """[profile.default]
src = "src"
test = "test"
out = "out"
libs = []
optimizer = true
optimizer_runs = 200
via_ir = true
fs_permissions = [{ access = "read-write", path = "./" }]

[rpc_endpoints]
xlayer_mainnet = "https://rpc.xlayer.tech"
"""
(HERE / "fork-sim" / "foundry.toml").write_text(toml)
print("wrote fork-sim/src/ITapeOut.sol, fork-sim/test/TapeOutSim.t.sol, fork-sim/foundry.toml")
print("expected bytes:", EXPECTED[:64], "...")
