import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from openai import OpenAI

# OpenAI-Client, nutzt automatisch die Umgebungsvariable OPENAI_API_KEY
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Geheimer Upseller-Prompt – wird sicher aus Railway-Variable geladen
UPSELLER_PROMPT = os.getenv("UPSELLER_PROMPT", "").strip()

app = FastAPI()

HTML_PAGE = """
<html>
<head>
    <title>Upseller PRO</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 750px; margin: 40px auto; }}
        textarea {{ width:100%; padding: 10px; font-size: 15px; }}
        button {{ padding: 10px 20px; font-size: 16px; cursor: pointer; }}
        .box {{ margin-top: 20px; padding: 15px; background: #f2f2f2; border-radius: 8px; }}
        .error {{ margin-top: 20px; padding: 15px; background: #ffdddd; border-radius: 8px; color: #900; }}
        .hint {{ margin-top: 10px; font-size: 13px; color: #777; }}
    </style>
</head>
<body>
    <h1>Upseller PRO – Test Dashboard</h1>
    <p>Füge unten deine Anzeige / Beschreibung ein (z. B. eBay, Kleinanzeigen, Vinted, Dienstleistung etc.).</p>
    <form method="post">
        <textarea name="text" rows="8"></textarea><br/><br/>
        <button type="submit">Mit KI optimieren</button>
    </form>

    <div class="hint">
        Die KI arbeitet mit deinem internen UPSELLER V2.0 Masterprompt (Level-System, Marktanalyse, Verhandlungslogik).
        Der Prompt liegt sicher auf dem Server und ist nicht im Code sichtbar.
    </div>

    {result}

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def form_get():
    # Startseite ohne Ergebnis
    return HTML_PAGE.format(result="")

@app.post("/", response_class=HTMLResponse)
async def form_post(text: str = Form(...)):
    # Falls dein Prompt nicht gesetzt ist, klare Fehlermeldung
    if not UPSELLER_PROMPT:
        error_html = (
            "<div class='error'><b>Fehler:</b> Der UPSELLER_PROMPT ist nicht gesetzt. "
            "Bitte in Railway unter <code>UPSELLER_PROMPT</code> deinen Masterprompt hinterlegen.</div>"
        )
        return HTML_PAGE.format(result=error_html)

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",  # günstig & schnell; kannst du später anpassen
            messages=[
                {
                    "role": "system",
                    "content": UPSELLER_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        "Der Nutzer hat folgenden Originaltext gesendet, den du nach deinem Level-System "
                        "und deinen Regeln von UPSELLER V2.0 optimieren sollst. "
                        "Arbeite ganz normal wie im Masterprompt definiert. "
                        "Gib NUR den optimierten Text zurück, in einem Block, ohne Erklärungen.\n\n"
                        f"{text}"
                    ),
                },
            ],
            max_tokens=800,
            temperature=0.7,
        )

        answer = completion.choices[0].message.content.strip()
    except Exception as e:
        # API-/Key-/Quota-Fehler freundlich anzeigen
        error_html = (
            "<div class='error'><b>KI-Fehler:</b><br>"
            f"{str(e)}</div>"
        )
        return HTML_PAGE.format(result=error_html)

    # Zeilenumbrüche in HTML umwandeln
    safe_answer = answer.replace("\n", "<br>")
    html_answer = f"<div class='box'><b>Upseller-PRO Antwort:</b><br>{safe_answer}</div>"
    return HTML_PAGE.format(result=html_answer)
