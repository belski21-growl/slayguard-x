// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {SlayGuardRegistry} from "../contracts/SlayGuardRegistry.sol";

/// @notice Bukti deploy + record + baca balik registry (EVM in-process).
///         Tanpa forge-std (tanpa network): assert() polos + try/catch.
///         Jalan: forge test -vv --gas-report
contract SlayGuardRegistryTest {
    SlayGuardRegistry internal reg;
    address internal target = address(0x1111111111111111111111111111111111111111);

    function setUp() public {
        reg = new SlayGuardRegistry();
    }

    function test_record_and_read_back() public {
        bytes32 h = keccak256("slayguard-x e2e");
        reg.recordAudit(target, SlayGuardRegistry.Verdict.HOLD, 42, h);
        SlayGuardRegistry.Audit memory a = reg.getAudit(target);
        assert(uint8(a.verdict) == uint8(SlayGuardRegistry.Verdict.HOLD));
        assert(a.score == 42);
        assert(a.findingsHash == h);
        assert(a.auditor == address(this));
        assert(reg.auditCount(target) == 1);
    }

    function test_record_twice_overwrites_and_counts() public {
        reg.recordAudit(target, SlayGuardRegistry.Verdict.CAUTION, 60,
                        keccak256("v1"));
        reg.recordAudit(target, SlayGuardRegistry.Verdict.GO, 90,
                        keccak256("v2"));
        SlayGuardRegistry.Audit memory a = reg.getAudit(target);
        assert(uint8(a.verdict) == uint8(SlayGuardRegistry.Verdict.GO));
        assert(a.score == 90);
        assert(reg.auditCount(target) == 2);
    }

    function test_revert_zero_target() public {
        try reg.recordAudit(address(0), SlayGuardRegistry.Verdict.GO, 90, 0) {
            assert(false); // harusnya revert
        } catch Error(string memory reason) {
            assert(
                keccak256(bytes(reason)) == keccak256(bytes("target zero"))
            );
        }
    }

    function test_revert_score_over_100() public {
        try reg.recordAudit(target, SlayGuardRegistry.Verdict.GO, 101, 0) {
            assert(false); // harusnya revert
        } catch Error(string memory reason) {
            assert(
                keccak256(bytes(reason)) == keccak256(bytes("score>100"))
            );
        }
    }

    function test_empty_audit_is_zero() public view {
        SlayGuardRegistry.Audit memory a =
            reg.getAudit(address(0x2222222222222222222222222222222222222222));
        assert(a.score == 0);
        assert(a.auditor == address(0));
    }
}
