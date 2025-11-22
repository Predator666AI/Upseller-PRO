from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from openai import OpenAI
import os

app = FastAPI()
client = OpenAI()

# Masterprompt aus Environment (UPSELLER_PROMPT), mit Fallback
UPSELLER_PROMPT = os.getenv(
    "UPSELLER_PROMPT",
    "Du bist UPSELLER ULTRA. Optimiere Verkaufsanzeigen Schritt für Schritt und gib am Ende einen Premium-Anzeigentext und einen KI-Check/Preisblatt-Block aus."
)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8" />
    <title>Upseller PRO – Test Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
            line-height: 1.5;
        }}
        h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        p {{
            font-size: 14px;
            color: #333;
        }}
        textarea {{
            width: 100%;
            padding: 12px;
            font-size: 14px;
            box-sizing: border-box;
            resize: vertical;
        }}
        button {{
            padding: 10px 18px;
            font-size: 14px;
            margin-top: 10px;
            cursor: pointer;
            border-radius: 4px;
            border: 1px solid #ccc;
            background: #f2f2f2;
        }}
        button:hover {{
            background: #e5e5e5;
        }}
        .hint {{
            font-size: 12px;
            color: #666;
            margin-top: 6px;
        }}
        .box {{
            margin-top: 24px;
            padding: 16px;
            background: #f7f7f7;
            border-radius: 8px;
            border: 1px solid #ddd;
        }}
        .box h2 {{
            margin-top: 0;
            font-size: 18px;
        }}
        .result-buttons {{
            margin-top: 10px;
        }}
        .result-buttons button {{
            margin-right: 8px;
            margin-bottom: 6px;
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <h1>Upseller PRO – Test Dashboard</h1>
    <p>
        Füge unten deine Antworten ein. Upseller ULTRA merkt sich den Verlauf,
        solange die Seite offen ist, und arbeitet mit deinem internen Masterprompt
        (Level-System, Marktanalyse, Verhandlung usw.).
    </p>

    <form method="post">
        <textarea name="user_input" rows="8" placeholder="LEVEL 1 – Welches Produkt möchtest du verkaufen?&#10;Antworte z. B.: &quot;Massivholzfenster 149 x 149 cm&quot;."></textarea>
        <br />
        <button type="submit">Mit KI optimieren</button>
        <p class="hint">
            Die KI arbeitet mit deinem internen UPSELLER V5.0 ULTRA Masterprompt.
            Der Prompt liegt sicher auf dem Server (Environment Variable UPSELLER_PROMPT)
            und ist nicht im Code sichtbar.
        </p>
    </form>

    <div class="box">
        <h2>Upseller-PRO Antwort</h2>
        <div class="result-buttons">
            <button type="button" onclick="copyAll()">Alles kopieren</button>
            <button type="button" onclick="copySection('Premium-Anzeigentext')">Anzeigentext kopieren</button>
            <button type="button" onclick="copySection('KI-Check (für andere KIs)')">KI-Check + Preisblatt kopieren</button>
        </div>
        <pre id="result-box">{result}</pre>
    </div>

    <script>
        function copyToClipboard(text) {{
            if (!text) {{
                alert("Es gibt aktuell nichts zu kopieren.");
                return;
            }}
            navigator.clipboard.writeText(text).then(function() {{
                alert("Text wurde in die Zwischenablage kopiert.");
            }}, function(err) {{
                console.error("Fehler beim Kopieren:", err);
                alert("Kopieren nicht möglich.");
            }});
        }}

        function copyAll() {{
            var full = document.getElementById("result-box").innerText;
            copyToClipboard(full);
        }}

        // Sucht im Ergebnis nach einer Überschrift wie
        // "Premium-Anzeigentext" oder "KI-Check (für andere KIs)"
        // und kopiert alles ab dieser Stelle bis zur nächsten Überschrift
        // oder bis zum Ende.
        function copySection(marker) {{
            var text = document.getElementById("result-box").innerText;
            if (!text) {{
                alert("Noch keine Antwort vorhanden.");
                return;
            }}

            var idx = text.indexOf(marker);
            if (idx === -1) {{
                alert('Der Abschnitt \"' + marker + '\" wurde im Ergebnis nicht gefunden. Stelle sicher, dass die KI diesen Block ausgegeben hat.');
                return;
            }}

            var sub = text.slice(idx);

            // Grob versuchen, bis zur nächsten großen Überschrift zu gehen
            var nextMarkers = [
                "Premium-Anzeigentext",
                "KI-Check (für andere KIs)",
                "⭐ LEVEL",
                "LEVEL 10",
                "Profi-Zusammenfassung"
            ];
            var cutIndex = sub.length;

            for (var i = 0; i < nextMarkers.length; i++) {{
                if (nextMarkers[i] === marker) continue;
                var pos = sub.indexOf(nextMarkers[i]);
                if (pos !== -1 && pos < cutIndex) {{
                    cutIndex = pos;
                }}
            }}

            var sectionText = sub.slice(0, cutIndex).trim();
            copyToClipboard(sectionText);
        }}
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def form_get():
    # Leere Startseite ohne Ergebnis
    return HTML_PAGE.format(result="")

@app.post("/", response_class=HTMLResponse)
async def form_post(user_input: str = Form(...)):
    # Hier die eigentliche KI-Logik
    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {{
                    "role": "system",
                    "content": [
                        {{"type": "text", "text": UPSELLER_PROMPT}}
                    ],
                }},
                {{
                    "role": "user",
                    "content": [
                        {{"type": "text", "text": user_input}}
                    ],
                }},
            ],
        )

        # Text aus der Responses-API holen
        ai_text = response.output[0].content[0].text

    except Exception as e:
        ai_text = f"Fehler bei der KI-Anfrage: {{e}}"

    # Geschweifte Klammern escapen, damit .format() nicht crasht
    safe_result = ai_text.replace("{{", "{{{{").replace("}}", "}}}}")
    return HTML_PAGE.format(result=safe_result)
