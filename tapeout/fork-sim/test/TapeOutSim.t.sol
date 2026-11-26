// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ITapeOutFactory, ITapeOutProcessor, ITapeOutTransistors, IERC20} from "../src/ITapeOut.sol";

/// @notice Minimal cheatcode interface (no forge-std dependency).
interface Vm {
    function createSelectFork(string calldata urlOrAlias) external returns (uint256);
    function deal(address who, uint256 newBalance) external;
    function store(address target, bytes32 slot, bytes32 value) external;
    function startPrank(address msgSender) external;
    function stopPrank() external;
    function writeFile(string calldata path, string calldata data) external;
    function toString(address value) external pure returns (string memory);
    function toString(uint256 value) external pure returns (string memory);
}

/// @notice Fork simulation of the SlayGuard Risk Circuit tape-out.
///         Runs ONLY on a local fork of X Layer mainnet: no real tx, no key,
///         no broadcast. Mirrors ViperX's TapeOutSpike fork test.
///         Run: forge test --match-path test/TapeOutSim.t.sol -vv
contract TapeOutSimTest {
    Vm internal constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address internal constant FACTORY = 0x1f09DAeFA827f02CBb40967cc91b259763760761;
    address internal constant OPERATOR = 0x8F3E972f8006aE76D55385cF9Df8bF86160983AA;
    address internal constant BEM = 0x60e62Efa9405d6873C5deaBD4E6CC91c25363952;
    bytes internal constant NETLIST = hex"00000005000005000000060000060000000900000a00000007000007000000080000080000000c00000d0000000b00000b0000000e00000e0000000f0000100000000500000600000012000012000000130000070000001400001400000005000006000000160000160000001700000800000018000018000000050000070000001a00001a0000001b0000080000001c00001c000000060000070000001e00001e0000001f000008000000200000200000001500001500000019000019000000220000230000001d00001d000000210000210000002500002600000024000024000000270000270000002800002900000002000002000000030000030000002b00002c000000040000040000002a00002a0000002e00002f0000002d00002d000000300000300000003100003200000033000033000000340000110000003500003500000033000033000000360000360000003700003700000038000038";
    bytes internal constant EXPECTED = hex"00010101010101010201010101010101020101010101010102010101010101010201010101010101020101010101010102010101010101010101010101010101020101010101010102010101010101010201010101010101010101010101010102010101010101010101010101010101010101010101010101010101010101010001010101010101020101010101010102010101010101010201010101010101020101010101010102010101010101010201010101010101010101010101010102010101010101010201010101010101020101010101010101010101010101010201010101010101010101010101010101010101010101010101010101010101";

    function test_tapeout_risk_circuit() public {
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
            "SlayGuard Risk Circuit", "SLAYRISK", "SlayGuard X risk circuit: audit verdict rules as NAND netlist.", 50, 0);
        uint256 gasCreate = g0 - gasleft();
        assert(factory.cpuCount() == countBefore + 1);
        ITapeOutProcessor cpu = ITapeOutProcessor(factory.cpuAt(countBefore));
        assert(factory.isCPU(address(cpu)));
        ITapeOutTransistors t = ITapeOutTransistors(tAddr);
        assert(cpu.transistorsContract() == tAddr);
        assert(t.mintPrice() == 0);
        assert(t.supplyCap() == 50);
        assert(t.NAND() == 0);

        uint256 mintCost = t.mintPrice() * 50 + t.protocolFee();
        IERC20(BEM).approve(tAddr, mintCost);
        g0 = gasleft();
        t.mint(t.NAND(), 50);
        uint256 gasMint = g0 - gasleft();
        assert(t.balanceOf(OPERATOR, t.NAND()) == 50);

        uint256 fee = cpu.TAPEOUT_FEE();
        g0 = gasleft();
        uint256 id = cpu.tapeout{value: fee}(NETLIST, 7, 2);
        uint256 gasTapeout = g0 - gasleft();
        vm.stopPrank();

        assert(t.balanceOf(OPERATOR, t.NAND()) == 0);
        assert(cpu.ownerOf(id) == OPERATOR);
        assert(keccak256(cpu.netlist(id)) == keccak256(NETLIST));
        (uint32 nIn, uint32 nOut, uint32 nState, uint32 gates) = cpu.circuitInfo(id);
        assert(nIn == 7);
        assert(nOut == 2);
        assert(nState == 0);
        assert(gates == 50);

        // Replay all 256 input vectors through eval on the fork.
        for (uint256 combo = 0; combo < 256; combo++) {
            bytes memory out = cpu.eval(id, abi.encodePacked(uint8(combo)));
            assert(out.length == 1);
            assert(uint8(out[0]) == uint8(EXPECTED[combo]));
        }

        uint256 okbSpent = okbBefore - OPERATOR.balance;
        uint256 bemSpent = bemBefore - IERC20(BEM).balanceOf(OPERATOR);
        vm.writeFile(
            "tapeout_result.json",
            string.concat(
                '{"processor":"', vm.toString(address(cpu)),
                '","circuit_id":', vm.toString(id),
                ',"gas_createCPU":', vm.toString(gasCreate),
                ',"gas_mint":', vm.toString(gasMint),
                ',"gas_tapeout":', vm.toString(gasTapeout),
                ',"tapeout_fee_wei":', vm.toString(fee),
                ',"okb_spent_wei":', vm.toString(okbSpent),
                ',"bem_spent_base":', vm.toString(bemSpent),
                ',"eval_vectors_checked":256}'
            )
        );
    }
}
