"""LLM explainer — OpenAI-compatible chat API, key HANYA dari env.

Env: SLAY_LLM_BASE_URL, SLAY_LLM_API_KEY, SLAY_LLM_MODEL.
Tanpa key -> fallback template (dilabeli 'heuristic'), app tetap jalan penuh.
Key TIDAK PERNAH ditulis ke file / log / response.
"""
import os

import requests


def explain(result):
    """Return (text, mode) — mode 'llm' atau 'heuristic'."""
    key = os.environ.get("SLAY_LLM_API_KEY", "").strip()
    base = os.environ.get("SLAY_LLM_BASE_URL", "").strip().rstrip("/")
    model = os.environ.get("SLAY_LLM_MODEL", "deepseek-v4.1-flash-free").strip()
    if not key or not base:
        return _template(result), "heuristic"

    verdict = result["verdict"]
    lines = [f"- [{f['severity']}] {f['title']}: {f['detail']}"
             for f in result["findings"]] or ["- No findings."]
    prompt = (
        "You are a smart contract security assistant. Explain this audit result to a lay user "
        "in English, max 6 short sentences: what the risk is, what is safe, and 1 action to "
        "take before interacting.\n"
        f"Address: {result['address']} ({result['chain']}), score {result['score']}/100, "
        f"verdict {verdict}.\nFindings:\n" + "\n".join(lines)
    )
    try:
        r = requests.post(f"{base}/chat/completions", json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3, "max_tokens": 400,
        }, timeout=60)
        data = r.json()
        text = data["choices"][0]["message"]["content"].strip()
        return text, "llm"
    except Exception as e:  # noqa: BLE001 - fallback aman
        t = _template(result)
        return t + f"\n\n(LLM failed: {type(e).__name__} — showing the heuristic explanation.)", "heuristic"


def _template(result):
    v = result["verdict"]
    n = len(result["findings"])
    if v == "GO":
        s = (f"Score {result['score']}/100 — no high-risk findings. "
             "This contract looks safe for standard interaction.")
    elif v == "CAUTION":
        s = (f"Score {result['score']}/100 — {n} findings. You can still interact, "
             "but read the findings below first and never approve without limits.")
    else:
        s = (f"Score {result['score']}/100 — HOLD. There is serious risk in the findings "
             "below. Do not mint/approve before the risk is clear.")
    s += " Action: check the owner & dangerous functions above; if the owner is unknown, stop here."
    return s
