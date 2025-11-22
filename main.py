import os
import textwrap
import base64
import json
from typing import Dict, Callable

import requests
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse

app = FastAPI()

# --------------------------------------------------------------------
# ENV-VARIABLEN
# --------------------------------------------------------------------
UPSELLER_PROMPT = os.getenv("UPSELLER_PROMPT", "Upseller Prompt fehlt – bitte ENV setzen.")
OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENAI_APIKEY")
    or os.getenv("OPENAI_KEY")
)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")  # in Railway anpassbar

# optionale weitere KIs – wenn kein Key gesetzt ist, werden sie einfach übersprungen
GROK_API_KEY = os.getenv("GROK_API_KEY")              # z.B. Grok / xAI
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")    # z.B. Claude
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")          # z.B. Google Gemini


# --------------------------------------------------------------------
# HTML-Template mit Copy-Buttons + verstecktem State
# --------------------------------------------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Upseller PRO – Verkaufs-KI</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{
      --bg: #020617;
      --card: #020617;
      --border: #1e293b;
      --accent: #facc15;
      --accent-soft: rgba(250, 204, 21, 0.08);
      --text-main: #e5e7eb;
      --text-muted: #9ca3af;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      padding: 0;
      min-height: 100vh;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", Arial, sans-serif;
      background: radial-gradient(circle at top, #111827 0, #020617 45%, #000 100%);
      color: var(--text-main);
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .shell {{
      width: 100%;
      max-width: 1120px;
      padding: 24px 16px;
    }}
    .card {{
      background: radial-gradient(circle at top left, #111827 0, #020617 40%, #020617 100%);
      border-radius: 24px;
      border: 1px solid rgba(148,163,184,0.4);
      box-shadow:
        0 24px 80px rgba(0,0,0,0.9),
        0 0 0 1px rgba(15,23,42,0.7);
      padding: 24px;
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(0, 3fr);
      gap: 24px;
    }}
    @media (max-width: 900px) {{
      .card {{
        grid-template-columns: minmax(0, 1fr);
      }}
    }}
    .logo-row {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }}
    .logo-mark {{
      width: 40px;
      height: 40px;
      border-radius: 999px;
      border: 1px solid rgba(250,204,21,0.4);
      background: radial-gradient(circle at 30% 0, #fbbf24 0, #f59e0b 40%, #92400e 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      letter-spacing: 0.04em;
      color: #020617;
      box-shadow: 0 0 20px rgba(250,204,21,0.6);
      font-size: 16px;
    }}
    .logo-text-main {{
      font-weight: 650;
      letter-spacing: 0.12em;
      font-size: 13px;
      text-transform: uppercase;
      color: var(--text-main);
    }}
    .logo-text-sub {{
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.18em;
    }}
    h1 {{
      margin: 0 0 6px 0;
      font-size: 24px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .headline-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 9px;
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,0.6);
      background: rgba(15,23,42,0.85);
      font-size: 11px;
      color: var(--text-muted);
      margin-bottom: 10px;
    }}
    .headline-badge span.accent {{
      color: var(--accent);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.16em;
    }}
    .lead {{
      font-size: 13px;
      color: var(--text-muted);
      max-width: 420px;
      line-height: 1.5;
    }}
    form {{
      margin-top: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    label {{
      font-size: 13px;
      font-weight: 500;
      color: var(--text-main);
    }}
    textarea {{
      width: 100%;
      min-height: 140px;
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid rgba(148,163,184,0.6);
      background: rgba(15,23,42,0.85);
      color: var(--text-main);
      font-size: 14px;
      resize: vertical;
    }}
    textarea::placeholder {{
      color: #6b7280;
    }}
    textarea:focus {{
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 1px rgba(250,204,21,0.5);
    }}
    .row {{
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }}
    input[type="file"] {{
      font-size: 12px;
      color: var(--text-muted);
    }}
    .primary-btn {{
      padding: 9px 18px;
      border-radius: 999px;
      border: 1px solid #facc15;
      background: radial-gradient(circle at 30% 0, #fbbf24 0, #f59e0b 35%, #92400e 100%);
      color: #020617;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      box-shadow:
        0 10px 30px rgba(250,204,21,0.45),
        0 0 0 1px rgba(148,163,184,0.4);
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}
    .primary-btn span.icon {{
      font-size: 14px;
    }}
    .primary-btn:hover {{
      filter: brightness(1.03);
    }}
    .hint {{
      font-size: 11px;
      color: var(--text-muted);
      max-width: 460px;
      line-height: 1.5;
    }}
    .hint b {{
      color: var(--accent);
      font-weight: 600;
    }}
    .result-panel {{
      border-radius: 18px;
      background: radial-gradient(circle at top left, #020617 0, #020617 45%, #020617 100%);
      border: 1px solid rgba(148,163,184,0.5);
      padding: 14px 14px 16px 14px;
      position: relative;
      overflow: hidden;
    }}
    .result-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      gap: 8px;
    }}
    .result-title {{
      font-size: 13px;
      font-weight: 500;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}
    .result-title span.sub {{
      font-size: 11px;
      color: var(--text-muted);
    }}
    .pill {{
      font-size: 11px;
      padding: 3px 9px;
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,0.6);
      background: rgba(15,23,42,0.9);
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.14em;
    }}
    .copy-btn {{
      font-size: 11px;
      padding: 4px 9px;
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,0.7);
      background: rgba(15,23,42,0.85);
      color: var(--text-main);
      cursor: pointer;
    }}
    .copy-btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
    }}
    .result-content {{
      background: radial-gradient(circle at top left, rgba(250,204,21,0.06) 0, rgba(15,23,42,0.95) 34%, rgba(15,23,42,1) 100%);
      border-radius: 14px;
      padding: 12px 11px;
      border: 1px solid rgba(148,163,184,0.4);
      font-size: 13px;
      line-height: 1.6;
      color: var(--text-main);
      max-height: 400px;
      overflow-y: auto;
      white-space: pre-wrap;
    }}
    .result-content::-webkit-scrollbar {{
      width: 6px;
    }}
    .result-content::-webkit-scrollbar-thumb {{
      background: rgba(148,163,184,0.7);
      border-radius: 999px;
    }}
    .result-footer {{
      margin-top: 8px;
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .result-footer span.accent {{
      color: var(--accent);
    }}
    .error {{
      color: #fecaca;
      font-weight: 500;
    }}
  </style>
  <script>
    function copyText(id) {{
      const el = document.getElementById(id);
      if (!el) return;
      const text = el.innerText || el.textContent || "";
      navigator.clipboard.writeText(text).then(function() {{
        alert("Inhalt kopiert ✔");
      }}, function(err) {{
        alert("Kopieren nicht möglich: " + err);
      }});
    }}
  </script>
</head>
<body>
  <div class="shell">
    <div class="card">
      <!-- Linke Seite: Eingabe -->
      <div>
        <div class="logo-row">
          <div class="logo-mark">UP</div>
          <div>
            <div class="logo-text-main">UPSELLER PRO</div>
            <div class="logo-text-sub">AI SELLING ENGINE</div>
          </div>
        </div>

        <div class="headline-badge">
          <span class="accent">V5.0 ULTRA</span>
          <span>Level-System · Marktanalyse · Verhandlung</span>
        </div>

        <h1>Dein persönlicher Verkaufsprofi</h1>
        <p class="lead">
          Starte mit einer kurzen Beschreibung deines Produkts. Upseller stellt dir automatisch
          Rückfragen (Level 1–8) und erstellt anschließend eine komplette Marktanalyse & Preisstrategie.
        </p>

        <form method="post" enctype="multipart/form-data">
          <div>
            <label for="text">LEVEL 1 – Welches Produkt möchtest du verkaufen?</label>
            <textarea id="text" name="text"
              placeholder='Z. B. "PS5 Disk Edition, 2 Controller, OVP, Rechnung, sehr guter Zustand"'></textarea>
          </div>

          <div class="row">
            <div>
              <label for="image">Bild (optional):</label><br>
              <input id="image" name="image" type="file" accept="image/*">
            </div>
            <div style="flex:1 1 auto"></div>
            <button type="submit" class="primary-btn">
              <span class="icon">⚡</span>
              <span>Mit KI optimieren</span>
            </button>
          </div>

          <p class="hint">
            Die KI arbeitet mit deinem internen <b>UPSELLER V5.0 ULTRA</b>-Masterprompt
            (Level-System, Marktanalyse, Verhandlungslogik). Der Prompt liegt nur auf dem Server
            und ist im Code nicht sichtbar.
          </p>
        </form>
      </div>

      <!-- Rechte Seite: Ergebnis -->
      <div class="result-panel">
        <div class="result-header">
          <div class="result-title">
            <span>Level 9 – Marktanalyse & Preisauswertung</span>
            <span class="sub">inkl. psychologischer Preisstrategie & Premium-Anzeigentext</span>
          </div>
          <div class="row" style="justify-content:flex-end;">
            <button type="button" class="copy-btn" onclick="copyText('result_block')">
              Ergebnis kopieren
            </button>
          </div>
        </div>

        <div id="result_block" class="result-content">
{result}
        </div>

        <div class="result-footer">
          <span>Auswertung mit <span class="accent">Upseller PRO</span> · AI Sales Engine</span>
          <span>Ideal für eBay, Kleinanzeigen, Vinted, Dienstleistungen u.v.m.</span>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""

# --------------------------------------------------------------------
# FastAPI Routen
# --------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def form_get():
    state = initial_state()
    question_html = question_for_level(state["level"])
    result_html = (
        "Starte mit LEVEL 1: Beschreibe dein Produkt kurz oben im Feld und "
        "klicke auf „Mit KI optimieren“. Danach kommen automatisch die nächsten Level."
    )
    return HTML_PAGE.format(
        result=result_html,
        question_html=question_html,
        state_b64=encode_state(state),
    )


@app.post("/", response_class=HTMLResponse)
async def form_post(
    text: str = Form(""),
    state_b64: str = Form(""),
    image: UploadFile | None = File(None),
):
    # State dekodieren
    state = decode_state(state_b64)
    level = int(state.get("level", 1))
    answer = (text or "").strip()

    # Solange wir noch in Level 1–8 sind: Antwort ist Pflicht + validieren
    if level <= 8:
        if not answer:
            result_html = "<span class='error'>Bitte beantworte zuerst die aktuelle Level-Frage.</span>"
            question_html = question_for_level(level)
            return HTML_PAGE.format(
                result=result_html,
                question_html=question_html,
                state_b64=encode_state(state),
            )
        ok, msg = validate_user_input(answer)
        if not ok:
            result_html = f"<span class='error'>{msg}</span>"
            question_html = question_for_level(level)
            return HTML_PAGE.format(
                result=result_html,
                question_html=question_html,
                state_b64=encode_state(state),
            )

    # Antwort speichern
    if level <= 8:
        state["answers"][str(level)] = answer

    # Wenn noch nicht alle Level gesammelt: einfach zum nächsten Level springen
    if level < 8:
        state["level"] = level + 1
        question_html = question_for_level(state["level"])
        summary = build_progress_summary(state)
        result_html = summary + "\n\nWeiter mit dem nächsten Level oben."
        return HTML_PAGE.format(
            result=result_html,
            question_html=question_html,
            state_b64=encode_state(state),
        )

    # Ab hier: Level 8 wurde gerade beantwortet -> Level 9 Analyse fahren
    state["level"] = 9
    user_context = build_human_readable_context(state)

    # Bild aktuell nur als Hinweis im Kontext – Vision können wir später einbauen
    if image and image.filename:
        user_context += f"\n\nHinweis: Es wurde ein Bild hochgeladen (Dateiname: {image.filename})."

    try:
        opinions = collect_opinions(user_context)
        meta = build_meta_analysis(user_context, opinions)

        providers_used = meta["providers_used"] or "nur OpenAI"
        level9_block = meta["level9"]
        kicheck_block = meta["kicheck"]

        result_html = f"""
Bisherige Antworten (Kurzüberblick):
{build_progress_summary(state)}

---

<div class="provider-list">
  Auswertung erstellt mit: {providers_used}
</div>

<div class="section-title">
  Level 9 – Marktanalyse & Preisauswertung
  <button class="copy-btn" type="button" onclick="copyText('level9_block')">Level-9 kopieren</button>
</div>
<pre id="level9_block">{level9_block}</pre>

<div class="section-title">
  Level 10 – KI-Vergleichs-Prompt (für andere KIs)
  <button class="copy-btn" type="button" onclick="copyText('kicheck_block')">KI-Prompt kopieren</button>
</div>
<p class="hint">
  Diesen Block kannst du in andere KIs (z. B. Grok, Claude, Gemini, ChatGPT) einfügen,
  damit sie dein Angebot unabhängig prüfen und ergänzen.
</p>
<pre id="kicheck_block">{kicheck_block}</pre>
        """

    except Exception as e:
        result_html = f"<span class='error'>Fehler bei der KI-Anfrage: {e}</span>"

    question_html = question_for_level(state["level"])
    return HTML_PAGE.format(
        result=result_html,
        question_html=question_html,
        state_b64=encode_state(state),
    )
