import io
import os
import re
import json
import base64
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

import streamlit as st

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

# PDF text extraction (best-effort)
try:
    import pypdf
except Exception:
    pypdf = None


# =========================
# Nastavení / cesty
# =========================

APP_TITLE = "EdRead AI – asistent učitele (pracovní listy + metodika)"
ASSETS_DIR = "assets"

# Pokud chceš 100% shodu tabulek s PDF, ulož je jako PNG do assets/
KNOWN_TABLES = {
    "Karetní hra": os.path.join(ASSETS_DIR, "karetni_table.png"),
    "Sladké mámení": os.path.join(ASSETS_DIR, "sladke_table.png"),
    "Věnečky": os.path.join(ASSETS_DIR, "venecky_table.png"),
}

ANIMALS: List[Tuple[str, str]] = [
    ("komár", "🦟"),
    ("myš", "🐭"),
    ("sardinka", "🐟"),
    ("ježek", "🦔"),
    ("okoun", "🐟"),
    ("liška", "🦊"),
    ("tuleň", "🦭"),
    ("lev", "🦁"),
    ("lední medvěd", "🐻‍❄️"),
    ("krokodýl", "🐊"),
    ("slon", "🐘"),
    ("kosatka", "🐬"),
    ("chameleon (žolík)", "🦎"),
]

# pořadí "síly" – od nejsilnějšího nahoře po nejslabší dole (včetně žolíka poslední)
PYRAMID_ORDER = [
    "kosatka",
    "slon",
    "krokodýl",
    "lední medvěd",
    "lev",
    "tuleň",
    "liška",
    "okoun",
    "ježek",
    "sardinka",
    "myš",
    "komár",
    "chameleon (žolík)",
]


# =========================
# OpenAI volání (bez SDK, přes requests)
# =========================

import os
import streamlit as st

def get_openai_key() -> str:
    # Streamlit Cloud secrets
    if "OPENAI_API_KEY" in st.secrets:
        return str(st.secrets["OPENAI_API_KEY"]).strip()
    # lokální / jiné hostování
    return (os.getenv("OPENAI_API_KEY") or "").strip()

def get_openai_model() -> str:
    """
    Model je konfigurovatelný přes Streamlit secrets nebo ENV.
    Když není nastaven, použije se rozumný default.
    """
    if "OPENAI_MODEL" in st.secrets:
        return str(st.secrets["OPENAI_MODEL"]).strip()
    return (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()

# =========================
# Textové nástroje
# =========================

def clean_text(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    if not pypdf:
        return ""
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return clean_text("\n\n".join(parts))


def extract_text_from_docx(docx_bytes: bytes) -> str:
    doc = Document(io.BytesIO(docx_bytes))
    paras = [p.text for p in doc.paragraphs if p.text.strip()]
    return clean_text("\n\n".join(paras))


# =========================
# AI generování variant + slovníčku + otázek
# =========================

def ai_generate_variants(full_text: str, grade: int, title: str) -> Dict[str, str]:
    """
    Vytvoří SIMPL a LMP/SPU z plného textu.
    """
    system = (
        "Jsi didaktik českého jazyka a odborník na čtenářskou gramotnost na 1. stupni ZŠ. "
        "Píšeš česky naprosto bezchybně (diakritika, gramatika, styl). "
        "Úpravy musí být věcně věrné původnímu textu (nesmíš si vymýšlet fakta)."
    )

    user = f"""
Mám výchozí text pro žáky. Název: {title}. Ročník: {grade}. třída.

Úkol:
1) Vytvoř "ZJEDNODUŠENOU VERZI" textu pro daný ročník:
- zachovej všechny důležité informace potřebné k odpovědím na otázky,
- zkrať dlouhé věty, nahraď těžká slova jednoduššími,
- zachovej logickou stavbu textu,
- žádné poznámky pro učitele, jen text pro žáka.

2) Vytvoř "LMP/SPU VERZI" textu:
- ještě kratší věty, jasné odstavce,
- vysvětli případně 1–2 klíčová slova přímo v textu v závorce (maximálně),
- zachovej všechna fakta.

Vrať výstup přesně v tomto formátu:

===SIMPL===
(tvoje zjednodušená verze)

===LMP===
(tvoje LMP/SPU verze)

VÝCHOZÍ TEXT:
\"\"\"{full_text}\"\"\"
"""
    out = call_openai_chat(system, user, temperature=0.15)
    simpl = ""
    lmp = ""
    m1 = re.search(r"===SIMPL===\s*(.*?)\s*===LMP===", out, flags=re.S)
    m2 = re.search(r"===LMP===\s*(.*)$", out, flags=re.S)
    if m1:
        simpl = clean_text(m1.group(1))
    if m2:
        lmp = clean_text(m2.group(1))

    # fallback: když by model výjimečně vrátil špatný formát
    if not simpl:
        simpl = full_text
    if not lmp:
        lmp = simpl

    return {"simplified": simpl, "lmp": lmp}


def ai_generate_vocab(full_text: str, grade: int) -> List[Tuple[str, str]]:
    """
    Vybere a vysvětlí slovíčka. Vrací list (slovo, vysvětlení).
    """
    system = (
        "Jsi učitel/ka 1. stupně a odborník/ce na slovní zásobu. "
        "Vysvětluješ dětem jednoduše, jednou větou. Nepoužíváš těžká slova."
    )

    user = f"""
Z textu vyber 10 až 14 slov, která mohou být pro žáky {grade}. třídy těžší nebo důležitá.
Ke každému napiš krátké vysvětlení (max 12 slov), dětsky a přesně.

Vrať JSON pole objektů se strukturou:
[{{"slovo":"...", "vysvetleni":"..."}}, ...]

Text:
\"\"\"{full_text}\"\"\"
"""
    out = call_openai_chat(system, user, temperature=0.2)

    # robustní parsování JSON
    try:
        data = json.loads(out)
        pairs = []
        for item in data:
            w = str(item.get("slovo", "")).strip()
            e = str(item.get("vysvetleni", "")).strip()
            if w:
                pairs.append((w, e))
        return pairs[:14]
    except Exception:
        # fallback: nic nevysvětlovat
        return []


def ai_generate_questions_abc(full_text: str, grade: int, title: str) -> List[str]:
    """
    Otázky A/B/C – pro čtenářskou gramotnost.
    """
    system = (
        "Jsi odborník na čtenářskou gramotnost na 1. stupni. "
        "Otázky jsou věcně správné, odpověditelné pouze z textu. "
        "Čeština je bezchybná. Nepiš nesmyslné volby typu 'Věneček č.' apod."
    )
    user = f"""
Vytvoř pracovní otázky k textu pro {grade}. třídu, název: {title}.
Struktura:
A) 3 otázky na vyhledání informací (jednoznačně z textu)
B) 2 otázky na porozumění/interpretaci
C) 1 otázka na vlastní názor (s oporou v textu)

Každou otázku napiš s řádkem na odpověď (podtržítka).
Nepoužívej test s náhodnými písmeny, jen otevřené odpovědi.

Vrať jako tři bloky textu (A, B, C).

Text:
\"\"\"{full_text}\"\"\"
"""
    out = call_openai_chat(system, user, temperature=0.2)
    blocks = [b.strip() for b in out.split("\n\n") if b.strip()]
    if not blocks:
        # fallback – minimální
        return [
            "A) Najdi v textu\n1) _______________________________\nOdpověď: ____________________________\n",
            "B) Vysvětli\n1) _______________________________\nOdpověď: ____________________________\n",
            "C) Můj názor\n1) _______________________________\nOdpověď: ____________________________\n",
        ]
    return blocks


# =========================
# DOCX generování
# =========================

def set_doc_style(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)


def add_heading(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(14)


def add_subheading(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(12)


def add_table_image(doc: Document, img_bytes: bytes, width_cm: float = 16.0) -> None:
    if not img_bytes:
        doc.add_paragraph("⚠ Tabulka nebyla vložena (chybí obrázek).")
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(io.BytesIO(img_bytes), width=Cm(width_cm))


def load_known_table_bytes(title: str) -> bytes:
    path = KNOWN_TABLES.get(title)
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return b""


def add_intro_for_dramatization(doc: Document) -> None:
    add_subheading(doc, "Úvod")
    doc.add_paragraph(
        "Nejdřív si zahrajeme krátkou scénku. "
        "Pomůže nám pochopit situaci a připraví nás na čtení."
    )


def add_dramatization(doc: Document, title: str) -> None:
    add_subheading(doc, "Dramatizace (krátká scénka)")
    if title == "Karetní hra":
        lines = [
            "Žák A: „Mám komára! Dám ho na stůl.“",
            "Žák B: „Já dám myš. Kdo koho přebije?“",
            "Žák C: „Nevím, kdy se dává pass. Najdeme to v pravidlech?“",
            "Žák D: „Mám chameleona (žolíka). Kdy ho můžu použít?“",
            "Společně: „Přečteme text a zkusíme to podle pravidel.“",
        ]
    elif title == "Věnečky":
        lines = [
            "Žák A: „Tenhle věneček vypadá nejlíp!“",
            "Žák B: „A je důležitější vzhled, nebo chuť?“",
            "Žák C: „Podle čeho budeme hodnotit? Krém? Těsto? Cena?“",
        ]
    else:
        lines = [
            "Žákyně A: „Proč se pořád mluví o sladkostech?“",
            "Žák B: „Co je na sladkostech problém?“",
            "Žákyně C: „Najdeme v textu fakta a odlišíme je od názorů.“",
        ]
    for l in lines:
        doc.add_paragraph(l)


def add_text_block(doc: Document, title: str, full_text: str) -> None:
    add_subheading(doc, "Text k přečtení")
    doc.add_paragraph(f"NÁZEV ÚLOHY: {title.upper()}    JMÉNO:")
    doc.add_paragraph("")
    if not full_text.strip():
        warn = doc.add_paragraph("⚠ CHYBÍ TEXT K PŘEČTENÍ – bez něj nelze odpovídat na otázky.")
        warn.runs[0].bold = True
        return
    for para in full_text.split("\n"):
        para = para.strip()
        if para:
            doc.add_paragraph(para)


def add_pyramid(doc: Document) -> None:
    add_subheading(doc, "Pyramida (sloupec) pro vlepování kartiček")
    doc.add_paragraph("Vystřihni kartičky a nalep je do okýnek: nahoře nejsilnější, dole nejslabší.")
    rows = len(PYRAMID_ORDER) + 2
    table = doc.add_table(rows=rows, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # zvětšené buňky – aby se tam kartičky vešly
    for r in range(rows):
        cell = table.cell(r, 0)
        cell.width = Cm(16)
        # dáme víc řádků, aby byla buňka vyšší i bez XML triků
        p = cell.paragraphs[0]
        p.add_run("\n\n\n")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    table.cell(0, 0).text = "NAHOŘE = NEJSILNĚJŠÍ"
    table.cell(rows - 1, 0).text = "DOLE = NEJSLABŠÍ"

    for i, name in enumerate(PYRAMID_ORDER, start=1):
        cell = table.cell(i, 0)
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        hint = p.add_run(f"(sem patří: {name})")
        hint.italic = True
        hint.font.size = Pt(9)


def add_animal_cards(doc: Document) -> None:
    add_subheading(doc, "Kartičky zvířat (3 sloupce – na stříhání)")
    cols = 3
    rows = (len(ANIMALS) + cols - 1) // cols
    table = doc.add_table(rows=rows, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.text = ""
            if idx < len(ANIMALS):
                name, emoji = ANIMALS[idx]
                p1 = cell.add_paragraph()
                p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run1 = p1.add_run(emoji)
                run1.font.size = Pt(22)

                p2 = cell.add_paragraph()
                p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run2 = p2.add_run(name)
                run2.font.size = Pt(12)
                idx += 1


def add_questions(doc: Document, blocks: List[str]) -> None:
    add_subheading(doc, "Otázky A/B/C")
    for b in blocks:
        doc.add_paragraph(b)


def add_vocab(doc: Document, vocab: List[Tuple[str, str]]) -> None:
    doc.add_page_break()
    add_subheading(doc, "Slovníček (na konec pracovního listu)")
    if not vocab:
        doc.add_paragraph("• (Slovníček se nepodařilo vygenerovat. Zkontroluj API klíč nebo text.)")
        return
    for w, e in vocab:
        if e:
            doc.add_paragraph(f"• {w} = {e}")
        else:
            doc.add_paragraph(f"• {w} = _______________________________")
        doc.add_paragraph("Poznámka: _______________________________")
        doc.add_paragraph("")


def doc_to_bytes(doc: Document) -> bytes:
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def build_student_doc(title: str, grade: int, variant_label: str, text_for_variant: str,
                      table_img: bytes, questions_blocks: List[str], vocab: List[Tuple[str, str]]) -> bytes:
    doc = Document()
    set_doc_style(doc)

    add_heading(doc, f"{title} – pracovní list ({variant_label})")
    doc.add_paragraph(f"Ročník: {grade}. třída")
    doc.add_paragraph("")

    add_intro_for_dramatization(doc)
    add_dramatization(doc, title)
    doc.add_paragraph("")

    add_text_block(doc, title, text_for_variant)
    doc.add_paragraph("")

    if table_img:
        add_subheading(doc, "Tabulka (z výchozího textu)")
        add_table_image(doc, table_img, width_cm=16.0)
        doc.add_paragraph("")

    # Karetní hra: pyramida + kartičky (do všech verzí)
    if title == "Karetní hra":
        add_pyramid(doc)
        doc.add_page_break()
        add_animal_cards(doc)
        doc.add_page_break()

    add_questions(doc, questions_blocks)
    add_vocab(doc, vocab)

    return doc_to_bytes(doc)


def build_methodology_doc(title: str, grade: int) -> bytes:
    doc = Document()
    set_doc_style(doc)
    add_heading(doc, f"Metodický list – {title} ({grade}. třída)")
    doc.add_paragraph("")

    add_subheading(doc, "Doporučený postup práce")
    doc.add_paragraph("1) Dramatizace – krátká scénka (motivace a aktivace zkušenosti).")
    doc.add_paragraph("2) Slovníček – žáci vyplní slovníček na konci pracovního listu.")
    doc.add_paragraph("3) Čtení textu – žáci se vrátí k části „Text k přečtení“ a čtou.")
    doc.add_paragraph("4) Práce s tabulkou – žáci vyhledávají údaje v tabulce.")
    doc.add_paragraph("5) Otázky A/B/C – A: vyhledání, B: interpretace, C: vlastní názor.")
    doc.add_paragraph("")

    add_subheading(doc, "Rozdíly mezi verzemi (FULL / ZJEDNODUŠENÝ / LMP-SPU)")
    doc.add_paragraph("FULL: původní text beze změn (jen formátování pro práci ve třídě).")
    doc.add_paragraph("ZJEDNODUŠENÝ: zkrácené věty, jednodušší slovní zásoba, zachovaná fakta.")
    doc.add_paragraph("LMP/SPU: nejjednodušší formulace, větší čitelnost, více prostoru na odpovědi.")
    doc.add_paragraph("Ve všech verzích zůstává stejná tabulka, protože je nutná pro řešení otázek.")

    return doc_to_bytes(doc)


# =========================
# Streamlit UI
# =========================

def persist_downloads():
    g = st.session_state.get("generated")
    if not g:
        return

    st.subheader("📥 Stažení dokumentů (nezmizí po kliknutí)")
    st.download_button("⬇️ Pracovní list – FULL", g["full"], g["names"]["full"],
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_full")
    st.download_button("⬇️ Pracovní list – ZJEDNODUŠENÝ", g["simpl"], g["names"]["simpl"],
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_simpl")
    st.download_button("⬇️ Pracovní list – LMP/SPU", g["lmp"], g["names"]["lmp"],
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_lmp")
    st.download_button("⬇️ Metodický list", g["met"], g["names"]["met"],
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_met")


def main():
    st.set_page_config(page_title=APP_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.write("Vlož plný text a EdRead AI vytvoří FULL / ZJEDNODUŠENÝ / LMP-SPU + metodiku a slovníček.")

    api_key = get_openai_key()
    if not api_key:
        st.error("Chybí OPENAI_API_KEY. Bez něj EdRead AI neumí automaticky tvořit zjednodušené a LMP/SPU verze.")
        st.info("Ve Streamlit Cloud: Settings → Secrets → přidej OPENAI_API_KEY.")
        return

    title = st.selectbox("Typ materiálu", ["Karetní hra", "Věnečky", "Sladké mámení", "Jiný text (vlastní)"])
    grade = st.selectbox("Pro jaký ročník?", [3, 4, 5])

    st.markdown("### Vstup textu")
    uploaded = st.file_uploader("Nahraj PDF nebo DOCX (volitelné)", type=["pdf", "docx"])
    pasted = st.text_area("…nebo vlož text sem", height=220)

    full_text = ""
    if uploaded is not None:
        data = uploaded.read()
        if uploaded.name.lower().endswith(".pdf"):
            full_text = extract_text_from_pdf(data)
        else:
            full_text = extract_text_from_docx(data)

    if pasted.strip():
        full_text = clean_text(pasted)

    full_text = clean_text(full_text)

    st.markdown("### Tabulka")
    table_choice = st.radio("Zdroj tabulky", ["Použít tabulku pro známý text (PNG v assets/)", "Nahrát tabulku jako obrázek (PNG/JPG)", "Bez tabulky"], index=0)
    table_img_bytes = b""

    if table_choice == "Použít tabulku pro známý text (PNG v assets/)":
        if title in KNOWN_TABLES:
            table_img_bytes = load_known_table_bytes(title)
            if not table_img_bytes:
                st.warning(f"Chybí soubor tabulky: {KNOWN_TABLES[title]}")
        else:
            st.info("Pro vlastní text můžeš nahrát tabulku jako obrázek.")
    elif table_choice == "Nahrát tabulku jako obrázek (PNG/JPG)":
        img = st.file_uploader("Nahraj obrázek tabulky", type=["png", "jpg", "jpeg"], key="tab_img")
        if img:
            table_img_bytes = img.read()

    st.divider()

    if st.button("🧠 Vygenerovat dokumenty", type="primary", disabled=not bool(full_text)):
        # 1) varianty textu
        variants = ai_generate_variants(full_text, grade, title)
        simplified = variants["simplified"]
        lmp = variants["lmp"]

        # 2) slovníček (z FULL textu)
        vocab = ai_generate_vocab(full_text, grade)

        # 3) otázky (z FULL textu – aby seděly na fakta)
        questions = ai_generate_questions_abc(full_text, grade, title)

        # 4) DOCX
        doc_full = build_student_doc(title, grade, "FULL", full_text, table_img_bytes, questions, vocab)
        doc_simpl = build_student_doc(title, grade, "ZJEDNODUŠENÝ", simplified, table_img_bytes, questions, vocab)
        doc_lmp = build_student_doc(title, grade, "LMP/SPU", lmp, table_img_bytes, questions, vocab)
        doc_met = build_methodology_doc(title, grade)

        st.session_state["generated"] = {
            "full": doc_full,
            "simpl": doc_simpl,
            "lmp": doc_lmp,
            "met": doc_met,
            "names": {
                "full": f"pracovni_list_{title}_FULL.docx",
                "simpl": f"pracovni_list_{title}_ZJEDNODUSENY.docx",
                "lmp": f"pracovni_list_{title}_LMP_SPU.docx",
                "met": f"metodicky_list_{title}.docx",
            }
        }
        st.success("Hotovo. Níže můžeš stáhnout všechny soubory (tlačítka zůstanou).")

    persist_downloads()


if __name__ == "__main__":
    main()


