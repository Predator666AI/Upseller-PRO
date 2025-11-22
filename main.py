import os
import textwrap
import json
import html as html_module
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
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# optionale weitere KIs – wenn kein Key gesetzt ist, werden sie einfach übersprungen
GROK_API_KEY = os.getenv("GROK_API_KEY")         # z.B. Grok / xAI
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # z.B. Claude
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")     # z.B. Google Gemini

# --------------------------------------------------------------------
# LEVEL-DEFINITION (1–8 werden vom Formular abgefragt)
# --------------------------------------------------------------------
LEVELS = [
    {
        "key": "product",
        "label": "LEVEL 1 – Welches Produkt möchtest du verkaufen?",
        "placeholder": 'Z. B. "Massivholzfenster 149 x 149 cm, 3-fach Verglasung, Baujahr 2021"',
    },
    {
        "key": "year",
        "label": "LEVEL 2 – In welchem Jahr wurde das Produkt hergestellt / gekauft?",
        "placeholder": "Z. B. 2021, 2018, ca. 10 Jahre alt …",
    },
    {
        "key": "condition",
        "label": "LEVEL 3 – In welchem Zustand ist das Produkt?",
        "placeholder": "Z. B. neuwertig, gebraucht, mit leichten Gebrauchsspuren …",
    },
    {
        "key": "extras",
        "label": "LEVEL 4 – Welche Ausstattung / Extras hat das Produkt?",
        "placeholder": "Z. B. Sonderverglasung, Markenbeschläge, Zubehör, OVP, Rechnung …",
    },
    {
        "key": "defects",
        "label": "LEVEL 5 – Gibt es Mängel oder Schäden?",
        "placeholder": "Z. B. Kratzer, Dellen, Glasfehler, leicht verzogen, keine Mängel …",
    },
    {
        "key": "quantity",
        "label": "LEVEL 6 – Wie viele Stück möchtest du verkaufen?",
        "placeholder": "Z. B. 1 Stück, 4 gleiche Fenster, Set aus 6 Teilen …",
    },
    {
        "key": "country",
        "label": "LEVEL 7 – In welchem Land / welcher Region wird verkauft?",
        "placeholder": "Z. B. Deutschland, Österreich, Schweiz, Region Brandenburg …",
    },
    {
        "key": "other",
        "label": "LEVEL 8 – Sonstige wichtige Infos?",
        "placeholder": "Alles, was wichtig ist: Maße, U-Wert, Marke, Besonderheiten, Lieferbedingungen …",
    },
]
TOTAL_LEVELS = len(LEVELS)


def create_initial_state() -> dict:
    return {
        "level": 1,
        "answers": {lvl["key"]: "" for lvl in LEVELS},
        "image_hint": "",
    }


def serialize_state(state: dict) -> str:
    try:
        return json.dumps(state)
    except Exception:
        return json.dumps(create_initial_state())


def deserialize_state(state_str: str | None) -> dict:
    if not state_str:
        return create_initial_state()
    try:
        return json.loads(state_str)
    except Exception:
        return create_initial_state()


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
      min-height: 160px;
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
    .level-indicator {{
      font-size: 12px;
      color: #444;
      margin-bottom: 6px;
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
  <p>Beantworte die Fragen Level für Level. Upseller ULTRA sammelt alles für die Auswertung.</p>

  <form method="post" enctype="multipart/form-data">
    <div class="level-indicator">
      Aktuelles Level: {current_level} / {total_levels}
    </div>

    <label for="text"><b>{question_label}</b></label><br>
    <textarea id="text" name="text" placeholder="{placeholder}">{prefill}</textarea>

    <div style="margin-top:10px;">
      <label for="image">Bild (optional):</label>
      <input id="image" name="image" type="file" accept="image/*">
    </div>

    <input type="hidden" name="state" value="{state_json}">

    <div style="margin-top:15px;">
      <button type="submit" class="primary-btn">Weiter / Auswertung starten</button>
    </div>

    <p class="hint">
      Die KI arbeitet mit deinem internen UPSELLER V5.0 ULTRA Masterprompt (Level-System, Marktanalyse, Verhandlungslogik).
      Der Prompt liegt sicher auf dem Server und ist nicht im Code sichtbar. Andere KIs (Grok, Claude, Gemini) werden
      automatisch genutzt, falls API-Keys hinterlegt sind.
    </p>
  </form>

  <div class="box">
    {result}
  </div>
</body>
</html>
"""


def render_page(result: str, state: dict) -> str:
    level = state.get("level", 1)
    if level < 1:
        level = 1
    if level > TOTAL_LEVELS:
        level = TOTAL_LEVELS

    lvl_def = LEVELS[level - 1]
    prefill = state.get("answers", {}).get(lvl_def["key"], "")

    state_json = serialize_state({**state, "level": level})
    state_json_escaped = html_module.escape(state_json, quote=True)

    return HTML_PAGE.format(
        current_level=level,
        total_levels=TOTAL_LEVELS,
        question_label=lvl_def["label"],
        placeholder=lvl_def["placeholder"],
        prefill=prefill,
        state_json=state_json_escaped,
        result=result,
    )


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
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-1.5-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
    )
    full_prompt = system_prompt + "\n\nNutzer:\n" + user_text
    data = {"contents": [{"parts": [{"text": full_prompt}]}]}
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
        "- Level 10: KI-Vergleichs-Prompt zum Kopieren, exakt im Block-Format.\n\n"
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
    2. Erstelle am Ende zusätzlich den Level-10-KI-Vergleichs-Prompt exakt im Block-Format
       (wie in deinem Masterprompt beschrieben).
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
    state = create_initial_state()
    result_html = "Gib zuerst die Infos für Level 1 ein und klicke dann auf „Weiter“."
    return render_page(result_html, state)


@app.post("/", response_class=HTMLResponse)
async def form_post(
    text: str = Form(...),
    state: str = Form(None),
    image: UploadFile | None = File(None),
):
    # bisherige Session laden
    session = deserialize_state(state)
    level = session.get("level", 1)

    # aktuelle Antwort speichern
    answer = (text or "").strip()
    if not answer:
        result_html = "<span class='error'>Bitte gib zuerst eine Antwort ein.</span>"
        return render_page(result_html, session)

    if level < 1:
        level = 1
    if level > TOTAL_LEVELS:
        level = TOTAL_LEVELS

    current_level_def = LEVELS[level - 1]
    key = current_level_def["key"]
    session.setdefault("answers", {})[key] = answer

    # Bild nur als Hinweis speichern (keine Vision-API, aber später erweiterbar)
    if image and image.filename:
        session["image_hint"] = f"Nutzer hat ein Bild hochgeladen (Dateiname: {image.filename})."

    # Wenn wir Level 1–7 bearbeiten → nur zum nächsten Level springen
    if level < TOTAL_LEVELS:
        session["level"] = level + 1

        # kurze Zusammenfassung der bisherigen Antworten
        summary_lines = ["Bisherige Antworten:"]
        for idx, lvl in enumerate(LEVELS[:level], start=1):
            val = session["answers"].get(lvl["key"], "").strip()
            if val:
                summary_lines.append(f"Level {idx}: {val}")
        summary_text = "\n".join(summary_lines)

        result_html = (
            f"Antwort für Level {level} gespeichert.\n"
            f"Als nächstes kommt: {LEVELS[level]['label']}\n\n"
            f"{summary_text}"
        )
        return render_page(result_html, session)

    # ----------------------------------------------------------------
    # Wir haben Level 8 gerade beantwortet -> Level 9 Auswertung
    # ----------------------------------------------------------------
    session["level"] = TOTAL_LEVELS  # bleibt 8, Fragen sind fertig

    # Nutzer-Kontext aus allen Level-Antworten bauen
    answers = session.get("answers", {})
    ctx_lines = []
    for idx, lvl in enumerate(LEVELS, start=1):
        val = answers.get(lvl["key"], "").strip()
        if val:
            ctx_lines.append(f"Level {idx} ({lvl['label']}): {val}")
    if session.get("image_hint"):
        ctx_lines.append(session["image_hint"])

    user_context = "\n".join(ctx_lines)

    try:
        # 1. Einzel-Gutachten einsammeln (OpenAI + optionale andere KIs)
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

    return render_page(result_html, session)
