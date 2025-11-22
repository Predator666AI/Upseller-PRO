import os
import textwrap
import base64
import json
from typing import Dict, Callable

import requests
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse

app = FastAPI()

# --------------------------------------------------------------------
# ENV-VARIABLEN
# --------------------------------------------------------------------
UPSELLER_PROMPT = os.getenv("UPSELLER_PROMPT", "Upseller Prompt fehlt – bitte ENV setzen.")
OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENAI_APIKEY")
    or os.getenv("OPENAI_KEY")
)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")  # in Railway anpassbar

# optionale weitere KIs – wenn kein Key gesetzt ist, werden sie einfach übersprungen
GROK_API_KEY = os.getenv("GROK_API_KEY")              # z.B. Grok / xAI
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")    # z.B. Claude
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")          # z.B. Google Gemini


# --------------------------------------------------------------------
# HTML-Template mit Copy-Buttons + verstecktem State
# --------------------------------------------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Upseller PRO – Test Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <style>
    :root {
      --bg: #020617;
      --bg-soft: #020617;
      --card: #020617;
      --card-soft: #0b1120;
      --border: #1f2937;
      --accent: #fbbf24;  /* Gold */
      --accent-soft: rgba(250, 191, 36, 0.15);
      --text-main: #e5e7eb;
      --text-muted: #9ca3af;
      --danger: #f97373;
      --shadow-soft: 0 24px 60px rgba(0, 0, 0, 0.75);
      --radius-lg: 18px;
      --radius-md: 10px;
      --radius-sm: 7px;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      padding: 24px 10px 40px;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", Arial, sans-serif;
      background: radial-gradient(circle at top, #111827 0, #020617 50%, #000000 100%);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: flex-start;
    }

    .app-shell {
      width: 100%;
      max-width: 980px;
      background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(3,7,18,0.98));
      border-radius: 26px;
      border: 1px solid rgba(148,163,184,0.25);
      box-shadow: var(--shadow-soft);
      overflow: hidden;
      position: relative;
    }

    .glow-ring {
      position: absolute;
      inset: -1px;
      border-radius: inherit;
      pointer-events: none;
      background: conic-gradient(from 160deg, rgba(250,204,21,0.18), transparent 35%, transparent 65%, rgba(251,191,36,0.3));
      opacity: 0.22;
      mix-blend-mode: screen;
    }

    .content {
      position: relative;
      z-index: 1;
      padding: 18px 22px 26px;
    }

    /* Top Bar / Logo */
    .top-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 12px;
    }

    .brand-wrap {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .logo-pill {
      width: 56px;
      height: 56px;
      border-radius: 999px;
      background: radial-gradient(circle at 25% 10%, #fef9c3, #f59e0b 55%, #78350f 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      border: 1px solid rgba(248,250,252,0.35);
      box-shadow: 0 18px 45px rgba(15,23,42,0.95);
    }

    .logo-pill img {
      max-width: 80%;
      max-height: 80%;
      object-fit: contain;
      filter: drop-shadow(0 4px 10px rgba(15,23,42,0.7));
    }

    .title-block h1 {
      font-size: 21px;
      letter-spacing: 0.03em;
      margin: 0 0 2px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .title-block h1 span.badge {
      font-size: 11px;
      padding: 2px 7px;
      border-radius: 999px;
      background: rgba(15,23,42,0.9);
      border: 1px solid rgba(251,191,36,0.6);
      color: var(--accent);
      text-transform: uppercase;
    }

    .title-block p {
      margin: 0;
      font-size: 13px;
      color: var(--text-muted);
    }

    .tagline-chip {
      font-size: 11px;
      padding: 5px 10px;
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,0.4);
      background: rgba(15,23,42,0.85);
      color: var(--text-muted);
      display: inline-flex;
      gap: 6px;
      align-items: center;
    }

    .tagline-chip strong {
      color: var(--accent);
      font-weight: 600;
    }

    /* Form Card */
    .card {
      margin-top: 14px;
      background: radial-gradient(circle at top left, rgba(55,65,81,0.35), rgba(15,23,42,0.96));
      border-radius: var(--radius-lg);
      border: 1px solid rgba(31,41,55,0.9);
      padding: 16px 16px 18px;
    }

    .card-header {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }

    .step-label {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      color: var(--accent);
    }

    .card-header-title {
      font-size: 15px;
      font-weight: 500;
    }

    .helper-text {
      font-size: 12px;
      color: var(--text-muted);
      margin: 4px 0 0;
    }

    textarea {
      width: 100%;
      min-height: 140px;
      padding: 10px 11px;
      margin-top: 8px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
      background: rgba(15,23,42,0.9);
      color: var(--text-main);
      font-size: 14px;
      resize: vertical;
      outline: none;
      box-shadow: inset 0 0 0 1px rgba(15,23,42,0.7);
    }

    textarea::placeholder {
      color: #6b7280;
    }

    textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 1px rgba(251,191,36,0.5), 0 0 0 999px rgba(15,23,42,0.35) inset;
    }

    .input-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px 14px;
      align-items: center;
      margin-top: 10px;
      justify-content: space-between;
    }

    .file-label {
      font-size: 12px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 6px;
    }

    input[type="file"] {
      font-size: 11px;
      max-width: 210px;
      color: var(--text-muted);
    }

    button {
      border-radius: 999px;
      border: 1px solid transparent;
      font-size: 14px;
      padding: 9px 18px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      transition: all 0.12s ease-in-out;
      background: #e5e7eb;
      color: #111827;
    }

    .btn-primary {
      background: radial-gradient(circle at top, #facc15, #eab308 55%, #b45309 100%);
      color: #111827;
      border-color: rgba(250,204,21,0.9);
      box-shadow: 0 10px 30px rgba(250,204,21,0.35);
      font-weight: 600;
    }

    .btn-primary:hover {
      transform: translateY(-1px);
      box-shadow: 0 14px 36px rgba(250,204,21,0.45);
      filter: brightness(1.02);
    }

    .btn-copy {
      font-size: 11px;
      padding: 5px 8px;
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,0.5);
      background: rgba(15,23,42,0.95);
      color: var(--text-muted);
    }

    .btn-copy:hover {
      border-color: var(--accent);
      color: var(--accent);
      transform: translateY(-0.5px);
    }

    .hint {
      font-size: 11px;
      color: var(--text-muted);
      margin: 8px 2px 0;
    }

    .hint strong {
      color: var(--accent);
      font-weight: 600;
    }

    /* Ergebnisbereich */
    .result-card {
      margin-top: 18px;
      background: radial-gradient(circle at 10% -10%, rgba(250,204,21,0.08), rgba(15,23,42,0.98));
      border-radius: var(--radius-lg);
      border: 1px solid rgba(55,65,81,0.9);
      padding: 14px 14px 16px;
    }

    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }

    .result-title {
      font-size: 13px;
      font-weight: 500;
      color: var(--text-muted);
    }

    .provider-list {
      font-size: 11px;
      color: var(--text-muted);
    }

    .section-title {
      margin-top: 10px;
      margin-bottom: 4px;
      font-size: 12px;
      font-weight: 600;
      color: #e5e7eb;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .section-title span {
      font-size: 11px;
      color: var(--text-muted);
      font-weight: 400;
    }

    pre {
      white-space: pre-wrap;
      word-wrap: break-word;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 12px;
      margin: 0;
      padding: 10px 11px;
      border-radius: var(--radius-md);
      background: rgba(15,23,42,0.95);
      border: 1px solid rgba(31,41,55,0.9);
      max-height: 420px;
      overflow: auto;
    }

    .error {
      color: var(--danger);
      font-weight: 600;
      font-size: 12px;
    }

    @media (max-width: 720px) {
      body {
        padding: 12px 6px 24px;
      }
      .content {
        padding: 14px 12px 18px;
      }
      .top-bar {
        flex-direction: column;
        align-items: flex-start;
      }
      .tagline-chip {
        margin-top: 6px;
      }
    }
  </style>

  <script>
    function copyText(id) {
      const el = document.getElementById(id);
      if (!el) return;
      const text = el.innerText || el.textContent || "";
      navigator.clipboard.writeText(text).then(function () {
        alert("In Zwischenablage kopiert.");
      }, function (err) {
        alert("Kopieren nicht möglich: " + err);
      });
    }
  </script>
</head>
<body>
  <div class="app-shell">
    <div class="glow-ring"></div>
    <div class="content">

      <!-- TOP / LOGO -->
      <header class="top-bar">
        <div class="brand-wrap">
          <div class="logo-pill">
            <!-- HIER DEIN LOGO-LINK EINTRAGEN: src="https://dein-bild-link.png" -->
            <img src="LOGO_URL_HERE" alt="Upseller PRO Logo">
          </div>
          <div class="title-block">
            <h1>
              Upseller PRO
              <span class="badge">V5.0 ULTRA</span>
            </h1>
            <p>Dein KI-Verkaufsprofi für maximal starke Anzeigen & Preise.</p>
          </div>
        </div>

        <div class="tagline-chip">
          <span>🔒 Prompt sicher auf dem Server ·</span>
          <strong>Multi-KI ready</strong>
        </div>
      </header>

      <!-- EINGABE-BEREICH -->
      <div class="card">
        <div class="card-header">
          <div>
            <div class="step-label">Level 1</div>
            <div class="card-header-title">Welches Produkt möchtest du verkaufen?</div>
            <p class="helper-text">Du kannst hier auch schon Maße, Zustand, Baujahr, Besonderheiten usw. mit reinschreiben.</p>
          </div>
        </div>

        <form method="post" enctype="multipart/form-data">
          <textarea id="text" name="text" placeholder='Z. B. "Massivholzfenster 149 × 149 cm, 3-fach Verglasung, Baujahr 2021, sehr guter Zustand, Restposten aus Ausstellung."'></textarea>

          <div class="input-row">
            <label class="file-label">
              📎 Bild (optional):
              <input id="image" name="image" type="file" accept="image/*">
            </label>

            <button type="submit" class="btn-primary">
              ⚡ Mit KI optimieren
            </button>
          </div>

          <p class="hint">
            Die KI arbeitet mit deinem internen <strong>UPSELLER V5.0 ULTRA Masterprompt</strong>
            (Level-System, Marktanalyse, Verhandlungslogik, KI-Vergleichs-Prompt).<br>
            Der Prompt liegt sicher auf dem Server und ist nicht im Code sichtbar.
          </p>
        </form>
      </div>

      <!-- ERGEBNIS-BEREICH -->
      <div class="result-card">
        <div class="result-header">
          <div class="result-title">Auswertung</div>
          <div class="provider-list">Erstellt mit: openai / Upseller-Engine</div>
        </div>

        {result}
      </div>

    </div>
  </div>
</body>
</html>
"""

# --------------------------------------------------------------------
# State-Handling für Level-Chat (im versteckten Feld)
# --------------------------------------------------------------------
def initial_state() -> dict:
    return {"level": 1, "answers": {}}


def encode_state(state: dict) -> str:
    raw = json.dumps(state)
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


def decode_state(state_b64: str) -> dict:
    if not state_b64:
        return initial_state()
    try:
        raw = base64.b64decode(state_b64.encode("utf-8")).decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return initial_state()
        return data
    except Exception:
        return initial_state()


def question_for_level(level: int) -> str:
    mapping = {
        1: "LEVEL 1 – Welches Produkt möchtest du verkaufen?",
        2: "LEVEL 2 – Aus welchem Jahr / Baujahr ist das Produkt?",
        3: "LEVEL 3 – In welchem Zustand ist es? (z.B. neu, wie neu, gebraucht, stark gebraucht)",
        4: "LEVEL 4 – Welche Ausstattung / Extras / Besonderheiten hat es?",
        5: "LEVEL 5 – Welche Mängel oder Schäden gibt es?",
        6: "LEVEL 6 – Wie viele Stück möchtest du verkaufen?",
        7: "LEVEL 7 – In welchem Land / welcher Region wird verkauft?",
        8: "LEVEL 8 – Gibt es sonst noch wichtige technische Daten oder Infos (Maße, U-Wert, Material, Modell etc.)?",
        9: "Alle Level 1–8 sind ausgefüllt. Wenn du etwas ändern willst, ändere oben deine letzte Antwort oder lade die Seite neu.",
    }
    return mapping.get(level, "LEVEL – Frage")


def build_human_readable_context(state: dict) -> str:
    """Baut aus den Level-Antworten einen sauberen Kontexttext für die KIs."""
    answers = state.get("answers", {})
    lines = [
        "Antworten des Nutzers aus dem Level-System:",
        f"LEVEL 1 – Produkt: {answers.get('1', '')}",
        f"LEVEL 2 – Jahrgang: {answers.get('2', '')}",
        f"LEVEL 3 – Zustand: {answers.get('3', '')}",
        f"LEVEL 4 – Ausstattung / Extras: {answers.get('4', '')}",
        f"LEVEL 5 – Mängel: {answers.get('5', '')}",
        f"LEVEL 6 – Stückzahl: {answers.get('6', '')}",
        f"LEVEL 7 – Marktregion / Land: {answers.get('7', '')}",
        f"LEVEL 8 – weitere technische Daten: {answers.get('8', '')}",
    ]
    return "\n".join(lines)


def build_progress_summary(state: dict) -> str:
    answers = state.get("answers", {})
    lines = ["Bisherige Antworten (Kurzüberblick):"]
    for lvl in range(1, min(state.get("level", 1) + 1, 9)):
        key = str(lvl)
        if key in answers:
            lines.append(f"LEVEL {lvl}: {answers[key]}")
    return "\n".join(lines)


def validate_user_input(text: str, max_length: int = 2000) -> tuple[bool, str]:
    """Einfache Validierung des User-Inputs."""
    if len(text) > max_length:
        return False, f"Text zu lang (max. {max_length} Zeichen erlaubt)."

    spam_keywords = ["viagra", "casino", "crypto pump"]
    if any(kw in text.lower() for kw in spam_keywords):
        return False, "Ungültiger Inhalt erkannt."

    return True, ""


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
    resp = requests.post(url, headers=headers, json=data, timeout=30)
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
    resp = requests.post(url, headers=headers, json=data, timeout=30)
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
    resp = requests.post(url, headers=headers, json=data, timeout=30)
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
    resp = requests.post(url, json=data, timeout=30)
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

    # OpenAI wird IMMER genutzt – ist auch unsere Meta-KI
    providers["openai"] = call_openai

    if GROK_API_KEY:
        providers["grok"] = call_grok
    if ANTHROPIC_API_KEY:
        providers["claude"] = call_claude
    if GEMINI_API_KEY:
        providers["gemini"] = call_gemini

    return providers


def collect_opinions(user_context: str) -> Dict[str, str]:
    """Ruft alle verfügbaren Provider auf und sammelt deren Roh-Antworten (sequenziell)."""
    providers = get_available_providers()
    opinions: Dict[str, str] = {}

    for name, func in providers.items():
        try:
            content = func(UPSELLER_PROMPT, user_context)
            opinions[name] = content
        except Exception as e:
            opinions[name] = f"[Fehler bei {name}: {e}]"

    return opinions


def safe_parse_meta(meta_answer: str) -> tuple[str, str]:
    """Robustes Parsing der Meta-Antwort mit Fallback."""
    level9 = ""
    kicheck = ""
    try:
        if "---LEVEL9_START---" in meta_answer and "---LEVEL9_END---" in meta_answer:
            part = meta_answer.split("---LEVEL9_START---", 1)[1]
            level9, rest = part.split("---LEVEL9_END---", 1)

            if "---KICHECK_START---" in rest and "---KICHECK_END---" in rest:
                part = rest.split("---KICHECK_START---", 1)[1]
                kicheck = part.split("---KICHECK_END---", 1)[0]
        else:
            # Fallback: einfache Zweiteilung
            parts = meta_answer.split("\n\n---\n\n", 1)
            level9 = parts[0] if parts else meta_answer
            kicheck = parts[1] if len(parts) > 1 else "Konnte nicht extrahiert werden"
    except Exception as e:
        level9 = meta_answer
        kicheck = f"Parsing-Fehler: {e}"

    return level9.strip(), kicheck.strip()


def build_meta_analysis(user_context: str, opinions: Dict[str, str]) -> Dict[str, str]:
    """
    Nutzt OpenAI (ChatGPT) als Meta-KI, um alle Einzel-Gutachten zu einer
    gemeinsamen Level-9-Auswertung + KI-Vergleichs-Prompt zu verschmelzen.

    WICHTIG: Die KI soll aktiv prüfen, ob für eine saubere Preisfindung
    Schlüsseldaten fehlen, und dann konkrete Rückfragen formulieren.
    """
    providers_used = ", ".join(opinions.keys())

    meta_system = (
        "Du bist UPSELLER ULTRA – Meta-Analyst.\n"
        "Du bekommst mehrere KI-Gutachten zum gleichen Verkaufsobjekt "
        "(z.B. OpenAI, Grok, Claude, Gemini) und die Level-1–8-Antworten des Nutzers.\n\n"
        "DEINE HAUPTAUFGABE:\n"
        "1. Baue daraus EINE konsistente Auswertung im UPSELLER V5.0 ULTRA Format:\n"
        "   - Level 9: Marktanalyse, Preisbereich, Wertfaktoren, Plattformen, Timing,\n"
        "     psychologische Preisstrategie, Premium-Anzeigentext, Profi-Zusammenfassung.\n"
        "   - Level 10: KI-Vergleichs-Prompt zum Kopieren, exakt im Block-Format.\n\n"
        "2. Prüfe AKTIV, ob für eine genaue Preisfindung wichtige Infos fehlen oder zu vage sind.\n"
        "   Typische Schlüsseldaten sind z.B.:\n"
        "   - exakte Produktbezeichnung / Typ / Marke\n"
        "   - Baujahr / Alter\n"
        "   - Zustand (inkl. Mängel)\n"
        "   - Maße / Größe / Stückzahl\n"
        "   - technische Daten (z.B. U-Wert, Verglasung, Material, Modell)\n"
        "   - Marktregion (Land / Region)\n"
        "   - besondere Ausstattung / Extras\n\n"
        "3. Wenn solche Schlüsseldaten fehlen oder unklar sind, MUSST du im Level-9-Block\n"
        "   einen eigenen Abschnitt einbauen:\n"
        "   \"Fehlende oder unklare Schlüsseldaten – bitte beantworten:\" \n"
        "   - Formuliere dort 3–8 KONKRETE Rückfragen in Stichpunkten.\n"
        "   - Mach klar, dass die aktuelle Preisspanne nur eine vorläufige\n"
        "     Einschätzung ist, bis diese Fragen geklärt sind.\n\n"
        "4. Falls Daten fehlen, trotzdem eine Preis-Spanne nennen – aber mit\n"
        "   Sicherheits-Puffer und einem klaren Unsicherheitshinweis.\n\n"
        "AUSGABESTRUKTUR (sehr wichtig):\n"
        "Nutze exakt diese Marker, damit die Anwendung deine Blöcke trennen kann:\n"
        "---LEVEL9_START---\n"
        "(komplette Level-9-Auswertung als Textblock, inkl. Abschnitt für fehlende Daten,\n"
        " falls etwas Wichtiges fehlt.)\n"
        "---LEVEL9_END---\n"
        "---KICHECK_START---\n"
        "(kompletter KI-Vergleichs-Prompt-Block im vorgegebenen Format)\n"
        "---KICHECK_END---\n"
    )

    opinions_text = ""
    for name, content in opinions.items():
        opinions_text += f"\n\n### Gutachten {name.upper()}:\n{content}\n"

    meta_user = textwrap.dedent(f"""
    NUTZER-KONTEXT (Antworten aus Level 1–8 – leere oder sehr kurze Antworten bedeuten: Info fehlt oder ist unklar):

    {user_context}

    GENUTZTE KIs: {providers_used}

    MEHRERE KI-GUTACHTEN:

    {opinions_text}

    AUFGABE:
    1. Ziehe aus den Gutachten eine einzige, saubere Level-9-Auswertung gemäß
       UPSELLER V5.0 ULTRA (Preisbereich, Wertfaktoren, Plattformen, Timing,
       psychologische Preisstrategie, Premium-Anzeigentext, Profi-Zusammenfassung).
    2. Prüfe, welche Schlüsseldaten für eine genaue Preisfindung fehlen oder unklar sind
       (z.B. fehlende Maße, Marke, Material, Region, Zustand, Mängel, technische Daten).
       Falls etwas Wichtiges fehlt, erstelle im Level-9-Block einen klaren Abschnitt:

       "Fehlende oder unklare Schlüsseldaten – bitte beantworten:"
       - Frage 1 …
       - Frage 2 …
       - usw. (3–8 Fragen, kurz & konkret)

       und kennzeichne die Preisempfehlung deutlich als vorläufige Spanne.
    3. Erstelle am Ende zusätzlich den Level-10-KI-Vergleichs-Prompt exakt im Block-Format
       (wie im UPSELLER-Prompt beschrieben).
    4. Nutze strikt die Marker ---LEVEL9_START--- / ---LEVEL9_END--- und
       ---KICHECK_START--- / ---KICHECK_END---, damit die Anwendung die Blöcke trennen kann.
    """)

    meta_answer = call_openai(meta_system, meta_user)

    level9_text, kicheck_text = safe_parse_meta(meta_answer)

    return {
        "providers_used": providers_used,
        "level9": level9_text,
        "kicheck": kicheck_text,
    }


# --------------------------------------------------------------------
# FastAPI Routen
# --------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def form_get():
    state = initial_state()
    question_html = question_for_level(state["level"])
    result_html = (
        "Starte mit LEVEL 1: Beschreibe dein Produkt kurz oben im Feld und "
        "klicke auf „Mit KI optimieren“. Danach kommen automatisch die nächsten Level."
    )
    return HTML_PAGE.format(
        result=result_html,
        question_html=question_html,
        state_b64=encode_state(state),
    )


@app.post("/", response_class=HTMLResponse)
async def form_post(
    text: str = Form(""),
    state_b64: str = Form(""),
    image: UploadFile | None = File(None),
):
    # State dekodieren
    state = decode_state(state_b64)
    level = int(state.get("level", 1))
    answer = (text or "").strip()

    # Solange wir noch in Level 1–8 sind: Antwort ist Pflicht + validieren
    if level <= 8:
        if not answer:
            result_html = "<span class='error'>Bitte beantworte zuerst die aktuelle Level-Frage.</span>"
            question_html = question_for_level(level)
            return HTML_PAGE.format(
                result=result_html,
                question_html=question_html,
                state_b64=encode_state(state),
            )
        ok, msg = validate_user_input(answer)
        if not ok:
            result_html = f"<span class='error'>{msg}</span>"
            question_html = question_for_level(level)
            return HTML_PAGE.format(
                result=result_html,
                question_html=question_html,
                state_b64=encode_state(state),
            )

    # Antwort speichern
    if level <= 8:
        state["answers"][str(level)] = answer

    # Wenn noch nicht alle Level gesammelt: einfach zum nächsten Level springen
    if level < 8:
        state["level"] = level + 1
        question_html = question_for_level(state["level"])
        summary = build_progress_summary(state)
        result_html = summary + "\n\nWeiter mit dem nächsten Level oben."
        return HTML_PAGE.format(
            result=result_html,
            question_html=question_html,
            state_b64=encode_state(state),
        )

    # Ab hier: Level 8 wurde gerade beantwortet -> Level 9 Analyse fahren
    state["level"] = 9
    user_context = build_human_readable_context(state)

    # Bild aktuell nur als Hinweis im Kontext – Vision können wir später einbauen
    if image and image.filename:
        user_context += f"\n\nHinweis: Es wurde ein Bild hochgeladen (Dateiname: {image.filename})."

    try:
        opinions = collect_opinions(user_context)
        meta = build_meta_analysis(user_context, opinions)

        providers_used = meta["providers_used"] or "nur OpenAI"
        level9_block = meta["level9"]
        kicheck_block = meta["kicheck"]

        result_html = f"""
Bisherige Antworten (Kurzüberblick):
{build_progress_summary(state)}

---

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
        """

    except Exception as e:
        result_html = f"<span class='error'>Fehler bei der KI-Anfrage: {e}</span>"

    question_html = question_for_level(state["level"])
    return HTML_PAGE.format(
        result=result_html,
        question_html=question_html,
        state_b64=encode_state(state),
    )
