import io
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

import streamlit as st
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn


# =========================
# Základní nastavení
# =========================

APP_TITLE = "EdRead AI (pro diplomovou práci) – generátor pracovních listů"

ASSETS_DIR = "assets"
TEXTS_DIR = os.path.join(ASSETS_DIR, "texts")

ASSET_MAP = {
    "karetni_hra_table": os.path.join(ASSETS_DIR, "karetni_table.png"),
    "sladke_mameni_table": os.path.join(ASSETS_DIR, "sladke_tab1.png"),
    "venecky_table": os.path.join(ASSETS_DIR, "venecky_tab.png"),
}

ANIMALS = [
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

PYRAMID_ORDER_TOP_TO_BOTTOM = [
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
# Textové balíčky
# =========================

@dataclass
class TextPack:
    key: str
    title: str
    grade: int
    full_text: str
    simplified_text: str
    lmp_text: str
    table_asset_key: Optional[str]
    dramatization_student: List[str]
    dramatization_teacher_note: str
    questions_abc: List[str]
    vocab_words: List[str]


def _norm_spaces(s: str) -> str:
    return re.sub(r"[ \t]+", " ", s).strip()


def load_text_from_file(pack_key: str, variant: str) -> Optional[str]:
    """
    variant: full | simplified | lmp
    """
    fname = f"{pack_key}_{variant}.txt"
    path = os.path.join(TEXTS_DIR, fname)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                txt = f.read().strip()
            return txt if txt else None
        except Exception:
            return None
    return None


# ==== ZÁLOŽNÍ TEXTY (pokud nechceš ukládat do assets/texts, necháš je tady) ====
# DŮLEŽITÉ: Pokud máš v aktuální appce texty už vložené, klidně je sem vlož zpět.
KARETNI_FULL = "SEM VLOŽ PLNÝ TEXT Karetní hra (nebo použij assets/texts/karetni_hra_full.txt)."
KARETNI_SIMPL = "SEM VLOŽ ZJEDNODUŠENÝ TEXT Karetní hra (nebo použij assets/texts/karetni_hra_simplified.txt)."
KARETNI_LMP = "SEM VLOŽ LMP/SPU TEXT Karetní hra (nebo použij assets/texts/karetni_hra_lmp.txt)."

SLADKE_FULL = "SEM VLOŽ PLNÝ TEXT Sladké mámení (nebo použij assets/texts/sladke_mameni_full.txt)."
SLADKE_SIMPL = "SEM VLOŽ ZJEDNODUŠENÝ TEXT Sladké mámení (nebo použij assets/texts/sladke_mameni_simplified.txt)."
SLADKE_LMP = "SEM VLOŽ LMP/SPU TEXT Sladké mámení (nebo použij assets/texts/sladke_mameni_lmp.txt)."

VENECKY_FULL = "SEM VLOŽ PLNÝ TEXT Věnečky (nebo použij assets/texts/venecky_full.txt)."
VENECKY_SIMPL = "SEM VLOŽ ZJEDNODUŠENÝ TEXT Věnečky (nebo použij assets/texts/venecky_simplified.txt)."
VENECKY_LMP = "SEM VLOŽ LMP/SPU TEXT Věnečky (nebo použij assets/texts/venecky_lmp.txt)."


PACKS: Dict[str, TextPack] = {
    "karetni_hra": TextPack(
        key="karetni_hra",
        title="Karetní hra",
        grade=3,
        full_text=KARETNI_FULL,
        simplified_text=KARETNI_SIMPL,
        lmp_text=KARETNI_LMP,
        table_asset_key="karetni_hra_table",
        dramatization_student=[
            "Žák A: „Zahraju komára!“",
            "Žák B: „Já dám myš. Přebiju tě?“",
            "Žák C: „Co když zahraju dvě stejné karty?“",
            "Žák D: „Mám chameleona – můžu ho dát samotného?“",
            "Společně: „Najdeme v textu pravidlo, kdo koho přebíjí a jak se hraje žolík.“",
        ],
        dramatization_teacher_note=(
            "Krátká motivační scénka před čtením. Cílem je vyvolat potřebu hledat odpovědi přímo v textu."
        ),
        questions_abc=[
            "A) Porozumění (najdi v textu)\n"
            "1) Co je cílem hry? (1 věta)\n"
            "______________________________________________\n\n"
            "2) Co znamená ve hře slovo „pass“?\n"
            "______________________________________________\n",
            "B) Přemýšlení (vysvětli)\n"
            "3) Proč se chameleon (žolík) nesmí hrát samostatně?\n"
            "______________________________________________\n"
            "______________________________________________\n",
            "C) Můj názor\n"
            "4) Co bys poradil/a spolužákovi, aby ve hře vyhrál? (1–2 věty)\n"
            "______________________________________________\n"
            "______________________________________________\n",
        ],
        vocab_words=[
            "karetní", "živočichů", "chameleon", "rozdat", "kombinace",
            "přebít", "pass",
        ],
    ),
    "sladke_mameni": TextPack(
        key="sladke_mameni",
        title="Sladké mámení",
        grade=5,
        full_text=SLADKE_FULL,
        simplified_text=SLADKE_SIMPL,
        lmp_text=SLADKE_LMP,
        table_asset_key="sladke_mameni_table",
        dramatization_student=[
            "Žákyně A: „Mám ráda sladké, ale říká se, že to není zdravé…“",
            "Žák B: „Proč se ve světě řeší nízkokalorické sladkosti?“",
            "Žákyně C: „Jak poznáme, co je fakt a co je názor?“",
        ],
        dramatization_teacher_note="Krátká debata – aktivace zkušenosti, pak práce se slovníkem a teprve poté čtení.",
        questions_abc=[
            "A) Najdi v textu\n1) Co je podle textu hlavní problém spojený se sladkostmi?\n__________________________________\n",
            "B) Vysvětli\n2) Proč roste poptávka po nízkokalorických sladkostech?\n__________________________________\n",
            "C) Můj názor\n3) Co si myslíš o uvádění energetické hodnoty na obalu?\n__________________________________\n",
        ],
        vocab_words=[
            "epidemie", "obezita", "poptávka", "nízkokalorický", "energetický",
            "náhražka", "vláknina",
        ],
    ),
    "venecky": TextPack(
        key="venecky",
        title="Věnečky",
        grade=4,
        full_text=VENECKY_FULL,
        simplified_text=VENECKY_SIMPL,
        lmp_text=VENECKY_LMP,
        table_asset_key="venecky_table",
        dramatization_student=[
            "Žák A: „Tahle cukrárna to určitě umí nejlíp!“",
            "Žákyně B: „A podle čeho to poznáš? Jen podle vzhledu?“",
            "Žák C: „Tak si řekněme, co budeme hodnotit: chuť, krém, těsto…“",
        ],
        dramatization_teacher_note="Scénka vede žáky k pojmenování kritérií hodnocení (fakt vs. dojem).",
        questions_abc=[
            "A) Porozumění (najdi)\n1) Který věneček byl hodnocen nejlépe?\n_____________________\n",
            "B) Interpretace (vysvětli)\n2) Proč hodnotitelka u věnečku č. 3 kritizuje rumovou vůni?\n_____________________\n",
            "C) Můj názor\n3) Souhlasíš, že cena odpovídá kvalitě? Proč?\n_____________________\n",
        ],
        vocab_words=[
            "odpalované", "korpus", "pachuť", "absence", "receptura",
            "nadlehčený", "verdikt", "upraveno",
        ],
    ),
}


# =========================
# DOCX – pomocné funkce
# =========================

def set_doc_styles(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    style.font.size = Pt(11)


def add_heading(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14)


def add_subheading(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(12)


def add_par(doc: Document, text: str) -> None:
    doc.add_paragraph(_norm_spaces(text))


def add_table_image(doc: Document, asset_path: str, width_cm: float = 16.0) -> None:
    if not asset_path or not os.path.exists(asset_path):
        doc.add_paragraph("⚠ Tabulka (obrázek) nebyla nalezena – zkontroluj složku assets/ a název souboru.")
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(asset_path, width=Cm(width_cm))


def add_student_intro_and_dramatization(doc: Document) -> None:
    add_subheading(doc, "Úvod (co budeme dělat)")
    add_par(doc, "Za chvíli si zahrajeme krátkou scénku. Pomůže nám to pochopit téma dřív, než začneme číst.")
    add_subheading(doc, "Dramatizace (zahájení hodiny – krátká scénka)")


def add_dramatization_lines(doc: Document, lines: List[str]) -> None:
    for l in lines:
        doc.add_paragraph(l)


def add_text_block(doc: Document, title: str, text: str) -> None:
    add_subheading(doc, "Text k přečtení")
    add_par(doc, f"NÁZEV ÚLOHY: {title.upper()}    JMÉNO:")
    doc.add_paragraph("")

    if not text or not text.strip():
        # Tohle zabrání situaci, kdy “zmizí text” a žák nemá z čeho čerpat.
        warn = doc.add_paragraph("⚠ CHYBÍ TEXT K PŘEČTENÍ! – Doplň text do assets/texts nebo do proměnných v app.py.")
        warn.runs[0].bold = True
        return

    # vlož text po odstavcích
    for para in text.split("\n"):
        para = para.strip()
        if para:
            doc.add_paragraph(para)


def add_questions(doc: Document, questions_abc: List[str]) -> None:
    add_subheading(doc, "Otázky A/B/C")
    for block in questions_abc:
        for line in block.split("\n"):
            doc.add_paragraph(line)


def add_vocab_section(doc: Document, words: List[str]) -> None:
    add_subheading(doc, "Slovníček (na konec pracovního listu)")
    for w in words:
        doc.add_paragraph(f"• {w} = _______________________________")
        doc.add_paragraph("Poznámka žáka/žákyně: _______________________________")
        doc.add_paragraph("")


def add_pyramid_column(doc: Document) -> None:
    add_subheading(doc, "Zvířecí „pyramida“ síly (lepení)")
    add_par(doc, "Vystřihni kartičky a nalep je do okýnek. Nahoře je nejsilnější zvíře, dole nejslabší.")

    rows = len(PYRAMID_ORDER_TOP_TO_BOTTOM) + 2
    table = doc.add_table(rows=rows, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    col_width = Cm(16.0)
    for r in range(rows):
        cell = table.cell(r, 0)
        cell.width = col_width

    table.cell(0, 0).text = "NAHOŘE = NEJSILNĚJŠÍ"
    table.cell(rows - 1, 0).text = "DOLE = NEJSLABŠÍ"

    for i, animal_name in enumerate(PYRAMID_ORDER_TOP_TO_BOTTOM, start=1):
        cell = table.cell(i, 0)
        cell.text = ""
        hint = cell.add_paragraph(f"(sem patří: {animal_name})")
        hint.runs[0].italic = True
        hint.runs[0].font.size = Pt(9)


def add_animal_cards(doc: Document) -> None:
    add_subheading(doc, "Kartičky zvířat (na stříhání)")
    add_par(doc, "Vystřihni kartičky. (3 sloupce)")

    cols = 3
    rows = (len(ANIMALS) + cols - 1) // cols
    table = doc.add_table(rows=rows, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for c in range(cols):
        for r in range(rows):
            table.cell(r, c).width = Cm(5.3)

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
                run1.font.size = Pt(20)
                p2 = cell.add_paragraph()
                p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run2 = p2.add_run(name)
                run2.font.size = Pt(12)
                idx += 1


def to_bytes(doc: Document) -> bytes:
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# =========================
# Generování dokumentů
# =========================

def get_variant_text(pack: TextPack, variant: str) -> str:
    """
    Vždy se pokusí načíst text ze souboru v assets/texts.
    Když není, použije text z kódu.
    """
    file_txt = load_text_from_file(pack.key, variant)
    if file_txt:
        return file_txt

    if variant == "full":
        return pack.full_text
    if variant == "simplified":
        return pack.simplified_text
    return pack.lmp_text


def build_student_doc(pack: TextPack, variant: str) -> bytes:
    doc = Document()
    set_doc_styles(doc)

    add_heading(doc, f"{pack.title} ({pack.grade}. třída) — verze: {variant.upper()}")
    doc.add_paragraph("")

    add_student_intro_and_dramatization(doc)
    add_dramatization_lines(doc, pack.dramatization_student)
    doc.add_paragraph("")

    # ✅ OPRAVA: text je vždy vložený před tabulkou a otázkami
    text = get_variant_text(pack, variant)
    add_text_block(doc, pack.title, text)
    doc.add_paragraph("")

    # Tabulka (PNG) – ve všech verzích
    if pack.table_asset_key:
        add_subheading(doc, "Tabulka (z výchozího textu)")
        add_table_image(doc, ASSET_MAP.get(pack.table_asset_key, ""), width_cm=16.0)
        doc.add_paragraph("")

    # Speciál pro Karetní hru
    if pack.key == "karetni_hra":
        add_pyramid_column(doc)
        doc.add_page_break()
        add_animal_cards(doc)
        doc.add_page_break()

    # Otázky
    add_questions(doc, pack.questions_abc)

    # Slovníček až na konec
    doc.add_page_break()
    add_vocab_section(doc, pack.vocab_words)

    return to_bytes(doc)


def build_methodology_doc(pack: TextPack) -> bytes:
    doc = Document()
    set_doc_styles(doc)

    add_heading(doc, f"Metodický list pro učitele – {pack.title} ({pack.grade}. třída)")
    doc.add_paragraph("")

    add_subheading(doc, "Doporučený postup (důležité pořadí kroků)")
    add_par(doc,
            "1) Dramatizace (motivace) – žáci sehrají krátkou scénku.\n"
            "2) Slovníček – žáci nejprve vyplní slovníček (je na konci pracovního listu).\n"
            "3) Čtení textu – žáci se vrátí na část „Text k přečtení“.\n"
            "4) Práce s tabulkou – žáci vyhledávají údaje v tabulce.\n"
            "5) Otázky A/B/C – A vyhledání, B interpretace, C vlastní názor.\n"
            "6) Krátká reflexe."
            )

    doc.add_paragraph("")
    add_subheading(doc, "Dramatizace – poznámka pro učitele")
    add_par(doc, pack.dramatization_teacher_note)

    doc.add_paragraph("")
    add_subheading(doc, "Rozdíly mezi verzemi (pro rychlé rozhodnutí)")
    add_par(doc,
            "FULL:\n- plný text\n- tabulka je vložená\n- kompletní otázky + slovníček\n\n"
            "ZJEDNODUŠENÁ:\n- zjednodušený text\n- tabulka zůstává stejná\n- jazykově přiměřené zadání\n\n"
            "LMP/SPU:\n- nejjednodušší verze\n- tabulka zůstává stejná\n- více prostoru na odpovědi"
            )

    return to_bytes(doc)


# =========================
# Streamlit UI
# =========================

def ensure_assets_warning(pack: TextPack) -> None:
    # Tabulka
    if pack.table_asset_key:
        p = ASSET_MAP.get(pack.table_asset_key, "")
        if not p or not os.path.exists(p):
            st.warning(
                f"Chybí tabulka PNG pro '{pack.title}'. Očekávám soubor: {p}\n"
                f"→ Vlož ho do repozitáře do složky assets/."
            )
    # Texty
    for variant in ["full", "simplified", "lmp"]:
        expected = os.path.join(TEXTS_DIR, f"{pack.key}_{variant}.txt")
        if os.path.exists(expected):
            continue
        # pokud nejsou externí soubory, jen upozorníme
        st.info(
            f"Tip: můžeš vložit text pro {pack.title} ({variant}) do: {expected}\n"
            f"Pak se vždy načte správně a nikdy nezmizí."
        )


def persist_download_buttons() -> None:
    if "generated" not in st.session_state:
        return

    gen = st.session_state["generated"]
    st.subheader("📥 Stažení dokumentů")

    st.download_button(
        "⬇️ Pracovní list – FULL",
        data=gen["pl_full"],
        file_name=gen["names"]["pl_full"],
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key="dl_pl_full",
    )
    st.download_button(
        "⬇️ Pracovní list – ZJEDNODUŠENÝ",
        data=gen["pl_simplified"],
        file_name=gen["names"]["pl_simplified"],
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key="dl_pl_simplified",
    )
    st.download_button(
        "⬇️ Pracovní list – LMP/SPU",
        data=gen["pl_lmp"],
        file_name=gen["names"]["pl_lmp"],
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key="dl_pl_lmp",
    )
    st.download_button(
        "⬇️ Metodický list (učitel)",
        data=gen["methodology"],
        file_name=gen["names"]["methodology"],
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key="dl_methodology",
    )


def main():
    st.set_page_config(page_title=APP_TITLE, layout="centered")
    st.title(APP_TITLE)

    st.write("Vyber textový balíček a vygeneruj pracovní listy ve 3 verzích + metodiku.")

    pack_key = st.selectbox(
        "Vyber text",
        options=list(PACKS.keys()),
        format_func=lambda k: f"{PACKS[k].title} ({PACKS[k].grade}. třída)",
    )
    pack = PACKS[pack_key]

    ensure_assets_warning(pack)

    st.divider()

    if st.button("🧠 Vygenerovat dokumenty", type="primary"):
        pl_full = build_student_doc(pack, "full")
        pl_simplified = build_student_doc(pack, "simplified")
        pl_lmp = build_student_doc(pack, "lmp")
        methodology = build_methodology_doc(pack)

        st.session_state["generated"] = {
            "pl_full": pl_full,
            "pl_simplified": pl_simplified,
            "pl_lmp": pl_lmp,
            "methodology": methodology,
            "names": {
                "pl_full": f"pracovni_list_{pack.title}_FULL.docx",
                "pl_simplified": f"pracovni_list_{pack.title}_ZJEDNODUSENY.docx",
                "pl_lmp": f"pracovni_list_{pack.title}_LMP_SPU.docx",
                "methodology": f"metodicky_list_{pack.title}.docx",
            }
        }

        st.success("Hotovo! Dokumenty jsou připravené ke stažení níže.")

    persist_download_buttons()

    st.divider()
    st.caption("Pozn.: Text k přečtení se vkládá vždy před tabulkou a otázkami. Tabulky jsou jako PNG pro 100% shodu s PDF.")


if __name__ == "__main__":
    main()
