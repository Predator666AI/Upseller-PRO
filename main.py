from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

HTML_PAGE = """
<html>
<head>
    <title>Upseller PRO</title>
    <style>
        body { font-family: Arial; max-width: 650px; margin: 40px auto; }
        textarea { width:100%; padding: 10px; font-size: 15px; }
        button { padding: 10px 20px; font-size: 16px; }
        .box { margin-top: 20px; padding: 15px; background: #f2f2f2; border-radius: 8px; }
    </style>
</head>
<body>
    <h1>Upseller PRO – Test Dashboard</h1>
    <p>Gib einen Text ein. Später kommt hier die KI-Logik rein.</p>
    <form method="post">
        <textarea name="text" rows="6"></textarea><br><br/>
        <button type="submit">Absenden</button>
    </form>

    {result}

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def form_get():
    return HTML_PAGE.format(result="")

@app.post("/", response_class=HTMLResponse)
async def form_post(text: str = Form(...)):
    antwort = f"<div class='box'><b>Upseller PRO hat deinen Text empfangen:</b><br>{text[:200]}...</div>"
    return HTML_PAGE.format(result=antwort)
