// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title SlayGuardRegistry — catatan verdict audit SlayGuard di X Layer
/// @notice Read-heavy: siapa pun bisa cek verdict terakhir sebuah alamat
///         kontrak sebelum mint/approve. Audit ditulis oleh auditor (server
///         SlayGuard / siapa pun yang menjalankan audit) — verdict bersifat
///         opini berbasis data on-chain publik, BUKAN nasihat finansial.
///         Deploy target: X Layer Testnet (chain 1952) untuk demo; mainnet
///         (chain 196) hanya setelah persetujuan user (butuh OKB asli).
contract SlayGuardRegistry {
    enum Verdict {
        GO,      // 0
        CAUTION, // 1
        HOLD     // 2
    }

    struct Audit {
        Verdict verdict;
        uint8 score; // 0-100, makin tinggi makin aman
        bytes32 findingsHash; // keccak256 dari ringkasan findings (off-chain)
        uint64 timestamp;
        address auditor;
    }

    mapping(address => Audit) public audits;
    mapping(address => uint256) public auditCount;

    event AuditRecorded(
        address indexed target,
        address indexed auditor,
        Verdict verdict,
        uint8 score,
        bytes32 findingsHash,
        uint64 timestamp
    );

    /// @notice Catat / perbarui verdict audit untuk `target`.
    function recordAudit(
        address target,
        Verdict verdict,
        uint8 score,
        bytes32 findingsHash
    ) external {
        require(target != address(0), "target zero");
        require(score <= 100, "score>100");
        audits[target] = Audit({
            verdict: verdict,
            score: score,
            findingsHash: findingsHash,
            timestamp: uint64(block.timestamp),
            auditor: msg.sender
        });
        auditCount[target]++;
        emit AuditRecorded(
            target, msg.sender, verdict, score, findingsHash,
            uint64(block.timestamp)
        );
    }

    /// @notice Verdict terakhir untuk `target` (revert-free: kembalikan struct kosong bila belum ada).
    function getAudit(address target) external view returns (Audit memory) {
        return audits[target];
    }
}
