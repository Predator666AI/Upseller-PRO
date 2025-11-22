from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import HTMLResponse
import requests
import base64
import os

app = FastAPI()

HTML_PAGE = """
<html>
<head>
<title>Upseller PRO – Test Dashboard</title>
<style>
 body { font-family: Arial; max-width: 780px; margin: 40px auto; }
 textarea { width:100%; padding: 10px; font-size: 15px; }
 button { padding: 10px 20px; font-size: 16px; }
 .box { margin-top: 20px; padding: 15px; background: #f2f2f2; border-radius: 8px; }
</style>
</head>
<body>

<h1>Upseller PRO – Test Dashboard</h1>

<p>Füge deine Antworten nacheinander ein. Upseller ULTRA merkt sich den Verlauf.</p>

<form method="post" enctype="multipart/form-data">
<textarea name="text" rows="5" placeholder='Antwort hier z. B.: "Massivholzfenster 149 x 149 cm".'></textarea><br><br>

Bild (optional): <input type="file" name="image"><br><br>

<button type="submit">Mit KI optimieren</button>
</form>

<p style="font-size:12px; color:#555;">
Du kannst Text + optional ein Bild senden. Upseller V5.0 ULTRA analysiert automatisch Zustand, Material, Verglasung usw.
</p>

{result}

</body>
</html>
"""

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
UPSELLER_PROMPT = os.getenv("UPSELLER_PROMPT", "Upseller Prompt missing!")

API_URL = "https://api.openai.com/v1/responses"


def encode_image(file):
    return base64.b64encode(file).decode("utf-8")


@app.get("/", response_class=HTMLResponse)
async def form_get():
    # Stellt sicher, dass Level 1 automatisch startet
    first_msg = "<div class='box'><b>LEVEL 1 – Welches Produkt möchtest du verkaufen?</b></div>"
    return HTML_PAGE.format(result=first_msg)


@app.post("/", response_class=HTMLResponse)
async def form_post(text: str = Form(""), image: UploadFile = File(None)):

    content_block = []

    # ➤ TEXT EINBAUEN
    if text.strip() != "":
        content_block.append({"type": "text", "text": text})

    # ➤ BILD EINBAUEN
    if image:
        img_bytes = await image.read()
        img_b64 = encode_image(img_bytes)
        content_block.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img_b64}"
            }
        })

    # ➤ API REQUEST
    payload = {
        "model": "gpt-4o-mini",
        "input": [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": UPSELLER_PROMPT}
                ]
            },
            {
                "role": "user",
                "content": content_block
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(API_URL, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()

        answer = data["output_text"]
    except Exception as e:
        answer = f"<b>Fehler bei der KI-Anfrage:</b><br>{str(e)}"

    result_box = f"<div class='box'>{answer}</div>"
    return HTML_PAGE.format(result=result_box)
