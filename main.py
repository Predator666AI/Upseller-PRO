import os
import textwrap
import requests
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

# -------------------------------------------------------------
# ENV VARIABLES
# -------------------------------------------------------------
OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENAI_KEY")
    or os.getenv("OPENAI_APIKEY")
)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
UPSELLER_PROMPT = os.getenv("UPSELLER_PROMPT", "PROMPT_FEHLT")


# -------------------------------------------------------------
# FASTAPI INIT
# -------------------------------------------------------------
app = FastAPI()


# -------------------------------------------------------------
# SIMPLE DARK UI
# -------------------------------------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Upseller ULTRA V6.0</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root { color-scheme: dark; }
    body {
      margin: 0; padding: 0;
      font-family: system-ui, sans-serif;
      background: #020617;
      color: #e5e7eb;
    }
    main {
      max-width: 900px;
      margin: 0 auto;
      padding: 30px 16px;
    }
    h1 {
      font-size: 26px;
      margin-bottom: 6px;
      font-weight: 600;
      text-shadow: 0 0 12px rgba(250,204,21,0.35);
    }
    p { font-size: 14px; color: #9ca3af; }
    textarea {
      width: 100%; min-height: 150px;
      padding: 12px;
      background: #0f172a;
      border-radius: 10px;
      border: 1px solid #1e293b;
      color: #e5e7eb;
      resize: vertical;
      font-size: 14px;
    }
    button {
      margin-top: 12px;
      padding: 10px 18px;
      border-radius: 999px;
      border: none;
      background: linear-gradient(135deg,#facc15,#f97316);
      font-weight: 600;
      cursor: pointer;
      color: #020617;
      box-shadow: 0 0 18px rgba(250,204,21,.35);
    }
    pre {
      white-space: pre-wrap;
      background: #0f172a;
      border: 1px solid #1e293b;
      padding: 16px;
      border-radius: 12px;
      margin-top: 20px;
      font-size: 14px;
      color: #e5e7eb;
    }
  </style>
</head>
<body>
<main>
  <h1>Upseller ULTRA V6.0</h1>
  <p>Beschreibe dein Produkt – die KI führt automatisch das Level-System aus.</p>

  <form method="post">
    <textarea name="text" placeholder="Z.B. Massivholzfenster 149×149 cm, 3-fach Verglasung, Baujahr 2021"></textarea>
    <button type="submit">Analyse starten</button>
  </form>

  <pre>{result}</pre>
</main>
</body>
</html>
"""


# -------------------------------------------------------------
# OPENAI CALL
# -------------------------------------------------------------
def call_openai(system_prompt: str, user_text: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY fehlt")

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    }

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=90
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


# -------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_PAGE.format(result="Upseller ist bereit.")


@app.post("/", response_class=HTMLResponse)
async def analyse(text: str = Form(...)):
    cleaned_input = textwrap.dedent(f"""
    NUTZER-EINGABE:
    {text}

    AUFGABE:
    Nutze das interne UPSELLER V6.0 Level-System.
    Führe automatisch Level 1–10 aus.
    Baue Unterlevels ein.
    Analysiere das Produkt komplett.
    Erstelle Premium-Anzeige, Preisstrategie & KI-Check.
    """)

    try:
        output = call_openai(UPSELLER_PROMPT, cleaned_input)
    except Exception as e:
        output = f"FEHLER: {e}"

    return HTML_PAGE.format(result=output)
