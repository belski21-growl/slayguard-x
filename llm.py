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
             for f in result["findings"]] or ["- Tidak ada temuan."]
    prompt = (
        "Kamu asisten keamanan smart contract. Jelaskan hasil audit ini ke pengguna "
        "awam dalam Bahasa Indonesia, maks 6 kalimat pendek: apa risikonya, apa yang "
        "aman, dan 1 aksi yang harus dilakukan sebelum interaksi.\n"
        f"Alamat: {result['address']} ({result['chain']}), skor {result['score']}/100, "
        f"verdict {verdict}.\nTemuan:\n" + "\n".join(lines)
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
        return t + f"\n\n(LLM gagal: {type(e).__name__} — tampil penjelasan heuristik.)", "heuristic"


def _template(result):
    v = result["verdict"]
    n = len(result["findings"])
    if v == "GO":
        s = (f"Skor {result['score']}/100 — tidak ada temuan berisiko tinggi. "
             "Kontrak ini terlihat aman untuk interaksi standar.")
    elif v == "CAUTION":
        s = (f"Skor {result['score']}/100 — ada {n} temuan. Masih bisa interaksi, "
             "tapi baca dulu temuan di bawah dan jangan approve tanpa batas.")
    else:
        s = (f"Skor {result['score']}/100 — HOLD. Ada risiko serius di temuan "
             "di bawah. Jangan mint/approve sebelum risikonya jelas.")
    s += " Aksi: cek owner & fungsi berbahaya di atas; kalau owner tidak dikenal, jangan lanjut."
    return s
