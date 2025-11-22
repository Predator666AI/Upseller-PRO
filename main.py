import os
import textwrap
from typing import Dict

import requests
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

# -------------------------------------------------
# ENV Variablen
# -------------------------------------------------

UPSELLER_PROMPT = os.getenv("UPSELLER_PROMPT", "").strip()

# Fallback, falls du mal vergaßt die Variable zu setzen
if not UPSELLER_PROMPT:
    UPSELLER_PROMPT = textwrap.dedent("""
    ⭐ UPSELLER V6.0 ULTRA — Verkaufs- & KI-Analyse-Masterprompt  
    (Fallback-Version im Code – bitte besser in Railway als UPSELLER_PROMPT setzen.)

    Du bist UPSELLER ULTRA V6.0 — ein KI-Verkaufsagent, spezialisiert auf:
    • maximalen Verkaufspreis  
    • perfekte Anzeige  
    • manipulationsfreie, intelligente Verhandlungen  
    • Marktanalysen  
    • psychologische Käuferführung  
    • Multi-KI-Auswertung  

    Du arbeitest:
    • Schritt für Schritt (Level-System)  
    • niemals springend  
    • immer präzise  
    • auto-fragend wenn Infos fehlen  
    • KI-autonom (du leitest den Flow)

    LEVEL-SYSTEM (Kurzfassung):

    LEVEL 1  – Produktname?
    LEVEL 2  – Jahrgang?
    LEVEL 3  – Zustand?
    LEVEL 4  – Ausstattung / Extras?
    LEVEL 5  – Mängel?
    LEVEL 6  – Stückzahl?
    LEVEL 7  – Verkaufsland
    LEVEL 8  – Bilder / optische Merkmale
    LEVEL 8.1 – fehlende Daten einzeln nachfragen.

    LEVEL 9 – Marktanalyse & Preisempfehlung (9.1–9.6)
    LEVEL 10 – Verhandlung (10.1–10.5)

    WICHTIG:
    • Arbeite IMMER levelbasiert.
    • Wenn Infos fehlen, stelle gezielte Rückfragen.
    • Am Ende immer einen 1-Klick-Copy-Block mit allen Ergebnissen ausgeben.
    • Der Nutzer sieht dich als Verkaufsprofi, nicht als klassische KI.
    """)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or os.getenv("OPENAI_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# Optional: zweite KI (nur für PRO-Modus, wenn vorhanden)
GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4-latest")

# -------------------------------------------------
# HTML (Dark Theme, Lite/Pro Umschalter)
# -------------------------------------------------

HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Upseller PRO – Test Dashboard</title>
  <style>
    :root {{
      color-scheme: dark;
    }}
    body {{
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top, #111827 0, #020617 55%);
      color: #e5e7eb;
    }}
    .shell {{
      max-width: 960px;
      margin: 32px auto 40px;
      padding: 0 16px 40px;
    }}
    .card {{
      background: rgba(15,23,42,0.92);
      border-radius: 16px;
      border: 1px solid rgba(148,163,184,0.25);
      box-shadow: 0 18px 45px rgba(0,0,0,0.55);
      padding: 20px 22px 26px;
      backdrop-filter: blur(14px);
    }}
    h1 {{
      margin: 0 0 6px;
      font-size: 26px;
      letter-spacing: 0.03em;
    }}
    .subtitle {{
      font-size: 13px;
      color: #9ca3af;
      margin-bottom: 16px;
    }}
    textarea {{
      width: 100%;
      min-height: 140px;
      border-radius: 10px;
      border: 1px solid rgba(148,163,184,0.35);
      background: rgba(15,23,42,0.95);
      color: #e5e7eb;
      padding: 10px 11px;
      font-size: 14px;
      resize: vertical;
      box-sizing: border-box;
    }}
    textarea::placeholder {{
      color: #6b7280;
    }}
    .mode-row {{
      display: flex;
      gap: 16px;
      align-items: center;
      margin: 10px 0 6px;
      flex-wrap: wrap;
      font-size: 13px;
      color: #9ca3af;
    }}
    .mode-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,0.4);
      background: rgba(15,23,42,0.8);
      cursor: pointer;
    }}
    .mode-pill input {{
      accent-color: #fbbf24;
    }}
    .btn-row {{
      margin-top: 14px;
      display: flex;
      gap: 10px;
      align-items: center;
    }}
    button {{
      border-radius: 999px;
      border: none;
      padding: 9px 18px;
      font-size: 14px;
      cursor: pointer;
      font-weight: 500;
    }}
    .primary-btn {{
      background: linear-gradient(90deg,#facc15,#f97316);
      color: #111827;
      box-shadow: 0 10px 30px rgba(251, 191, 36,0.35);
    }}
    .hint {{
      font-size: 11px;
      color: #9ca3af;
      margin-top: 6px;
    }}
    .result-card {{
      margin-top: 22px;
      background: rgba(15,23,42,0.9);
      border-radius: 14px;
      border: 1px solid rgba(55,65,81,0.8);
      padding: 14px 14px 16px;
      white-space: pre-wrap;
      font-size: 13px;
    }}
    .result-header {{
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 4px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .tag {{
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,0.6);
      color: #e5e7eb;
    }}
    .copy-btn {{
      font-size: 11px;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,0.7);
      background: transparent;
      color: #e5e7eb;
      cursor: pointer;
    }}
    .error {{
      color: #fecaca;
      font-size: 13px;
      font-weight: 500;
    }}
    .second-opinion {{
      margin-top: 14px;
      border-top: 1px solid rgba(55,65,81,0.8);
      padding-top: 10px;
      font-size: 12px;
      color: #9ca3af;
    }}
    @media (max-width: 640px) {{
      .card {{
        padding: 16px 14px 22px;
      }}
      h1 {{
        font-size: 22px;
      }}
    }}
  </style>
  <script>
    function copyBlock(id) {{
      const el = document.getElementById(id);
      if (!el) return;
      const text = el.innerText || el.textContent || "";
      navigator.clipboard.writeText(text).then(function() {{
        alert("Text in die Zwischenablage kopiert.");
      }}, function(err) {{
        alert("Kopieren nicht möglich: " + err);
      }});
    }}
  </script>
</head>
<body>
  <div class="shell">
    <div class="card">
      <h1>Upseller PRO – Test Dashboard</h1>
      <div class="subtitle">
        Wähle unten Lite oder PRO, gib dein Produkt ein – Upseller ULTRA V6.0 übernimmt die Level, Marktanalyse & Verhandlung.
      </div>

      <form method="post">
        <div class="mode-row">
          <span>Modus:</span>
          <label class="mode-pill">
            <input type="radio" name="mode" value="lite" {mode_lite_checked}>
            Lite – 1× GPT (günstiger)
          </label>
          <label class="mode-pill">
            <input type="radio" name="mode" value="pro" {mode_pro_checked}>
            PRO – GPT + externe KI (falls Keys gesetzt)
          </label>
        </div>

        <textarea name="text" placeholder='Beschreibe hier kurz dein Produkt oder füge deine bisherigen Level-Antworten ein (z. B. "PS5 Disc Version, 2022, sehr guter Zustand, 2 Controller, OVP, Deutschland").'>{text_value}</textarea>

        <div class="btn-row">
          <button type="submit" class="primary-btn">Mit KI optimieren</button>
        </div>

        <div class="hint">
          Die KI nutzt deinen internen UPSELLER V6.0 ULTRA Masterprompt aus der Environment-Variable <code>UPSELLER_PROMPT</code>.
          API-Keys bleiben sicher auf dem Server.
        </div>
      </form>

      <div class="result-card">
        {result_html}
      </div>
    </div>
  </div>
</body>
</html>
"""

# -------------------------------------------------
# KI Call–Funktionen
# -------------------------------------------------


def call_openai(system_prompt: str, user_text: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY ist nicht gesetzt.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_text,
            },
        ],
        "temperature": 0.4,
    }
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def call_grok(system_prompt: str, user_text: str) -> str:
    """Einfache Grok-Abfrage – wird nur genutzt, wenn GROK_API_KEY gesetzt ist UND Modus=pro."""
    if not GROK_API_KEY:
        raise RuntimeError("GROK_API_KEY ist nicht gesetzt.")

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": GROK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "stream": False,
        "temperature": 0,
    }
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


# -------------------------------------------------
# FastAPI App
# -------------------------------------------------

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def form_get():
    result_html = "Upseller wartet auf deine Eingabe. Starte mit einem Produkt oder deiner ersten Level-Antwort."
    return HTML_PAGE.format(
        mode_lite_checked="checked",
        mode_pro_checked="",
        text_value="",
        result_html=result_html,
    )


@app.post("/", response_class=HTMLResponse)
async def form_post(
    mode: str = Form("lite"),
    text: str = Form(""),
):
    text = (text or "").strip()
    if not text:
        result_html = "<span class='error'>Bitte beschreibe dein Produkt oder füge deine bisherigen Antworten ein.</span>"
        return HTML_PAGE.format(
            mode_lite_checked="checked" if mode != "pro" else "",
            mode_pro_checked="checked" if mode == "pro" else "",
            text_value="",
            result_html=result_html,
        )

    # Systemprompt + Zusatzinfo je nach Modus
    system_prompt = UPSELLER_PROMPT + "\n\n[Hinweis: Aktueller Modus: {}]".format(
        "LITE – nur GPT als Kern-KI"
        if mode != "pro"
        else "PRO – GPT + ggf. externe KIs (Grok etc.) für Gegenprüfungen"
    )

    try:
        # 1) Hauptauswertung mit OpenAI
        main_answer = call_openai(system_prompt, text)

        # 2) Optional: zweite Meinung via Grok im PRO-Modus
        second_opinion_block = ""
        if mode == "pro" and GROK_API_KEY:
            try:
                grok_answer = call_grok(
                    "Du bist eine Verkaufs-KI, die die Ergebnisse eines anderen Upseller-Systems gegenprüft. "
                    "Fasse dich kurz (max. 8 Sätze).",
                    f"Produkt-/Kontextbeschreibung:\n{text}\n\n"
                    f"Ergebnis der Haupt-KI:\n{main_answer}\n\n"
                    "Gib mir eine kurz zusammengefasste Zweitmeinung (Preisrange & Risiko).",
                )
                second_opinion_block = (
                    "<div class='second-opinion'>"
                    "<div class='result-header'><span>Zweitmeinung (Grok)</span></div>"
                    f"<div>{grok_answer}</div>"
                    "</div>"
                )
            except Exception as e:
                second_opinion_block = (
                    "<div class='second-opinion'>"
                    f"Zweitmeinung (Grok) nicht verfügbar: {e}"
                    "</div>"
                )

        # Ergebnisbereich inkl. Copy-Button
        result_html = f"""
        <div class="result-header">
          <span>Upseller-Antwort (Level-System & Analyse)</span>
          <button type="button" class="copy-btn" onclick="copyBlock('result_block')">Alles kopieren</button>
        </div>
        <div id="result_block">{main_answer}</div>
        {second_opinion_block}
        """

    except Exception as e:
        result_html = f"<span class='error'>Fehler bei der KI-Anfrage: {e}</span>"

    return HTML_PAGE.format(
        mode_lite_checked="checked" if mode != "pro" else "",
        mode_pro_checked="checked" if mode == "pro" else "",
        text_value=text,
        result_html=result_html,
    )
