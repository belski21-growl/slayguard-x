# Voiceover script — SlayGuard X demo (English, Helio voice)
# Video: slayguard-x-demo.mp4, 97.3s. Narration is placed per segment
# with ffmpeg adelay; each clip must fit its slot (next clip's start).
# Facts are from the actual video: CAUTION 65, factory proxy, 46 NAND gates,
# depth 15, 256/256 verified, registry 0x55b9…42e5, ~$0.0013 mainnet cost.
# The circuit is NOT taped out yet — the script says "computable on-chain",
# never that tape-out is done. No addresses, hashes or URLs read aloud.
# Do NOT read addresses, hashes or URLs aloud.

## A — title card — start 0.0s, slot ~8s
SlayGuard X. Audit any X Layer contract before you click.

## B — problem — start 8.0s, slot ~15s
One wrong mint, one wrong approval, and a wallet is drained. Most people cannot read a contract, so they click blind.

## C — live audit — start 23.6s, slot ~16s
The TapeOut factory is a proxy, so the real logic lives in its implementation contract. We audit that logic, live. Verdict: caution, sixty-five out of a hundred. The upgrade function means the logic can be swapped entirely, and the owner can withdraw funds. The report explains it in plain language.

## D — TapeOut live + gas — start 42.0s, slot ~18s
The factory and its market are live on X Layer mainnet, and gas is two hundredths of a gwei. Reading the chain costs effectively nothing.

## E — Risk Circuit — start 58.4s, slot ~8s
The verdict rules are also a circuit: forty-six NAND gates, depth fifteen, checked against all two hundred fifty-six inputs. The same verdict, computable on-chain.

## F — registry on-chain — start 69.0s, slot ~11s
And the verdict is on-chain. The registry on X Layer mainnet holds caution, sixty-five, for the factory, recorded for about a tenth of a cent. Anyone can read it back before they click.

## G — model — start 80.5s, slot ~10s
Audits are free for everyone. Pro reports, a paid API, and integrations for wallets and marketplaces pay for it.

## H — close — start 88.0s, slot ~10s
SlayGuard X. Audit before you click. Built for OKX Build X on X Layer.
