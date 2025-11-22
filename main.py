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
    Füge deine Antworten nacheinander ein. Upseller ULTRA merkt sich den Verlauf (solange die Seite offen ist).
  </p>

  <form method="post">
    <textarea name="text" rows="4" placeholder="Antworte hier z. B.: &quot;Massivholzfenster 149 x 149 cm&quot;."></textarea>
    <!-- Versteckter Gesprächsverlauf (wird bei jedem Request mitgeschickt) -->
    <input type="hidden" name="history" value="{history}" />
    <br/>
    <button type="submit">Mit KI optimieren</button>
  </form>

  <div class="hint">
    Dein interner UPSELLER V5.0 ULTRA Prompt (Level-System, Marktanalyse, Verhandlungslogik, KI-Check) liegt sicher
    auf dem Server und ist nicht im Code sichtbar. Für Folgefragen oder die nächsten Level (Jahrgang, Zustand,
    Ausstattung, Verhandlung usw.) einfach wieder etwas in das Feld schreiben und auf den Button klicken.
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
    """
    ERSTER AUFRUF:
    - Wir starten direkt mit LEVEL 1 als Assistant-Nachricht.
    - Die Frage steht sofort unten im grauen Kasten.
    - Der Verlauf (mit dieser ersten Assistant-Nachricht) liegt schon im Hidden-Feld.
    """
    conversation = [
        {
            "role": "assistant",
            "content": (
                "⭐ LEVEL 1 – PRODUKTNAME\n\n"
                "Welches Produkt möchtest du verkaufen? Schreib bitte kurz den Produktnamen "
                "(z. B. „Massivholzfenster 149 x 149 cm“, „iPhone 14 Pro 256 GB“, "
                "„Bosch Akkuschrauber-Set“, „Dienstleistung: Gartenpflege in Brandenburg“)."
            ),
        }
    ]

    history_json = json.dumps(conversation, ensure_ascii=False)
    first_answer = conversation[0]["content"].replace("\n", "<br>")

    result_html = f"""
    <div class="box">
      <b>Upseller-ULTRA Antwort:</b><br><br>
      {first_answer}
    </div>
    """

    return HTML_PAGE.format(
        history=_escape_html_attr(history_json),
        result=result_html,
    )


@app.post("/", response_class=HTMLResponse)
async def form_post(
    text: str = Form(...),
    history: str = Form("[]"),
):
    """
    - Nimmt den aktuellen Text aus der Textarea (deine Antwort / Frage)
    - Liest den bisherigen Verlauf (history) ein
    - Ruft OpenAI mit:
        • System: dein originaler UPSELLER-Prompt (aus Environment)
        • System 2: Zusatz-Anweisung für KI-CHECK-Block am Ende
        • kompletter Conversation-Verlauf
    - Hängt die neue Assistant-Antwort wieder an die History an
    - Gibt alles zurück (History bleibt unsichtbar im Hidden-Feld)
    """

    # 1. Masterprompt sicher aus Environment lesen (dein Original)
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

    # 3. Neue User-Nachricht an den Verlauf anhängen
    conversation.append({"role": "user", "content": text})

    # 4. Zusatz-System-Instruktion: KI-CHECK-BLOCK nur am Ende nach Level 9
    extra_system_instruction = (
        "WICHTIG: Du arbeitest mit dem originalen UPSELLER V5.0 ULTRA Prompt (Level-System). "
        "Wenn du eine vollständige Marktanalyse inkl. Preisspanne, Plattformen, Psychologie und Premium-Anzeigentext "
        "(also Level 9) geliefert hast, füge GANZ AM ENDE deiner Antwort einen zusätzlichen Block an, der als "
        "KI-CHECK-BLOCK für andere KIs (Claude, Grok, GPT, Llama etc.) dient. Nutze dafür dein vorgegebenes Schema "
        "für 'KI-Check (für andere KIs)' und 'PREISEMPFEHLUNG (Kurzform)' und 'VERGLEICHSBASIS'. "
        "Fülle die Felder so gut wie möglich aus, basierend auf den bisherigen Informationen. "
        "Formatiere diesen Block so, dass der Nutzer ihn mit einem Klick kopieren kann, z. B. mit einer klaren Überschrift:\n"
        "\"--- KI-CHECK-BLOCK (für andere KIs – Copy & Paste) ---\".\n"
        "Schreibe darunter in 1–2 Sätzen kurz, dass dieser Block dazu dient, deine Einschätzung in anderen KIs zu prüfen. "
        "Füge diesen Block NUR ANS ENDE deiner Antwort an. Nach diesem Block kommt nichts mehr."
    )

    # 5. Messages für OpenAI bauen
    messages = [
        {"role": "system", "content": masterprompt},
        {"role": "system", "content": extra_system_instruction},
        *conversation,
    ]

    # 6. OpenAI anfragen
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",  # günstig & gut – bei Bedarf anpassbar
            messages=messages,
            temperature=0.7,
        )

        answer = response.choices[0].message.content.strip()
        # Antwort in den Verlauf eintragen
        conversation.append({"role": "assistant", "content": answer})

        # HTML-Ausgabe: komplette Antwort (inkl. KI-CHECK-BLOCK) anzeigen
        result_html = f"""
        <div class="box">
          <b>Upseller-ULTRA Antwort:</b><br><br>
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
