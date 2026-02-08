# app.py — EdRead AI (Streamlit + python-docx)
# FIX: Tabulka "Kdo přebije koho?" je VŽDY součástí všech verzí (plná / zjednodušená / LMP-SPU)
# a je vložena jako obrázek z originálního PDF (100% shoda).

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Dict, Optional

import streamlit as st
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

# =========================
# Nastavení assets
# =========================
ASSETS = {
    # Tabulka z pravidel Karetní hry (originál)
    "karetni_kdo_prebije_koho": "assets/karetni_kdo_prebije_koho.png",
}

# =========================
# Předpřipravený text – Karetní hra
# (Tabulka je uvnitř textu přes placeholder [TABULKA])
# =========================
KARETNI_FULL_TEXT = """
NÁZEV ÚLOHY: KARETNÍ HRA

Hra se zvířaty (karetní hra)

Herní materiál:
V balíčku jsou karty se zvířaty a jeden žolík (chameleon). Hráči dostanou karty do ruky a postupně vykládají.

Pravidla (zjednodušeně):
Hráč může vyložit takové zvíře (nebo zvířata), které je silnější než předchozí vyložená karta.
Když nemůže nebo nechce vyložit silnější kartu, řekne „PASS“.

Kdo přebije koho? (tabulka z pravidel hry)
[TABULKA]

Žolík:
Chameleon je žolík – může se počítat jako jiné zvíře (podle domluvy pravidel hry).
"""

# =========================
# Pomocné funkce – DOCX styl
# =========================
def set_doc_style(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

def add_h1(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(16)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

def add_h2(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(13)

def add_note(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    if p.runs:
        p.runs[0].italic = True

def doc_to_bytes(doc: Document) -> bytes:
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def add_table_image(doc: Document, asset_path: str, width_cm: float = 16.5) -> None:
    """
    Vloží tabulku jako obrázek – tím se zaručí, že bude identická s PDF.
    """
    try:
        doc.add_picture(asset_path, width=Cm(width_cm))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    except Exception:
        add_note(doc, f"(Chybí soubor s tabulkou: {asset_path}. Zkontroluj složku assets/.)")

# =========================
# Textové úpravy (zjednodušený / LMP)
# =========================
def simplify_text(text: str, grade: int) -> str:
    # jednoduché, stabilní zjednodušení bez rozbití placeholderu [TABULKA]
    # - zkrátí dlouhé věty
    # - ponechá řádky a bloky
    t = text.strip()
    lines = t.splitlines()
    out_lines = []
    max_len = 140 if grade >= 4 else 110

    for ln in lines:
        s = ln.strip()
        if not s:
            out_lines.append("")
            continue
        if s == "[TABULKA]":
            out_lines.append(s)
            continue
        # krátké nadpisy nech
        if len(s) <= max_len:
            out_lines.append(s)
            continue

        # rozdělení dlouhých vět
        parts = re.split(r",\s+", s)
        if len(parts) > 1:
            out_lines.append(parts[0] + ".")
            for p in parts[1:3]:
                p = p.strip()
                if p:
                    out_lines.append(p + ".")
        else:
            out_lines.append(s)

    return "\n".join(out_lines).strip()

def lmp_text(text: str, grade: int) -> str:
    # LMP/SPU = kratší úseky, častější prázdné řádky, ale TABULKA zůstává
    t = simplify_text(text, grade)
    # vlož více odstavců (bez zásahu do [TABULKA])
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t

# =========================
# Vloží text + tabulku UVNITŘ textu
# =========================
def insert_text_with_table(doc: Document, text: str, table_asset_key: Optional[str]) -> None:
    """
    Rozdělí text podle [TABULKA] a na toto místo vloží obrázek tabulky.
    Díky tomu tabulka zůstane i v easy/LMP, protože i ty verze používají [TABULKA].
    """
    parts = text.split("[TABULKA]")
    for i, part in enumerate(parts):
        part = part.strip("\n")
        if part:
            for para in part.split("\n"):
                doc.add_paragraph(para)
        if i < len(parts) - 1:
            # vložení tabulky
            if table_asset_key:
                add_note(doc, "TABULKA (originál z pravidel hry):")
                add_table_image(doc, ASSETS[table_asset_key], width_cm=16.5)
            else:
                add_note(doc, "(Tabulka není nastavena.)")

# =========================
# Dramatizace (bez učitelské věty, ta patří jen do metodiky)
# =========================
def add_dramatization_karetni(doc: Document) -> None:
    add_h2(doc, "1) KRÁTKÁ DRAMATIZACE (na začátku)")
    doc.add_paragraph("Zahrajte krátkou scénku, aby děti pochopily smysl tabulky „Kdo přebije koho?“ ještě před čtením.")
    lines = [
        "Hráč 1: „Vykládám lišku!“",
        "Hráč 2: „Chci tě přebít. Podívám se do tabulky, kdo lišku přebije.“",
        "Hráč 3: „Já mám tuleně! Tak vykládám tuleně.“",
        "Hráč 1: „Nemám nic silnějšího, říkám PASS.“",
        "Hráč 2: „Mám žolíka – chameleona. Pomůže mi doplnit kombinaci.“",
    ]
    for ln in lines:
        doc.add_paragraph(f"• {ln}")

# =========================
# Otázky (jednoduché a stabilní)
# =========================
def add_questions_karetni(doc: Document) -> None:
    add_h2(doc, "2) OTÁZKY K TEXTU")
    doc.add_paragraph("A) Najdi v textu")
    doc.add_paragraph("1. Co udělá hráč, když nemůže vyložit silnější kartu?")
    doc.add_paragraph("Odpověď: _________________________________________________")
    doc.add_paragraph("2. K čemu slouží tabulka „Kdo přebije koho?“")
    doc.add_paragraph("Odpověď: _________________________________________________")
    doc.add_paragraph("")
    doc.add_paragraph("B) Přemýšlej")
    doc.add_paragraph("3. Proč je výhodné umět se v tabulce rychle orientovat?")
    doc.add_paragraph("Odpověď: _________________________________________________")
    doc.add_paragraph("")
    doc.add_paragraph("C) Můj názor")
    doc.add_paragraph("4. Líbí se ti taková hra? Proč ano / ne?")
    doc.add_paragraph("Odpověď: _________________________________________________")

# =========================
# Metodika – manuál
# =========================
def build_methodology_doc() -> Document:
    doc = Document()
    set_doc_style(doc)
    add_h1(doc, "METODICKÝ LIST – KARETNÍ HRA (3. třída)")

    add_h2(doc, "Doporučený postup hodiny")
    doc.add_paragraph("1) Úvod a naladění (1 min): učitel stručně řekne, že si žáci zahrají scénku, aby pochopili pravidla.")
    doc.add_paragraph("2) Dramatizace (5 min): krátká scénka podle pracovního listu.")
    doc.add_paragraph("3) Slovníček (5 min): učitel pošle žáky na konec listu – vyjasní významy slov.")
    doc.add_paragraph("4) Čtení textu (10–12 min): žáci čtou a pracují s tabulkou uvnitř textu.")
    doc.add_paragraph("5) Otázky (12–15 min): žáci odpovídají s oporou o text a tabulku.")

    add_h2(doc, "Rozdíly mezi verzemi")
    doc.add_paragraph("• Plná verze: plný text + tabulka uvnitř textu.")
    doc.add_paragraph("• Zjednodušená: jednodušší věty, ale tabulka zůstává na stejném místě.")
    doc.add_paragraph("• LMP/SPU: kratší odstavce, více členění, tabulka zůstává na stejném místě.")

    add_h2(doc, "Poznámka k tabulce")
    doc.add_paragraph("Tabulka je vložena jako obrázek z originálních pravidel → je identická ve všech verzích.")

    return doc

# =========================
# SLOVNÍČEK – na konec (jednoduchý, ale funkční)
# =========================
def add_vocab_end(doc: Document) -> None:
    doc.add_page_break()
    add_h2(doc, "SLOVNÍČEK (na konec pracovního listu)")
    items = [
        ("přebít", "zahrát silnější kartu"),
        ("PASS", "když nehraju a nechám hrát dalšího"),
        ("žolík", "karta, která může být „za jiné“"),
        ("orientovat se", "rychle najít, co potřebuji"),
    ]
    for w, exp in items:
        p = doc.add_paragraph()
        r = p.add_run(f"• {w} – ")
        r.bold = True
        p.add_run(exp)
        doc.add_paragraph("Moje poznámka: ________________________________________________")

# =========================
# Build student doc (full/easy/lmp) – TABULKA vždy uvnitř
# =========================
@dataclass
class Pack:
    title: str
    grade: int
    full_text: str
    table_asset_key: Optional[str]

def build_student_doc(pack: Pack, variant: str) -> Document:
    doc = Document()
    set_doc_style(doc)

    add_h1(doc, f"PRACOVNÍ LIST – {pack.title}")
    doc.add_paragraph("Jméno: ____________________________   Třída: ________   Datum: __________")

    # dramatizace
    add_dramatization_karetni(doc)

    # text podle verze (ale placeholder [TABULKA] se zachová)
    add_h2(doc, "TEXT K PŘEČTENÍ")
    if variant == "full":
        t = pack.full_text
    elif variant == "easy":
        t = simplify_text(pack.full_text, pack.grade)
    else:
        t = lmp_text(pack.full_text, pack.grade)

    # vložení textu + tabulky uvnitř textu
    insert_text_with_table(doc, t, pack.table_asset_key)

    # otázky
    add_questions_karetni(doc)

    # slovníček na konec
    add_vocab_end(doc)

    return doc

# =========================
# STREAMLIT UI – tlačítka nezmizí (session_state)
# =========================
def main():
    st.set_page_config(page_title="EdRead AI – Karetní hra", layout="wide")
    st.title("EdRead AI – Karetní hra (3. třída)")

    st.info(
        "Tento modul generuje 3 pracovní listy (plný / zjednodušený / LMP-SPU) + metodiku.\n"
        "Tabulka „Kdo přebije koho?“ je vždy vložena jako obrázek z originálu a je stejná ve všech verzích."
    )

    pack = Pack(
        title="KARETNÍ HRA",
        grade=3,
        full_text=KARETNI_FULL_TEXT.strip(),
        table_asset_key="karetni_kdo_prebije_koho",
    )

    if "docs" not in st.session_state:
        st.session_state.docs = {}

    if st.button("Vygenerovat dokumenty", type="primary"):
        pl_full = build_student_doc(pack, "full")
        pl_easy = build_student_doc(pack, "easy")
        pl_lmp = build_student_doc(pack, "lmp")
        metodika = build_methodology_doc()

        st.session_state.docs = {
            "Pracovní list – plný.docx": doc_to_bytes(pl_full),
            "Pracovní list – zjednodušený.docx": doc_to_bytes(pl_easy),
            "Pracovní list – LMP-SPU.docx": doc_to_bytes(pl_lmp),
            "Metodický list.docx": doc_to_bytes(metodika),
        }
        st.success("Hotovo. Dokumenty jsou připravené ke stažení.")

    st.subheader("Stažení")
    if st.session_state.docs:
        for fname, fbytes in st.session_state.docs.items():
            st.download_button(
                label=f"⬇️ {fname}",
                data=fbytes,
                file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"dl_{fname}",  # unikátní klíč → tlačítka po kliknutí nemizí
            )
    else:
        st.write("Nejdřív klikni na **Vygenerovat dokumenty**.")

if __name__ == "__main__":
    main()
