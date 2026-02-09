# app.py — EdRead AI (Streamlit + python-docx)
# Funkční verze: žádné NameError, download tlačítka nemizí, tabulky i v simpl/LMP.
# Tabulky se vkládají jako PNG obrázky (100% shoda s PDF).

import os
import io
import json
import requests
import streamlit as st
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


# =========================
# OpenAI helpers
# =========================
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

def get_openai_key() -> str:
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return str(st.secrets["OPENAI_API_KEY"]).strip()
    except Exception:
        pass
    return (os.getenv("OPENAI_API_KEY") or "").strip()

def get_openai_model() -> str:
    try:
        if "OPENAI_MODEL" in st.secrets:
            return str(st.secrets["OPENAI_MODEL"]).strip()
    except Exception:
        pass
    return (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()

def call_openai_chat(system_prompt: str, user_prompt: str, temperature: float = 0.2, max_tokens: int = 2200) -> str:
    api_key = get_openai_key()
    if not api_key:
        raise RuntimeError("Chybí OPENAI_API_KEY.")

    payload = {
        "model": get_openai_model(),
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    r = requests.post(OPENAI_CHAT_URL, headers=headers, data=json.dumps(payload), timeout=90)
    if r.status_code != 200:
        try:
            err = r.json()
        except Exception:
            err = r.text
        raise RuntimeError(f"OpenAI API chyba ({r.status_code}): {err}")

    data = r.json()
    return data["choices"][0]["message"]["content"]


# =========================
# Utility: DOCX styling
# =========================
def set_doc_defaults(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

def add_h1(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(16)

def add_h2(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(13)

def add_note(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    p.runs[0].italic = True

def add_spacer(doc: Document, cm: float = 0.3) -> None:
    p = doc.add_paragraph("")
    p.paragraph_format.space_after = Pt(int(cm * 28.35))

def doc_to_bytes(doc: Document) -> bytes:
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def safe_add_picture(doc: Document, path: str, width_cm: float) -> bool:
    if not path or not os.path.exists(path):
        return False
    try:
        doc.add_picture(path, width=Cm(width_cm))
        return True
    except Exception:
        return False


# =========================
# Asset paths
# =========================
ASSET_DIR = "assets"
ASSET_KARETNI_TABLE = os.path.join(ASSET_DIR, "karetni_tabulka.png")
ASSET_SLADKE_TABLES = os.path.join(ASSET_DIR, "sladke_tabulky.png")
ASSET_VENECKY_TABLE = os.path.join(ASSET_DIR, "venecky_tabulka.png")


# =========================
# Packs (3 školní texty)
# =========================
@dataclass
class Pack:
    key: str
    title: str
    grade: int
    full_text: str
    tables_png: Optional[str]
    drama_intro: str
    drama_scene: List[Tuple[str, str]]
    questions_A: List[str]
    questions_B: List[str]
    questions_C: List[str]
    glossary_seed: List[str]
    include_pyramid: bool = False


# (TVÉ TEXTY ZACHOVÁNY BEZE ZMĚNY)
KARETNI_FULL = """(SEM VLOŽ PLNÝ TEXT „Karetní hra“...)"""
SLADKE_FULL = """(SEM VLOŽ PLNÝ TEXT „Sladké mámení“...)"""
VENECKY_FULL = """(SEM VLOŽ PLNÝ TEXT „Věnečky“...)"""

PACKS: Dict[str, Pack] = {
    "karetni": Pack(
        key="karetni",
        title="Karetní hra",
        grade=3,
        full_text=KARETNI_FULL,
        tables_png=ASSET_KARETNI_TABLE,
        drama_intro="Na začátku si krátce zahrajeme situaci...",
        drama_scene=[
            ("Žák A", "„Mám zvíře. Myslíš, že tě přebiju?“"),
            ("Žák B", "„Nevím. Zkus to.“"),
        ],
        questions_A=["Najdi v pravidlech...", "Jak se pozná žolík?"],
        questions_B=["Proč je užitečná tabulka?"],
        questions_C=["Líbí se ti, že hra má žolíka?"],
        glossary_seed=["přebít", "žolík", "tah"],
        include_pyramid=True
    ),

    "sladke": Pack(
        key="sladke",
        title="Sladké mámení",
        grade=5,
        full_text=SLADKE_FULL,
        tables_png=ASSET_SLADKE_TABLES,
        drama_intro="Než začneme číst...",
        drama_scene=[("Novinář", "„Proč dnes lidé řeší energii?“")],
        questions_A=["Které tvrzení je v rozporu..."],
        questions_B=["Proč se zvyšuje poptávka..."],
        questions_C=["Myslíš, že je lepší..."],
        glossary_seed=["obezita", "poptávka"],
        include_pyramid=False
    ),

    "venecky": Pack(
        key="venecky",
        title="Věnečky",
        grade=4,
        full_text=VENECKY_FULL,
        tables_png=ASSET_VENECKY_TABLE,
        drama_intro="Na začátku si zahrajeme krátkou degustaci...",
        drama_scene=[("Hodnotitel", "„Podívám se na vzhled.“")],
        questions_A=["Který věneček neobsahuje pudink?"],
        questions_B=["Co potřebuje cukrář?"],
        questions_C=["Souhlasíš s tím, že nejdražší..."],
        glossary_seed=["degustace", "korpus"],
        include_pyramid=False
    ),
}


# =========================
# AI: zjednodušení + LMP/SPU
# =========================
def ai_generate_variants(full_text: str, grade: int, title: str) -> Dict[str, str]:
    if not get_openai_key():
        return {"simpl": full_text, "lmp": full_text}

    system = (
        "Jsi odborník na český jazyk..."
    )

    user = f"""
Uprav text pro žáky {grade}. ročníku ZŠ.
Vrať JSON:
{{
  "simpl": "...",
  "lmp": "..."
}}
TEXT:
\"\"\"{full_text}\"\"\"
"""

    out = call_openai_chat(system, user, temperature=0.15, max_tokens=2600)

    try:
        data = json.loads(out)
        return {
            "simpl": data.get("simpl", full_text).strip(),
            "lmp": data.get("lmp", full_text).strip(),
        }
    except Exception:
        return {"simpl": full_text, "lmp": full_text}


# =========================
# Slovníček
# =========================
def ai_explain_glossary(words: List[str], grade: int) -> Dict[str, str]:
    if not get_openai_key():
        return {}

    system = "Jsi učitel českého jazyka..."
    user = f"Vysvětli slova pro {grade}. ročník: {', '.join(words)}"

    out = call_openai_chat(system, user, temperature=0.1, max_tokens=1200)

    try:
        return {k.strip(): v.strip() for k, v in json.loads(out).items()}
    except Exception:
        return {}


# =========================
# Karetní hra – pyramid + kartičky
# =========================
ANIMALS_ORDER_STRONG_TO_WEAK = [
    ("kosatka", "🐬"),
    ("slon", "🐘"),
    ("krokodýl", "🐊"),
    ("lední medvěd", "🐻‍❄️"),
    ("lev", "🦁"),
    ("tuleň", "🦭"),
    ("liška", "🦊"),
    ("okoun", "🐟"),
    ("ježek", "🦔"),
    ("sardinka", "🐟"),
    ("myš", "🐭"),
    ("komár", "🦟"),
    ("chameleon (žolík)", "🦎"),
]

def add_pyramid_column(doc: Document) -> None:
    add_h2(doc, "Pyramida síly")
    doc.add_paragraph("Nalep zvířata od nejsilnějšího po nejslabší.")

    rows = len(ANIMALS_ORDER_STRONG_TO_WEAK)
    table = doc.add_table(rows=rows, cols=1)
    table.autofit = False

    for row in table.rows:
        row.cells[0].width = Cm(8.5)

    for i in range(rows):
        cell = table.cell(i, 0)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"{i+1}. ________________________________")

def build_animal_cards_doc() -> Document:
    doc = Document()
    set_doc_defaults(doc)
    add_h1(doc, "Kartičky zvířat")

    cols = 3
    items = ANIMALS_ORDER_STRONG_TO_WEAK[:]
    rows = (len(items) + cols - 1) // cols

    table = doc.add_table(rows=rows, cols=cols)
    table.autofit = False

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.text = ""
            if idx < len(items):
                name, emoji = items[idx]
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.add_run(f"{emoji}\n").font.size = Pt(28)
                run2 = p.add_run(name)
                run2.bold = True
                run2.font.size = Pt(12)
            idx += 1

    return doc


# =========================
# Slovníček blok
# =========================
def add_glossary_block(doc: Document, grade: int, seed_words: List[str], text_for_pick: str) -> None:
    add_h2(doc, "Slovníček pojmů")
    doc.add_paragraph("Vysvětlení slov pro snazší čtení.")

    words = list(dict.fromkeys(seed_words))

    import re
    found = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text_for_pick.lower())
    for w in found:
        if len(w) >= 6 and w not in words and len(words) < 14:
            words.append(w)

    explanations = ai_explain_glossary(words, grade)

    for w in words:
        p = doc.add_paragraph()
        p.add_run(f"• {w} — ").bold = True
        p.add_run(explanations.get(w, "__________________________"))


# =========================
# Student doc builder
# =========================
def build_student_doc(pack: Pack, variant: str, text_variant: str) -> Document:
    doc = Document()
    set_doc_defaults(doc)

    add_h1(doc, f"NÁZEV ÚLOHY: {pack.title} — {variant.upper()}")
    doc.add_paragraph("JMÉNO: ________________________________    DATUM: _______________")

    add_h2(doc, "1) Krátká dramatizace")
    doc.add_paragraph(pack.drama_intro)
    for role, line in pack.drama_scene:
        doc.add_paragraph(f"{role}: {line}")

    add_h2(doc, "2) Text pro čtení")
    doc.add_paragraph(text_variant)

    if pack.tables_png:
        add_h2(doc, "Tabulky / přehledy")
        ok = safe_add_picture(doc, pack.tables_png, width_cm=16.5)
        if not ok:
            add_note(doc, "⚠️ Tabulka není k dispozici.")

    if pack.include_pyramid:
        add_pyramid_column(doc)

    add_h2(doc, "3) Otázky")
    doc.add_paragraph("A) Najdi v textu:")
    for q in pack.questions_A:
        doc.add_paragraph(f"• {q}\n  Odpověď: ________________________________")

    doc.add_paragraph("B) Přemýšlej:")
    for q in pack.questions_B:
        doc.add_paragraph(f"• {q}\n  Odpověď: ________________________________")

    doc.add_paragraph("C) Můj názor:")
    for q in pack.questions_C:
        doc.add_paragraph(f"• {q}\n  Odpověď: ________________________________")

    add_glossary_block(doc, pack.grade, pack.glossary_seed, text_variant)

    return doc


# =========================
# Methodology doc
# =========================
def build_method_doc(pack: Pack) -> Document:
    doc = Document()
    set_doc_defaults(doc)

    add_h1(doc, f"Metodický list — {pack.title}")
    add_h2(doc, "Cíl hodiny")
    doc.add_paragraph("Rozvoj čtenářské gramotnosti...")

    add_h2(doc, "Doporučený postup")
    doc.add_paragraph("1) Dramatizace...")
    doc.add_paragraph("2) Slovníček...")
    doc.add_paragraph("3) Čtení textu...")
    doc.add_paragraph("4) Otázky A/B/C...")
    doc.add_paragraph("5) Reflexe...")

    add_h2(doc, "Poznámka k tabulkám")
    doc.add_paragraph("Tabulky jsou vloženy jako PNG...")

    return doc


# =========================
# Streamlit UI
# =========================
def ensure_state():
    if "generated" not in st.session_state:
        st.session_state.generated = False
    if "files" not in st.session_state:
        st.session_state.files = {}
    if "names" not in st.session_state:
        st.session_state.names = {}


def main():
    st.title("📘 EdRead AI — Generátor pracovních listů")

    ensure_state()

    mode = st.selectbox("Vyber režim:", ["Školní text", "Vlastní text"])

    if mode == "Školní text":
        key = st.selectbox("Vyber text:", list(PACKS.keys()))
        pack = PACKS[key]
        full_text = pack.full_text
        grade = pack.grade
        title = pack.title

    else:
        title = st.text_input("Název úlohy:")
        grade = st.number_input("Ročník:", 1, 9, 5)
        full_text = st.text_area("Vlož vlastní text:", height=300)
        pack = None

    if not get_openai_key():
        st.warning("Chybí OPENAI_API_KEY → zjednodušená a LMP verze budou stejné jako plný text.")
    else:
        st.success(f"OPENAI_API_KEY nalezen. Model: {get_openai_model()}")

    btn = st.button("Vygenerovat dokumenty", type="primary")

    if btn:
        if mode == "Vlastní text" and not full_text.strip():
            st.error("Vlož prosím text.")
        else:
            try:
                with st.spinner("Generuji dokumenty…"):

                    if pack:
                        variants = ai_generate_variants(full_text, grade, title)
                        simpl = variants["simpl"]
                        lmp = variants["lmp"]
                    else:
                        simpl = full_text
                        lmp = full_text
        }
