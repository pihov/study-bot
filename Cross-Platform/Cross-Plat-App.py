# Cross-Plat-app.py — Study Bot Cross-Platform Version
# Requirements: pip install -r requirements.txt
# Chrome/Chromium must be running with: --remote-debugging-port=9222

import os
import re
import json
import time
import random
import datetime
import threading
import queue
import subprocess
import platform
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

from groq import Groq
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WDM_AVAILABLE = True
except ImportError:
    WDM_AVAILABLE = False

try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SESSIONS_DIR    = os.path.join(BASE_DIR, "sessions")
SPACED_REP_FILE = os.path.join(SESSIONS_DIR, "spaced_rep.json")
DRUGS_FILE      = os.path.join(SESSIONS_DIR, "drugs_data.json")
STUDY_GUIDES_DIR = os.path.join(BASE_DIR, "study_guides")
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(STUDY_GUIDES_DIR, exist_ok=True)

DRUG_CATEGORIES = {
    "Anticoagulants":        ["Warfarin (Coumadin)", "Heparin", "Enoxaparin (Lovenox)",
                              "Rivaroxaban (Xarelto)", "Apixaban (Eliquis)", "Dabigatran (Pradaxa)"],
    "Antiplatelets":         ["Aspirin", "Clopidogrel (Plavix)", "Ticagrelor (Brilinta)"],
    "Cardiac":               ["Digoxin (Lanoxin)", "Metoprolol (Lopressor)", "Atenolol (Tenormin)",
                              "Amiodarone (Cordarone)", "Diltiazem (Cardizem)", "Verapamil (Calan)",
                              "Lisinopril (Zestril)", "Losartan (Cozaar)", "Amlodipine (Norvasc)",
                              "Hydralazine", "Nitroglycerin", "Adenosine (Adenocard)",
                              "Atropine", "Dopamine", "Dobutamine", "Norepinephrine", "Epinephrine"],
    "Diuretics":             ["Furosemide (Lasix)", "Hydrochlorothiazide (HCTZ)",
                              "Spironolactone (Aldactone)", "Mannitol"],
    "Antihyperlipidemics":   ["Atorvastatin (Lipitor)", "Simvastatin (Zocor)", "Rosuvastatin (Crestor)"],
    "Thrombolytics":         ["Alteplase (tPA)", "Tenecteplase (TNKase)"],
    "Antibiotics":           ["Amoxicillin", "Ampicillin", "Penicillin G", "Vancomycin",
                              "Clindamycin", "Metronidazole (Flagyl)", "Ciprofloxacin (Cipro)",
                              "Levofloxacin (Levaquin)", "Azithromycin (Zithromax)", "Doxycycline",
                              "Gentamicin", "Tobramycin", "Ceftriaxone (Rocephin)",
                              "Cefazolin (Ancef)", "Piperacillin-Tazobactam (Zosyn)", "Meropenem",
                              "Trimethoprim-Sulfamethoxazole (Bactrim)", "Nitrofurantoin (Macrobid)",
                              "Linezolid (Zyvox)", "Daptomycin"],
    "Antivirals / Antifungals": ["Acyclovir (Zovirax)", "Oseltamivir (Tamiflu)", "Remdesivir",
                              "Fluconazole (Diflucan)", "Amphotericin B", "Nystatin"],
    "Analgesics / Opioids":  ["Morphine", "Hydromorphone (Dilaudid)", "Oxycodone (Percocet)",
                              "Fentanyl", "Codeine", "Tramadol (Ultram)",
                              "Acetaminophen (Tylenol)", "Ibuprofen (Advil)", "Ketorolac (Toradol)",
                              "Naloxone (Narcan)"],
    "CNS / Seizure":         ["Phenytoin (Dilantin)", "Levetiracetam (Keppra)",
                              "Valproic Acid (Depakote)", "Carbamazepine (Tegretol)",
                              "Gabapentin (Neurontin)", "Pregabalin (Lyrica)",
                              "Lorazepam (Ativan)", "Diazepam (Valium)", "Midazolam (Versed)",
                              "Alprazolam (Xanax)", "Zolpidem (Ambien)"],
    "Psychiatric":           ["Haloperidol (Haldol)", "Risperidone (Risperdal)",
                              "Quetiapine (Seroquel)", "Olanzapine (Zyprexa)",
                              "Lithium (Lithobid)", "Fluoxetine (Prozac)", "Sertraline (Zoloft)",
                              "Escitalopram (Lexapro)", "Venlafaxine (Effexor)",
                              "Bupropion (Wellbutrin)", "Amitriptyline (Elavil)",
                              "Clozapine (Clozaril)"],
    "Endocrine / Diabetes":  ["Insulin Regular", "Insulin NPH", "Insulin Glargine (Lantus)",
                              "Insulin Lispro (Humalog)", "Metformin (Glucophage)",
                              "Glipizide (Glucotrol)", "Sitagliptin (Januvia)",
                              "Levothyroxine (Synthroid)", "Propylthiouracil (PTU)",
                              "Methimazole (Tapazole)", "Prednisone", "Hydrocortisone",
                              "Dexamethasone", "Glucagon", "Dextrose 50%"],
    "Respiratory":           ["Albuterol (ProAir)", "Ipratropium (Atrovent)",
                              "Fluticasone (Flovent)", "Budesonide (Pulmicort)",
                              "Montelukast (Singulair)", "Theophylline",
                              "Acetylcysteine (Mucomyst)"],
    "GI":                    ["Ondansetron (Zofran)", "Metoclopramide (Reglan)",
                              "Omeprazole (Prilosec)", "Pantoprazole (Protonix)",
                              "Sucralfate (Carafate)", "Lactulose", "Docusate (Colace)",
                              "Bisacodyl (Dulcolax)", "Magnesium Hydroxide (MOM)"],
    "Electrolytes / Reversal": ["Potassium Chloride (KCl)", "Magnesium Sulfate",
                              "Calcium Gluconate", "Sodium Bicarbonate",
                              "Vitamin K (Phytonadione)", "Protamine Sulfate",
                              "Flumazenil (Romazicon)", "Oxytocin (Pitocin)",
                              "Betamethasone"],
    "Immunosuppressants":    ["Cyclosporine (Sandimmune)", "Tacrolimus (Prograf)",
                              "Mycophenolate (CellCept)", "Azathioprine (Imuran)",
                              "Methotrexate"],
}

# ====================== CONFIG ======================

API_KEYS = [
    "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",
]
current_key_index = 0
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# ====================== THEME ======================

BG          = "#0f172a"
CARD        = "#1e293b"
PANEL       = "#334155"
BORDER      = "#475569"
TEXT        = "#f1f5f9"
MUTED       = "#94a3b8"
BLUE        = "#3b82f6"
GREEN       = "#22c55e"
ORANGE      = "#f97316"
RED         = "#ef4444"
PURPLE      = "#a855f7"
CYAN        = "#06b6d4"
FEEDBACK_BG = "#1a1400"

_SYS = platform.system()
if _SYS == "Darwin":
    _FF, _FM = "SF Pro Text", "Menlo"
elif _SYS == "Windows":
    _FF, _FM = "Segoe UI", "Consolas"
else:
    _FF, _FM = "DejaVu Sans", "DejaVu Sans Mono"

FONT_TITLE = (_FF, 20, "bold")
FONT_HDR   = (_FF, 12, "bold")
FONT_BODY  = (_FF, 11)
FONT_SMALL = (_FF, 10)
FONT_MONO  = (_FM, 10)
FONT_BTN   = (_FF, 11, "bold")

def _mk_btn(parent, **kw):
    """Wrapper around tk.Button that fixes macOS active-state highlight."""
    bg = kw.get("bg", PANEL)
    fg = kw.get("fg", TEXT)
    kw.setdefault("activebackground", bg)
    kw.setdefault("activeforeground", fg)
    kw.setdefault("highlightthickness", 0)
    kw.setdefault("overrelief", "flat")
    return tk.Button(parent, **kw)



# ====================== PROMPTS ======================

TOPIC_PROMPT = """
You are a nursing education specialist.
Analyze the following nursing quiz questions and identify the primary clinical topic.
Return ONLY valid JSON:
{
  "main_topic": "Heart Failure",
  "subtopics": ["fluid management", "diuretics", "cardiac output"],
  "nursing_category": "Cardiovascular"
}
"""

STUDY_MATERIAL_PROMPT = """
You are an expert nursing professor creating exam prep material for NCLEX and KAPLAN.

CRITICAL INSTRUCTION: Pathophysiology is the foundation of ALL clinical reasoning. Your professor and the NCLEX both expect deep pathophysiology understanding. Treat it as the most important section — be thorough, mechanistic, and specific.

Use EXACTLY this structure:

## PATHOPHYSIOLOGY / MECHANISM  ⬅ MOST IMPORTANT SECTION
Provide a detailed, step-by-step mechanistic explanation. Use cause -> effect -> compensation -> decompensation chains. Explain WHAT happens at the cellular/organ level and WHY it causes the clinical signs the nurse sees. Do not be superficial here.

## BIG PICTURE
2-3 sentences: where does this condition fit in nursing practice and why does it matter?

## KEY ASSESSMENT FINDINGS
Critical signs, symptoms, and lab values in priority order. Flag LIFE-THREATENING findings clearly.

## PRIORITY NURSING INTERVENTIONS
Numbered, in priority order using ABCs/Maslow. Explain WHY each intervention is that priority.

## MEDICATIONS TO KNOW
For each drug: Name (Brand) | Class | Mechanism | Key Nursing Considerations | What to monitor

## NCLEX HIGH-YIELD FACTS
- Most testable, frequently-appearing exam facts
- Normal lab values and critical values
- NCLEX buzzwords and trigger phrases

## COMMON DISTRACTORS & TRAPS
What wrong answers do students pick and exactly WHY they are incorrect?

## DELEGATION & SAFETY
RN vs LPN/LVN vs UAP scope. Priority safety concerns.

## BLOOM'S TAXONOMY BREAKDOWN
Show how this topic maps to each cognitive level. Be specific — not generic.

**REMEMBER (Level 1 — What to memorize):**
Key facts, definitions, normal values, drug names. These are floor-level knowledge.

**UNDERSTAND (Level 2 — Explain in your own words):**
What is the mechanism? Why does this happen? Explain cause and effect.

**APPLY (Level 3 — Use it at the bedside):**
Given a patient scenario, what would you do? How does the knowledge translate to action?

**ANALYZE (Level 4 — Break down the question):**
How do you recognize what the question is really asking? What cues signal priority? How do you eliminate distractors?

**EVALUATE (Level 5 — Clinical judgment):**
How do you decide which intervention is BEST when multiple options seem correct? What criteria do you use?
"""

QUIZ_PROMPT = """
You are an expert NCLEX/KAPLAN exam writer.
Generate the requested number of rigorous, clinical-judgment-focused nursing exam questions on the given topic.

Rules:
- All questions must be scenario-based (not simple recall)
- Distractors must be realistic and plausible
- Mix: priority, delegation, assessment vs intervention, pharmacology, teaching questions
- Each rationale must explain why correct is right AND why main distractors are wrong
- Approximately 25% of questions should be SATA (Select All That Apply)

For EACH question include:
- "type": "MC" for multiple choice OR "SATA" for select all that apply
- "bloom_level": one of "Remember", "Understand", "Apply", "Analyze", "Evaluate"
- "bloom_approach": 1-2 sentences telling the student HOW to think through this question

MC questions: "correct" is a single letter string. Options A-D only.
SATA questions: "correct" is a JSON array of letters e.g. ["A","C","E"]. Options A-E (five options).
For SATA, begin the question stem with "Select all that apply."

Aim for mostly Apply, Analyze, and Evaluate — that is what NCLEX tests.

Return ONLY valid JSON:
{
  "questions": [
    {
      "id": 1,
      "type": "MC",
      "question": "A nurse is caring for a 68-year-old client admitted with...",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct": "B",
      "bloom_level": "Analyze",
      "bloom_approach": "Break down the clinical picture first — what is the underlying mechanism here?",
      "rationale": "B is correct because... A is incorrect because... C is incorrect because... D is incorrect because..."
    },
    {
      "id": 2,
      "type": "SATA",
      "question": "The nurse is assessing a client with... Select all that apply.",
      "options": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
      "correct": ["A", "C", "E"],
      "bloom_level": "Apply",
      "bloom_approach": "Evaluate each option independently — ask yourself if this option alone is true for this condition.",
      "rationale": "A is correct because... B is incorrect because... C is correct because... D is incorrect because... E is correct because..."
    }
  ]
}
"""

REMEDIATION_PROMPT = """
You are a nursing professor giving personalized feedback to a student who answered an NCLEX question incorrectly.
Be encouraging, clear, and exam-focused.

Structure your response:
1. WHY the correct answer is right — use clinical reasoning
2. WHY the student's choice was wrong — address the specific misconception
3. KEY CONCEPT to remember — one clear takeaway

Use specific nursing terminology. Keep it focused and actionable.
"""

REQUIZ_PROMPT = """
You are an expert NCLEX/KAPLAN exam writer.
A nursing student struggled with certain questions. Generate exactly 5 NEW practice questions testing the same concepts from completely different clinical scenarios.

Do NOT reuse the same scenarios, patient presentations, or wording.
Same difficulty level as the originals.
Include approximately 25% SATA (Select All That Apply) questions.

For EACH question include:
- "type": "MC" for multiple choice OR "SATA" for select all that apply
- "bloom_level": one of "Remember", "Understand", "Apply", "Analyze", "Evaluate"

MC: "correct" is a single letter string. Options A-D only.
SATA: "correct" is a JSON array of letters e.g. ["A","C"]. Options A-E (five options).
For SATA, begin the question stem with "Select all that apply."

Return ONLY valid JSON:
{
  "questions": [
    {
      "id": 1,
      "type": "MC",
      "question": "...",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct": "A",
      "bloom_level": "Apply",
      "rationale": "..."
    }
  ]
}
"""

CHAT_PROMPT = """You are an expert NCLEX nursing tutor in a one-on-one study session.
You have been given the student's current study material as context — use it as your primary reference.
Keep answers concise, clinically accurate, and exam-focused. Use nursing terminology.
When relevant, connect your answer to NCLEX clinical judgment and Bloom's taxonomy thinking.
If the student asks something outside the study material, answer from your nursing expertise.
"""

VISUALS_PROMPT = """
You are an expert nursing professor creating visual study aids for NCLEX preparation.

PATHOPHYSIOLOGY is the centerpiece — make the flow detailed and clinically accurate.
Each step in the pathophysiology chain must show cause and effect clearly.

Generate structured data for visual learning materials. Return ONLY valid JSON:
{
  "pathophysiology_flow": {
    "title": "Pathophysiology of [Topic]",
    "steps": [
      {"step": "Initial Trigger / Cause", "detail": "What starts this process and why"},
      {"step": "Primary Physiologic Change", "detail": "First major body response"},
      {"step": "Compensatory Mechanism", "detail": "How the body tries to compensate"},
      {"step": "Compensation Failure", "detail": "Why compensation eventually fails"},
      {"step": "Cascade Effect", "detail": "What systems are affected downstream"},
      {"step": "Clinical Manifestations", "detail": "What the nurse assesses at the bedside"},
      {"step": "Life-Threatening Complication", "detail": "Critical outcome if untreated"}
    ]
  },
  "medications_table": [
    {
      "name": "Drug Name (Brand)",
      "class": "Drug Class",
      "action": "Mechanism of action",
      "considerations": "Key nursing considerations",
      "monitor": "What to monitor"
    }
  ],
  "lab_values_table": [
    {
      "lab": "Lab Name",
      "normal": "Normal range",
      "critical": "Abnormal value in this condition",
      "significance": "Clinical meaning"
    }
  ],
  "priority_actions": [
    "Action 1 — reason why this is priority",
    "Action 2 — reason why",
    "Action 3 — reason why",
    "Action 4 — reason why",
    "Action 5 — reason why",
    "Action 6 — reason why"
  ],
  "bloom_breakdown": {
    "remember": ["Specific fact 1 to memorize for this topic", "Specific fact 2"],
    "understand": ["Explain this concept in plain language", "Why does X cause Y?"],
    "apply": ["Given a patient with this condition, you would...", "Bedside application example"],
    "analyze": ["How to recognize what an NCLEX question is really asking about this topic", "How to eliminate distractors"],
    "evaluate": ["How to choose the BEST option when multiple seem correct", "Clinical judgment criteria"]
  }
}
"""

MED_DETAIL_PROMPT = """
You are an expert nursing pharmacology professor creating NCLEX study material.
Given a medication, provide detailed clinical information a nursing student needs to know.
Return ONLY valid JSON:
{
  "side_effects": [
    "Most clinically important adverse effect",
    "Second adverse effect",
    "Life-threatening adverse effect if applicable"
  ],
  "contraindications": [
    "Contraindication 1",
    "Contraindication 2"
  ],
  "antidote": "Specific antidote or reversal agent. If none: 'No specific antidote — supportive care'",
  "patient_teaching": [
    "Teaching point 1",
    "Teaching point 2",
    "Teaching point 3"
  ],
  "nclex_tips": [
    "Most commonly tested NCLEX fact about this drug",
    "Common NCLEX trap or distractor related to this drug",
    "Priority nursing assessment before administering this drug"
  ]
}
"""

LAB_DETAIL_PROMPT = """
You are an expert nursing professor specializing in laboratory value interpretation.
Given a lab value in a clinical context, provide detailed NCLEX-focused information.
Return ONLY valid JSON:
{
  "causes_elevated": [
    "Condition or factor that elevates this lab",
    "Second cause of elevation"
  ],
  "causes_decreased": [
    "Condition or factor that decreases this lab",
    "Second cause of decrease"
  ],
  "related_labs": [
    "Related lab to check and why",
    "Second related lab and why"
  ],
  "notify_physician_when": "Specific critical values or trends requiring immediate notification",
  "nursing_interventions": [
    "Priority nursing action for an abnormal result",
    "Second nursing action",
    "Third nursing action"
  ],
  "nclex_tips": [
    "Most commonly tested fact about this lab on NCLEX",
    "Common NCLEX trap related to this lab",
    "Priority action NCLEX expects for a critical value"
  ]
}
"""

# ====================== SCROLL HELPER ======================

def _bind_scroll(widget, canvas):
    """Cross-platform mouse wheel scroll binding."""
    if _SYS == "Darwin":
        widget.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(-1 * e.delta, "units"), add="+")
    elif _SYS == "Windows":
        widget.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"), add="+")
    else:
        widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"), add="+")
        widget.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"), add="+")

# ====================== BROWSER ======================

def _find_chrome():
    sys_name = platform.system()
    if sys_name == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    elif sys_name == "Windows":
        candidates = [
            os.path.join(os.environ.get("PROGRAMFILES", ""),       r"Google\Chrome\Application\chrome.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""),  r"Google\Chrome\Application\chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""),       r"Google\Chrome\Application\chrome.exe"),
        ]
    else:
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None

def init_driver():
    try:
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        if WDM_AVAILABLE:
            service = Service(ChromeDriverManager().install())
        else:
            service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        return driver, None
    except Exception as e:
        return None, str(e)

def extract_question_from_page(driver):
    try:
        driver.switch_to.default_content()
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            driver.switch_to.frame(iframes[0])
        body_text = driver.find_element(By.TAG_NAME, "body").text
        driver.switch_to.default_content()

        start_match = re.search(r"Question\s+\d+\s+of\s+\d+", body_text, re.IGNORECASE)
        end_match   = re.search(r"SUBMIT ANSWER", body_text, re.IGNORECASE)

        if not start_match:
            return None, "No question found on page (missing 'Question X of Y')"

        start = start_match.end()
        end   = end_match.start() if end_match else len(body_text)
        block = body_text[start:end].strip()

        parts = re.split(r'\n\s*[A-D][.\)]\s+', block)
        stem  = parts[0].strip()

        if len(stem) < 20:
            return None, "Question text too short — may not be on a quiz page"

        return stem, None

    except Exception as e:
        driver.switch_to.default_content()
        return None, str(e)

def launch_chromium():
    try:
        chrome_path = _find_chrome()
        if not chrome_path:
            return False
        profile_dir = os.path.join(os.path.expanduser("~"), ".study-bot-profile")
        subprocess.Popen([chrome_path, "--remote-debugging-port=9222",
                          f"--user-data-dir={profile_dir}"])
        return True
    except Exception:
        return False

# ====================== AI ======================

# ── Key-handoff state (thread-safe) ──────────────────────────────────────────
_key_needed_event   = threading.Event()   # background thread signals UI
_key_provided_event = threading.Event()   # UI signals background thread
_new_key_holder     = [None]              # UI places new key here

def get_client():
    return Groq(api_key=API_KEYS[current_key_index])

def call_groq(system_prompt, user_content, json_mode=False, max_tokens=4096, temperature=0.3):
    global current_key_index

    def _attempt():
        client = get_client()
        kwargs = dict(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_content},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    for _ in range(len(API_KEYS)):
        try:
            return _attempt(), None
        except Exception as e:
            err = str(e).lower()
            if any(x in err for x in ["rate limit", "quota", "invalid api key"]):
                current_key_index = (current_key_index + 1) % len(API_KEYS)
            else:
                return None, str(e)

    # All keys exhausted — ask the user for a new one
    _new_key_holder[0] = None
    _key_provided_event.clear()
    _key_needed_event.set()          # wake up the UI polling loop
    _key_provided_event.wait(timeout=300)   # block thread up to 5 minutes

    if _new_key_holder[0]:
        try:
            return _attempt(), None
        except Exception as e:
            return None, str(e)

    return None, "API key exhausted — no new key was provided"

def web_search(topic):
    if not SEARCH_AVAILABLE:
        return ""
    snippets = []
    queries = [
        f"NCLEX {topic} nursing key concepts assessment interventions",
        f"{topic} nursing pathophysiology",
    ]
    try:
        ddgs = DDGS()
        for q in queries:
            results = ddgs.text(q, max_results=3)
            for r in results:
                if r.get("body"):
                    snippets.append(f"{r.get('title', '')}: {r['body']}")
            time.sleep(0.5)
    except Exception:
        pass
    return "\n\n".join(snippets[:5])

def ai_identify_topic(questions):
    content = "Nursing quiz questions:\n\n" + "\n\n".join(f"- {q}" for q in questions)
    raw, err = call_groq(TOPIC_PROMPT, content, json_mode=True, temperature=0)
    if err:
        return None, err
    try:
        return json.loads(raw), None
    except Exception:
        return None, "Could not parse topic response"

def ai_generate_study_material(topic_data, snippets, questions):
    topic = topic_data.get("main_topic", "the topic")
    user_content = f"""
Topic: {topic}
Subtopics: {', '.join(topic_data.get('subtopics', []))}
Nursing Category: {topic_data.get('nursing_category', '')}

Questions from the student's quiz:
{chr(10).join(f'- {q}' for q in questions)}
"""
    if snippets:
        user_content += f"\n\nSupplementary reference material:\n{snippets}"
    return call_groq(STUDY_MATERIAL_PROMPT, user_content,
                     json_mode=False, max_tokens=4096, temperature=0.2)

def ai_generate_quiz(topic_data, study_material, n=10):
    topic = topic_data.get("main_topic", "the topic")
    user_content = f"""
Topic: {topic}
Subtopics: {', '.join(topic_data.get('subtopics', []))}

Study material context:
{study_material[:1500] if study_material else ''}

Generate exactly {n} NCLEX-style questions on this topic.
"""
    raw, err = call_groq(QUIZ_PROMPT, user_content, json_mode=True, temperature=0.5)
    if err:
        return None, err
    try:
        questions = json.loads(raw).get("questions", [])
        for q in questions:
            if q.get("type") == "SATA":
                c = q.get("correct", [])
                if isinstance(c, str):
                    q["correct"] = [x.strip() for x in c.replace(",", " ").split() if x.strip()]
        return questions, None
    except Exception:
        return None, "Could not parse quiz response"

def ai_chat(history, study_context, topic):
    system = (CHAT_PROMPT +
              f"\n\nCurrent topic: {topic}\n\nStudy material:\n{study_context[:2500]}")
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system}] + history,
            max_tokens=1024,
            temperature=0.4,
        )
        return resp.choices[0].message.content or "", None
    except Exception as e:
        return None, str(e)

def ai_generate_visuals(topic_data, study_material):
    topic = topic_data.get("main_topic", "the topic")
    user_content = f"""
Topic: {topic}
Subtopics: {', '.join(topic_data.get('subtopics', []))}
Nursing Category: {topic_data.get('nursing_category', '')}

Study material for context:
{study_material[:2000] if study_material else ''}

Generate visual study aid data for this topic.
"""
    raw, err = call_groq(VISUALS_PROMPT, user_content, json_mode=True,
                         max_tokens=2048, temperature=0.2)
    if err:
        return None, err
    try:
        return json.loads(raw), None
    except Exception:
        return None, "Could not parse visuals response"

def ai_med_detail(med_data, topic):
    user_content = f"""
Topic context: {topic}
Medication: {med_data.get('name', '')}
Class: {med_data.get('class', '')}
Mechanism: {med_data.get('action', '')}
Key considerations: {med_data.get('considerations', '')}
Monitor: {med_data.get('monitor', '')}
"""
    raw, err = call_groq(MED_DETAIL_PROMPT, user_content, json_mode=True,
                         max_tokens=1024, temperature=0.2)
    if err:
        return None, err
    try:
        return json.loads(raw), None
    except Exception:
        return None, "Could not parse medication detail response"

def ai_lab_detail(lab_data, topic):
    user_content = f"""
Topic context: {topic}
Lab: {lab_data.get('lab', '')}
Normal range: {lab_data.get('normal', '')}
Critical in this condition: {lab_data.get('critical', '')}
Clinical significance: {lab_data.get('significance', '')}
"""
    raw, err = call_groq(LAB_DETAIL_PROMPT, user_content, json_mode=True,
                         max_tokens=1024, temperature=0.2)
    if err:
        return None, err
    try:
        return json.loads(raw), None
    except Exception:
        return None, "Could not parse lab detail response"

def ai_remediation(question, options, correct, user_answer, topic):
    if isinstance(correct, list):
        correct_str   = ", ".join(correct)
        correct_block = "\n".join(f"  {l}: {options.get(l,'')}" for l in correct)
        user_content  = f"""
Topic: {topic}
Question type: SATA (Select All That Apply)
Question: {question}
Options:
  A: {options.get('A', '')}
  B: {options.get('B', '')}
  C: {options.get('C', '')}
  D: {options.get('D', '')}
  E: {options.get('E', '')}
Correct answers: {correct_str}
  {correct_block}
Student's answers: {user_answer}
"""
    else:
        user_content = f"""
Topic: {topic}
Question: {question}
Options:
  A: {options.get('A', '')}
  B: {options.get('B', '')}
  C: {options.get('C', '')}
  D: {options.get('D', '')}
Correct answer: {correct} — {options.get(correct, '')}
Student's answer: {user_answer} — {options.get(user_answer, '')}
"""
    return call_groq(REMEDIATION_PROMPT, user_content, json_mode=False, temperature=0.3)

def ai_requiz(topic, missed):
    def _correct_str(m):
        c = m["correct"]
        if isinstance(c, list):
            return ", ".join(c)
        return f"{c} — {m['options'].get(c, '')}"
    missed_summary = "\n".join(
        f"- {m['question'][:120]}... (correct: {_correct_str(m)})"
        for m in missed
    )
    user_content = f"""
Topic: {topic}
The student missed these types of questions:
{missed_summary}

Generate 5 new questions on the same concepts from different angles.
"""
    raw, err = call_groq(REQUIZ_PROMPT, user_content, json_mode=True, temperature=0.5)
    if err:
        return None, err
    try:
        questions = json.loads(raw).get("questions", [])
        for q in questions:
            if q.get("type") == "SATA":
                c = q.get("correct", [])
                if isinstance(c, str):
                    q["correct"] = [x.strip() for x in c.replace(",", " ").split() if x.strip()]
        return questions, None
    except Exception:
        return None, "Could not parse requiz response"

# ====================== GLASS TABLE WIDGET ======================

class _MacTable(tk.Frame):
    """Canvas-based table: macOS Aqua glass row hover + clickable animated headers."""
    HDR_H   = 30
    ROW_H   = 28
    SHEEN   = 8          # top highlight strip height on row hover
    HDR_NRM = PANEL      # header normal
    HDR_HOV = "#3d4f6b"  # header hover   (lighter)
    HDR_PRE = "#16263a"  # header pressed (darker = "depressed")
    ROW_EVN = "#1c2d42"  # even row — richer blue than CARD for more pop
    ROW_ODD = "#273d55"  # odd  row — midpoint between CARD and PANEL

    def __init__(self, parent, columns, widths, height_rows=8, **kw):
        kw.setdefault("bg", CARD)
        kw.setdefault("bd", 0)
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", BORDER)
        kw.setdefault("highlightcolor", BORDER)
        super().__init__(parent, **kw)
        self._cols     = columns
        self._widths   = widths
        self._total_w  = sum(widths)
        self._rows     = []
        self._items    = []   # (bg_id, sheen_id, [labels], orig_fill)
        self._hdr_ids  = []   # canvas rect_id per column header cell
        self._hover    = -1
        self._hdr_hov  = -1
        self._click_cb = None

        hsb = tk.Scrollbar(self, orient="horizontal")
        vsb = tk.Scrollbar(self, orient="vertical")
        h_px = self.HDR_H + height_rows * self.ROW_H
        self._c = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0,
                             height=h_px,
                             xscrollcommand=hsb.set,
                             yscrollcommand=vsb.set)
        hsb.config(command=self._c.xview)
        vsb.config(command=self._c.yview)
        self._c.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._right_click_cb  = None
        self._note_click_cb   = None
        self._row_types       = []   # "data" or "note" per canvas row

        self._c.bind("<Motion>",          self._on_motion)
        self._c.bind("<Leave>",           self._on_leave)
        self._c.bind("<ButtonPress-1>",   self._on_press)
        self._c.bind("<ButtonRelease-1>", self._on_release)

        self._draw_header()

    # ── public ────────────────────────────────────────────────────────────

    def set_click_cb(self, cb):
        self._click_cb = cb

    def set_right_click_cb(self, cb):
        self._right_click_cb = cb

    def set_note_click_cb(self, cb):
        self._note_click_cb = cb

    def add_note_row(self, note_dict):
        # note_dict = {"name": str, "content": str}
        c    = self._c
        i    = len(self._rows)
        self._rows.append(("__NOTE__", note_dict))
        self._row_types.append("note")
        y       = self.HDR_H + i * self.ROW_H
        w       = self._total_w
        NOTE_BG = "#1c1400"
        label   = note_dict.get("name", "") if isinstance(note_dict, dict) else str(note_dict)

        bg_id    = c.create_rectangle(0, y, w, y + self.ROW_H, fill=NOTE_BG, outline="")
        sheen_id = c.create_rectangle(0, y, w, y + self.SHEEN,
                                       fill=NOTE_BG, outline="", state="hidden")
        c.create_line(0, y + self.ROW_H - 1, w, y + self.ROW_H - 1,
                      fill=BORDER, width=1)
        lbl = tk.Label(c, text=f"  ✏  {label}",
                       font=(_FF, 10, "italic"),
                       bg=NOTE_BG, fg="#fbbf24", anchor="w", padx=8,
                       cursor="hand2", bd=0, highlightthickness=0)
        c.create_window(0, y, window=lbl, anchor="nw", width=w, height=self.ROW_H)
        lbl.bind("<ButtonRelease-1>", lambda e, ri=i: self._fire_note_click(ri))
        lbl.bind("<ButtonRelease-3>", lambda e, ri=i: self._fire_right_click(ri, e))
        self._items.append((bg_id, sheen_id, [lbl], NOTE_BG))
        c.configure(scrollregion=(0, 0, w,
                                   self.HDR_H + len(self._rows) * self.ROW_H + 2))

    def add_row(self, values):
        c    = self._c
        i    = len(self._rows)
        self._rows.append(values)
        self._row_types.append("data")
        y    = self.HDR_H + i * self.ROW_H
        orig = self.ROW_EVN if i % 2 == 0 else self.ROW_ODD
        w    = self._total_w

        bg_id    = c.create_rectangle(0, y, w, y + self.ROW_H,
                                       fill=orig, outline="")
        sheen_id = c.create_rectangle(0, y, w, y + self.SHEEN,
                                       fill="#60a5fa", outline="", state="hidden")
        c.create_line(0, y + self.ROW_H - 1, w, y + self.ROW_H - 1,
                      fill=BORDER, width=1)

        labels = []
        x = 0
        for val, cw in zip(values, self._widths):
            lbl = tk.Label(c, text=str(val), font=FONT_BODY,
                           bg=orig, fg=TEXT, anchor="w", padx=8,
                           bd=0, highlightthickness=0)
            c.create_window(x, y, window=lbl, anchor="nw",
                            width=cw, height=self.ROW_H)
            lbl.bind("<Motion>",           lambda e, ri=i: self._set_hover_row(ri))
            lbl.bind("<Leave>",            self._on_leave)
            lbl.bind("<ButtonRelease-1>",  lambda e, ri=i: self._fire_click(ri))
            lbl.bind("<ButtonRelease-3>",  lambda e, ri=i: self._fire_right_click(ri, e))
            labels.append(lbl)
            x += cw

        self._items.append((bg_id, sheen_id, labels, orig))
        c.configure(scrollregion=(0, 0, w,
                                   self.HDR_H + len(self._rows) * self.ROW_H + 2))

    # ── internal ──────────────────────────────────────────────────────────

    def _draw_header(self):
        c = self._c
        w = self._total_w
        # top sheen line across full header (gives "raised" 3-D feel)
        c.create_line(0, 1, w, 1, fill="#4a6080", width=1)
        x = 0
        for col, cw in zip(self._cols, self._widths):
            rid = c.create_rectangle(x, 0, x + cw, self.HDR_H,
                                      fill=self.HDR_NRM, outline="")
            c.create_text(x + 8, self.HDR_H // 2, text=col,
                          anchor="w", fill=TEXT,
                          font=(_FF, 9, "bold"))
            self._hdr_ids.append(rid)
            x += cw
            if col != self._cols[-1]:
                c.create_line(x - 1, 4, x - 1, self.HDR_H - 4,
                              fill=BORDER, width=1)
        c.create_line(0, self.HDR_H, w, self.HDR_H, fill=BORDER, width=2)
        c.configure(scrollregion=(0, 0, w, self.HDR_H))

    def _col_at(self, ex):
        x = int(self._c.canvasx(ex))
        pos = 0
        for i, cw in enumerate(self._widths):
            if pos <= x < pos + cw:
                return i
            pos += cw
        return -1

    def _row_from_y(self, cy):
        y = int(self._c.canvasy(cy))
        if y < self.HDR_H:
            return -1
        r = (y - self.HDR_H) // self.ROW_H
        return r if 0 <= r < len(self._rows) else -1

    def _set_hover_row(self, row):
        if row == self._hover:
            return
        self._set_hover(self._hover, False)
        self._hover = row
        self._set_hover(row, True)

    def _set_hover(self, i, on):
        if not (0 <= i < len(self._items)):
            return
        bg_id, sheen_id, labels, orig = self._items[i]
        if on:
            self._c.itemconfig(bg_id,    fill="#1e40af")
            self._c.itemconfig(sheen_id, state="normal")
            for lbl in labels:
                lbl.configure(bg="#1e40af", fg="white")
        else:
            self._c.itemconfig(bg_id,    fill=orig)
            self._c.itemconfig(sheen_id, state="hidden")
            for lbl in labels:
                lbl.configure(bg=orig, fg=TEXT)

    def _set_hdr_hover(self, col):
        if col == self._hdr_hov:
            return
        if self._hdr_hov >= 0:
            self._c.itemconfig(self._hdr_ids[self._hdr_hov], fill=self.HDR_NRM)
        self._hdr_hov = col
        if col >= 0:
            self._c.itemconfig(self._hdr_ids[col], fill=self.HDR_HOV)

    def _on_motion(self, e):
        cy = int(self._c.canvasy(e.y))
        if cy < self.HDR_H:
            self._set_hdr_hover(self._col_at(e.x))
            self._set_hover(self._hover, False)
            self._hover = -1
        else:
            self._set_hdr_hover(-1)
            self._set_hover_row(self._row_from_y(e.y))

    def _on_press(self, e):
        cy = int(self._c.canvasy(e.y))
        if cy < self.HDR_H:
            col = self._col_at(e.x)
            if col >= 0:
                self._c.itemconfig(self._hdr_ids[col], fill=self.HDR_PRE)

    def _on_release(self, e):
        cy = int(self._c.canvasy(e.y))
        if cy < self.HDR_H:
            col = self._col_at(e.x)
            for i, rid in enumerate(self._hdr_ids):
                self._c.itemconfig(rid,
                    fill=self.HDR_HOV if i == col else self.HDR_NRM)
        else:
            row = self._row_from_y(e.y)
            if row >= 0 and self._click_cb:
                self._click_cb(row)

    def _on_leave(self, e):
        try:
            mx, my = e.widget.winfo_pointerxy()
            fx, fy = self.winfo_rootx(), self.winfo_rooty()
            fw, fh = self.winfo_width(), self.winfo_height()
            if not (fx <= mx < fx + fw and fy <= my < fy + fh):
                self._set_hover(self._hover, False)
                self._hover = -1
                self._set_hdr_hover(-1)
        except Exception:
            pass

    def _fire_click(self, row):
        if self._click_cb and row < len(self._row_types) and self._row_types[row] == "data":
            # translate canvas row → data row index
            data_idx = sum(1 for t in self._row_types[:row + 1] if t == "data") - 1
            self._click_cb(data_idx)

    def _fire_note_click(self, canvas_row):
        if not self._note_click_cb:
            return
        preceding = [t for t in self._row_types[:canvas_row] if t == "data"]
        if not preceding:
            return
        data_idx = len(preceding) - 1
        self._note_click_cb(data_idx)

    def _fire_right_click(self, canvas_row, event):
        if not self._right_click_cb:
            return
        if canvas_row < 0 or canvas_row >= len(self._row_types):
            return
        row_type = self._row_types[canvas_row]
        if row_type == "note":
            preceding = [t for t in self._row_types[:canvas_row] if t == "data"]
            if not preceding:
                return
            data_idx = len(preceding) - 1
        else:
            data_idx = sum(1 for t in self._row_types[:canvas_row + 1] if t == "data") - 1
        rx = event.widget.winfo_rootx() + event.x
        ry = event.widget.winfo_rooty() + event.y
        self._right_click_cb(data_idx, rx, ry)


DRUG_CARD_PROMPT = """\
You are an expert NCLEX pharmacology tutor. When given a drug name (which may be a generic \
name, brand name, or abbreviation), generate a concise high-yield drug reference card.

Start your response with these two lines EXACTLY:
## DRUG: Generic Name (Brand Name)
## CATEGORY: <best matching category>

For the CATEGORY line, choose the single best match from this list:
Anticoagulants, Antiplatelets, Cardiac, Diuretics, Antihyperlipidemics, Thrombolytics, \
Antibiotics, Antivirals / Antifungals, Analgesics / Opioids, CNS / Seizure, Psychiatric, \
Endocrine / Diabetes, Respiratory, GI, Electrolytes / Reversal, Immunosuppressants

If no common brand name exists, use: ## DRUG: Generic Name

Then include these section headers in order:
## CLASS / MECHANISM
## INDICATIONS
## KEY SIDE EFFECTS & ADVERSE EFFECTS
## NURSING CONSIDERATIONS
## MONITORING PARAMETERS
## PATIENT EDUCATION
## ANTIDOTE / REVERSAL

If a section does not apply, write "N/A" under that header. \
Keep each section focused and brief — bullet points preferred. \
Use **bold** for the most critical NCLEX-testable facts."""

def ai_drug_card(drug_name):
    return call_groq(DRUG_CARD_PROMPT, f"Drug: {drug_name}",
                     json_mode=False, max_tokens=1200, temperature=0.2)


# ====================== APP ======================

class StudyBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Study Bot — NCLEX Study Assistant")
        self.root.geometry("820x940")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.driver             = None
        self.wq                 = queue.Queue()
        self.questions          = []
        self.topic_data         = None
        self.study_text_content = ""

        self.quiz_qs      = []
        self.quiz_idx     = 0
        self.quiz_score   = 0
        self.quiz_results = []
        self.missed       = []

        self.requiz_qs      = []
        self.requiz_idx     = 0
        self.requiz_score   = 0
        self.requiz_results = []
        self.in_requiz      = False
        self._key_dialog_open = False  # prevent duplicate dialogs

        # References to visuals widgets so we can clear and rebuild them
        self._patho_canvas_widget = None
        self._patho_fig           = None
        self._visuals_inner       = None
        self._current_meds        = []
        self._current_labs        = []
        self._current_actions     = []
        self._visuals_data        = {}
        self._session_file        = None
        self.quiz_length_var      = tk.IntVar(value=10)
        self.chat_history         = []
        self._study_sections      = {}
        self._study_highlights    = set()
        self._highlight_mode      = False
        self._table_notes         = {"meds": {}, "labs": {}}
        self._drug_cache          = self._load_drug_cache()
        self._drug_custom         = self._load_drug_custom()
        self._drug_categories_map = self._load_drug_categories_map()
        self._drug_search_var     = tk.StringVar()
        self._drug_search_var.trace_add("write", lambda *_: self._filter_drugs())

        self._apply_styles()
        self._build_ui()
        self.root.after(150, self._poll_queue)

    # ==================== STYLES ====================

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TNotebook",
            background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("TNotebook.Tab",
            background=CARD, foreground=MUTED,
            padding=[14, 8], font=FONT_BTN, borderwidth=0)
        style.map("TNotebook.Tab",
            background=[("selected", BLUE), ("active", PANEL)],
            foreground=[("selected", TEXT),  ("active", TEXT)])

        style.configure("TProgressbar",
            background=BLUE, troughcolor=PANEL,
            borderwidth=0, thickness=10,
            darkcolor=BLUE, lightcolor=BLUE)

        # Dark treeview for tables
        style.configure("Dark.Treeview",
            background=CARD, foreground=TEXT,
            fieldbackground=CARD, rowheight=30,
            font=FONT_BODY, borderwidth=0)
        style.configure("Dark.Treeview.Heading",
            background=PANEL, foreground=TEXT,
            font=(_FF, 10, "bold"), relief="flat")
        style.map("Dark.Treeview",
            background=[("selected", BLUE)],
            foreground=[("selected", TEXT)])

    # ==================== HELPERS ====================

    def _btn(self, parent, text, cmd, color=BLUE, state="normal", width=None, small=False):
        font   = (_FF, 10, "bold") if small else FONT_BTN
        height = 1 if small else 2
        kw = dict(
            text=text, command=cmd, font=font,
            bg=color, fg=TEXT, relief="flat", cursor="hand2",
            activebackground=color, activeforeground=TEXT,
            highlightthickness=0, overrelief="flat",
            height=height, state=state, bd=0, padx=14,
        )
        if width:
            kw["width"] = width
        b = _mk_btn(parent, **kw)

        def _lighten(c):
            r  = min(255, int(c[1:3], 16) + 30)
            g  = min(255, int(c[3:5], 16) + 30)
            b2 = min(255, int(c[5:7], 16) + 30)
            return f"#{r:02x}{g:02x}{b2:02x}"

        b.bind("<Enter>", lambda e: b.config(bg=_lighten(color)))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    def _text_area(self, parent, height=8, font=FONT_MONO, bg=CARD):
        return scrolledtext.ScrolledText(
            parent, font=font, wrap="word", height=height,
            bd=0, relief="flat", bg=bg, fg=TEXT,
            insertbackground=TEXT, selectbackground=BLUE,
            selectforeground=TEXT, padx=14, pady=10,
            state="disabled",
        )

    def _section_label(self, parent, text, color=MUTED):
        tk.Label(parent, text=text, font=(_FF, 9, "bold"),
                 bg=BG, fg=color).pack(padx=16, anchor="w", pady=(10, 3))

    def _make_scrollable_frame(self, parent):
        """Returns a scrollable inner frame. Saves canvas as self._visuals_canvas."""
        outer = tk.Frame(parent, bg=BG)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview,
                           bg=PANEL, troughcolor=CARD, relief="flat", bd=0)
        inner = tk.Frame(canvas, bg=BG)

        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.configure(yscrollcommand=vsb.set)

        # Direct bindings on canvas itself (for empty space)
        _bind_scroll(canvas, canvas)

        self._visuals_canvas = canvas

        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        return inner

    def _bind_scroll_recursive(self, widget):
        """Bind scroll events to widget and all descendants so nothing swallows them."""
        canvas = getattr(self, "_visuals_canvas", None)
        if canvas is None:
            return
        try:
            _bind_scroll(widget, canvas)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._bind_scroll_recursive(child)

    # ==================== UI BUILD ====================

    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        tk.Label(hdr, text="STUDY BOT", font=FONT_TITLE, bg=BG, fg=TEXT).pack(side="left")
        tk.Label(hdr, text="NCLEX / KAPLAN Study Assistant",
                 font=FONT_SMALL, bg=BG, fg=MUTED).pack(side="left", padx=(12, 0), pady=(7, 0))

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(8, 10))

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self._tab_questions()   # 0
        self._tab_study()       # 1
        self._tab_visuals()     # 2
        self._tab_drugs()       # 3
        self._tab_quiz()        # 4
        self._tab_results()     # 5
        self._tab_chat()        # 6
        self._tab_sessions()    # 7

    # ---- Tab 0: Questions ----
    def _tab_questions(self):
        outer = tk.Frame(self.nb, bg=BG)
        self.nb.add(outer, text="  Questions  ")

        btn_row = tk.Frame(outer, bg=CARD)
        btn_row.pack(fill="x", padx=14, pady=(14, 0))
        inner = tk.Frame(btn_row, bg=CARD)
        inner.pack(fill="x", padx=10, pady=10)

        self._btn(inner, "Launch Browser",       self._launch_browser,  color=PANEL, small=True).pack(side="left", padx=(0, 6))
        self._btn(inner, "Extract from Browser", self._extract_question, color=BLUE,  small=True).pack(side="left", padx=(0, 6))
        self._btn(inner, "Add Custom Questions", self._custom_dialog,    color=GREEN, small=True).pack(side="left", padx=(0, 6))
        self._btn(inner, "Clear All",            self._clear_questions,  color=RED,   small=True).pack(side="left")

        self.q_status = tk.Label(outer,
            text="No questions yet.  Extract from browser or add manually.",
            font=FONT_SMALL, bg=BG, fg=MUTED)
        self.q_status.pack(padx=16, anchor="w", pady=(8, 0))

        self._section_label(outer, "COLLECTED QUESTIONS")

        list_frame = tk.Frame(outer, bg=CARD)
        list_frame.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        sb = tk.Scrollbar(list_frame, bg=PANEL, troughcolor=CARD, relief="flat", bd=0)
        sb.pack(side="right", fill="y")
        self.q_list = tk.Listbox(
            list_frame, yscrollcommand=sb.set,
            font=FONT_BODY, bg=CARD, fg=TEXT,
            selectbackground=BLUE, selectforeground=TEXT,
            activestyle="none", bd=0, relief="flat", highlightthickness=0,
        )
        self.q_list.pack(fill="both", expand=True, padx=4, pady=4)
        sb.config(command=self.q_list.yview)

        self.gen_btn = self._btn(outer, "Generate Study Material  ->",
                                  self._generate_study, color=ORANGE, state="disabled")
        self.gen_btn.pack(fill="x", padx=14, pady=(0, 14))

    # ---- Tab 1: Study Material ----
    def _tab_study(self):
        outer = tk.Frame(self.nb, bg=BG)
        self.nb.add(outer, text="  Study Material  ")

        hdr = tk.Frame(outer, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14, 6))
        self.topic_lbl = tk.Label(hdr, text="Topic: —", font=FONT_HDR, bg=BG, fg=TEXT)
        self.topic_lbl.pack(side="left")
        self._btn(hdr, "Save", self._save_study, color=PANEL, small=True).pack(side="right", padx=(6, 0))
        self.collapse_btn = self._btn(hdr, "Collapse All", self._toggle_collapse_all,
                                       color=PANEL, small=True)
        self.collapse_btn.pack(side="right", padx=(0, 6))
        self.highlight_btn = self._btn(hdr, "Highlight", self._toggle_highlight_mode,
                                        color=PANEL, small=True)
        self.highlight_btn.pack(side="right", padx=(0, 6))
        self._btn(hdr, "Find  Ctrl+F", self._open_study_search,
                  color=PANEL, small=True).pack(side="right", padx=(0, 6))
        self.study_status_lbl = tk.Label(hdr, text="", font=FONT_SMALL, bg=BG, fg=ORANGE)
        self.study_status_lbl.pack(side="right")

        self.study_box = self._text_area(outer, height=32, font=FONT_MONO, bg=CARD)
        self.study_box.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        self.study_box.bind("<Control-f>", lambda e: self._open_study_search())

        # ── search bar (hidden until opened) ──
        self._study_search_frame = tk.Frame(outer, bg=PANEL)
        self._study_search_var   = tk.StringVar()
        self._study_search_matches = []
        self._study_search_idx     = 0
        tk.Label(self._study_search_frame, text="  Find:", font=FONT_SMALL,
                 bg=PANEL, fg=TEXT).pack(side="left")
        self._study_search_entry = tk.Entry(
            self._study_search_frame, textvariable=self._study_search_var,
            font=FONT_BODY, bg=CARD, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=0, width=28)
        self._study_search_entry.pack(side="left", padx=6, pady=5, ipady=4)
        self._study_search_entry.bind("<Return>",   lambda e: self._study_search_next())
        self._study_search_entry.bind("<Escape>",   lambda e: self._close_study_search())
        self._study_search_var.trace_add("write", lambda *_: self._do_study_search())
        self._study_search_lbl = tk.Label(self._study_search_frame, text="",
                                           font=FONT_SMALL, bg=PANEL, fg=MUTED)
        self._study_search_lbl.pack(side="left")
        self._btn(self._study_search_frame, "Next",  self._study_search_next,
                  color=BLUE, small=True).pack(side="left", padx=(6, 2))
        self._btn(self._study_search_frame, "Prev",  self._study_search_prev,
                  color=BLUE, small=True).pack(side="left", padx=(0, 6))
        self._btn(self._study_search_frame, "Close", self._close_study_search,
                  color=PANEL, small=True).pack(side="left")

        len_row = tk.Frame(outer, bg=BG)
        len_row.pack(fill="x", padx=14, pady=(0, 4))
        tk.Label(len_row, text="Quiz length:", font=FONT_SMALL,
                 bg=BG, fg=MUTED).pack(side="left")
        for n in (5, 10, 15, 20):
            tk.Radiobutton(len_row, text=str(n), variable=self.quiz_length_var, value=n,
                           font=FONT_SMALL, bg=BG, fg=TEXT, selectcolor=PANEL,
                           activebackground=BG, activeforeground=TEXT,
                           highlightthickness=0).pack(side="left", padx=8)

        self.quiz_start_btn = self._btn(outer, "Start Quiz  ->",
                                         self._start_quiz, color=PURPLE, state="disabled")
        self.quiz_start_btn.pack(fill="x", padx=14, pady=(0, 14))

    # ---- Tab 2: Visuals & Tables ----
    def _tab_visuals(self):
        outer = tk.Frame(self.nb, bg=BG)
        self.nb.add(outer, text="  Visuals & Tables  ")

        hdr = tk.Frame(outer, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14, 4))

        self.visuals_status_lbl = tk.Label(hdr,
            text="Generate study material first to populate visuals.",
            font=FONT_SMALL, bg=BG, fg=MUTED)
        self.visuals_status_lbl.pack(side="left")

        self.visuals_regen_btn = _mk_btn(hdr, text="↻  Rebuild Visuals",
            font=FONT_SMALL, bg=PANEL, fg=TEXT, relief="flat", bd=0,
            activebackground=BLUE, activeforeground=TEXT, cursor="hand2",
            padx=10, pady=3, command=self._regenerate_visuals)
        # hidden until study material is loaded without visuals

        self._visuals_scroll_outer = outer
        self._visuals_inner = self._make_scrollable_frame(outer)

    # ---- Tab 3: Drugs ----
    def _tab_drugs(self):
        outer = tk.Frame(self.nb, bg=BG)
        self.nb.add(outer, text="  Drugs  ")

        # ── top bar ──
        top = tk.Frame(outer, bg=BG)
        top.pack(fill="x", padx=14, pady=(14, 6))
        tk.Label(top, text="Drug Reference", font=FONT_HDR, bg=BG, fg=TEXT).pack(side="left")
        self._btn(top, "+ Add Drug", self._drug_add, color=GREEN, small=True).pack(side="right")
        self._btn(top, "Delete", self._drug_delete, color=RED, small=True).pack(side="right", padx=(0, 6))

        # ── category filter + search ──
        filter_row = tk.Frame(outer, bg=CARD)
        filter_row.pack(fill="x", padx=14, pady=(0, 0))
        tk.Label(filter_row, text="  Category:", font=FONT_SMALL, bg=CARD, fg=MUTED).pack(side="left")
        self._drug_category_var = tk.StringVar(value="All")
        cat_choices = ["All"] + list(DRUG_CATEGORIES.keys())
        cat_menu = tk.OptionMenu(filter_row, self._drug_category_var, *cat_choices,
                                  command=lambda _: self._filter_drugs())
        cat_menu.config(font=FONT_SMALL, bg=PANEL, fg=TEXT, activebackground=BLUE,
                        activeforeground=TEXT, relief="flat", bd=0,
                        highlightthickness=0, indicatoron=True)
        cat_menu["menu"].config(font=FONT_SMALL, bg=PANEL, fg=TEXT,
                                 activebackground=BLUE, activeforeground=TEXT, bd=0)
        cat_menu.pack(side="left", padx=6, pady=4)

        search_frame = tk.Frame(outer, bg=CARD)
        search_frame.pack(fill="x", padx=14, pady=(0, 6))
        tk.Label(search_frame, text="  Search:", font=FONT_SMALL, bg=CARD, fg=MUTED).pack(side="left")
        tk.Entry(search_frame, textvariable=self._drug_search_var,
                 font=FONT_BODY, bg=PANEL, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=0).pack(side="left", fill="x", expand=True, padx=6, pady=6)

        # ── two-panel body ──
        body = tk.Frame(outer, bg=BG)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # left: drug listbox
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="y", padx=(0, 10))
        sb = tk.Scrollbar(left, orient="vertical", bg=PANEL, troughcolor=BG)
        self.drug_listbox = tk.Listbox(left, yscrollcommand=sb.set,
                                        font=FONT_BODY, bg=CARD, fg=TEXT,
                                        selectbackground=BLUE, selectforeground=TEXT,
                                        relief="flat", bd=0, width=30,
                                        activestyle="none",
                                        highlightthickness=0)
        sb.config(command=self.drug_listbox.yview)
        sb.pack(side="right", fill="y")
        self.drug_listbox.pack(side="left", fill="both", expand=True)
        self.drug_listbox.bind("<<ListboxSelect>>", self._on_drug_select)

        # right: drug card
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self.drug_name_lbl = tk.Label(right, text="Select a drug to view its reference card.",
                                       font=FONT_HDR, bg=BG, fg=MUTED,
                                       anchor="w", padx=4)
        self.drug_name_lbl.pack(fill="x", pady=(0, 6))

        self.drug_status_lbl = tk.Label(right, text="", font=FONT_SMALL,
                                         bg=BG, fg=ORANGE, anchor="w", padx=4)
        self.drug_status_lbl.pack(fill="x")

        card_frame = tk.Frame(right, bg=CARD)
        card_frame.pack(fill="both", expand=True)
        drug_sb = tk.Scrollbar(card_frame, orient="vertical", bg=PANEL, troughcolor=BG)
        self.drug_card_box = tk.Text(card_frame, yscrollcommand=drug_sb.set,
                                      font=FONT_BODY, bg=CARD, fg=TEXT,
                                      relief="flat", bd=0, padx=14, pady=10,
                                      state="disabled", cursor="arrow",
                                      wrap="word", highlightthickness=0)
        drug_sb.config(command=self.drug_card_box.yview)
        drug_sb.pack(side="right", fill="y")
        self.drug_card_box.pack(side="left", fill="both", expand=True)

        self._drug_all_names = []
        self._populate_drug_list()

    def _populate_drug_list(self):
        self.drug_listbox.delete(0, "end")
        self._drug_all_names = []
        for category, drugs in DRUG_CATEGORIES.items():
            for d in drugs:
                self._drug_all_names.append(d)
        for d in self._drug_custom:
            if d not in self._drug_all_names:
                self._drug_all_names.append(d)
        self._drug_all_names.sort(key=lambda x: x.lower())
        for name in self._drug_all_names:
            self.drug_listbox.insert("end", f"  {name}")

    def _filter_drugs(self):
        query    = self._drug_search_var.get().lower().strip()
        category = self._drug_category_var.get() if hasattr(self, "_drug_category_var") else "All"
        self.drug_listbox.delete(0, "end")
        for name in self._drug_all_names:
            if query and query not in name.lower():
                continue
            if category != "All":
                # built-in drugs: check DRUG_CATEGORIES
                in_builtin = name in DRUG_CATEGORIES.get(category, [])
                # custom drugs: check categories map
                in_custom  = self._drug_categories_map.get(name) == category
                if not in_builtin and not in_custom:
                    continue
            self.drug_listbox.insert("end", f"  {name}")

    def _parse_canonical_drug_name(self, card_text):
        for line in card_text.splitlines():
            if line.startswith("## DRUG:"):
                return line[8:].strip()
        return None

    def _parse_drug_category(self, card_text):
        for line in card_text.splitlines():
            if line.startswith("## CATEGORY:"):
                cat = line[12:].strip()
                if cat in DRUG_CATEGORIES:
                    return cat
        return None

    def _on_drug_select(self, event=None):
        sel = self.drug_listbox.curselection()
        if not sel:
            return
        name = self.drug_listbox.get(sel[0]).strip()
        self.drug_name_lbl.config(text=name, fg=TEXT)

        if name in self._drug_cache:
            self._render_drug_card(self._drug_cache[name])
            self.drug_status_lbl.config(text="(cached)")
            return

        self.drug_status_lbl.config(text="Looking up drug info...")
        self._set_drug_card_text("")

        def worker():
            card, err = ai_drug_card(name)
            if err or not card:
                self.wq.put(("drug_card_error", f"Could not load info: {err}"))
                return
            canonical = self._parse_canonical_drug_name(card) or name
            category  = self._parse_drug_category(card)
            self._drug_cache[canonical] = card
            if name != canonical:
                self._drug_cache[name] = card
                if name in self._drug_custom:
                    self._drug_custom.remove(name)
                    if canonical not in self._drug_custom:
                        self._drug_custom.append(canonical)
                # migrate category key
                if name in self._drug_categories_map:
                    self._drug_categories_map.pop(name)
            if category:
                self._drug_categories_map[canonical] = category
            self._save_drugs_file()
            self.wq.put(("drug_card_ready", (canonical, card)))

        threading.Thread(target=worker, daemon=True).start()

    def _render_drug_card(self, text):
        self._set_drug_card_text(text)
        self.drug_status_lbl.config(text="")

    def _set_drug_card_text(self, text):
        import re as _re
        box = self.drug_card_box
        box.config(state="normal")
        box.delete("1.0", "end")

        CARD_COLORS = {
            "CLASS":          "#3b82f6",
            "MECHANISM":      "#3b82f6",
            "INDICATIONS":    "#22c55e",
            "SIDE EFFECTS":   "#ef4444",
            "ADVERSE":        "#ef4444",
            "NURSING":        "#a855f7",
            "MONITORING":     "#f97316",
            "PATIENT":        "#06b6d4",
            "ANTIDOTE":       "#ec4899",
            "REVERSAL":       "#ec4899",
        }

        def hdr_color(title):
            t = title.upper()
            for k, c in CARD_COLORS.items():
                if k in t:
                    return c
            return BLUE

        box.tag_configure("hdr",    font=(_FF, 12, "bold"), spacing1=12, spacing3=4)
        box.tag_configure("bold",   font=(_FF, 11, "bold"), foreground=TEXT)
        box.tag_configure("body",   font=FONT_BODY, foreground=TEXT)
        box.tag_configure("bullet", font=FONT_BODY, foreground=TEXT, lmargin1=20, lmargin2=28)

        if not text:
            box.config(state="disabled")
            return

        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                title = stripped[3:]
                color = hdr_color(title)
                box.tag_configure("hdr", foreground=color)
                box.insert("end", title + "\n", "hdr")
            elif stripped.startswith("- ") or stripped.startswith("* "):
                content = stripped[2:]
                box.insert("end", "  - ", "bullet")
                parts = _re.split(r'(\*\*[^*]+\*\*)', content)
                for p in parts:
                    if p.startswith("**") and p.endswith("**"):
                        box.insert("end", p[2:-2], "bold")
                    else:
                        box.insert("end", p, "bullet")
                box.insert("end", "\n", "bullet")
            else:
                parts = _re.split(r'(\*\*[^*]+\*\*)', line)
                for p in parts:
                    if p.startswith("**") and p.endswith("**"):
                        box.insert("end", p[2:-2], "bold")
                    else:
                        box.insert("end", p, "body")
                box.insert("end", "\n", "body")

        box.config(state="disabled")

    def _drug_add(self):
        name = self._simple_input_dialog("Add Drug", "Enter drug name:")
        if not name:
            return
        name = name.strip()
        if not name:
            return
        if name not in self._drug_custom:
            self._drug_custom.append(name)
            self._save_drug_custom()
        self._populate_drug_list()
        # select the new entry
        for i in range(self.drug_listbox.size()):
            if self.drug_listbox.get(i).strip() == name:
                self.drug_listbox.selection_clear(0, "end")
                self.drug_listbox.selection_set(i)
                self.drug_listbox.see(i)
                self._on_drug_select()
                break

    def _drug_delete(self):
        sel = self.drug_listbox.curselection()
        if not sel:
            return
        name = self.drug_listbox.get(sel[0]).strip()
        if name not in self._drug_custom:
            messagebox.showinfo("Built-in Drug",
                                f'"{name}" is part of the built-in list and cannot be deleted.')
            return
        if messagebox.askyesno("Delete Drug", f'Remove "{name}" from your custom list?'):
            self._drug_custom.remove(name)
            self._save_drug_custom()
            if name in self._drug_cache:
                del self._drug_cache[name]
                self._save_drug_cache()
            self._populate_drug_list()
            self.drug_name_lbl.config(text="Select a drug to view its reference card.", fg=MUTED)
            self._set_drug_card_text("")

    def _simple_input_dialog(self, title, prompt):
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.config(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()
        tk.Label(dlg, text=prompt, font=FONT_BODY, bg=BG, fg=TEXT,
                 padx=16, pady=12).pack(anchor="w")
        var = tk.StringVar()
        entry = tk.Entry(dlg, textvariable=var, font=FONT_BODY,
                         bg=PANEL, fg=TEXT, insertbackground=TEXT,
                         relief="flat", bd=0, width=36)
        entry.pack(padx=16, pady=(0, 10), ipady=6)
        entry.focus_set()
        result = [None]
        def ok(e=None):
            result[0] = var.get()
            dlg.destroy()
        def cancel(e=None):
            dlg.destroy()
        btn_row = tk.Frame(dlg, bg=BG)
        btn_row.pack(fill="x", padx=16, pady=(0, 12))
        self._btn(btn_row, "OK", ok, color=BLUE, small=True).pack(side="left")
        self._btn(btn_row, "Cancel", cancel, color=PANEL, small=True).pack(side="left", padx=8)
        entry.bind("<Return>", ok)
        entry.bind("<Escape>", cancel)
        dlg.wait_window()
        return result[0]

    def _load_drug_cache(self):
        try:
            with open(DRUGS_FILE, encoding="utf-8") as f:
                return json.load(f).get("cache", {})
        except Exception:
            return {}

    def _load_drug_custom(self):
        try:
            with open(DRUGS_FILE, encoding="utf-8") as f:
                return json.load(f).get("custom", [])
        except Exception:
            return []

    def _load_drug_categories_map(self):
        try:
            with open(DRUGS_FILE, encoding="utf-8") as f:
                return json.load(f).get("categories", {})
        except Exception:
            return {}

    def _save_drug_cache(self):
        self._save_drugs_file()

    def _save_drug_custom(self):
        self._save_drugs_file()

    def _save_drugs_file(self):
        try:
            with open(DRUGS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "cache":      self._drug_cache,
                    "custom":     self._drug_custom,
                    "categories": self._drug_categories_map,
                }, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # ---- Tab 4: Quiz ----
    def _tab_quiz(self):
        outer = tk.Frame(self.nb, bg=BG)
        self.nb.add(outer, text="  Quiz  ")

        prog_card = tk.Frame(outer, bg=CARD)
        prog_card.pack(fill="x", padx=14, pady=(14, 0))
        prog_inner = tk.Frame(prog_card, bg=CARD)
        prog_inner.pack(fill="x", padx=14, pady=10)
        self.q_num_lbl = tk.Label(prog_inner, text="Question — / —",
                                   font=FONT_HDR, bg=CARD, fg=TEXT)
        self.q_num_lbl.pack(side="left")
        self.score_lbl = tk.Label(prog_inner, text="Score: 0",
                                   font=FONT_HDR, bg=CARD, fg=GREEN)
        self.score_lbl.pack(side="right")

        self.quiz_prog = ttk.Progressbar(outer, orient="horizontal",
                                          mode="determinate", maximum=10)
        self.quiz_prog.pack(fill="x", padx=14, pady=(4, 10))

        # Bloom's level indicator
        bloom_row = tk.Frame(outer, bg=BG)
        bloom_row.pack(fill="x", padx=14, pady=(0, 4))
        self.bloom_badge = tk.Label(bloom_row, text="",
                                     font=(_FF, 9, "bold"),
                                     bg=PANEL, fg=TEXT, padx=10, pady=4)
        self.bloom_badge.pack(side="left")
        self.bloom_approach_lbl = tk.Label(bloom_row, text="",
                                            font=(_FF, 9, "italic"),
                                            bg=BG, fg=MUTED,
                                            wraplength=580, justify="left", padx=10)
        self.bloom_approach_lbl.pack(side="left", fill="x", expand=True)

        q_card = tk.Frame(outer, bg=CARD)
        q_card.pack(fill="x", padx=14, pady=(0, 8))
        self.quiz_q_lbl = tk.Label(q_card,
            text="Complete study material and start the quiz.",
            font=FONT_BODY, bg=CARD, fg=TEXT,
            wraplength=740, justify="left", anchor="nw",
            padx=14, pady=14)
        self.quiz_q_lbl.pack(fill="x")

        self._section_label(outer, "SELECT YOUR ANSWER")
        opts_card = tk.Frame(outer, bg=CARD)
        opts_card.pack(fill="x", padx=14, pady=(0, 8))

        # MC frame (flat toggle buttons, A-D)
        self.mc_frame   = tk.Frame(opts_card, bg=CARD)
        self.mc_frame.pack(fill="x")
        self.answer_var = tk.StringVar()
        self.opt_btns   = {}
        for letter in "ABCD":
            btn = _mk_btn(
                self.mc_frame, text=f"  {letter}.  ", font=FONT_BODY,
                bg=PANEL, fg=TEXT, relief="flat", bd=0,
                activebackground=BLUE, activeforeground=TEXT,
                anchor="w", justify="left",
                highlightthickness=0, state="disabled",
                command=lambda l=letter: self._select_mc(l),
            )
            btn.pack(fill="x", padx=14, pady=3)
            self.opt_btns[letter] = btn

        # SATA frame (flat toggle buttons, A-E) — hidden until a SATA question loads
        self.sata_frame = tk.Frame(opts_card, bg=CARD)
        tk.Label(self.sata_frame, text="  Select ALL that apply:",
                 font=(_FF, 9, "italic"), bg=CARD, fg=ORANGE,
                 padx=14, pady=4).pack(anchor="w")
        self.sata_vars = {}
        self.sata_btns = {}
        for letter in "ABCDE":
            var = tk.BooleanVar(value=False)
            btn = _mk_btn(
                self.sata_frame, text=f"  {letter}.  ", font=FONT_BODY,
                bg=PANEL, fg=TEXT, relief="flat", bd=0,
                activebackground=BLUE, activeforeground=TEXT,
                anchor="w", justify="left",
                highlightthickness=0, state="disabled",
                command=lambda l=letter: self._toggle_sata(l),
            )
            btn.pack(fill="x", padx=14, pady=3)
            self.sata_vars[letter] = var
            self.sata_btns[letter] = btn

        self.submit_btn = self._btn(outer, "Submit Answer",
                                     self._submit_answer, color=BLUE, state="disabled")
        self.submit_btn.pack(fill="x", padx=14, pady=(0, 6))

        self._section_label(outer, "FEEDBACK")
        self.feedback_box = self._text_area(outer, height=6,
                                             font=FONT_BODY, bg=FEEDBACK_BG)
        self.feedback_box.pack(fill="x", padx=14, pady=(0, 6))

        self.next_btn = self._btn(outer, "Next Question  ->",
                                   self._next_question, color=GREEN, state="disabled")
        self.next_btn.pack(fill="x", padx=14, pady=(0, 14))

    # ---- Tab 4: Results & Review ----
    def _tab_results(self):
        outer = tk.Frame(self.nb, bg=BG)
        self.nb.add(outer, text="  Results & Review  ")

        res_card = tk.Frame(outer, bg=CARD)
        res_card.pack(fill="x", padx=14, pady=(14, 6))
        res_inner = tk.Frame(res_card, bg=CARD)
        res_inner.pack(fill="x", padx=14, pady=10)
        self.results_lbl = tk.Label(res_inner,
            text="Finish the quiz to see your results.",
            font=FONT_HDR, bg=CARD, fg=TEXT)
        self.results_lbl.pack(side="left")
        self._btn(res_inner, "Progress Chart", self._open_progress_chart,
                  color=PANEL, small=True).pack(side="right")

        # ── Weak Areas panel ─────────────────────────────────────────────
        self._section_label(outer, "WEAK AREAS — BLOOM'S BREAKDOWN")
        self._weak_frame = tk.Frame(outer, bg=CARD)
        self._weak_frame.pack(fill="x", padx=14, pady=(0, 8))
        tk.Label(self._weak_frame,
                 text="Complete a quiz to see your performance breakdown.",
                 font=FONT_SMALL, bg=CARD, fg=MUTED, padx=14, pady=10
                 ).pack(anchor="w")

        self._section_label(outer, "DETAILED REVIEW")
        self.review_box = self._text_area(outer, height=20, font=FONT_BODY, bg=CARD)
        self.review_box.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        self.requiz_btn = self._btn(outer, "Re-Quiz Me on Missed Topics  ->",
                                     self._start_requiz, color=RED, state="disabled")
        self.requiz_btn.pack(fill="x", padx=14, pady=(0, 14))

    # ==================== VISUALS RENDERING ====================

    def _clear_visuals(self):
        if self._patho_fig is not None:
            plt.close(self._patho_fig)
            self._patho_fig = None
        for widget in self._visuals_inner.winfo_children():
            widget.destroy()

    def _render_visuals(self, data):
        self._visuals_data = data
        self._clear_visuals()
        inner = self._visuals_inner

        # ── Pathophysiology Flow ──────────────────────────────────────────
        patho = data.get("pathophysiology_flow", {})
        steps = patho.get("steps", [])
        title = patho.get("title", "Pathophysiology")

        tk.Label(inner, text="PATHOPHYSIOLOGY FLOW",
                 font=(_FF, 10, "bold"), bg=BG, fg=CYAN
                 ).pack(padx=16, anchor="w", pady=(12, 4))

        if MATPLOTLIB_AVAILABLE and steps:
            fig = self._draw_patho_chart(steps, title)
            self._patho_fig = fig
            canvas_w = FigureCanvasTkAgg(fig, master=inner)
            canvas_w.draw()
            canvas_w.get_tk_widget().pack(fill="x", padx=14, pady=(0, 14))
            self._patho_canvas_widget = canvas_w
        else:
            # Fallback: text cards
            for i, s in enumerate(steps):
                card = tk.Frame(inner, bg=CARD)
                card.pack(fill="x", padx=14, pady=2)
                badge = tk.Label(card, text=f"  {i+1}  ",
                                  font=(_FF, 10, "bold"),
                                  bg=BLUE, fg=TEXT)
                badge.pack(side="left", fill="y")
                txt = f"{s.get('step','')}  —  {s.get('detail','')}"
                tk.Label(card, text=txt, font=FONT_BODY, bg=CARD, fg=TEXT,
                          anchor="w", padx=10, pady=8,
                          wraplength=660, justify="left").pack(side="left", fill="x")

        # ── Medications Table ─────────────────────────────────────────────
        meds = data.get("medications_table", [])
        self._current_meds = meds
        if meds:
            tk.Label(inner, text="MEDICATIONS TABLE",
                     font=(_FF, 10, "bold"), bg=BG, fg=ORANGE
                     ).pack(padx=16, anchor="w", pady=(10, 4))

            med_table = _MacTable(inner,
                                   columns=("Name", "Class", "Action", "Key Considerations", "Monitor"),
                                   widths=(200, 180, 340, 480, 560),
                                   height_rows=min(len(meds) + 1, 8))
            med_table.pack(fill="x", padx=14, pady=(0, 12))

            for m in meds:
                row_key = m.get("name", "")
                med_table.add_row((
                    row_key, m.get("class", ""),
                    m.get("action", ""), m.get("considerations", ""),
                    m.get("monitor", ""),
                ))
                note = self._table_notes.get("meds", {}).get(row_key)
                if note:
                    med_table.add_note_row(note)

            def on_med_click(i, ml=meds):
                self._open_med_popup(ml[i])
            med_table.set_click_cb(on_med_click)
            med_table.set_right_click_cb(
                lambda di, rx, ry, tbl=med_table, ml=meds:
                self._on_table_right_click("meds", ml, tbl, di, rx, ry))
            med_table.set_note_click_cb(
                lambda di, ml=meds:
                self._on_note_row_click("meds", ml, di))

        # ── Lab Values Table ──────────────────────────────────────────────
        labs = data.get("lab_values_table", [])
        self._current_labs = labs
        if labs:
            tk.Label(inner, text="LAB VALUES REFERENCE",
                     font=(_FF, 10, "bold"), bg=BG, fg=GREEN
                     ).pack(padx=16, anchor="w", pady=(10, 4))

            lab_table = _MacTable(inner,
                                   columns=("Lab", "Normal Range", "Critical in This Condition", "Clinical Significance"),
                                   widths=(160, 200, 320, 560),
                                   height_rows=min(len(labs) + 1, 8))
            lab_table.pack(fill="x", padx=14, pady=(0, 12))

            for lab in labs:
                row_key = lab.get("lab", "")
                lab_table.add_row((
                    row_key, lab.get("normal", ""),
                    lab.get("critical", ""), lab.get("significance", ""),
                ))
                note = self._table_notes.get("labs", {}).get(row_key)
                if note:
                    lab_table.add_note_row(note)

            def on_lab_click(i, ll=labs):
                self._open_lab_popup(ll[i])
            lab_table.set_click_cb(on_lab_click)
            lab_table.set_right_click_cb(
                lambda di, rx, ry, tbl=lab_table, ll=labs:
                self._on_table_right_click("labs", ll, tbl, di, rx, ry))
            lab_table.set_note_click_cb(
                lambda di, ll=labs:
                self._on_note_row_click("labs", ll, di))

        # ── Priority Nursing Actions ──────────────────────────────────────
        actions = data.get("priority_actions", [])
        self._current_actions = actions
        if actions:
            tk.Label(inner, text="PRIORITY NURSING ACTIONS",
                     font=(_FF, 10, "bold"), bg=BG, fg=PURPLE
                     ).pack(padx=16, anchor="w", pady=(10, 4))

            badge_colors = [RED, ORANGE, BLUE, PURPLE, CYAN, GREEN]
            for i, action in enumerate(actions):
                card = tk.Frame(inner, bg=CARD)
                card.pack(fill="x", padx=14, pady=3)
                color = badge_colors[i % len(badge_colors)]
                tk.Label(card, text=f"  {i+1}  ",
                          font=(_FF, 11, "bold"),
                          bg=color, fg=TEXT, padx=6
                          ).pack(side="left", fill="y")
                tk.Label(card, text=action, font=FONT_BODY, bg=CARD, fg=TEXT,
                          anchor="w", padx=12, pady=10,
                          wraplength=680, justify="left"
                          ).pack(side="left", fill="x", expand=True)

        # ── Bloom's Taxonomy Breakdown ────────────────────────────────────
        bloom = data.get("bloom_breakdown", {})
        if bloom:
            tk.Label(inner, text="BLOOM'S TAXONOMY BREAKDOWN",
                     font=(_FF, 10, "bold"), bg=BG, fg="#f59e0b"
                     ).pack(padx=16, anchor="w", pady=(14, 4))

            bloom_levels = [
                ("REMEMBER",   "#6b7280", bloom.get("remember", [])),
                ("UNDERSTAND", "#3b82f6", bloom.get("understand", [])),
                ("APPLY",      "#22c55e", bloom.get("apply", [])),
                ("ANALYZE",    "#f97316", bloom.get("analyze", [])),
                ("EVALUATE",   "#a855f7", bloom.get("evaluate", [])),
            ]

            for level_name, color, items in bloom_levels:
                if not items:
                    continue
                row = tk.Frame(inner, bg=CARD)
                row.pack(fill="x", padx=14, pady=3)

                # Level badge
                tk.Label(row, text=f"  {level_name}  ",
                          font=(_FF, 9, "bold"),
                          bg=color, fg=TEXT, padx=6
                          ).pack(side="left", fill="y")

                # Items
                body = "\n".join(f"- {item}" for item in items)
                tk.Label(row, text=body, font=(_FF, 10),
                          bg=CARD, fg=TEXT, anchor="w",
                          padx=12, pady=8,
                          wraplength=660, justify="left"
                          ).pack(side="left", fill="x", expand=True)

        tk.Frame(inner, bg=BG, height=20).pack()

        # Propagate scroll through every child (matplotlib canvas swallows it otherwise)
        self._bind_scroll_recursive(inner)

    def _on_note_row_click(self, table_name, data, data_idx):
        key_field = "name" if table_name == "meds" else "lab"
        if data_idx < 0 or data_idx >= len(data):
            return
        row_key  = data[data_idx].get(key_field, "")
        existing = self._table_notes.get(table_name, {}).get(row_key)
        if existing:
            self._table_note_dialog(table_name, row_key, existing)

    def _on_table_right_click(self, table_name, data, table, data_idx, rx, ry):
        key_field = "name" if table_name == "meds" else "lab"
        if data_idx < 0 or data_idx >= len(data):
            return
        row_key  = data[data_idx].get(key_field, "")
        existing = self._table_notes.get(table_name, {}).get(row_key)

        menu = tk.Menu(self.root, tearoff=0, bg=PANEL, fg=TEXT,
                       activebackground=BLUE, activeforeground=TEXT,
                       font=FONT_BODY, bd=0, relief="flat")
        if existing:
            menu.add_command(label="Edit Note",
                             command=lambda: self._table_note_dialog(
                                 table_name, row_key, existing))
            menu.add_command(label="Remove Note",
                             command=lambda: self._remove_table_note(
                                 table_name, row_key))
        else:
            menu.add_command(label="Add Note",
                             command=lambda: self._table_note_dialog(
                                 table_name, row_key, None))
        try:
            menu.tk_popup(rx, ry)
        finally:
            menu.grab_release()

    def _table_note_dialog(self, table_name, row_key, existing=None):
        win = tk.Toplevel(self.root)
        win.title("Edit Note" if existing else "Add Note")
        win.config(bg=BG)
        win.geometry("560x520")
        win.minsize(460, 400)
        win.resizable(True, True)
        win.grab_set()

        # ── header ────────────────────────────────────────────────────────
        tk.Label(win, text=f"For:  {row_key[:62]}",
                 font=FONT_SMALL, bg=BG, fg=MUTED,
                 padx=16, pady=6).pack(anchor="w")

        # ── name field ────────────────────────────────────────────────────
        tk.Label(win, text="Name  (shown in table):",
                 font=FONT_SMALL, bg=BG, fg=TEXT, padx=16).pack(anchor="w")
        name_var  = tk.StringVar(value=existing["name"] if isinstance(existing, dict) else "")
        name_ent  = tk.Entry(win, textvariable=name_var, font=FONT_BODY,
                             bg=PANEL, fg=TEXT, insertbackground=TEXT,
                             relief="flat", bd=0)
        name_ent.pack(fill="x", padx=16, pady=(2, 10), ipady=5)

        # ── toolbar ───────────────────────────────────────────────────────
        tbar = tk.Frame(win, bg=CARD, padx=6, pady=4)
        tbar.pack(fill="x", padx=16, pady=(0, 4))

        def tbtn(label, cmd):
            b = _mk_btn(tbar, text=label,
                          font=(_FF, 9, "bold"),
                          bg=PANEL, fg=TEXT, relief="flat", bd=0,
                          activebackground=BLUE, activeforeground=TEXT,
                          padx=9, pady=3, cursor="hand2", command=cmd)
            b.pack(side="left", padx=2)
            return b

        # ── text area ─────────────────────────────────────────────────────
        txt_frame = tk.Frame(win, bg=PANEL, bd=0)
        txt_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        txt = tk.Text(txt_frame, font=FONT_BODY, bg=PANEL, fg=TEXT,
                      insertbackground=TEXT, relief="flat", bd=0,
                      wrap="word", undo=True, padx=10, pady=8,
                      selectbackground=BLUE, selectforeground=TEXT)
        vsb = tk.Scrollbar(txt_frame, orient="vertical", command=txt.yview,
                           bg=PANEL, troughcolor=BG)
        txt.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)

        if isinstance(existing, dict):
            txt.insert("1.0", existing.get("content", ""))

        # ── tag styling inside editor ─────────────────────────────────────
        txt.tag_config("bullet",   foreground=ORANGE)
        txt.tag_config("numbered", foreground=CYAN)
        txt.tag_config("divider",  foreground=MUTED)
        txt.tag_config("bold_mk",  foreground="#fbbf24")

        def _refresh_tags(_=None):
            for tag in ("bullet", "numbered", "divider", "bold_mk"):
                txt.tag_remove(tag, "1.0", "end")
            for ln in range(1, int(txt.index("end").split(".")[0])):
                line = txt.get(f"{ln}.0", f"{ln}.end")
                if line.startswith("* ") or line.startswith("- "):
                    txt.tag_add("bullet",   f"{ln}.0", f"{ln}.end")
                elif re.match(r"^\d+\.\s", line):
                    txt.tag_add("numbered", f"{ln}.0", f"{ln}.end")
                elif line.strip().startswith("---"):
                    txt.tag_add("divider",  f"{ln}.0", f"{ln}.end")
                for m in re.finditer(r"\*\*.+?\*\*", line):
                    txt.tag_add("bold_mk", f"{ln}.{m.start()}", f"{ln}.{m.end()}")
        txt.bind("<KeyRelease>", _refresh_tags)
        _refresh_tags()

        # ── toolbar actions ───────────────────────────────────────────────
        def _sel_lines():
            try:
                return txt.index("sel.first linestart"), txt.index("sel.last lineend")
            except tk.TclError:
                cur = txt.index("insert linestart")
                return cur, txt.index("insert lineend")

        def do_bullet():
            s, e  = _sel_lines()
            lines = txt.get(s, e).splitlines()
            new   = []
            all_bullets = all(l.startswith("* ") for l in lines if l.strip())
            for l in lines:
                if all_bullets:
                    new.append(l[2:] if l.startswith("* ") else l)
                else:
                    clean = re.sub(r"^(\* |- |\d+\. )", "", l)
                    new.append("* " + clean)
            txt.delete(s, e)
            txt.insert(s, "\n".join(new))
            _refresh_tags()

        def do_numbered():
            s, e  = _sel_lines()
            lines = txt.get(s, e).splitlines()
            new   = []
            for n, l in enumerate(lines, 1):
                clean = re.sub(r"^(\* |- |\d+\. )", "", l)
                new.append(f"{n}. {clean}")
            txt.delete(s, e)
            txt.insert(s, "\n".join(new))
            _refresh_tags()

        def do_indent():
            s, e  = _sel_lines()
            lines = txt.get(s, e).splitlines()
            txt.delete(s, e)
            txt.insert(s, "\n".join("    " + l for l in lines))

        def do_outdent():
            s, e  = _sel_lines()
            lines = txt.get(s, e).splitlines()
            txt.delete(s, e)
            txt.insert(s, "\n".join(
                l[4:] if l.startswith("    ") else l.lstrip(" ") for l in lines))

        def do_bold():
            try:
                sel = txt.get("sel.first", "sel.last")
                txt.delete("sel.first", "sel.last")
                txt.insert("insert", f"**{sel}**")
            except tk.TclError:
                txt.insert("insert", "****")
                txt.mark_set("insert", f"insert-2c")
            _refresh_tags()

        def do_divider():
            end_of_line = txt.index("insert lineend")
            txt.insert(end_of_line, "\n" + "-" * 48 + "\n")
            _refresh_tags()

        tbtn("* Bullet",  do_bullet)
        tbtn("1. List",   do_numbered)
        tbtn("B Bold",    do_bold)
        tbtn("-> Indent", do_indent)
        tbtn("<- Back",   do_outdent)
        tbtn("--- Line",  do_divider)
        tbtn("Undo",      lambda: (txt.edit_undo(), _refresh_tags()))

        # ── save / cancel ─────────────────────────────────────────────────
        def save():
            name    = name_var.get().strip()
            content = txt.get("1.0", "end").strip()
            if not name:
                name_ent.config(bg="#3b1a1a")
                return
            self._table_notes.setdefault(table_name, {})[row_key] = {
                "name": name, "content": content}
            win.destroy()
            self._auto_save_session()
            if self._visuals_data:
                self._render_visuals(self._visuals_data)

        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack(fill="x", padx=16, pady=(0, 14))
        self._btn(btn_row, "Save",   save,        color=BLUE,  small=True).pack(side="left")
        self._btn(btn_row, "Cancel", win.destroy, color=PANEL, small=True).pack(side="left", padx=8)
        name_ent.focus_set()

    def _remove_table_note(self, table_name, row_key):
        self._table_notes.get(table_name, {}).pop(row_key, None)
        self._auto_save_session()
        if self._visuals_data:
            self._render_visuals(self._visuals_data)

    def _open_med_popup(self, med):
        topic = self.topic_data.get("main_topic", "") if self.topic_data else ""
        win = tk.Toplevel(self.root)
        win.title(med.get("name", "Medication Detail"))
        win.geometry("660x660")
        win.configure(bg=BG)
        win.resizable(True, True)

        # Header
        hdr = tk.Frame(win, bg=CARD)
        hdr.pack(fill="x")
        hdr_inner = tk.Frame(hdr, bg=CARD)
        hdr_inner.pack(fill="x", padx=16, pady=14)
        tk.Label(hdr_inner, text=med.get("name", ""),
                 font=(_FF, 15, "bold"), bg=CARD, fg=TEXT
                 ).pack(anchor="w")
        tk.Label(hdr_inner, text=med.get("class", ""),
                 font=FONT_BODY, bg=CARD, fg=ORANGE
                 ).pack(anchor="w")

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x")

        # Known fields
        fields = [
            ("Mechanism of Action",       "action"),
            ("Key Nursing Considerations", "considerations"),
            ("What to Monitor",            "monitor"),
        ]
        for label, key in fields:
            val = med.get(key, "").strip()
            if not val:
                continue
            tk.Label(win, text=label, font=(_FF, 9, "bold"),
                     bg=BG, fg=MUTED).pack(padx=16, anchor="w", pady=(12, 2))
            row = tk.Frame(win, bg=CARD)
            row.pack(fill="x", padx=14)
            tk.Label(row, text=val, font=FONT_BODY, bg=CARD, fg=TEXT,
                     anchor="w", padx=12, pady=10, wraplength=580, justify="left"
                     ).pack(fill="x")

        # Divider
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(14, 0))
        self.extras_hdr_med = tk.Label(win,
            text="Loading additional NCLEX detail...",
            font=(_FF, 9, "bold"), bg=BG, fg=ORANGE)
        self.extras_hdr_med.pack(padx=16, anchor="w", pady=(8, 4))

        extras = scrolledtext.ScrolledText(win, font=FONT_BODY, wrap="word",
                                            height=12, bd=0, relief="flat",
                                            bg=CARD, fg=TEXT,
                                            insertbackground=TEXT,
                                            padx=12, pady=10, state="disabled")
        extras.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        def worker():
            data, err = ai_med_detail(med, topic)
            if err or not data:
                win.after(0, lambda: self.extras_hdr_med.config(
                    text=f"Could not load extra detail: {err}"))
                return
            lines = []
            if data.get("side_effects"):
                lines.append("SIDE EFFECTS / ADVERSE REACTIONS")
                lines += [f"  - {s}" for s in data["side_effects"]]
                lines.append("")
            if data.get("contraindications"):
                lines.append("CONTRAINDICATIONS")
                lines += [f"  - {c}" for c in data["contraindications"]]
                lines.append("")
            if data.get("antidote"):
                lines.append(f"ANTIDOTE / REVERSAL\n  {data['antidote']}")
                lines.append("")
            if data.get("patient_teaching"):
                lines.append("PATIENT TEACHING")
                lines += [f"  - {p}" for p in data["patient_teaching"]]
                lines.append("")
            if data.get("nclex_tips"):
                lines.append("NCLEX TIPS")
                lines += [f"  - {t}" for t in data["nclex_tips"]]
            text = "\n".join(lines).strip()
            def update():
                self.extras_hdr_med.config(text="ADDITIONAL NCLEX DETAIL")
                extras.config(state="normal")
                extras.delete("1.0", "end")
                extras.insert("end", text)
                extras.config(state="disabled")
            win.after(0, update)

        threading.Thread(target=worker, daemon=True).start()

    def _open_lab_popup(self, lab):
        topic = self.topic_data.get("main_topic", "") if self.topic_data else ""
        win = tk.Toplevel(self.root)
        win.title(lab.get("lab", "Lab Detail"))
        win.geometry("660x660")
        win.configure(bg=BG)
        win.resizable(True, True)

        # Header
        hdr = tk.Frame(win, bg=CARD)
        hdr.pack(fill="x")
        hdr_inner = tk.Frame(hdr, bg=CARD)
        hdr_inner.pack(fill="x", padx=16, pady=14)
        tk.Label(hdr_inner, text=lab.get("lab", ""),
                 font=(_FF, 15, "bold"), bg=CARD, fg=TEXT
                 ).pack(anchor="w")

        # Normal / Critical inline badges
        badge_row = tk.Frame(hdr_inner, bg=CARD)
        badge_row.pack(anchor="w", pady=(4, 0))
        tk.Label(badge_row, text=f"  Normal: {lab.get('normal','')}  ",
                 font=(_FF, 9, "bold"), bg="#15803d", fg=TEXT,
                 padx=4, pady=2).pack(side="left", padx=(0, 6))
        tk.Label(badge_row, text=f"  Critical: {lab.get('critical','')}  ",
                 font=(_FF, 9, "bold"), bg="#b91c1c", fg=TEXT,
                 padx=4, pady=2).pack(side="left")

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x")

        # Clinical significance
        sig = lab.get("significance", "").strip()
        if sig:
            tk.Label(win, text="Clinical Significance", font=(_FF, 9, "bold"),
                     bg=BG, fg=MUTED).pack(padx=16, anchor="w", pady=(12, 2))
            row = tk.Frame(win, bg=CARD)
            row.pack(fill="x", padx=14)
            tk.Label(row, text=sig, font=FONT_BODY, bg=CARD, fg=TEXT,
                     anchor="w", padx=12, pady=10, wraplength=580, justify="left"
                     ).pack(fill="x")

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(14, 0))
        self.extras_hdr_lab = tk.Label(win,
            text="Loading additional NCLEX detail...",
            font=(_FF, 9, "bold"), bg=BG, fg=GREEN)
        self.extras_hdr_lab.pack(padx=16, anchor="w", pady=(8, 4))

        extras = scrolledtext.ScrolledText(win, font=FONT_BODY, wrap="word",
                                            height=14, bd=0, relief="flat",
                                            bg=CARD, fg=TEXT,
                                            insertbackground=TEXT,
                                            padx=12, pady=10, state="disabled")
        extras.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        def worker():
            data, err = ai_lab_detail(lab, topic)
            if err or not data:
                win.after(0, lambda: self.extras_hdr_lab.config(
                    text=f"Could not load extra detail: {err}"))
                return
            lines = []
            if data.get("causes_elevated"):
                lines.append("CAUSES OF ELEVATION")
                lines += [f"  - {c}" for c in data["causes_elevated"]]
                lines.append("")
            if data.get("causes_decreased"):
                lines.append("CAUSES OF DECREASE")
                lines += [f"  - {c}" for c in data["causes_decreased"]]
                lines.append("")
            if data.get("related_labs"):
                lines.append("RELATED LABS TO CHECK")
                lines += [f"  - {r}" for r in data["related_labs"]]
                lines.append("")
            if data.get("notify_physician_when"):
                lines.append(f"NOTIFY PHYSICIAN WHEN\n  {data['notify_physician_when']}")
                lines.append("")
            if data.get("nursing_interventions"):
                lines.append("NURSING INTERVENTIONS")
                lines += [f"  - {n}" for n in data["nursing_interventions"]]
                lines.append("")
            if data.get("nclex_tips"):
                lines.append("NCLEX TIPS")
                lines += [f"  - {t}" for t in data["nclex_tips"]]
            text = "\n".join(lines).strip()
            def update():
                self.extras_hdr_lab.config(text="ADDITIONAL NCLEX DETAIL")
                extras.config(state="normal")
                extras.delete("1.0", "end")
                extras.insert("end", text)
                extras.config(state="disabled")
            win.after(0, update)

        threading.Thread(target=worker, daemon=True).start()

    def _draw_patho_chart(self, steps, title):
        n = len(steps)
        fig_h = max(5, n * 1.5 + 1.2)
        fig, ax = plt.subplots(figsize=(8.5, fig_h))
        fig.patch.set_facecolor("#1e293b")
        ax.set_facecolor("#1e293b")
        ax.set_xlim(0, 10)
        ax.set_ylim(-0.3, n * 1.5 + 0.6)
        ax.axis("off")

        step_colors = ["#1d4ed8", "#2563eb", "#3b82f6", "#0891b2",
                       "#0d9488", "#16a34a", "#dc2626"]

        for i, s in enumerate(steps):
            y     = (n - 1 - i) * 1.5 + 0.2
            color = step_colors[min(i, len(step_colors) - 1)]

            # Box
            box = mpatches.FancyBboxPatch(
                (0.3, y - 0.42), 9.4, 0.88,
                boxstyle="round,pad=0.08",
                linewidth=1.8, edgecolor=color, facecolor="#263447",
            )
            ax.add_patch(box)

            # Number badge
            badge = plt.Circle((0.95, y + 0.02), 0.28, color=color, zorder=3)
            ax.add_patch(badge)
            ax.text(0.95, y + 0.02, str(i + 1),
                    ha="center", va="center", color="white",
                    fontsize=8, fontweight="bold", zorder=4)

            # Step title
            ax.text(1.55, y + 0.12, s.get("step", ""),
                    ha="left", va="center", color="#f1f5f9",
                    fontsize=9.5, fontweight="bold")

            # Detail
            detail = s.get("detail", "")
            if detail:
                ax.text(1.55, y - 0.13, detail[:90],
                        ha="left", va="center", color="#94a3b8", fontsize=7.8)

            # Arrow between steps
            if i < n - 1:
                ax.annotate(
                    "", xy=(5, y - 0.42 - 0.12), xytext=(5, y - 0.42),
                    arrowprops=dict(
                        arrowstyle="-|>", color="#3b82f6",
                        lw=1.8, mutation_scale=14),
                )

        ax.set_title(title, color="#f1f5f9", fontsize=11,
                     fontweight="bold", pad=10, loc="center")
        plt.tight_layout(pad=0.6)
        return fig

    # ==================== ACTIONS ====================

    def _launch_browser(self):
        if launch_chromium():
            self.q_status.config(
                text="Browser launched.  Navigate to your quiz then click Extract.")
        else:
            messagebox.showerror("Error", "Could not launch Chromium.")

    def _extract_question(self):
        def worker():
            if self.driver is None:
                drv, err = init_driver()
                if err:
                    self.wq.put(("error", f"Browser connection failed: {err}"))
                    return
                self.driver = drv
            q, err = extract_question_from_page(self.driver)
            if err:
                self.wq.put(("error", err))
            elif q:
                self.wq.put(("add_q", q))
            else:
                self.wq.put(("error", "No question found on current page."))
        threading.Thread(target=worker, daemon=True).start()

    def _custom_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Add Custom Questions")
        win.geometry("640x460")
        win.configure(bg=BG)
        tk.Label(win,
            text="Paste questions below.  Separate multiple with a blank line.",
            font=FONT_SMALL, bg=BG, fg=MUTED,
        ).pack(padx=14, pady=(14, 4), anchor="w")
        ta = scrolledtext.ScrolledText(win, font=FONT_BODY, wrap="word", height=18,
                                        bd=0, relief="flat", bg=CARD, fg=TEXT,
                                        insertbackground=TEXT, padx=10, pady=8)
        ta.pack(fill="both", expand=True, padx=14, pady=4)

        menu = tk.Menu(ta, tearoff=0, bg=CARD, fg=TEXT,
                       activebackground=BLUE, activeforeground=TEXT,
                       relief="flat", bd=0)
        menu.add_command(label="Cut",   command=lambda: ta.event_generate("<<Cut>>"))
        menu.add_command(label="Copy",  command=lambda: ta.event_generate("<<Copy>>"))
        menu.add_command(label="Paste", command=lambda: ta.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: ta.tag_add("sel", "1.0", "end"))

        def show_menu(e):
            menu.tk_popup(e.x_root, e.y_root)
        ta.bind("<Button-3>", show_menu)

        def save():
            content = ta.get("1.0", "end").strip()
            if not content:
                win.destroy()
                return
            parts = re.split(r'\n\s*\n|\n(?=\d+[\.\)])', content)
            for p in parts:
                p = p.strip()
                if len(p) > 20:
                    self.wq.put(("add_q", p))
            win.destroy()

        self._btn(win, "Add Questions", save, color=GREEN).pack(
            fill="x", padx=14, pady=10)

    def _clear_questions(self):
        self.questions.clear()
        self.q_list.delete(0, "end")
        self.q_status.config(
            text="No questions yet.  Extract from browser or add manually.")
        self.gen_btn.config(state="disabled")

    def _generate_study(self):
        if not self.questions:
            messagebox.showwarning("No Questions", "Add questions first.")
            return
        self._session_file     = None
        self._study_highlights = set()
        self._study_sections   = {}
        self._table_notes      = {"meds": {}, "labs": {}}
        self.gen_btn.config(state="disabled", text="Working...")
        self.nb.select(1)
        self._set_study_text("")
        self.study_status_lbl.config(text="Identifying topic...")

        def worker():
            topic_data, err = ai_identify_topic(self.questions)
            if err or not topic_data:
                self.wq.put(("error", f"Topic identification failed: {err}"))
                self.wq.put(("gen_done", None))
                return
            self.wq.put(("topic", topic_data))

            self.wq.put(("study_status", "Searching reference material..."))
            snippets = web_search(topic_data.get("main_topic", ""))

            self.wq.put(("study_status", "Generating study notes..."))
            material, err = ai_generate_study_material(topic_data, snippets, self.questions)
            if err:
                self.wq.put(("error", f"Study generation failed: {err}"))
                self.wq.put(("gen_done", None))
                return

            self.wq.put(("study_material", (material, topic_data)))
            self.wq.put(("gen_done", None))

            # Generate visuals in the same thread after study material
            self.wq.put(("visuals_status", "Building charts and tables..."))
            visuals_data, err = ai_generate_visuals(topic_data, material)
            if err or not visuals_data:
                self.wq.put(("visuals_status", f"Visuals failed: {err}"))
                return
            self.wq.put(("visuals_ready", visuals_data))

        threading.Thread(target=worker, daemon=True).start()

    def _start_quiz(self):
        if self.quiz_qs:
            self._load_question()
            return
        self.quiz_start_btn.config(state="disabled", text="Generating quiz...")
        self.study_status_lbl.config(text="Generating quiz questions...")

        quiz_total = self.quiz_length_var.get()
        topic      = self.topic_data.get("main_topic", "Unknown") if self.topic_data else "Unknown"

        bank       = self._load_spaced_rep()
        topic_bank = bank.get(topic, [])
        inject_n   = min(len(topic_bank), max(0, quiz_total // 4))
        injected   = random.sample(topic_bank, inject_n) if inject_n else []
        new_n      = quiz_total - inject_n

        def worker():
            qs, err = ai_generate_quiz(self.topic_data, self.study_text_content, n=new_n)
            if err or not qs:
                self.wq.put(("error", f"Quiz generation failed: {err}"))
                self.wq.put(("quiz_gen_fail", None))
                return
            combined = injected + qs
            random.shuffle(combined)
            self.wq.put(("quiz_ready", combined))
            if inject_n:
                self.wq.put(("study_status", f"Quiz ready (+{inject_n} spaced-rep review)"))

        threading.Thread(target=worker, daemon=True).start()

    def _load_question(self):
        qs  = self.requiz_qs  if self.in_requiz else self.quiz_qs
        idx = self.requiz_idx if self.in_requiz else self.quiz_idx

        if idx >= len(qs):
            self._finish_quiz()
            return

        q = qs[idx]
        self.nb.select(4)

        prefix = "Re-Quiz: " if self.in_requiz else ""
        self.q_num_lbl.config(text=f"{prefix}Question {idx + 1} / {len(qs)}")
        self.quiz_prog["maximum"] = len(qs)
        self.quiz_prog["value"]   = idx
        score = self.requiz_score if self.in_requiz else self.quiz_score
        self.score_lbl.config(text=f"Score: {score}")

        q_type = q.get("type", "MC")
        self.quiz_q_lbl.config(text=q["question"])

        if q_type == "SATA":
            self.mc_frame.pack_forget()
            self.sata_frame.pack(fill="x")
            for letter in "ABCDE":
                self.sata_vars[letter].set(False)
                opt_text = q["options"].get(letter, "")
                if opt_text:
                    self.sata_btns[letter].config(
                        text=f"  {letter}.  {opt_text}", state="normal", bg=PANEL)
                else:
                    self.sata_btns[letter].config(text="", state="disabled", bg=PANEL)
        else:
            self.sata_frame.pack_forget()
            self.mc_frame.pack(fill="x")
            self.answer_var.set("")
            for letter in "ABCD":
                self.opt_btns[letter].config(
                    text=f"  {letter}.  {q['options'].get(letter, '')}",
                    state="normal", bg=PANEL,
                )

        # Bloom's badge
        bloom_level    = q.get("bloom_level", "")
        bloom_approach = q.get("bloom_approach", "")
        bloom_colors = {
            "Remember":   "#6b7280",
            "Understand": "#3b82f6",
            "Apply":      "#22c55e",
            "Analyze":    "#f97316",
            "Evaluate":   "#a855f7",
        }
        if bloom_level:
            b_color = bloom_colors.get(bloom_level, PANEL)
            self.bloom_badge.config(text=f"  {bloom_level.upper()}  ", bg=b_color)
            self.bloom_badge.pack(side="left")
        else:
            self.bloom_badge.pack_forget()
        self.bloom_approach_lbl.config(text=bloom_approach)

        self._set_feedback("")
        self.submit_btn.config(state="normal")
        is_last = (idx == len(qs) - 1)
        self.next_btn.config(
            state="disabled",
            text="Finish Quiz" if is_last else "Next Question  ->",
            command=self._finish_quiz if is_last else self._next_question,
        )

    def _submit_answer(self):
        qs  = self.requiz_qs  if self.in_requiz else self.quiz_qs
        idx = self.requiz_idx if self.in_requiz else self.quiz_idx
        q       = qs[idx]
        correct = q["correct"]
        q_type  = q.get("type", "MC")

        if q_type == "SATA":
            selected = sorted([l for l, v in self.sata_vars.items() if v.get()])
            if not selected:
                messagebox.showwarning("No Answer", "Please select at least one answer.")
                return
            correct_list = sorted(correct) if isinstance(correct, list) else [correct]
            is_correct   = selected == correct_list
            correct_text = "\n".join(
                f"  {l}: {q['options'].get(l, '')}" for l in correct_list)
            feedback = (
                f"CORRECT! All required answers selected.\n\n{q.get('rationale', '')}"
                if is_correct else
                f"INCORRECT\nYou selected: {', '.join(selected)}\n"
                f"Correct answers: {', '.join(correct_list)}\n{correct_text}\n\n"
                f"{q.get('rationale', '')}"
            )
            answer_recorded = ", ".join(selected)
        else:
            answer = self.answer_var.get()
            if not answer:
                messagebox.showwarning("No Answer", "Please select an answer.")
                return
            is_correct = answer == correct
            feedback = (
                f"CORRECT!\n\n{q.get('rationale', '')}"
                if is_correct else
                f"INCORRECT\n"
                f"Correct answer: {correct} — {q['options'].get(correct, '')}\n\n"
                f"{q.get('rationale', '')}"
            )
            answer_recorded = answer

        self._set_feedback(feedback)

        result = {
            "question":     q["question"],
            "options":      q["options"],
            "correct":      correct,
            "user_answer":  answer_recorded,
            "correct_bool": is_correct,
            "rationale":    q.get("rationale", ""),
            "bloom_level":  q.get("bloom_level", ""),
            "type":         q_type,
        }

        if self.in_requiz:
            if is_correct: self.requiz_score += 1
            self.requiz_results.append(result)
            self.score_lbl.config(text=f"Score: {self.requiz_score}")
        else:
            if is_correct: self.quiz_score += 1
            self.quiz_results.append(result)
            self.score_lbl.config(text=f"Score: {self.quiz_score}")

        self.submit_btn.config(state="disabled")
        self.next_btn.config(state="normal")
        for btn in self.opt_btns.values():
            btn.config(state="disabled")
        for btn in self.sata_btns.values():
            btn.config(state="disabled")

    def _select_mc(self, letter):
        self.answer_var.set(letter)
        for l, btn in self.opt_btns.items():
            btn.config(bg=BLUE if l == letter else PANEL)

    def _toggle_sata(self, letter):
        new_val = not self.sata_vars[letter].get()
        self.sata_vars[letter].set(new_val)
        self.sata_btns[letter].config(bg=BLUE if new_val else PANEL)

    def _next_question(self):
        if self.in_requiz:
            self.requiz_idx += 1
        else:
            self.quiz_idx += 1
        self._load_question()

    def _finish_quiz(self):
        if self.in_requiz:
            total = len(self.requiz_qs)
            score = self.requiz_score
            pct   = int(score / total * 100) if total else 0
            self.nb.select(5)
            self.results_lbl.config(
                text=f"Re-Quiz Complete!   {score} / {total}   ({pct}%)")
            self.requiz_btn.config(state="disabled", text="Re-Quiz Complete")
            self.missed = [r for r in self.requiz_results if not r["correct_bool"]]
            if self.missed:
                self._build_remediation()
            else:
                self._set_review_text(
                    "Perfect re-quiz score!  All answers correct.\n\n"
                    "Great job reinforcing your weak areas!")
        else:
            total  = len(self.quiz_qs)
            score  = self.quiz_score
            pct    = int(score / total * 100) if total else 0
            self.missed = [r for r in self.quiz_results if not r["correct_bool"]]
            try:
                self._auto_save_session()
            except Exception:
                pass
            try:
                self._update_weak_areas()
            except Exception:
                pass
            try:
                self._update_spaced_rep()
            except Exception:
                pass
            self.nb.select(5)
            self.results_lbl.config(
                text=f"Quiz Complete!   Score: {score} / {total}   ({pct}%)")
            if self.missed:
                self.requiz_btn.config(state="normal")
                self._build_remediation()
            else:
                self._set_review_text(
                    "Perfect score!  All answers correct.\n\n"
                    "Excellent clinical judgment!")

    def _build_remediation(self):
        self._set_review_text("Generating explanations for missed questions...\n")
        topic = self.topic_data.get("main_topic", "") if self.topic_data else ""

        def worker():
            text = f"Review of Missed Questions — {topic}\n{'=' * 60}\n\n"
            for i, r in enumerate(self.missed):
                text += f"Question {i + 1}\n{r['question']}\n\n"
                q_type  = r.get("type", "MC")
                correct = r["correct"]
                if q_type == "SATA" or isinstance(correct, list):
                    correct_str = ", ".join(correct) if isinstance(correct, list) else correct
                    text += f"  Your answers:    {r['user_answer']}\n"
                    text += f"  Correct answers: {correct_str}\n\n"
                else:
                    text += (f"  Your answer:    {r['user_answer']} — "
                             f"{r['options'].get(r['user_answer'], '')}\n")
                    text += (f"  Correct answer: {correct} — "
                             f"{r['options'].get(correct, '')}\n\n")
                explanation, _ = ai_remediation(
                    r["question"], r["options"],
                    correct, r["user_answer"], topic)
                if explanation:
                    text += f"{explanation}\n"
                text += "\n" + "-" * 60 + "\n\n"
                self.wq.put(("review_text", text))

        threading.Thread(target=worker, daemon=True).start()

    def _open_progress_chart(self):
        files = sorted(
            [f for f in os.listdir(SESSIONS_DIR)
             if f.endswith(".json") and f not in (
                 os.path.basename(SPACED_REP_FILE), os.path.basename(DRUGS_FILE))],
        )
        data_points = []
        for fname in files:
            try:
                with open(os.path.join(SESSIONS_DIR, fname), encoding="utf-8") as f:
                    d = json.load(f)
                score = d.get("score")
                total = d.get("total", 0)
                if score is None or not total:
                    continue
                ts    = d.get("timestamp", "")[:10]
                topic = (d.get("topic_data") or {}).get("main_topic", "?")[:20]
                pct   = int(score / total * 100)
                data_points.append((ts, topic, score, total, pct))
            except Exception:
                continue

        win = tk.Toplevel(self.root)
        win.title("Progress Chart")
        win.config(bg=BG)
        win.geometry("700x460")
        win.resizable(True, True)

        tk.Label(win, text="Quiz Score Progress", font=FONT_HDR, bg=BG, fg=TEXT
                 ).pack(pady=(14, 4))

        if not data_points:
            tk.Label(win, text="No quiz sessions found yet.",
                     font=FONT_BODY, bg=BG, fg=MUTED).pack(pady=40)
            return

        c_w, c_h = 660, 340
        pad_l, pad_r, pad_t, pad_b = 60, 20, 20, 60
        chart_w = c_w - pad_l - pad_r
        chart_h = c_h - pad_t - pad_b

        canvas = tk.Canvas(win, width=c_w, height=c_h, bg=CARD,
                           highlightthickness=0, bd=0)
        canvas.pack(padx=20, pady=(0, 10))

        # grid lines at 25, 50, 75, 100%
        for pct_line in (25, 50, 75, 100):
            y = pad_t + chart_h - int(pct_line / 100 * chart_h)
            canvas.create_line(pad_l, y, pad_l + chart_w, y,
                               fill=PANEL, dash=(4, 4))
            canvas.create_text(pad_l - 6, y, text=f"{pct_line}%",
                               font=FONT_SMALL, fill=MUTED, anchor="e")

        # axes
        canvas.create_line(pad_l, pad_t, pad_l, pad_t + chart_h,
                           fill=MUTED, width=1)
        canvas.create_line(pad_l, pad_t + chart_h,
                           pad_l + chart_w, pad_t + chart_h,
                           fill=MUTED, width=1)

        n     = len(data_points)
        step  = chart_w / max(n - 1, 1) if n > 1 else chart_w / 2
        points = []

        for i, (ts, topic, score, total, pct) in enumerate(data_points):
            x = pad_l + (i * step if n > 1 else chart_w / 2)
            y = pad_t + chart_h - int(pct / 100 * chart_h)
            color = GREEN if pct >= 75 else (ORANGE if pct >= 50 else RED)
            points.append((x, y, color, pct, ts, topic))

            # x-axis label (date, rotated via angled text)
            canvas.create_text(x, pad_t + chart_h + 10,
                               text=ts, font=(_FF, 8),
                               fill=MUTED, anchor="n")

        # draw connecting line
        if len(points) > 1:
            for i in range(len(points) - 1):
                x1, y1 = points[i][0], points[i][1]
                x2, y2 = points[i+1][0], points[i+1][1]
                canvas.create_line(x1, y1, x2, y2, fill=BLUE, width=2)

        # draw dots + score labels
        for x, y, color, pct, ts, topic in points:
            canvas.create_oval(x-6, y-6, x+6, y+6, fill=color, outline="")
            canvas.create_text(x, y - 14, text=f"{pct}%",
                               font=(_FF, 9, "bold"),
                               fill=color, anchor="s")

        # legend / summary
        avg = sum(p[4] for p in data_points) // len(data_points)
        best = max(p[4] for p in data_points)
        tk.Label(win,
                 text=f"Sessions: {n}   |   Best: {best}%   |   Average: {avg}%",
                 font=FONT_SMALL, bg=BG, fg=MUTED).pack()

    def _start_requiz(self):
        self.requiz_btn.config(state="disabled", text="Generating re-quiz...")
        topic = self.topic_data.get("main_topic", "") if self.topic_data else ""

        def worker():
            qs, err = ai_requiz(topic, self.missed)
            if err or not qs:
                self.wq.put(("error", f"Re-quiz generation failed: {err}"))
                self.wq.put(("requiz_fail", None))
                return
            self.wq.put(("requiz_ready", qs))

        threading.Thread(target=worker, daemon=True).start()

    # ==================== SPACED REPETITION ====================

    def _load_spaced_rep(self):
        try:
            with open(SPACED_REP_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_spaced_rep(self, bank):
        try:
            with open(SPACED_REP_FILE, "w", encoding="utf-8") as f:
                json.dump(bank, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _update_spaced_rep(self):
        if not self.topic_data or not self.quiz_results:
            return
        topic      = self.topic_data.get("main_topic", "Unknown")
        bank       = self._load_spaced_rep()
        topic_bank = bank.get(topic, [])
        bank_qs    = {q["question"] for q in topic_bank}

        for r in self.quiz_results:
            if not r["correct_bool"]:
                if r["question"] not in bank_qs:
                    topic_bank.append({
                        "question":    r["question"],
                        "options":     r["options"],
                        "correct":     r["correct"],
                        "rationale":   r.get("rationale", ""),
                        "bloom_level": r.get("bloom_level", ""),
                        "type":        r.get("type", "MC"),
                    })
                    bank_qs.add(r["question"])
            else:
                topic_bank = [q for q in topic_bank
                              if q["question"] != r["question"]]
                bank_qs.discard(r["question"])

        bank[topic] = topic_bank[-40:]
        self._save_spaced_rep(bank)

    # ==================== TEXT HELPERS ====================

    def _set_feedback(self, text):
        self.feedback_box.config(state="normal")
        self.feedback_box.delete("1.0", "end")
        if text:
            self.feedback_box.insert("end", text)
        self.feedback_box.config(state="disabled")

    # ==================== SESSION PERSISTENCE ====================

    def _auto_save_session(self):
        if not self.study_text_content:
            return
        topic = self.topic_data.get("main_topic", "Unknown") if self.topic_data else "Unknown"
        now   = datetime.datetime.now()
        if self._session_file is None:
            safe = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')[:40]
            self._session_file = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{safe}.json"
        filename = self._session_file
        payload  = {
            "timestamp":          now.isoformat(),
            "topic_data":         self.topic_data,
            "questions":          self.questions,
            "study_text_content": self.study_text_content,
            "study_highlights":   sorted(self._study_highlights),
            "table_notes":        self._table_notes,
            "visuals_data":       self._visuals_data,
            "quiz_results":       self.quiz_results,
            "score":              self.quiz_score,
            "total":              len(self.quiz_qs),
        }
        try:
            with open(os.path.join(SESSIONS_DIR, filename), "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _regenerate_visuals(self):
        if not self.study_text_content or not self.topic_data:
            return
        self.visuals_regen_btn.config(state="disabled", text="Building...")
        self.visuals_status_lbl.config(text="Rebuilding charts and tables...")
        topic_data = self.topic_data
        material   = self.study_text_content

        def worker():
            visuals_data, err = ai_generate_visuals(topic_data, material)
            if err or not visuals_data:
                self.wq.put(("visuals_status", f"Visuals failed: {err}"))
                self.root.after(0, lambda: self.visuals_regen_btn.config(
                    state="normal", text="↻  Rebuild Visuals"))
                return
            self.wq.put(("visuals_ready", visuals_data))

        threading.Thread(target=worker, daemon=True).start()

    def _load_session(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
        except Exception as e:
            messagebox.showerror("Load failed", str(e))
            return

        self.topic_data          = d.get("topic_data") or {}
        self.questions           = d.get("questions", [])
        self.study_text_content  = d.get("study_text_content", "")
        self._study_highlights   = set(d.get("study_highlights", []))
        self._table_notes        = d.get("table_notes", {"meds": {}, "labs": {}})
        self._visuals_data       = d.get("visuals_data", {})
        self.quiz_results        = d.get("quiz_results", [])
        self.quiz_score          = d.get("score", 0)
        self.quiz_qs             = []

        # restore questions list
        self.q_list.delete(0, "end")
        for i, q in enumerate(self.questions):
            display = q[:90] + "..." if len(q) > 90 else q
            self.q_list.insert("end", f"  {i+1}.  {display}")
        count = len(self.questions)
        self.q_status.config(text=f"{count} question(s) loaded from session.")
        if count:
            self.gen_btn.config(state="normal")

        # restore study material
        topic = self.topic_data.get("main_topic", "") if self.topic_data else ""
        self.topic_lbl.config(text=f"Topic: {topic}" if topic else "Topic: —")
        self._set_study_text(self.study_text_content)
        if self.study_text_content:
            self.quiz_start_btn.config(state="normal")
            self.chat_topic_lbl.config(text=f"Topic: {topic}")

        # restore visuals
        if self._visuals_data:
            try:
                self._render_visuals(self._visuals_data)
                self.visuals_regen_btn.pack_forget()
            except Exception:
                self.visuals_status_lbl.config(text="Visuals failed to render — click to rebuild.")
                self.visuals_regen_btn.config(state="normal", text="↻  Rebuild Visuals")
                self.visuals_regen_btn.pack(side="left", padx=(10, 0))
        elif self.study_text_content:
            self.visuals_status_lbl.config(text="Visuals not saved in this session.")
            self.visuals_regen_btn.config(state="normal", text="↻  Rebuild Visuals")
            self.visuals_regen_btn.pack(side="left", padx=(10, 0))

        # restore results
        total = d.get("total", 0)
        if self.quiz_results and total:
            pct = int(self.quiz_score / total * 100)
            self.results_lbl.config(
                text=f"Loaded session — Score: {self.quiz_score} / {total}  ({pct}%)")
            self.missed = [r for r in self.quiz_results if not r["correct_bool"]]
            if self.missed:
                self.requiz_btn.config(state="normal")
            self._update_weak_areas()
        else:
            self.results_lbl.config(text="Session loaded — no quiz data yet.")

        self.nb.select(1)
        messagebox.showinfo("Session loaded", f"Loaded: {topic or path}")

    def _update_weak_areas(self):
        """Read all session files and rebuild the Bloom's breakdown panel."""
        bloom_totals = {}
        bloom_correct = {}
        for level in ("Remember", "Understand", "Apply", "Analyze", "Evaluate"):
            bloom_totals[level]  = 0
            bloom_correct[level] = 0

        session_count = 0
        for fname in sorted(os.listdir(SESSIONS_DIR)):
            if not fname.endswith(".json") or fname in (
                    os.path.basename(SPACED_REP_FILE), os.path.basename(DRUGS_FILE)):
                continue
            try:
                with open(os.path.join(SESSIONS_DIR, fname), encoding="utf-8") as f:
                    d = json.load(f)
                for r in d.get("quiz_results", []):
                    lvl = r.get("bloom_level", "")
                    if lvl in bloom_totals:
                        bloom_totals[lvl]  += 1
                        if r.get("correct_bool"):
                            bloom_correct[lvl] += 1
                if d.get("quiz_results"):
                    session_count += 1
            except Exception:
                continue

        # Rebuild widget
        for w in self._weak_frame.winfo_children():
            w.destroy()

        if session_count == 0:
            tk.Label(self._weak_frame,
                     text="Complete a quiz to see your performance breakdown.",
                     font=FONT_SMALL, bg=CARD, fg=MUTED, padx=14, pady=10
                     ).pack(anchor="w")
            return

        tk.Label(self._weak_frame,
                 text=f"Across {session_count} session(s):",
                 font=FONT_SMALL, bg=CARD, fg=MUTED, padx=14, pady=8
                 ).pack(anchor="w")

        bloom_colors = {
            "Remember":   "#6b7280",
            "Understand": BLUE,
            "Apply":      GREEN,
            "Analyze":    ORANGE,
            "Evaluate":   PURPLE,
        }

        for level in ("Remember", "Understand", "Apply", "Analyze", "Evaluate"):
            total   = bloom_totals[level]
            correct = bloom_correct[level]
            if total == 0:
                continue
            pct   = correct / total
            color = bloom_colors[level]
            flag  = "  needs work" if pct < 0.6 else ""

            row = tk.Frame(self._weak_frame, bg=CARD)
            row.pack(fill="x", padx=14, pady=2)

            tk.Label(row, text=f"{level:<12}", font=FONT_BODY,
                     bg=CARD, fg=TEXT, width=12, anchor="w"
                     ).pack(side="left")

            bar_bg = tk.Frame(row, bg=PANEL, height=14, width=160)
            bar_bg.pack(side="left", padx=(6, 0))
            bar_bg.pack_propagate(False)
            fill_w = max(4, int(160 * pct))
            tk.Frame(bar_bg, bg=color, width=fill_w, height=14).place(x=0, y=0)

            lbl_color = RED if pct < 0.6 else (ORANGE if pct < 0.75 else GREEN)
            tk.Label(row, text=f"  {int(pct*100)}%  ({correct}/{total}){flag}",
                     font=FONT_SMALL, bg=CARD, fg=lbl_color
                     ).pack(side="left", padx=(8, 0))

    # ==================== SESSIONS TAB ====================

    # ---- Tab 5: Chat ----
    def _tab_chat(self):
        outer = tk.Frame(self.nb, bg=BG)
        self.nb.add(outer, text="  Chat  ")

        hdr = tk.Frame(outer, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(hdr, text="AI Tutor", font=FONT_HDR, bg=BG, fg=TEXT).pack(side="left")
        self.chat_topic_lbl = tk.Label(hdr,
            text="Generate study material first.",
            font=FONT_SMALL, bg=BG, fg=MUTED)
        self.chat_topic_lbl.pack(side="left", padx=10)
        _mk_btn(hdr, text="Clear Chat", font=FONT_SMALL, bg=PANEL, fg=MUTED,
                  relief="flat", bd=0, padx=8, pady=2, cursor="hand2",
                  command=self._clear_chat).pack(side="right")

        self.chat_box = self._text_area(outer, height=24, font=FONT_BODY, bg=CARD)
        self.chat_box.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        self.chat_box.tag_configure("user_tag", foreground=BLUE,
                                    font=(_FF, 10, "bold"))
        self.chat_box.tag_configure("ai_tag",   foreground=GREEN,
                                    font=(_FF, 10, "bold"))
        self.chat_box.tag_configure("body",     foreground=TEXT)
        self.chat_box.tag_configure("sep",      foreground=MUTED)

        input_card = tk.Frame(outer, bg=PANEL,
                              highlightthickness=1, highlightbackground=BORDER)
        input_card.pack(fill="x", padx=14, pady=(0, 14))

        self.chat_input = tk.Text(input_card, height=3, font=FONT_BODY,
                                   bg=CARD, fg=TEXT, insertbackground=TEXT,
                                   relief="flat", bd=0, wrap="word")
        self.chat_input.pack(fill="x", padx=8, pady=(8, 4))
        self.chat_input.bind("<Return>",       self._on_chat_enter)
        self.chat_input.bind("<Shift-Return>", lambda e: None)

        send_row = tk.Frame(input_card, bg=PANEL)
        send_row.pack(fill="x", padx=8, pady=(0, 8))
        tk.Label(send_row, text="Enter to send  |  Shift+Enter for new line",
                 font=FONT_SMALL, bg=PANEL, fg=MUTED).pack(side="left")
        self.chat_send_btn = _mk_btn(send_row, text="Send  ->",
                                        font=FONT_SMALL, bg=BLUE, fg=TEXT,
                                        relief="flat", bd=0, padx=12, pady=4,
                                        cursor="hand2",
                                        activebackground=PANEL, activeforeground=TEXT,
                                        command=self._send_chat)
        self.chat_send_btn.pack(side="right")

    def _on_chat_enter(self, event):
        if not (event.state & 0x1):   # Shift not held
            self._send_chat()
            return "break"

    def _clear_chat(self):
        self.chat_history.clear()
        self.chat_box.config(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.config(state="disabled")

    def _append_chat(self, sender, message, tag):
        self.chat_box.config(state="normal")
        self.chat_box.insert("end", f"\n{sender}:\n", tag)
        self.chat_box.insert("end", message + "\n", "body")
        self.chat_box.insert("end", "-" * 48 + "\n", "sep")
        self.chat_box.see("end")
        self.chat_box.config(state="disabled")

    def _send_chat(self):
        if not self.study_text_content:
            messagebox.showwarning("No material", "Generate study material first.")
            return
        msg = self.chat_input.get("1.0", "end").strip()
        if not msg:
            return
        self.chat_input.delete("1.0", "end")
        self.chat_send_btn.config(state="disabled", text="Thinking...")
        self._append_chat("You", msg, "user_tag")
        self.chat_history.append({"role": "user", "content": msg})
        topic   = self.topic_data.get("main_topic", "") if self.topic_data else ""
        context = self.study_text_content
        history = list(self.chat_history)

        def worker():
            reply, err = ai_chat(history, context, topic)
            self.wq.put(("chat_reply", (reply, err)))

        threading.Thread(target=worker, daemon=True).start()

    # ---- Tab 6: Sessions ----
    def _tab_sessions(self):
        outer = tk.Frame(self.nb, bg=BG)
        self.nb.add(outer, text="  Sessions  ")

        hdr = tk.Frame(outer, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(hdr, text="SAVED SESSIONS", font=FONT_HDR, bg=BG, fg=TEXT).pack(side="left")
        self._btn(hdr, "Refresh", lambda: self._refresh_sessions(scroll_inner),
                  color=PANEL, small=True).pack(side="right")

        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(0, 8))

        # Scrollable container
        wrap = tk.Frame(outer, bg=BG)
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        vsb    = tk.Scrollbar(wrap, orient="vertical", bg=PANEL,
                               troughcolor=CARD, relief="flat", bd=0)
        canvas = tk.Canvas(wrap, bg=BG, bd=0, highlightthickness=0,
                            yscrollcommand=vsb.set)
        vsb.config(command=canvas.yview)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        scroll_inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=scroll_inner, anchor="nw")

        def _on_resize(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", _on_resize)

        def _on_frame_resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scroll_inner.bind("<Configure>", _on_frame_resize)

        _bind_scroll(canvas, canvas)

        self._sessions_canvas = canvas
        self._refresh_sessions(scroll_inner)

    def _refresh_sessions(self, container):
        for w in container.winfo_children():
            w.destroy()

        files = sorted(
            [f for f in os.listdir(SESSIONS_DIR)
             if f.endswith(".json") and f not in (os.path.basename(SPACED_REP_FILE), os.path.basename(DRUGS_FILE))],
            reverse=True
        )

        if not files:
            tk.Label(container,
                     text="No saved sessions yet. Complete a quiz to auto-save.",
                     font=FONT_BODY, bg=BG, fg=MUTED, pady=20
                     ).pack(anchor="w", padx=8)
            return

        for fname in files:
            path = os.path.join(SESSIONS_DIR, fname)
            try:
                with open(path, encoding="utf-8") as f:
                    d = json.load(f)
                ts_raw = d.get("timestamp", "")
                try:
                    ts = datetime.datetime.fromisoformat(ts_raw).strftime("%Y-%m-%d  %H:%M")
                except Exception:
                    ts = ts_raw[:16]
                topic = (d.get("topic_data") or {}).get("main_topic", "Unknown topic")
                score = d.get("score", None)
                total = d.get("total", 0)
                if score is not None and total:
                    pct       = int(score / total * 100)
                    score_txt = f"{score}/{total}  ({pct}%)"
                    s_color   = GREEN if pct >= 75 else (ORANGE if pct >= 50 else RED)
                else:
                    score_txt = "No quiz"
                    s_color   = MUTED
            except Exception:
                continue

            card = tk.Frame(container, bg=CARD)
            card.pack(fill="x", pady=4)

            # score badge on far right
            badge_frame = tk.Frame(card, bg=s_color, width=72)
            badge_frame.pack(side="right", fill="y")
            badge_frame.pack_propagate(False)
            tk.Label(badge_frame, text=score_txt, font=(_FF, 10, "bold"),
                     bg=s_color, fg=TEXT if s_color != MUTED else BG,
                     justify="center", wraplength=68
                     ).place(relx=0.5, rely=0.5, anchor="center")

            # action buttons
            btns = tk.Frame(card, bg=CARD)
            btns.pack(side="right", padx=10, pady=10)
            self._btn(btns, "Load",   lambda p=path, c=container: self._load_session(p),
                      color=BLUE, small=True).pack(side="left", padx=(0, 6))
            self._btn(btns, "Delete", lambda p=path, c=container: self._delete_session(p, c),
                      color=RED, small=True).pack(side="left")

            # info
            info = tk.Frame(card, bg=CARD)
            info.pack(side="left", fill="x", expand=True, padx=14, pady=10)
            tk.Label(info, text=ts, font=FONT_SMALL, bg=CARD, fg=MUTED
                     ).pack(anchor="w")
            tk.Label(info, text=topic, font=(_FF, 11, "bold"),
                     bg=CARD, fg=TEXT).pack(anchor="w")

    def _delete_session(self, path, container):
        if not messagebox.askyesno("Delete session",
                                    "Permanently delete this session?"):
            return
        try:
            os.remove(path)
        except Exception:
            pass
        self._refresh_sessions(container)

    def _save_study(self):
        if not self.study_text_content:
            messagebox.showinfo("Nothing to save", "Generate study material first.")
            return

        topic = self.topic_data.get("main_topic", "Study Notes") if self.topic_data else "Study Notes"
        safe  = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')
        path  = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
            initialdir=STUDY_GUIDES_DIR,
            initialfile=f"{safe}.txt",
            title="Save study notes",
        )
        if not path:
            return

        lines = []
        sep   = "=" * 60
        thin  = "-" * 60

        lines += [sep, f"  STUDY NOTES — {topic.upper()}", sep, ""]

        lines += ["STUDY MATERIAL", thin, self.study_text_content.strip(), ""]

        if self._current_meds:
            lines += ["MEDICATIONS TABLE", thin]
            col_h = ["Name", "Class", "Action", "Key Considerations", "Monitor"]
            lines.append("  |  ".join(f"{h:<22}" for h in col_h))
            lines.append(thin)
            for m in self._current_meds:
                row = [m.get("name",""), m.get("class",""), m.get("action",""),
                       m.get("considerations",""), m.get("monitor","")]
                lines.append("  |  ".join(f"{c:<22}" for c in row))
            lines.append("")

        if self._current_labs:
            lines += ["LAB VALUES REFERENCE", thin]
            col_h = ["Lab", "Normal Range", "Critical Value", "Clinical Significance"]
            lines.append("  |  ".join(f"{h:<22}" for h in col_h))
            lines.append(thin)
            for lb in self._current_labs:
                row = [lb.get("lab",""), lb.get("normal",""),
                       lb.get("critical",""), lb.get("significance","")]
                lines.append("  |  ".join(f"{c:<22}" for c in row))
            lines.append("")

        if self._current_actions:
            lines += ["PRIORITY NURSING ACTIONS", thin]
            for i, a in enumerate(self._current_actions, 1):
                lines.append(f"  {i}. {a}")
            lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        messagebox.showinfo("Saved", f"Notes saved to:\n{path}")

    # ---- study text rendering ----

    _SECTION_COLORS = {
        "PATHOPHYSIOLOGY": "#3b82f6",  # blue
        "MECHANISM":       "#3b82f6",
        "BIG PICTURE":     "#6b7280",  # muted gray
        "KEY ASSESSMENT":  "#ef4444",  # red
        "ASSESSMENT":      "#ef4444",
        "PRIORITY NURSING":"#a855f7",  # purple
        "INTERVENTIONS":   "#a855f7",
        "MEDICATIONS":     "#f97316",  # orange
        "PHARMACOLOGY":    "#f97316",
        "NCLEX":           "#22c55e",  # green
        "HIGH-YIELD":      "#22c55e",
        "DISTRACTORS":     "#ec4899",  # pink
        "TRAPS":           "#ec4899",
        "DELEGATION":      "#06b6d4",  # cyan
        "SAFETY":          "#06b6d4",
    }

    def _section_color(self, title):
        t = title.upper()
        for key, color in self._SECTION_COLORS.items():
            if key in t:
                return color
        return "#3b82f6"

    def _render_inline(self, box, text, base_tag, bold_tag):
        import re as _re
        parts = _re.split(r'(\*\*[^*]+\*\*)', text)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                box.insert("end", part[2:-2], bold_tag)
            else:
                box.insert("end", part, base_tag)

    def _set_study_text(self, text):
        import re as _re
        box = self.study_box
        box.config(state="normal")
        box.delete("1.0", "end")
        self._study_sections = {}

        # base tags
        box.tag_configure("body",      font=FONT_BODY, foreground=TEXT)
        box.tag_configure("bold",      font=(_FF, 11, "bold"), foreground=TEXT)
        box.tag_configure("bullet",    font=FONT_BODY, foreground=TEXT,  lmargin1=20, lmargin2=28)
        box.tag_configure("bold_bul",  font=(_FF, 11, "bold"), foreground=TEXT,
                          lmargin1=20, lmargin2=28)
        box.tag_configure("sub",       font=FONT_BODY, foreground=MUTED, lmargin1=36, lmargin2=44)
        box.tag_configure("bold_sub",  font=(_FF, 11, "bold"), foreground=MUTED,
                          lmargin1=36, lmargin2=44)
        box.tag_configure("highlight", background="#854d0e", foreground="#fef3c7")

        if not text:
            box.config(state="disabled")
            return

        # parse into sections
        lines   = text.splitlines()
        sections = []
        current  = None
        preamble = []
        for line in lines:
            if line.startswith("## "):
                if current is not None:
                    sections.append(current)
                current = {"title": line[3:].strip(), "lines": []}
            elif current is None:
                preamble.append(line)
            else:
                current["lines"].append(line)
        if current is not None:
            sections.append(current)

        def render_line(line, extra=()):
            stripped = line.lstrip()
            indent   = len(line) - len(stripped)
            if stripped.startswith("- ") or stripped.startswith("* "):
                if indent >= 4:
                    box.insert("end", "    * ", ("sub",) + extra)
                    self._render_inline(box, stripped[2:], ("sub",) + extra, ("bold_sub",) + extra)
                else:
                    box.insert("end", "  - ", ("bullet",) + extra)
                    self._render_inline(box, stripped[2:], ("bullet",) + extra, ("bold_bul",) + extra)
                box.insert("end", "\n", ("body",) + extra)
            else:
                self._render_inline(box, line, ("body",) + extra, ("bold",) + extra)
                box.insert("end", "\n", ("body",) + extra)

        for line in preamble:
            render_line(line)

        for i, sec in enumerate(sections):
            sec_id   = f"sec_{i}"
            body_tag = f"body_{sec_id}"
            hdr_tag  = f"hdr_{sec_id}"
            color    = self._section_color(sec["title"])

            box.tag_configure(hdr_tag,  font=(_FF, 13, "bold"),
                              foreground=color, spacing1=14, spacing3=6)
            box.tag_configure(body_tag, elide=False)

            self._study_sections[sec_id] = {
                "body_tag":  body_tag,
                "hdr_tag":   hdr_tag,
                "collapsed": False,
                "title":     sec["title"],
            }

            box.insert("end", f"[-] {sec['title']}\n", hdr_tag)
            box.tag_bind(hdr_tag, "<Button-1>",
                         lambda e, sid=sec_id: self._toggle_study_section(sid))
            box.tag_bind(hdr_tag, "<Enter>",
                         lambda e: box.config(cursor="hand2"))
            box.tag_bind(hdr_tag, "<Leave>",
                         lambda e: box.config(cursor=""))

            for line in sec["lines"]:
                render_line(line, extra=(body_tag,))
            box.insert("end", "\n", (body_tag,))

        # restore highlights
        self._apply_study_highlights()

        box.config(state="disabled")

    def _apply_study_highlights(self):
        box = self.study_box
        for ln in self._study_highlights:
            try:
                box.tag_add("highlight", f"{ln}.0", f"{ln}.end+1c")
            except Exception:
                pass

    def _toggle_study_section(self, sec_id):
        if sec_id not in self._study_sections:
            return
        sec      = self._study_sections[sec_id]
        collapsed = not sec["collapsed"]
        sec["collapsed"] = collapsed
        box = self.study_box
        box.config(state="normal")
        box.tag_configure(sec["body_tag"], elide=collapsed)
        ranges = box.tag_ranges(sec["hdr_tag"])
        if ranges:
            start = str(ranges[0])
            end   = str(ranges[1])
            old   = box.get(start, end)
            indicator = "[+]" if collapsed else "[-]"
            box.delete(start, end)
            box.insert(start, indicator + old[3:], sec["hdr_tag"])
        box.config(state="disabled")

    def _toggle_collapse_all(self):
        if not self._study_sections:
            return
        any_expanded = any(
            not s["collapsed"] for s in self._study_sections.values()
        )
        for sec_id in self._study_sections:
            sec = self._study_sections[sec_id]
            if any_expanded != sec["collapsed"]:
                self._toggle_study_section(sec_id)
        self.collapse_btn.config(
            text="Expand All" if any_expanded else "Collapse All"
        )

    def _toggle_highlight_mode(self):
        self._highlight_mode = not self._highlight_mode
        if self._highlight_mode:
            self.highlight_btn.config(bg=ORANGE)
            self.study_box.bind("<Button-1>", self._on_study_highlight_click)
        else:
            self.highlight_btn.config(bg=PANEL)
            self.study_box.unbind("<Button-1>")

    def _on_study_highlight_click(self, event):
        box  = self.study_box
        idx  = box.index(f"@{event.x},{event.y}")
        ln   = int(idx.split(".")[0])
        line_start = f"{ln}.0"
        line_end   = f"{ln}.end+1c"
        box.config(state="normal")
        if "highlight" in box.tag_names(line_start):
            box.tag_remove("highlight", line_start, line_end)
            self._study_highlights.discard(ln)
        else:
            box.tag_add("highlight", line_start, line_end)
            self._study_highlights.add(ln)
        box.config(state="disabled")

    # ---- Ctrl+F search ----
    def _open_study_search(self):
        self._study_search_frame.pack(fill="x", padx=14, pady=(0, 4))
        self._study_search_entry.focus_set()
        self._study_search_entry.select_range(0, "end")

    def _close_study_search(self):
        self._study_search_frame.pack_forget()
        self.study_box.tag_remove("search_match", "1.0", "end")
        self.study_box.tag_remove("search_cur",   "1.0", "end")
        self._study_search_matches = []
        self._study_search_var.set("")

    def _do_study_search(self):
        box   = self.study_box
        query = self._study_search_var.get()
        box.tag_remove("search_match", "1.0", "end")
        box.tag_remove("search_cur",   "1.0", "end")
        self._study_search_matches = []
        self._study_search_idx     = 0
        if not query:
            self._study_search_lbl.config(text="")
            return
        box.tag_configure("search_match", background="#854d0e", foreground="#fef3c7")
        box.tag_configure("search_cur",   background="#ca8a04", foreground="#000000")
        start = "1.0"
        while True:
            pos = box.search(query, start, stopindex="end", nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            box.tag_add("search_match", pos, end)
            self._study_search_matches.append((pos, end))
            start = end
        count = len(self._study_search_matches)
        if count:
            self._study_search_lbl.config(text=f"  1 of {count}")
            self._highlight_search_cur(0)
        else:
            self._study_search_lbl.config(text="  No results")

    def _highlight_search_cur(self, idx):
        box = self.study_box
        box.tag_remove("search_cur", "1.0", "end")
        if not self._study_search_matches:
            return
        pos, end = self._study_search_matches[idx]
        box.tag_add("search_cur", pos, end)
        box.see(pos)
        n = len(self._study_search_matches)
        self._study_search_lbl.config(text=f"  {idx+1} of {n}")

    def _study_search_next(self):
        if not self._study_search_matches:
            return
        self._study_search_idx = (self._study_search_idx + 1) % len(self._study_search_matches)
        self._highlight_search_cur(self._study_search_idx)

    def _study_search_prev(self):
        if not self._study_search_matches:
            return
        self._study_search_idx = (self._study_search_idx - 1) % len(self._study_search_matches)
        self._highlight_search_cur(self._study_search_idx)

    def _set_review_text(self, text):
        self.review_box.config(state="normal")
        self.review_box.delete("1.0", "end")
        if text:
            self.review_box.insert("end", text)
        self.review_box.config(state="disabled")

    # ==================== QUEUE ====================

    def _poll_queue(self):
        try:
            while not self.wq.empty():
                key, val = self.wq.get_nowait()

                if key == "add_q":
                    if val not in self.questions:
                        self.questions.append(val)
                        display = val[:95] + "..." if len(val) > 95 else val
                        self.q_list.insert("end", f"  {len(self.questions)}.  {display}")
                    self.q_status.config(
                        text=f"{len(self.questions)} question(s) collected.")
                    self.gen_btn.config(state="normal")

                elif key == "error":
                    messagebox.showerror("Error", val)

                elif key == "topic":
                    self.topic_data = val
                    self.topic_lbl.config(
                        text=f"Topic: {val.get('main_topic', '—')}")

                elif key == "study_status":
                    self.study_status_lbl.config(text=val)

                elif key == "study_material":
                    material, topic_data = val
                    self.study_text_content = material
                    self.topic_data = topic_data
                    self._set_study_text(material)
                    self.quiz_start_btn.config(state="normal")
                    self.study_status_lbl.config(text="Done")
                    self.chat_topic_lbl.config(
                        text=f"Topic: {topic_data.get('main_topic', '')}")
                    self._auto_save_session()

                elif key == "gen_done":
                    self.gen_btn.config(
                        state="normal", text="Generate Study Material  ->")

                elif key == "visuals_status":
                    self.visuals_status_lbl.config(text=val)

                elif key == "visuals_ready":
                    self.visuals_status_lbl.config(text="Charts and tables ready")
                    self.visuals_regen_btn.pack_forget()
                    self._render_visuals(val)
                    self._auto_save_session()

                elif key == "quiz_ready":
                    self.quiz_qs = val
                    self.quiz_idx = 0
                    self.quiz_score = 0
                    self.quiz_results.clear()
                    self.quiz_start_btn.config(state="normal", text="Start Quiz  ->")
                    self.study_status_lbl.config(text="Quiz ready")
                    self.quiz_prog["maximum"] = len(val)
                    self._load_question()

                elif key == "quiz_gen_fail":
                    self.quiz_start_btn.config(state="normal", text="Start Quiz  ->")

                elif key == "review_text":
                    self._set_review_text(val)

                elif key == "requiz_ready":
                    self.requiz_qs = val
                    self.requiz_idx = 0
                    self.requiz_score = 0
                    self.requiz_results.clear()
                    self.in_requiz = True
                    self.requiz_btn.config(
                        state="normal",
                        text="Re-Quiz Me on Missed Topics  ->")
                    self._load_question()

                elif key == "requiz_fail":
                    self.requiz_btn.config(
                        state="normal",
                        text="Re-Quiz Me on Missed Topics  ->")

                elif key == "chat_reply":
                    reply, err = val
                    self.chat_send_btn.config(state="normal", text="Send  ->")
                    if err:
                        self._append_chat("Error", err, "sep")
                    else:
                        self.chat_history.append(
                            {"role": "assistant", "content": reply})
                        self._append_chat("Tutor", reply, "ai_tag")

                elif key == "drug_card_ready":
                    name, card = val
                    self.drug_name_lbl.config(text=name, fg=TEXT)
                    self._render_drug_card(card)
                    self._populate_drug_list()  # refresh list with canonical name

                elif key == "drug_card_error":
                    self.drug_status_lbl.config(text=val, fg=RED)

        except queue.Empty:
            pass

        # Check if a background thread is waiting for a new API key
        if _key_needed_event.is_set() and not self._key_dialog_open:
            _key_needed_event.clear()
            self._open_key_dialog()

        self.root.after(150, self._poll_queue)


    def _open_key_dialog(self):
        self._key_dialog_open = True

        win = tk.Toplevel(self.root)
        win.title("Add API Key")
        win.geometry("480x380")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()  # modal

        # Center on parent
        win.update_idletasks()
        px = self.root.winfo_x() + (self.root.winfo_width()  - 480) // 2
        py = self.root.winfo_y() + (self.root.winfo_height() - 380) // 2
        win.geometry(f"480x380+{px}+{py}")

        # ── Header bar ────────────────────────────────────────────────────
        hdr = tk.Frame(win, bg=CARD)
        hdr.pack(fill="x")
        hdr_inner = tk.Frame(hdr, bg=CARD)
        hdr_inner.pack(fill="x", padx=20, pady=16)
        tk.Label(hdr_inner, text="API KEY REQUIRED",
                 font=(_FF, 14, "bold"), bg=CARD, fg=TEXT
                 ).pack(anchor="w")
        tk.Label(hdr_inner, text="Your Groq key hit its rate limit",
                 font=FONT_SMALL, bg=CARD, fg=MUTED
                 ).pack(anchor="w")

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x")

        # ── Body ──────────────────────────────────────────────────────────
        body = tk.Frame(win, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=20)

        tk.Label(body,
            text="Paste a new Groq API key below and your session\n"
                 "will resume automatically — no restart needed.",
            font=FONT_BODY, bg=BG, fg=TEXT,
            justify="left", anchor="w"
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(body,
            text="Get a free key at:  console.groq.com",
            font=(_FF, 10, "bold"), bg=BG, fg=BLUE,
            justify="left", anchor="w"
        ).pack(anchor="w", pady=(0, 16))

        # Key entry field
        entry_frame = tk.Frame(body, bg=PANEL, padx=2, pady=2)
        entry_frame.pack(fill="x", pady=(0, 6))
        entry = tk.Entry(entry_frame, font=FONT_MONO,
                         bg=CARD, fg=TEXT, insertbackground=TEXT,
                         relief="flat", bd=0)
        entry.pack(fill="x", padx=10, pady=8)
        entry.focus_set()

        # Inline validation label
        val_lbl = tk.Label(body, text="", font=FONT_SMALL, bg=BG, fg=RED)
        val_lbl.pack(anchor="w", pady=(0, 14))

        # ── Buttons ───────────────────────────────────────────────────────
        def on_submit(e=None):
            key = entry.get().strip()
            if not key:
                val_lbl.config(text="Please paste a key first.")
                return
            if not key.startswith("gsk_"):
                val_lbl.config(text="Invalid key — Groq keys start with 'gsk_'")
                return
            API_KEYS.append(key)
            _new_key_holder[0] = key
            _key_provided_event.set()
            self._key_dialog_open = False
            win.destroy()

        def on_cancel():
            _new_key_holder[0] = None
            _key_provided_event.set()   # unblock the thread so it fails gracefully
            self._key_dialog_open = False
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_cancel)
        entry.bind("<Return>", on_submit)

        add_btn = self._btn(body, "Add Key & Resume Session",
                            on_submit, color=BLUE)
        add_btn.pack(fill="x", pady=(0, 8))

        tk.Label(body, text="Cancel  (current action will fail and can be retried)",
                 font=FONT_SMALL, bg=BG, fg=MUTED,
                 cursor="hand2"
                 ).pack(anchor="center")
        body.winfo_children()[-1].bind("<Button-1>", lambda e: on_cancel())


# ====================== MAIN ======================

if __name__ == "__main__":
    root = tk.Tk()
    app = StudyBotApp(root)
    root.mainloop()
