import os
import textwrap
import base64
import asyncio
from typing import Dict, Callable

import requests
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse

# ------------------------------------------------------------
# ENV-VARIABLEN
# ------------------------------------------------------------

UPSELLER_PROMPT = os.getenv("UPSELLER_PROMPT", "Upseller Prompt fehlt – bitte ENV setzen.")

OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENAI_APIKEY")
    or os.getenv("OPENAI_KEY")
)

# Standard-Modell – kannst du in Railway anpassen
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# Optionale weitere KIs (werden nur genutzt, wenn Keys gesetzt sind)
GROK_API_KEY = os.getenv("GROK_API_KEY")          # z. B. xAI / Grok
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # z. B. Claude
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")      # z. B. Google Gemini

# Logo (hier kannst du später deine eigene URL hinterlegen)
LOGO_URL = os.getenv(
    "UPSELLER_LOGO_URL",
    "https://i.imgur.com/xxxxxxxx.png"  # Platzhalter – bei Bedarf ersetzen
)

# ------------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------------

app = FastAPI()

# ------------------------------------------------------------
# HTML-Template (Dark-Look + Copy-Buttons)
# ------------------------------------------------------------

HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Upseller PRO – Test Dashboard</title>
  <style>
    :root {{
      color-scheme: dark;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top, #1f2937 0, #020617 55%);
      color: #e5e7eb;
    }}
    .page {{
      min-height: 100vh;
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding: 32px 12px;
    }}
    .card {{
      width: 100%;
      max-width: 960px;
      background: rgba(15, 23, 42, 0.92);
      border-radius: 18px;
      border: 1px solid rgba(148, 163, 184, 0.3);
      box-shadow: 0 20px 45px rgba(0, 0, 0, 0.65);
      padding: 22px 22px 26px;
    }}
    .header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
    }}
    .header-left {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .logo {{
      width: 40px;
      height: 40px;
      border-radius: 50%;
      border: 1px solid rgba(252, 211, 77, 0.7);
      background: radial-gradient(circle at 30% 30%, #facc15 0, #92400e 65%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      color: #111827;
      font-size: 18px;
      box-shadow: 0 0 18px rgba(250, 204, 21, 0.45);
    }}
    .title-main {{
      font-size: 22px;
      font-weight: 650;
    }}
    .title-sub {{
      font-size: 12px;
      color: #9ca3af;
    }}
    .badge {{
      font-size: 11px;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid rgba(252, 211, 77, 0.5);
      background: linear-gradient(to right, rgba(253, 224, 71, 0.12), rgba(249, 115, 22, 0.18));
      color: #facc15;
      white-space: nowrap;
    }}
    form {{
      margin-top: 10px;
      margin-bottom: 12px;
    }}
    label {{
      font-size: 13px;
      font-weight: 500;
      display: block;
      margin-bottom: 4px;
    }}
    textarea {{
      width: 100%;
      min-height: 120px;
      padding: 10px 12px;
      font-size: 14px;
      color: #e5e7eb;
      background: rgba(15, 23, 42, 0.9);
      border-radius: 10px;
      border: 1px solid rgba(55, 65, 81, 0.9);
      resize: vertical;
      outline: none;
    }}
    textarea::placeholder {{
      color: #6b7280;
    }}
    textarea:focus {{
      border-color: #fbbf24;
      box-shadow: 0 0 0 1px rgba(251, 191, 36, 0.45);
    }}
    input[type="file"] {{
      font-size: 12px;
      margin-top: 3px;
    }}
    .row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-top: 10px;
    }}
    .hint {{
      font-size: 11px;
      color: #9ca3af;
      margin-top: 6px;
    }}
    button {{
      padding: 9px 16px;
      border-radius: 999px;
      border: 1px solid rgba(55, 65, 81, 1);
      background: #111827;
      color: #e5e7eb;
      font-size: 14px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    button.primary-btn {{
      border-color: rgba(251, 191, 36, 0.8);
      background: radial-gradient(circle at 30% 0, #facc15 0, #b45309 45%, #111827 95%);
      color: #020617;
      font-weight: 600;
    }}
    button.primary-btn:hover {{
      filter: brightness(1.08);
    }}
    .box {{
      margin-top: 18px;
      padding: 14px 14px 16px;
      background: rgba(15, 23, 42, 0.95);
      border-radius: 12px;
      border: 1px solid rgba(75, 85, 99, 0.8);
      white-space: pre-wrap;
      font-size: 13px;
    }}
    .section-title {{
      font-weight: 600;
      font-size: 13px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin: 10px 0 4px;
    }}
    .copy-btn {{
      font-size: 11px;
      padding: 4px 9px;
      border-radius: 999px;
      border: 1px solid rgba(55, 65, 81, 1);
      background: rgba(15, 23, 42, 0.9);
      color: #e5e7eb;
    }}
    .copy-btn:hover {{
      border-color: #fbbf24;
      color: #fbbf24;
    }}
    pre {{
      white-space: pre-wrap;
      word-wrap: break-word;
      margin: 0;
      font-family: inherit;
      font-size: 13px;
      color: #e5e7eb;
    }}
    .provider-list {{
      font-size: 11px;
      color: #9ca3af;
      margin-bottom: 4px;
    }}
    .error {{
      color: #fecaca;
      font-weight: 500;
    }}
    @media (max-width: 640px) {{
      .card {{
        padding: 18px 14px 20px;
        border-radius: 14px;
      }}
      .title-main {{
        font-size: 18px;
      }}
      .header {{
        flex-direction: column;
        align-items: flex-start;
      }}
      .row {{
        flex-direction: column;
        align-items: flex-start;
      }}
      button {{
        width: 100%;
        justify-content: center;
      }}
    }}
  </style>
  <script>
    function copyText(id) {{
      const el = document.getElementById(id);
      if (!el) return;
      const text = el.innerText || el.textContent || "";
      navigator.clipboard.writeText(text).then(
        function() {{ alert("In Zwischenablage kopiert."); }},
        function(err) {{ alert("Kopieren nicht möglich: " + err); }}
      );
    }}
  </script>
</head>
<body>
  <div class="page">
    <div class="card">
      <div class="header">
        <div class="header-left">
          <div class="logo">U</div>
          <div>
            <div class="title-main">Upseller PRO</div>
            <div class="title-sub">V5.0 ULTRA – Verkaufs- &amp; KI-Analyse</div>
          </div>
        </div>
        <div class="badge">interner Masterprompt – serverseitig geschützt</div>
      </div>

      <form method="post" enctype="multipart/form-data">
        <label for="text">LEVEL 1 – Welches Produkt möchtest du verkaufen?</label>
        <textarea id="text" name="text"
          placeholder='Z. B. "Massivholzfenster 149 x 149 cm, 3-fach Verglasung, Baujahr 2021"'></textarea>

        <div class="row">
          <div>
            <label for="image">Bild (optional, für Zustandsanalyse):</label>
            <input id="image" name="image" type="file" accept="image/*">
          </div>
          <div>
            <button type="submit" class="primary-btn">
              ⚡ Mit KI optimieren
            </button>
          </div>
        </div>

        <p class="hint">
          Upseller arbeitet mit deinem internen Level-System (1–10), Marktanalyse, Verhandlungslogik
          &amp; KI-Vergleichsprompt. Der Masterprompt liegt nur als Server-Variable vor und ist nicht im Code sichtbar.
        </p>
      </form>

      <div class="box">
        {result}
      </div>
    </div>
  </div>
</body>
</html>
"""


# ------------------------------------------------------------
# Hilfsfunktionen: OpenAI + optionale andere KIs
# ------------------------------------------------------------

def call_openai(system_prompt: str, user_text: str) -> str:
    """Standardaufruf an OpenAI (wird auch für die Meta-Auswertung genutzt)."""
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


def call_openai_vision(system_prompt: str, user_text: str, image_b64: str) -> str:
    """Sehr einfache Vision-Analyse mit demselben Modell (funktioniert mit gpt-4.x / gpt-4o)."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY ist nicht gesetzt.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}"
                    },
                },
            ],
        },
    ]
    data = {"model": OPENAI_MODEL, "messages": messages}
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# Placeholder für andere KIs – bei Bedarf echte Endpoints eintragen
def call_grok(system_prompt: str, user_text: str) -> str:
    if not GROK_API_KEY:
        raise RuntimeError("GROK_API_KEY nicht gesetzt.")
    # TODO: mit echter Grok-API ersetzen
    raise RuntimeError("Grok-API-Aufruf ist noch nicht implementiert.")


def call_claude(system_prompt: str, user_text: str) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY nicht gesetzt.")
    # TODO: mit echter Claude-API ersetzen
    raise RuntimeError("Claude-API-Aufruf ist noch nicht implementiert.")


def call_gemini(system_prompt: str, user_text: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY nicht gesetzt.")
    # TODO: mit echter Gemini-API ersetzen
    raise RuntimeError("Gemini-API-Aufruf ist noch nicht implementiert.")


def call_provider_safe(name: str, func: Callable[[str, str], str],
                       system_prompt: str, user_text: str) -> str:
    """Wrappt die einzelnen Provider mit robustem Fehler-Handling."""
    try:
        return func(system_prompt, user_text)
    except requests.Timeout:
        return f"[{name}: Timeout nach 60s]"
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        return f"[{name}: HTTP-Fehler {code}]"
    except Exception as e:
        return f"[{name}: {type(e).__name__} – {e}]"


def get_available_providers() -> Dict[str, Callable[[str, str], str]]:
    """Ermittelt dynamisch alle verfügbaren Provider anhand der ENV-Variablen."""
    providers: Dict[str, Callable[[str, str], str]] = {
        "openai": call_openai
    }
    if GROK_API_KEY:
        providers["grok"] = call_grok
    if ANTHROPIC_API_KEY:
        providers["claude"] = call_claude
    if GEMINI_API_KEY:
        providers["gemini"] = call_gemini
    return providers


def collect_opinions(user_context: str) -> Dict[str, str]:
    """Sammelt die Roh-Gutachten aller verfügbaren KIs."""
    providers = get_available_providers()
    opinions: Dict[str, str] = {}

    for name, func in providers.items():
        opinions[name] = call_provider_safe(name, func, UPSELLER_PROMPT, user_context)

    return opinions


# ------------------------------------------------------------
# Meta-Analyse / Parsing
# ------------------------------------------------------------

def safe_parse_meta(meta_answer: str) -> tuple[str, str]:
    """
    Versucht, die Blöcke mit Markern zu extrahieren.
    Fällt robust zurück, wenn die Marker fehlen.
    """
    level9 = ""
    kicheck = ""

    try:
        if "---LEVEL9_START---" in meta_answer and "---LEVEL9_END---" in meta_answer:
            part = meta_answer.split("---LEVEL9_START---", 1)[1]
            level9, rest = part.split("---LEVEL9_END---", 1)

            if "---KICHECK_START---" in rest and "---KICHECK_END---" in rest:
                part2 = rest.split("---KICHECK_START---", 1)[1]
                kicheck = part2.split("---KICHECK_END---", 1)[0]
        else:
            # Fallback: grobe Zweiteilung
            parts = meta_answer.split("\n\n---\n\n", 1)
            level9 = parts[0] if parts else meta_answer
            kicheck = parts[1] if len(parts) > 1 else "KI-Vergleichsprompt konnte nicht extrahiert werden."
    except Exception as e:
        level9 = meta_answer
        kicheck = f"Parsing-Fehler: {e}"

    return level9.strip(), kicheck.strip()


def build_meta_analysis(user_context: str, opinions: Dict[str, str]) -> Dict[str, str]:
    """
    Nutzt OpenAI als Meta-Analyst, um alle Einzel-Gutachten zu
    einer gemeinsamen Level-9-Auswertung + KI-Vergleichsprompt zu verschmelzen.
    """
    providers_used = ", ".join(opinions.keys()) or "openai"

    meta_system = """
<role>UPSELLER ULTRA Meta-Analyst</role>

<task>
Du erhältst:
- die Antworten des Nutzers aus Level 1–8
- mehrere KI-Gutachten (OpenAI + optional andere KIs)

Deine Aufgaben:
1. Erstelle eine saubere Level-9-Auswertung:
   - Marktanalyse
   - Preisbereich (Maximal, realistisch, Geduld, Schnellverkauf)
   - Wertfaktoren
   - Plattformempfehlung(en)
   - Timing & Preisprognose
   - psychologische Preisstrategie
   - Premium-Anzeigentext (1-Block, 1-Klick Copy tauglich)
   - kurze Profi-Zusammenfassung

2. Erzeuge einen KI-Vergleichs-Prompt (Level 10),
   mit dem andere KIs das Angebot gegenchecken können.
   Verwende die strukturierte Liste:
   PRODUKT, JAHR, ZUSTAND, ABMESSUNGEN, HERSTELLER, VERGLASUNG,
   SCHEIBEN, U-WERT/TECHNIK, MATERIAL/PROFIL, FUNKTIONEN,
   SICHERHEIT, GEWICHT, MÄNGEL, STÜCKZAHL, MARKTREGION,
   MARKTLAGE, REFERENZBILD, PREISEMPFEHLUNG (Kurzform) usw.

3. Identifiziere fehlende Schlüsseldaten, die man nachfragen sollte.

Formatiere deine Antwort GENAU so:

---LEVEL9_START---
[komplette Level-9-Auswertung]
---LEVEL9_END---
---KICHECK_START---
[kompletter KI-Vergleichs-Prompt-Block]
---KICHECK_END---
</task>
"""

    opinions_text = ""
    for name, content in opinions.items():
        opinions_text += f"\n\n### Gutachten {name.upper()}:\n{content}\n"

    meta_user = textwrap.dedent(f"""
    NUTZER-KONTEXT (Level 1–8 Antworten):

    {user_context}

    GENUTZTE KIs: {providers_used}

    MEHRERE KI-GUTACHTEN:

    {opinions_text}

    Erstelle jetzt die Auswertung im vorgegebenen Format.
    """)

    meta_answer = call_openai(meta_system, meta_user)
    level9_text, kicheck_text = safe_parse_meta(meta_answer)

    return {
        "providers_used": providers_used,
        "level9": level9_text,
        "kicheck": kicheck_text,
    }


# ------------------------------------------------------------
# ROUTEN
# ------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def form_get():
    start_text = (
        "Gib oben dein Produkt ein und starte Upseller ULTRA.\n"
        "Du bekommst eine Level-9-Auswertung plus KI-Vergleichs-Prompt."
    )
    return HTML_PAGE.format(result=start_text)


@app.post("/", response_class=HTMLResponse)
async def form_post(
    text: str = Form(...),
    image: UploadFile | None = File(None),
):
    user_context = text.strip()

    if not user_context:
        result_html = "<span class='error'>Bitte gib zuerst eine Beschreibung deines Produkts ein.</span>"
        return HTML_PAGE.format(result=result_html)

    # optional: Bildanalyse
    if image and image.filename:
        try:
            content = await image.read()
            image_b64 = base64.b64encode(content).decode("utf-8")
            image_analysis = await asyncio.to_thread(
                call_openai_vision,
                "Analysiere dieses Produktbild für einen Verkauf (Zustand, Material, Besonderheiten, Kratzer, Qualität).",
                user_context,
                image_b64,
            )
            user_context += "\n\nBILD-ANALYSE:\n" + image_analysis
        except Exception as e:
            # Bildfehler sollen nicht alles kaputt machen
            user_context += f"\n\n[Hinweis: Bildanalyse fehlgeschlagen: {e}]"

    try:
        # 1. Roh-Gutachten sammeln (OpenAI + optionale KIs)
        opinions = await asyncio.to_thread(collect_opinions, user_context)

        # 2. Meta-Auswertung mit OpenAI
        meta = await asyncio.to_thread(build_meta_analysis, user_context, opinions)

        providers_used = meta["providers_used"]
        level9_block = meta["level9"]
        kicheck_block = meta["kicheck"]

        # 3. HTML-Ergebnis
        result_html = f"""
        <div>
          <div class="provider-list">
            Auswertung erstellt mit: {providers_used}
          </div>

          <div class="section-title">
            Level 9 – Marktanalyse &amp; Preisauswertung
            <button class="copy-btn" type="button" onclick="copyText('level9_block')">
              Level&nbsp;9 kopieren
            </button>
          </div>
          <pre id="level9_block">{level9_block}</pre>

          <div class="section-title">
            Level 10 – KI-Vergleichs-Prompt (für andere KIs)
            <button class="copy-btn" type="button" onclick="copyText('kicheck_block')">
              KI-Prompt kopieren
            </button>
          </div>
          <p class="hint">
            Diesen Block kannst du in andere KIs (z.&nbsp;B. Grok, Claude, Gemini, ChatGPT) einfügen,
            damit sie dein Angebot unabhängig prüfen und ergänzen.
          </p>
          <pre id="kicheck_block">{kicheck_block}</pre>
        </div>
        """

    except Exception as e:
        result_html = f"<span class='error'>Fehler bei der KI-Anfrage: {e}</span>"

    return HTML_PAGE.format(result=result_html)
