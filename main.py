import os
import textwrap
from typing import Dict, Callable, Tuple, Optional

import requests
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse

app = FastAPI()

# --------------------------------------------------------------------
# ENV-VARIABLEN
# --------------------------------------------------------------------
UPSELLER_PROMPT = os.getenv(
    "UPSELLER_PROMPT",
    "Upseller Prompt fehlt – bitte in den Environment Variables setzen."
)

OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENAI_APIKEY")
    or os.getenv("OPENAI_KEY")
)

# Du kannst das Modell in Railway über eine Variable OPENAI_MODEL anpassen
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# optionale weitere KIs – wenn kein Key gesetzt ist, werden sie einfach übersprungen
GROK_API_KEY = os.getenv("GROK_API_KEY")         # z.B. Grok / xAI
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # z.B. Claude
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")     # z.B. Google Gemini


# --------------------------------------------------------------------
# HTML-Template (Dark Mode + Logo + Copy-Buttons)
# --------------------------------------------------------------------
# Trage hier dein echtes Logo ein (direkter Bild-Link, z. B. von Imgur)
LOGO_URL = "https://i.imgur.com/placeholder.png"

HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Upseller PRO – Test Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{
      color-scheme: dark;
    }}
    body {{
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top, #1f2937 0, #020617 55%, #000 100%);
      color: #e5e7eb;
    }}
    .shell {{
      max-width: 960px;
      margin: 32px auto;
      padding: 0 16px 32px;
    }}
    .header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 24px;
    }}
    .logo {{
      width: 40px;
      height: 40px;
      border-radius: 12px;
      background: linear-gradient(135deg, #fbbf24, #f97316);
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }}
    .logo img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}
    .title-main {{
      font-size: 22px;
      font-weight: 700;
    }}
    .title-sub {{
      font-size: 13px;
      color: #9ca3af;
    }}
    .card {{
      background: rgba(15, 23, 42, 0.92);
      border-radius: 18px;
      padding: 20px 20px 16px;
      box-shadow:
        0 18px 45px rgba(15, 23, 42, 0.9),
        0 0 0 1px rgba(148, 163, 184, 0.1);
      border: 1px solid rgba(148, 163, 184, 0.18);
      backdrop-filter: blur(18px);
    }}
    label {{
      font-size: 13px;
      color: #9ca3af;
    }}
    textarea {{
      width: 100%;
      min-height: 180px;
      margin-top: 6px;
      padding: 10px 11px;
      font-size: 14px;
      border-radius: 10px;
      border: 1px solid rgba(55, 65, 81, 0.9);
      background: rgba(15, 23, 42, 0.9);
      color: #e5e7eb;
      resize: vertical;
      box-sizing: border-box;
    }}
    textarea::placeholder {{
      color: #6b7280;
    }}
    input[type="file"] {{
      margin-top: 6px;
      font-size: 13px;
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-top: 14px;
    }}
    button {{
      border-radius: 999px;
      border: 1px solid transparent;
      padding: 9px 16px;
      font-size: 13px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #111827;
      color: #e5e7eb;
      transition: background 0.15s ease, transform 0.07s ease, box-shadow 0.15s ease;
      box-shadow: 0 12px 25px rgba(15, 23, 42, 0.75);
    }}
    button.primary {{
      background: linear-gradient(135deg, #f97316, #facc15);
      color: #0b1120;
      box-shadow: 0 16px 35px rgba(250, 204, 21, 0.55);
    }}
    button:hover {{
      transform: translateY(-1px);
      box-shadow: 0 18px 40px rgba(15, 23, 42, 0.8);
      filter: brightness(1.03);
    }}
    .hint {{
      font-size: 11px;
      color: #9ca3af;
      margin-top: 10px;
      line-height: 1.5;
    }}
    .results {{
      margin-top: 22px;
      display: grid;
      gap: 16px;
    }}
    .result-card {{
      border-radius: 14px;
      padding: 14px 14px 11px;
      background: radial-gradient(circle at top left, rgba(250, 204, 21, 0.08) 0, rgba(15, 23, 42, 0.98) 40%);
      border: 1px solid rgba(55, 65, 81, 0.9);
    }}
    .result-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }}
    .result-title {{
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.02em;
      text-transform: uppercase;
      color: #e5e7eb;
    }}
    .copy-btn {{
      font-size: 11px;
      padding: 4px 9px;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(148, 163, 184, 0.5);
      color: #e5e7eb;
      box-shadow: none;
    }}
    .copy-btn:hover {{
      background: #020617;
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-wrap: break-word;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 13px;
      line-height: 1.5;
      color: #e5e7eb;
    }}
    .providers {{
      font-size: 11px;
      color: #9ca3af;
      margin-top: 3px;
    }}
    .error {{
      color: #fecaca;
      font-size: 13px;
      font-weight: 500;
    }}
    @media (max-width: 640px) {{
      .shell {{
        margin-top: 20px;
      }}
      .card {{
        padding: 16px 14px 14px;
      }}
    }}
  </style>
  <script>
    function copyText(id) {{
      const el = document.getElementById(id);
      if (!el) return;
      const text = el.innerText || el.textContent || "";
      navigator.clipboard.writeText(text).then(
        function() {{ alert("Inhalt in die Zwischenablage kopiert."); }},
        function(err) {{ alert("Konnte nicht kopieren: " + err); }}
      );
    }}
  </script>
</head>
<body>
  <div class="shell">
    <div class="header">
      <div class="logo">
        <img src="{logo_url}" alt="Upseller Logo">
      </div>
      <div>
        <div class="title-main">Upseller PRO</div>
        <div class="title-sub">V5.0 ULTRA · Verkaufs- & KI-Analyse-Dashboard</div>
      </div>
    </div>

    <div class="card">
      <form method="post" enctype="multipart/form-data">
        <label for="text">LEVEL 1 – Welches Produkt möchtest du verkaufen?</label>
        <textarea id="text" name="text" placeholder='Z. B. "PS5 Disc Edition, 2 Controller, 3 Spiele, wie neu"'></textarea>

        <div style="margin-top:10px;">
          <label for="image">Bild (optional):</label><br>
          <input id="image" name="image" type="file" accept="image/*">
        </div>

        <div class="actions">
          <button type="submit" class="primary">Mit KI optimieren</button>
        </div>

        <p class="hint">
          Die KI arbeitet mit deinem internen UPSELLER V5.0 ULTRA Masterprompt (Level-System, Marktanalyse, Verhandlungslogik).
          Der Prompt liegt sicher als Environment Variable auf dem Server und ist nicht im Code sichtbar.
        </p>
      </form>

      <div class="results">
        {result}
      </div>
    </div>
  </div>
</body>
</html>
"""


# --------------------------------------------------------------------
# KI-Provider-Wrapper
# --------------------------------------------------------------------

def call_openai(system_prompt: str, user_text: str) -> str:
    """Standard-Aufruf an OpenAI (wird auch für die Meta-Auswertung genutzt)."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY nicht gesetzt.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    }
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_grok(system_prompt: str, user_text: str) -> str:
    """Beispiel für Grok / xAI – wird nur aufgerufen, wenn GROK_API_KEY gesetzt ist."""
    if not GROK_API_KEY:
        raise RuntimeError("GROK_API_KEY nicht gesetzt.")
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
      "Authorization": f"Bearer {GROK_API_KEY}",
      "Content-Type": "application/json",
    }
    data = {
        "model": "grok-beta",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    }
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_claude(system_prompt: str, user_text: str) -> str:
    """Beispiel für Anthropic Claude – wird nur genutzt, wenn ANTHROPIC_API_KEY gesetzt ist."""
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY nicht gesetzt.")
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1200,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_text},
        ],
    }
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    msg = resp.json()["content"][0]["text"]
    return msg


def call_gemini(system_prompt: str, user_text: str) -> str:
    """Beispiel für Google Gemini – wird nur genutzt, wenn GEMINI_API_KEY gesetzt ist."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY nicht gesetzt.")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-1.5-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
    )
    full_prompt = system_prompt + "\n\nNutzer:\n" + user_text
    data = {"contents": [{"parts": [{"text": full_prompt}]}]}
    resp = requests.post(url, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def get_available_providers() -> Dict[str, Callable[[str, str], str]]:
    """
    Baut automatisch eine Liste aller verfügbaren KIs anhand der gesetzten ENV-Variablen.
    OpenAI ist immer dabei und dient auch als Meta-KI.
    """
    providers: Dict[str, Callable[[str, str], str]] = {}
    providers["openai"] = call_openai

    if GROK_API_KEY:
        providers["grok"] = call_grok
    if ANTHROPIC_API_KEY:
        providers["claude"] = call_claude
    if GEMINI_API_KEY:
        providers["gemini"] = call_gemini

    return providers


def call_provider_safe(
    name: str,
    func: Callable[[str, str], str],
    system_prompt: str,
    user_text: str,
) -> str:
    """
    Ruft einen Provider sicher auf und gibt im Fehlerfall eine Text-Fehlermeldung zurück,
    statt die gesamte App crashen zu lassen.
    """
    try:
        return func(system_prompt, user_text)
    except requests.Timeout:
        return f"[{name}: Timeout nach 60s]"
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        return f"[{name}: HTTP-Fehler {status}]"
    except Exception as e:  # noqa: BLE001
        return f"[{name}: {type(e).__name__}: {e}]"


def collect_opinions(user_context: str) -> Dict[str, str]:
    """
    Ruft alle verfügbaren Provider nacheinander auf und sammelt deren Roh-Antworten.
    (Synchron, aber robust.)
    """
    providers = get_available_providers()
    opinions: Dict[str, str] = {}

    for name, func in providers.items():
        opinions[name] = call_provider_safe(name, func, UPSELLER_PROMPT, user_context)

    return opinions


def safe_parse_meta(meta_answer: str) -> Tuple[str, str]:
    """
    Robustes Parsing der Antwort der Meta-KI in:
      - Level 9 Block
      - KI-Vergleichs-Prompt Block
    Erwartet Marker:
      ---LEVEL9_START--- ... ---LEVEL9_END---
      ---KICHECK_START--- ... ---KICHECK_END---
    Fällt bei Fehlern auf eine einfache Ausgabe zurück.
    """
    level9 = ""
    kicheck = ""

    try:
        if ("---LEVEL9_START---" in meta_answer
                and "---LEVEL9_END---" in meta_answer):
            part = meta_answer.split("---LEVEL9_START---", 1)[1]
            level9, rest = part.split("---LEVEL9_END---", 1)

            if ("---KICHECK_START---" in rest
                    and "---KICHECK_END---" in rest):
                part2 = rest.split("---KICHECK_START---", 1)[1]
                kicheck = part2.split("---KICHECK_END---", 1)[0]
        else:
            # Fallback: Versuche, Antwort grob zu teilen
            parts = meta_answer.split("\n\n---\n\n", 1)
            level9 = parts[0] if parts else meta_answer
            if len(parts) > 1:
                kicheck = parts[1]
            else:
                kicheck = "KI-Vergleichs-Prompt konnte nicht extrahiert werden."
    except Exception as e:  # noqa: BLE001
        level9 = meta_answer
        kicheck = f"Parsing-Fehler: {e}"

    return level9.strip(), kicheck.strip()


def build_meta_analysis(user_context: str, opinions: Dict[str, str]) -> Dict[str, str]:
    """
    Nutzt OpenAI (ChatGPT) als Meta-KI, um alle Einzel-Gutachten zu einer
    gemeinsamen Level-9-Auswertung + KI-Vergleichs-Prompt zu verschmelzen.
    """
    providers_used = ", ".join(opinions.keys()) if opinions else "openai"

    meta_system = """
<role>UPSELLER ULTRA Meta-Analyst</role>

<task>
Du bekommst mehrere KI-Gutachten zu einem Verkaufsobjekt (z. B. openai, grok, claude, gemini)
und sollst daraus EINE konsistente Auswertung erstellen:
1. Level 9: Marktanalyse & Preisspanne, Wertfaktoren, Plattformen, Timing,
   psychologische Preisstrategie, Premium-Anzeigentext, Profi-Zusammenfassung.
2. Level 10: KI-Vergleichs-Prompt, der als Block von anderen KIs kopiert/verstanden werden kann.
3. Wenn wichtige Infos fehlen (Maße, Zustand, Baujahr, Region etc.), ergänze diese plausibel,
   aber kennzeichne sie als 'Schätzung'.
</task>

<output_format>
---LEVEL9_START---
[Deine konsolidierte Level-9-Auswertung als zusammenhängender Textblock]
---LEVEL9_END---
---KICHECK_START---
[Vollständiger KI-Vergleichs-Prompt im vom Nutzer gewünschten Format]
---KICHECK_END---
</output_format>

Antwort NUR in diesem Format, ohne zusätzliche Erklärungen.
"""

    opinions_text = ""
    for name, content in opinions.items():
        opinions_text += f"\n\n### Gutachten {name.upper()}:\n{content}\n"

    meta_user = textwrap.dedent(f"""
    NUTZER-KONTEXT (Antworten aus Level 1–8, Beschreibung etc.):

    {user_context}

    GENUTZTE KIs: {providers_used}

    MEHRERE KI-GUTACHTEN:

    {opinions_text}

    AUFGABE:
    1. Ziehe aus den Gutachten eine einzige, saubere Level-9-Auswertung gemäß
       UPSELLER V5.0 ULTRA (Preisbereich, Wertfaktoren, Plattformen, Timing,
       psychologische Preisstrategie, Premium-Anzeigentext, Profi-Zusammenfassung).
    2. Erstelle am Ende zusätzlich den Level-10-KI-Vergleichs-Prompt exakt im Block-Format,
       damit andere KIs das Angebot prüfen können.
    3. Nutze strikt die Marker ---LEVEL9_START--- / ---LEVEL9_END--- und
       ---KICHECK_START--- / ---KICHECK_END---.
    """)

    meta_raw = call_openai(meta_system, meta_user)
    level9_text, kicheck_text = safe_parse_meta(meta_raw)

    return {
        "providers_used": providers_used,
        "level9": level9_text,
        "kicheck": kicheck_text,
    }


# --------------------------------------------------------------------
# FastAPI Routes
# --------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def form_get() -> HTMLResponse:
    """Erstes Laden des Dashboards."""
    info = (
        "Starte mit einer kurzen Beschreibung deines Produkts – "
        "Upseller ULTRA übernimmt danach die Marktanalyse & Preisfindung."
    )
    result_html = f"<div class='hint'>{info}</div>"
    return HTMLResponse(HTML_PAGE.format(result=result_html, logo_url=LOGO_URL))


@app.post("/", response_class=HTMLResponse)
async def form_post(
    text: str = Form(...),
    image: Optional[UploadFile] = File(None),  # aktuell nur Info, keine Vision-Auswertung
) -> HTMLResponse:
    user_context = text.strip()

    if not user_context:
        result_html = "<div class='error'>Bitte gib zuerst eine Beschreibung deines Produkts ein.</div>"
        return HTMLResponse(HTML_PAGE.format(result=result_html, logo_url=LOGO_URL))

    # Falls ein Bild hochgeladen wurde, erweitern wir nur den Kontext-Hinweis.
    if image is not None and image.filename:
        user_context += (
            "\n\nHinweis: Es wurde ein Bild hochgeladen "
            f"(Dateiname: {image.filename}). "
            "Upseller darf den Zustand/Beschreibung des Produkts anhand eines Fotos "
            "zusätzlich präzisieren, auch ohne Vision-API."
        )

    try:
        # 1. Gutachten aller verfügbaren KIs einsammeln
        opinions = collect_opinions(user_context)

        # 2. Meta-Auswertung durch openai
        meta = build_meta_analysis(user_context, opinions)

        providers_used = meta["providers_used"]
        level9_block = meta["level9"]
        kicheck_block = meta["kicheck"]

        result_html = f"""
        <div class="providers">
          Auswertung erstellt mit: {providers_used}
        </div>

        <div class="result-card">
          <div class="result-header">
            <div class="result-title">Level 9 – Marktanalyse &amp; Preis-Auswertung</div>
            <button type="button" class="copy-btn" onclick="copyText('level9_block')">Level 9 kopieren</button>
          </div>
          <pre id="level9_block">{level9_block}</pre>
        </div>

        <div class="result-card">
          <div class="result-header">
            <div class="result-title">Level 10 – KI-Vergleichs-Prompt</div>
            <button type="button" class="copy-btn" onclick="copyText('kicheck_block')">KI-Prompt kopieren</button>
          </div>
          <pre id="kicheck_block">{kicheck_block}</pre>
        </div>
        """

    except Exception as e:  # noqa: BLE001
        result_html = (
            "<div class='result-card'>"
            "<div class='result-header'><div class='result-title'>Fehler</div></div>"
            f"<pre class='error'>Fehler bei der KI-Anfrage: {e}</pre>"
            "</div>"
        )

    return HTMLResponse(HTML_PAGE.format(result=result_html, logo_url=LOGO_URL))
