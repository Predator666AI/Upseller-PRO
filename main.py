import os
import textwrap
import requests
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

# --------------------------------------------------------------------
# ENV-VARIABLEN
# --------------------------------------------------------------------
UPSELLER_PROMPT = os.getenv(
    "UPSELLER_PROMPT",
    "Upseller Prompt fehlt – bitte UPSELLER_PROMPT in Railway setzen."
)

OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENAI_APIKEY")
    or os.getenv("OPENAI_KEY")
)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


# --------------------------------------------------------------------
# HTML-Oberfläche (einfach, aber schick & dunkel)
# --------------------------------------------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Upseller ULTRA – Verkaufsoptimierung</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      color-scheme: dark;
    }
    body {{
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #020617;
      color: #e5e7eb;
    }}
    .wrap {{
      max-width: 900px;
      margin: 0 auto;
      padding: 24px 16px 40px;
    }}
    .card {{
      background: #020617;
      border-radius: 16px;
      border: 1px solid #1f2937;
      padding: 20px 18px;
      box-shadow: 0 18px 45px rgba(0,0,0,0.65);
    }}
    h1 {{
      font-size: 24px;
      margin: 0 0 6px;
    }}
    h2 {{
      font-size: 16px;
      margin: 18px 0 4px;
    }}
    p {{
      font-size: 14px;
      color: #9ca3af;
      margin: 4px 0 10px;
    }}
    textarea {{
      width: 100%;
      min-height: 120px;
      border-radius: 10px;
      border: 1px solid #1f2937;
      background: #020617;
      color: #e5e7eb;
      padding: 10px 12px;
      font-size: 14px;
      resize: vertical;
      box-sizing: border-box;
    }}
    textarea::placeholder {{
      color: #6b7280;
    }}
    button {{
      margin-top: 14px;
      padding: 10px 18px;
      border-radius: 999px;
      border: 0;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      background: linear-gradient(135deg, #facc15, #f97316);
      color: #020617;
      transition: transform 0.08s ease, box-shadow 0.08s ease, filter 0.08s ease;
      box-shadow: 0 10px 30px rgba(250, 204, 21, 0.35);
    }}
    button:hover {{
      transform: translateY(-1px);
      filter: brightness(1.05);
      box-shadow: 0 16px 40px rgba(250, 204, 21, 0.45);
    }}
    button:active {{
      transform: translateY(0);
      filter: brightness(0.97);
      box-shadow: 0 6px 20px rgba(15, 23, 42, 0.9);
    }}
    .result-box {{
      margin-top: 20px;
      padding: 14px 12px;
      border-radius: 12px;
      border: 1px solid #111827;
      background: radial-gradient(circle at top left, #0f172a, #020617 56%);
      white-space: pre-wrap;
      font-size: 14px;
      color: #e5e7eb;
    }}
    .label {{
      font-size: 13px;
      font-weight: 500;
      color: #e5e7eb;
      margin-bottom: 4px;
      display: block;
    }}
    .hint {{
      font-size: 12px;
      color: #6b7280;
      margin-top: 6px;
    }}
    .error {{
      color: #fca5a5;
      font-weight: 500;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 2px 10px;
      border-radius: 999px;
      border: 1px solid #1f2937;
      background: rgba(15,23,42,0.9);
      font-size: 11px;
      color: #9ca3af;
      margin-bottom: 10px;
    }}
    .badge-dot {{
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: #22c55e;
      box-shadow: 0 0 8px rgba(34,197,94,0.8);
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="badge">
        <span class="badge-dot"></span>
        Upseller ULTRA · Server aktiv
      </div>
      <h1>Upseller ULTRA</h1>
      <p>Dein Verkaufs-KI-Assistent: analysiert dein Produkt, simuliert Marktpreise und erstellt eine fertige Anzeige.</p>

      <form method="post">
        <label class="label" for="text">
          Was möchtest du verkaufen?
        </label>
        <textarea
          id="text"
          name="text"
          placeholder='Beispiel: "Massivholzfenster 149×149 cm, 3-fach Verglasung, Baujahr 2021, sehr guter Zustand"'
        ></textarea>

        <button type="submit">Upseller Analyse starten</button>

        <p class="hint">
          Tipp: Du kannst auch mehr Details direkt mit reinschreiben (Alter, Zustand, Marke, Mängel, Standort).
        </p>
      </form>

      <div class="result-box">
        {result}
      </div>
    </div>
  </div>
</body>
</html>
"""


# --------------------------------------------------------------------
# OpenAI-Helfer
# --------------------------------------------------------------------
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
            {"role": "user", "content": user_text},
        ],
    }
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# --------------------------------------------------------------------
# Routen
# --------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def form_get():
    """
    Startseite – zeigt das Formular.
    """
    start_text = (
        "Upseller ULTRA ist bereit.\n\n"
        "Beschreibe oben dein Produkt oder kopiere eine vorhandene Anzeige hinein.\n"
        "Die KI analysiert dann marktgerecht und erstellt eine neue, optimierte Anzeige "
        "mit Preisspanne und Strategie."
    )
    return HTML_PAGE.format(result=start_text)


@app.post("/", response_class=HTMLResponse)
async def form_post(text: str = Form(...)):
    user_text = (text or "").strip()

    if not user_text:
        result_html = "<span class='error'>Bitte beschreibe zuerst dein Produkt.</span>"
        return HTML_PAGE.format(result=result_html)

    # Input evtl. leicht aufbereiten, damit der Prompt klaren Kontext hat
    wrapped_input = textwrap.dedent(f"""
    NUTZER-BESCHREIBUNG / BESTEHENDE ANZEIGE:

    {user_text}

    AUFGABE:
    Nutze deinen internen UPSELLER-Masterprompt, arbeite das Level-System intern ab
    und liefere mir eine vollständige Auswertung gemäß LEVEL 9 und LEVEL 10:

    - Preisspanne
    - Marktanalyse
    - psychologische Preisstrategie
    - Premium-Anzeigentext (1-Block-Copy)
    - KI-Check-Block für andere KIs

    Antwort bitte als einen durchgehenden, gut lesbaren Textblock.
    """)

    try:
        answer = call_openai(UPSELLER_PROMPT, wrapped_input)
        result_html = answer
    except Exception as e:
        result_html = (
            "<span class='error'>Fehler bei der KI-Anfrage: "
            + str(e)
            + "</span>"
        )

    return HTML_PAGE.format(result=result_html)
