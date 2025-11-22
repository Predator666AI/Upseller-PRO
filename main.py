from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import os
import json
from openai import OpenAI

app = FastAPI()

# OpenAI-Client (API-Key kommt aus Railway-Variable OPENAI_API_KEY)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# HTML-Template mit verstecktem Verlauf
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Upseller PRO</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      max-width: 900px;
      margin: 40px auto;
      padding: 0 15px;
    }}
    h1 {{
      font-size: 26px;
      margin-bottom: 5px;
    }}
    p.subtitle {{
      margin-top: 0;
      color: #555;
      font-size: 14px;
    }}
    textarea {{
      width: 100%;
      padding: 10px;
      font-size: 15px;
      box-sizing: border-box;
    }}
    button {{
      margin-top: 10px;
      padding: 10px 20px;
      font-size: 15px;
      cursor: pointer;
    }}
    .hint {{
      margin-top: 10px;
      font-size: 12px;
      color: #666;
    }}
    .box {{
      margin-top: 25px;
      padding: 15px;
      background: #f2f2f2;
      border-radius: 8px;
      white-space: pre-wrap;
    }}
    .error {{
      color: #b00020;
      font-weight: bold;
    }}
  </style>
</head>
<body>
  <h1>Upseller PRO – Test Dashboard</h1>
  <p class="subtitle">
    Füge unten deine Anzeige / Beschreibung ein (z. B. eBay, Kleinanzeigen, Vinted, Dienstleistung etc.).
  </p>

  <form method="post">
    <textarea name="text" rows="8" placeholder="Schreib hier deine Anzeige, Produktbeschreibung oder Frage an deinen Upseller-Profi hinein."></textarea>
    <!-- Versteckter Gesprächsverlauf (wird bei jedem Request mitgeschickt) -->
    <input type="hidden" name="history" value="{history}" />
    <br/>
    <button type="submit">Mit KI optimieren</button>
  </form>

  <div class="hint">
    Die KI arbeitet mit deinem internen UPSELLER V2.0 Masterprompt (Level-System, Marktanalyse, Verhandlungslogik).
    Der Prompt liegt sicher auf dem Server und ist nicht im Code sichtbar. Für Folgefragen einfach wieder etwas
    unter die letzte Antwort schreiben (z. B. „Warum so teuer?“ oder „Mach mir eine weichere Verhandlungsversion“)
    – der Verlauf bleibt erhalten, solange die Seite offen ist.
  </div>

  {result}
</body>
</html>
"""


def _escape_html_attr(value: str) -> str:
    """
    Kleiner Helper, damit das JSON im hidden-Input nicht das HTML kaputt macht.
    """
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


@app.get("/", response_class=HTMLResponse)
async def form_get():
    # Leerer Start: noch kein Verlauf, kein Ergebnis
    empty_history_json = "[]"
    return HTML_PAGE.format(
        history=_escape_html_attr(empty_history_json),
        result=""
    )


@app.post("/", response_class=HTMLResponse)
async def form_post(
    text: str = Form(...),
    history: str = Form("[]"),
):
    """
    - Nimmt den aktuellen Text aus der Textarea
    - Liest den bisherigen Verlauf (history) ein
    - Ruft OpenAI mit Systemprompt + kompletter History + neuer User-Nachricht auf
    - Hängt die neue Assistant-Antwort wieder an die History an
    - Gibt alles zurück (History bleibt unsichtbar im Hidden-Feld)
    """

    # 1. Masterprompt sicher aus Environment lesen
    masterprompt = os.getenv(
        "UPSELLER_PROMPT",
        "Du bist ein Verkaufsprofi. Wenn der UPSELLER_PROMPT nicht gesetzt ist, arbeite einfach so gut du kannst."
    )

    # 2. Verlauf aus hidden-field parsen
    try:
        conversation = json.loads(history)
        if not isinstance(conversation, list):
            conversation = []
    except Exception:
        conversation = []

    # 3. Neue User-Nachricht an den Verlauf anhängen (für OpenAI)
    conversation.append({"role": "user", "content": text})

    # 4. Messages für OpenAI bauen
    messages = [{"role": "system", "content": masterprompt}] + conversation

    # 5. OpenAI anfragen
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",  # günstig & gut – bei Bedarf anpassen
            messages=messages,
            temperature=0.7,
        )

        answer = response.choices[0].message.content.strip()
        # 6. Antwort in den Verlauf eintragen
        conversation.append({"role": "assistant", "content": answer})

        # HTML-Ausgabe: nur die letzte Antwort anzeigen
        result_html = f"""
        <div class="box">
          <b>Upseller-PRO Antwort:</b><br><br>
          {answer.replace('\n', '<br>')}
        </div>
        """

    except Exception as e:
        # Fehler schön ausgeben
        result_html = f"""
        <div class="box error">
          Fehler bei der KI-Anfrage: {str(e)}
        </div>
        """

    # 7. Verlauf wieder als JSON ins versteckte Feld zurückschreiben
    history_json = json.dumps(conversation, ensure_ascii=False)
    return HTML_PAGE.format(
        history=_escape_html_attr(history_json),
        result=result_html
    )
