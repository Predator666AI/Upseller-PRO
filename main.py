import os
import textwrap
from typing import Dict, Callable

import requests
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse


app = FastAPI()

# --------------------------------------------------------------------
# ENV-VARIABLEN
# --------------------------------------------------------------------
UPSELLER_PROMPT = os.getenv("UPSELLER_PROMPT", "Upseller Prompt fehlt – bitte ENV setzen.")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or os.getenv("OPENAI_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")  # kannst du in Railway anpassen

# optionale weitere KIs – wenn kein Key gesetzt ist, werden sie einfach übersprungen
GROK_API_KEY = os.getenv("GROK_API_KEY")         # z.B. Grok / xAI
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # z.B. Claude
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")     # z.B. Google Gemini


# --------------------------------------------------------------------
# HTML-Template mit Copy-Buttons
# --------------------------------------------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Upseller PRO – Test Dashboard</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      max-width: 900px;
      margin: 40px auto;
      padding: 0 10px;
    }}
    h1 {{
      font-size: 26px;
      margin-bottom: 5px;
    }}
    textarea {{
      width: 100%;
      min-height: 180px;
      padding: 10px;
      font-size: 15px;
      box-sizing: border-box;
    }}
    input[type="file"] {{
      margin-top: 4px;
    }}
    button {{
      padding: 10px 20px;
      font-size: 15px;
      cursor: pointer;
      border-radius: 4px;
      border: 1px solid #ccc;
      background: #f2f2f2;
    }}
    .primary-btn {{
      background: #111827;
      color: #ffffff;
      border-color: #111827;
    }}
    .box {{
      margin-top: 25px;
      padding: 15px;
      background: #f7f7f7;
      border-radius: 8px;
      border: 1px solid #e0e0e0;
      white-space: pre-wrap;
    }}
    .hint {{
      font-size: 12px;
      color: #555;
      margin-top: 8px;
    }}
    .section-title {{
      margin-top: 20px;
      margin-bottom: 5px;
      font-weight: bold;
    }}
    .copy-btn {{
      float: right;
      font-size: 12px;
      padding: 5px 8px;
      margin-left: 8px;
    }}
    pre {{
      white-space: pre-wrap;
      word-wrap: break-word;
      font-family: inherit;
      margin: 0;
    }}
    .provider-list {{
      font-size: 12px;
      color: #555;
      margin-top: 6px;
    }}
    .error {{
      color: #b91c1c;
      font-weight: bold;
    }}
  </style>
  <script>
    function copyText(id) {{
      const el = document.getElementById(id);
      if (!el) return;
      const text = el.innerText || el.textContent || "";
      navigator.clipboard.writeText(text).then(function() {{
        alert("In Zwischenablage kopiert.");
      }}, function(err) {{
        alert("Kopieren nicht möglich: " + err);
      }});
    }}
  </script>
</head>
<body>
  <h1>Upseller PRO – Test Dashboard</h1>
  <p>Füge deine Antworten nacheinander ein. Upseller ULTRA merkt sich den Verlauf (solange die Seite offen ist).</p>

  <form method="post" enctype="multipart/form-data">
    <label for="text"><b>LEVEL 1 – Welches Produkt möchtest du verkaufen?</b></label><br>
    <textarea id="text" name="text" placeholder='Z. B. "Massivholzfenster 149 x 149 cm, 3-fach Verglasung, Baujahr 2021"'></textarea>

    <div style="margin-top:10px;">
      <label for="image">Bild (optional):</label>
      <input id="image" name="image" type="file" accept="image/*">
    </div>

    <div style="margin-top:15px;">
      <button type="submit" class="primary-btn">Mit KI optimieren</button>
    </div>

    <p class="hint">
      Die KI arbeitet mit deinem internen UPSELLER V5.0 ULTRA Masterprompt (Level-System, Marktanalyse, Verhandlungslogik).
      Der Prompt liegt sicher auf dem Server und ist nicht im Code sichtbar.
    </p>
  </form>

  <div class="box">
    {result}
  </div>
</body>
</html>
"""


# --------------------------------------------------------------------
# Hilfsfunktionen: einzelne KIs aufrufen
# --------------------------------------------------------------------

def call_openai(system_prompt: str, user_text: str) -> str:
    """Standard-Aufruf an OpenAI (wird auch für die Meta-Auswertung genutzt)."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY nicht gesetzt.")

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


def call_grok(system_prompt: str, user_text: str) -> str:
    """Beispiel für Grok / xAI – wird nur aufgerufen, wenn GROK_API_KEY gesetzt ist."""
    if not GROK_API_KEY:
        raise RuntimeError("GROK_API_KEY nicht gesetzt.")
    # ACHTUNG: Endpoint / Modellnamen ggf. mit aktueller Grok-Doku abgleichen
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "grok-beta",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    }
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_claude(system_prompt: str, user_text: str) -> str:
    """Beispiel für Anthropic Claude – wird nur genutzt, wenn ANTHROPIC_API_KEY gesetzt ist."""
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY nicht gesetzt.")
    # Vereinfachtes Beispiel – bitte ggf. mit offizieller Anthropic-Doku abgleichen
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1000,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_text},
        ],
    }
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    msg = resp.json()["content"][0]["text"]
    return msg


def call_gemini(system_prompt: str, user_text: str) -> str:
    """Beispiel für Google Gemini – wird nur genutzt, wenn GEMINI_API_KEY gesetzt ist."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY nicht gesetzt.")
    # stark vereinfacht; bitte ggf. mit aktueller Gemini-Doku anpassen
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    full_prompt = system_prompt + "\n\nNutzer:\n" + user_text
    data = {
        "contents": [{"parts": [{"text": full_prompt}]}]
    }
    resp = requests.post(url, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


# --------------------------------------------------------------------
# Ensemble-Logik
# --------------------------------------------------------------------

def get_available_providers() -> Dict[str, Callable[[str, str], str]]:
    """
    Baut automatisch eine Liste aller verfügbaren KIs,
    anhand der gesetzten ENV-Variablen.
    """
    providers: Dict[str, Callable[[str, str], str]] = {}

    # OpenAI wird IMMER als Provider genutzt – ist auch unsere Meta-KI
    providers["openai"] = call_openai

    if GROK_API_KEY:
        providers["grok"] = call_grok
    if ANTHROPIC_API_KEY:
        providers["claude"] = call_claude
    if GEMINI_API_KEY:
        providers["gemini"] = call_gemini

    return providers


def collect_opinions(user_context: str) -> Dict[str, str]:
    """
    Ruft alle verfügbaren Provider auf und sammelt deren Roh-Antworten.
    """
    providers = get_available_providers()
    opinions: Dict[str, str] = {}

    for name, func in providers.items():
        try:
            content = func(UPSELLER_PROMPT, user_context)
            opinions[name] = content
        except Exception as e:
            # Fehler nicht tödlich – wird als Hinweis mit ausgegeben
            opinions[name] = f"[Fehler bei {name}: {e}]"

    return opinions


def build_meta_analysis(user_context: str, opinions: Dict[str, str]) -> Dict[str, str]:
    """
    Nutzt OpenAI (ChatGPT) als Meta-KI, um alle Einzel-Gutachten zu einer
    gemeinsamen Level-9-Auswertung + KI-Vergleichs-Prompt zu verschmelzen.
    """
    providers_used = ", ".join(opinions.keys())

    meta_system = (
        "Du bist UPSELLER ULTRA – Meta-Analyst.\n"
        "Du bekommst mehrere KI-Gutachten zum gleichen Verkaufsobjekt "
        "(z.B. OpenAI, Grok, Claude, Gemini). "
        "Du sollst daraus EINE konsistente Auswertung im UPSELLER-V5.0-Format bauen:\n"
        "- Level 9: Marktanalyse, Preisbereich, Wertfaktoren, Plattformen, Timing,\n"
        "  psychologische Preisstrategie, Premium-Anzeigentext, Profi-Zusammenfassung.\n"
        "- Level 10: KI-Vergleichs-Prompt zum Kopieren, exakt im Block-Format, "
        "damit andere KIs das Angebot nachprüfen können.\n\n"
        "WICHTIG: Antworte strukturiert mit folgenden Markern:\n"
        "---LEVEL9_START---\n"
        "(komplette Level-9-Auswertung als Textblock)\n"
        "---LEVEL9_END---\n"
        "---KICHECK_START---\n"
        "(kompletter KI-Vergleichs-Prompt-Block im vorgegebenen Format)\n"
        "---KICHECK_END---\n"
    )

    opinions_text = ""
    for name, content in opinions.items():
        opinions_text += f"\n\n### Gutachten {name.upper()}:\n{content}\n"

    meta_user = textwrap.dedent(f"""
    NUTZER-KONTEXT (Antworten aus Level 1–8):

    {user_context}

    GENUTZTE KIs: {providers_used}

    MEHRERE KI-GUTACHTEN:

    {opinions_text}

    AUFGABE:
    1. Ziehe aus den Gutachten eine einzige, saubere Level-9-Auswertung gemäß
       UPSELLER V5.0 ULTRA (Preisbereich, Wertfaktoren, Plattformen, Timing,
       psychologische Preisstrategie, Premium-Anzeigentext, Profi-Zusammenfassung).
    2. Erstelle am Ende zusätzlich den Level-10-KI-Vergleichs-Prompt exakt im Block-Format:

       KI-Check (für andere KIs):

       PRODUKT: …
       JAHR: …
       ZUSTAND: …
       ABMESSUNGEN: …
       HERSTELLER: …
       VERGLASUNG: …
       SCHEIBEN: …
       U-WERT / TECHNIK: …
       MATERIAL / PROFIL: …
       FUNKTIONEN: …
       SICHERHEIT: …
       GEWICHT: …
       MÄNGEL: …
       STÜCKZAHL: …
       MARKTREGION: …
       MARKTLAGE: …
       REFERENZBILD: …

       PREISEMPFEHLUNG (Kurzform):
       Maximalpreis: … €
       Optimaler realistischer Preis: … €
       Geduld-Spanne: … €
       Schnellverkauf: … €

       VERGLEICHSBASIS:
       • technische Daten
       • regionale Nachfrage
       • Marktpreise (Simulated Scraping)
       • Material & Zustand
       • Ausstattung
       • Konkurrenzangebote
       • Preisentwicklung

    3. Nutze strikt die Marker ---LEVEL9_START--- / ---LEVEL9_END--- und
       ---KICHECK_START--- / ---KICHECK_END---, damit ich die Blöcke sauber trennen kann.
    """)

    meta_answer = call_openai(meta_system, meta_user)

    # Parsing der Blöcke
    try:
        part_after_l9_start = meta_answer.split("---LEVEL9_START---", 1)[1]
        level9_text, rest = part_after_l9_start.split("---LEVEL9_END---", 1)
        part_after_kicheck_start = rest.split("---KICHECK_START---", 1)[1]
        kicheck_text = part_after_kicheck_start.split("---KICHECK_END---", 1)[0]
    except Exception:
        # Fallback: wenn Marker fehlen, alles als Level9, kein KI-Block
        level9_text = meta_answer
        kicheck_text = "KI-Vergleichs-Prompt konnte nicht automatisch extrahiert werden."

    return {
        "providers_used": providers_used,
        "level9": level9_text.strip(),
        "kicheck": kicheck_text.strip(),
    }


# --------------------------------------------------------------------
# FastAPI Routen
# --------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def form_get():
    return HTML_PAGE.format(result="Gib dein Produkt oben ein und starte Upseller ULTRA.")


@app.post("/", response_class=HTMLResponse)
async def form_post(
    text: str = Form(...),
    image: UploadFile | None = File(None),
):
    user_context = text.strip()

    if not user_context:
        result_html = "<span class='error'>Bitte gib zuerst eine Beschreibung deines Produkts ein.</span>"
        return HTML_PAGE.format(result=result_html)

    try:
        # 1. Einzel-Gutachten einsammeln
        opinions = collect_opinions(user_context)

        # 2. Meta-Analyse mit OpenAI (ChatGPT) bauen
        meta = build_meta_analysis(user_context, opinions)

        providers_used = meta["providers_used"] or "nur OpenAI"
        level9_block = meta["level9"]
        kicheck_block = meta["kicheck"]

        # 3. Ergebnis-HTML mit Copy-Buttons
        result_html = f"""
        <div>
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
        </div>
        """

    except Exception as e:
        result_html = f"<span class='error'>Fehler bei der KI-Anfrage: {e}</span>"

    return HTML_PAGE.format(result=result_html)
