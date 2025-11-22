from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from openai import OpenAI

app = FastAPI()
client = OpenAI()  # benutzt automatisch OPENAI_API_KEY aus den Umgebungsvariablen

HTML_PAGE = """
<html>
<head>
    <title>Upseller PRO</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 750px; margin: 40px auto; }}
        textarea {{ width:100%; padding: 10px; font-size: 15px; }}
        button {{ padding: 10px 20px; font-size: 16px; cursor: pointer; }}
        .box {{ margin-top: 20px; padding: 15px; background: #f2f2f2; border-radius: 8px; }}
        .hint {{ margin-top: 10px; font-size: 13px; color: #777; }}
    </style>
</head>
<body>
    <h1>Upseller PRO – Test Dashboard</h1>
    <p>Gib einen Text ein (z.B. deine eBay-Anzeige, Produktbeschreibung, Nachricht an Kunden).</p>
    <form method="post">
        <textarea name="text" rows="8"></textarea><br/><br/>
        <button type="submit">Mit KI optimieren</button>
    </form>

    <div class="hint">
        Die KI arbeitet wie dein geheimer Verkaufsprofi: Sie macht Texte knackiger, klarer und verkaufsstärker –
        ohne deinen Stil komplett zu zerstören.
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
    """
    Nimmt den eingegebenen Text, schickt ihn an OpenAI
    und zeigt die optimierte Upseller-Version an.
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",   # günstig & schnell; später leicht änderbar
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du bist UPSELLER PRO, ein Profi für Verkaufspsychologie und Konversion. "
                        "Deine Aufgabe: Optimiere Texte für Kleinanzeigen, eBay, Vinted, Immobilien, "
                        "Dienstleistungen usw. "
                        "Ziele: mehr Vertrauen, höherer Preis, klarer Nutzen für den Kunden. "
                        "Sprache: deutsch, locker-professionell. "
                        "Maximiere den wahrgenommenen Wert, aber bleib ehrlich – keine Lügen."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Hier ist der Originaltext, den du optimieren sollst. "
                        "Gib mir NUR den optimierten Text zurück, keine Erklärungen.\n\n"
                        f"{text}"
                    ),
                },
            ],
            max_tokens=450,
            temperature=0.7,
        )

        answer = completion.choices[0].message.content.strip()
    except Exception as e:
        # Falls API-Fehler, zeige Fehlermeldung im Browser
        answer = f"Fehler bei der KI-Anfrage: {e}"

    safe_answer = answer.replace("\n", "<br>")
    html_answer = f"<div class='box'><b>Upseller-PRO Antwort:</b><br>{safe_answer}</div>"
    return HTML_PAGE.format(result=html_answer)
