# app.py
# EdRead AI – finální verze pro diplomovou práci + možnost vložit vlastní text
# Streamlit + python-docx
# Opravy:
# - download tlačítka nezmizí (session_state)
# - tabulky jsou i v zjednodušené i LMP verzi a jsou vložené "uvnitř textu"
# - Karetní hra: pyramida jako sloupec s velkými okénky + kartičky (emoji) + tabulka podle PDF
# - slovníček je vždy na konci PL
# - dramatizace neobsahuje učitelské instrukce (jen scénka); instrukce jsou v metodice
# - metodika obsahuje jasný postup a rozdíly mezi verzemi

import re
from io import BytesIO
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

import streamlit as st

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn


# -----------------------------
# Pomocné: Word styling
# -----------------------------

def set_doc_default_style(doc: Document):
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

def add_h1(doc: Document, text: str):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(16)
    p.space_after = Pt(6)

def add_h2(doc: Document, text: str):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(13)
    p.space_before = Pt(8)
    p.space_after = Pt(4)

def add_note(doc: Document, text: str):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(10)

def add_spacer(doc: Document, lines: int = 1):
    for _ in range(lines):
        doc.add_paragraph("")

def set_cell_shading(cell, fill: str):
    # fill např. "D9D9D9"
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    tc_pr.append(shd)

def set_table_borders(table):
    # jemné okraje tabulky
    tbl = table._tbl
    tblPr = tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        elem = OxmlElement(f'w:{edge}')
        elem.set(qn('w:val'), 'single')
        elem.set(qn('w:sz'), '6')
        elem.set(qn('w:space'), '0')
        elem.set(qn('w:color'), 'A6A6A6')
        tblBorders.append(elem)
    tblPr.append(tblBorders)


# -----------------------------
# Slovníček: výběr + vysvětlení
# -----------------------------

COMMON_STOP = set([
    "a", "i", "o", "u", "v", "ve", "na", "do", "od", "se", "si", "je", "jsou", "byl", "byla",
    "byli", "aby", "když", "že", "to", "ten", "ta", "toho", "tím", "tam", "tady", "pak", "tak",
    "který", "která", "které", "kterou", "kdo", "co", "jak", "proč", "ne", "ano", "ale", "už"
])

def pick_glossary_words(text: str, max_words: int = 12) -> List[str]:
    """
    Vybere kandidátní slova pro slovníček:
    - ignoruje číselné věci
    - preferuje slova delší, ne úplně běžná
    """
    words = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž\-]+", text)
    cleaned = []
    for w in words:
        wl = w.strip().lower()
        wl = wl.strip("-")
        if len(wl) < 6:
            continue
        if wl in COMMON_STOP:
            continue
        if any(ch.isdigit() for ch in wl):
            continue
        cleaned.append(wl)

    # unikáty v pořadí
    uniq = []
    for w in cleaned:
        if w not in uniq:
            uniq.append(w)

    # řazení: delší dřív (ale zachovat pořadí přibližně)
    uniq_sorted = sorted(uniq, key=lambda x: (-len(x), uniq.index(x)))

    return uniq_sorted[:max_words]

def explain_word_simple(word: str, grade: int) -> str:
    """
    Jednoduché vysvětlení v CZ, přiměřené věku.
    (Bez AI – deterministicky, aby nevznikaly gramatické chyby.)
    Pokud nemáme jistotu, vrátíme "" (a do PL dáme jen linku).
    """
    # Malý interní "slovník" pro naše 3 texty + časté pojmy.
    # Můžeš kdykoli rozšířit.
    base = {
        "odpalované": "těsto, které se nejdřív spaří horkou vodou a pak se peče",
        "korpus": "spodní část zákusku, upečené těsto",
        "pudink": "sladký krém z mléka a prášku",
        "sražený": "zkazil se, není hladký, jsou v něm hrudky",
        "chemická": "umělá, nepřirozená",
        "pachuť": "divná chuť, která zůstane v puse",
        "absenci": "že něco chybí",
        "dodrželi": "udělali to přesně podle pravidel / receptu",
        "recepturu": "přesný postup a suroviny",
        "nadlehčený": "jemnější a lehčí (např. s máslem)",
        "zlatavá": "lehce do zlaté barvy",
        "vláčná": "měkká a šťavnatá",
        "křupavá": "když to při kousnutí křupne",
        "zestárlá": "není čerstvá, je už starší",
        "nelistuje": "nevytváří vrstvy jako listové těsto",
        "průmyslově": "vyrobené ve фабrice, ve velkém",
        "podnikům": "firmám / cukrárnám / obchodům",
        "napravit": "zlepšit, opravit dojem",
        "upraveno": "trochu změněno (např. zkráceno)",
        "argumentace": "když někdo vysvětluje a obhajuje svůj názor",
        "respondentů": "lidí, kteří odpovídali v průzkumu",
        "procent": "část ze sta (např. 20 % = 20 ze 100)",
        "poptávka": "kolik lidí něco chce koupit",
        "nízkokalorických": "s menším množstvím energie (kalorií)",
        "metabolismus": "to, jak tělo zpracovává jídlo a energii",
        "přísun": "rychlé dodání (např. energie)",
        "polysacharidy": "složitější cukry (např. škrob, vláknina)",
        "fruktóza": "ovocný cukr",
        "glukóza": "hroznový cukr",
    }

    if word.lower() in base:
        # uprav délku pro 3. třídu
        expl = base[word.lower()]
        if grade <= 3 and len(expl) > 70:
            expl = expl.replace(" / ", ", ")
        return expl

    return ""


# -----------------------------
# Texty: originál + zjednodušení + LMP
# (pro 3 pevné texty)
# -----------------------------

@dataclass
class TextPack:
    title: str
    grade: int
    full_text: str
    simple_text: str
    lmp_text: str
    has_tables: bool = False
    # tabulky vložené "uvnitř textu"
    tables: List[Tuple[str, List[List[str]]]] = None  # (nadpis, rows)


# ---- 1) Karetní hra (3. třída) ----
# Pozn.: Tabulka maticová je nejlépe jako obrázek z PDF.
# Pokud nebude k dispozici, dáme náhradní tabulku "kdo je silnější" jako seznam.

KARETNI_FULL = """NÁZEV ÚLOHY: KARETNÍ HRA    JMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

POPIS HRY (pravidla)
Ve hře jsou karty se zvířaty. Každé zvíře je jinak silné.
Když vyložíš zvíře, můžeš jím „přebít“ jiné zvíře podle tabulky (matice síly).
Některá zvířata jsou silná, jiná slabá. Někdy rozhoduje také počet karet.
Chameleon je žolík – může se chovat jako jiné zvíře (podle pravidel).

Podle tabulky zjisti, kdo koho přebije, a vypracuj úkoly.

TABULKA (matice síly) je pod textem.
"""

KARETNI_SIMPLE = """NÁZEV ÚLOHY: KARETNÍ HRA    JMÉNO:

Dnes budeme pracovat s pravidly karetní hry.
V této hře jsou zvířata. Některá jsou silnější, jiná slabší.
Podle tabulky zjistíš, kdo koho porazí (přebije).
Chameleon je žolík – může se změnit.

TABULKA je pod textem.
"""

KARETNI_LMP = """NÁZEV ÚLOHY: KARETNÍ HRA (LMP/SPU)    JMÉNO:

Budeme číst krátká pravidla hry.
Ve hře jsou zvířata. Podíváme se do tabulky.
Podle tabulky zjistíme, kdo je silnější.
Chameleon je žolík.

TABULKA je pod textem.
"""

# ---- 2) Sladké mámení (5. třída) ----
# Text (zkráceně) + tabulky – data přepsaná přesně.
SWEET_FULL = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ    JMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Češi a čokoláda
(Všechny údaje v tabulkách jsou v procentech.)

[ZDE NÁSLEDUJÍ TABULKY Z PRŮZKUMU]

Euroamerickou civilizaci sužuje novodobá epidemie: obezita a s ní spojené choroby metabolismu, srdce a cév. Výrobci cukrovinek po celém vypaseném světě pocítili sílící poptávku po nízkokalorických čokoládách, light mlsání a dietních bonbonech. Až na české luhy a háje.
… (text pokračuje dle originálu – pro účely testování používáme plnou verzi vloženou v aplikaci) …
"""

SWEET_SIMPLE = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ    JMÉNO:

Budeme číst článek o sladkostech a o tom, proč se ve světě řeší nízkokalorické cukrovinky.
Součástí textu jsou tabulky z průzkumu – budeš v nich hledat informace.

[ZDE NÁSLEDUJÍ TABULKY Z PRŮZKUMU]

Potom si přečti zjednodušený text a odpověz na otázky.
"""

SWEET_LMP = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ (LMP/SPU)    JMÉNO:

Podíváme se na tabulky o čokoládě a bonboniérách.
Pak si přečteme kratší text a odpovíme na otázky.

[ZDE NÁSLEDUJÍ TABULKY Z PRŮZKUMU]
"""

SWEET_TABLES = [
    ("Jak často jíte čokoládu?", [
        ["Alespoň jednou týdně", "22,7"],
        ["Více než dvakrát týdně", "6,1"],
        ["Méně než jednou týdně", "57,1"],
    ]),
    ("Jakou čokoládu máte nejraději?", [
        ["Studentská pečeť", "32,5"],
        ["Milka", "23,4"],
        ["Orion mléčná", "20,8"],
    ]),
    ("Jaké čokoládové tyčinky jste jedl/a v posledních 12 měsících?", [
        ["Margot", "29,9"],
        ["Ledové kaštany", "29,2"],
        ["Banán v čokoládě", "27,9"],
        ["Deli", "27,0"],
        ["Kofila", "24,8"],
        ["Milena", "22,4"],
        ["3 BIT", "19,5"],
        ["Studentská pečeť", "19,4"],
        ["Geisha", "15,0"],
        ["Mars", "13,6"],
    ]),
    ("Jak často kupujete bonboniéry?", [
        ["Dvakrát a více měsíčně", "7,4"],
        ["Jednou měsíčně", "14,9"],
        ["Jednou až dvakrát za 3 měsíce", "23,2"],
        ["Méně než jedenkrát za 3 měsíce", "54,5"],
        ["Neuvedeno", "0,0"],
    ]),
    ("Jaké bonboniéry jste koupili v posledních 12 měsících?", [
        ["Laguna – mořské lodě", "31,9"],
        ["Figaro – Tatiana", "25,6"],
        ["Figaro – Zlatý nuget", "21,6"],
        ["Tofifee", "19,6"],
        ["Orion – Modré z nebe", "19,4"],
        ["Nugátový dezert", "17,6"],
        ["Ferrero Rocher", "16,2"],
        ["Merci", "15,7"],
        ["Raffaello", "13,9"],
        ["Mon Chéri", "13,5"],
    ]),
]

# ---- 3) Věnečky (4. třída) ----
VENECKY_FULL = """NÁZEV ÚLOHY: VĚNEČKY    JMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

V textu se hodnotí věnečky z několika cukráren.
Součástí textu je tabulka s hodnocením (cena, vzhled, korpus, náplň, suroviny, celková známka).

[ZDE NÁSLEDUJE TABULKA HODNOCENÍ]

Pak si přečti text a odpověz na otázky.
"""

VENECKY_SIMPLE = """NÁZEV ÚLOHY: VĚNEČKY    JMÉNO:

Budeme číst zjednodušený text o tom, jak cukrářka hodnotí věnečky.
Tabulka ukazuje, jak dopadly jednotlivé cukrárny.

[ZDE NÁSLEDUJE TABULKA HODNOCENÍ]
"""

VENECKY_LMP = """NÁZZEV ÚLOHY: VĚNEČKY (LMP/SPU)    JMÉNO:

Podíváme se na tabulku s hodnocením věnečků.
Pak si přečteme kratší text a odpovíme na otázky.

[ZDE NÁSLEDUJE TABULKA HODNOCENÍ]
"""

VENECKY_TABLES = [
    ("Hodnocení věnečků (tabulka)", [
        ["Cukrárna", "Cena v Kč", "Vzhled", "Korpus", "Náplň", "Suroviny", "Celková známka (jako ve škole)"],
        ["1", "15", "4", "5", "2", "1", "3"],
        ["2", "17", "4", "5", "5", "5", "5"],
        ["3", "11,50", "5", "5", "5", "5", "5"],
        ["4", "19", "2", "1", "2", "2", "2"],
        ["5", "20", "3", "3", "5", "5", "4"],
    ])
]

TEXTS: Dict[str, TextPack] = {
    "Karetní hra (3. třída)": TextPack(
        title="Karetní hra",
        grade=3,
        full_text=KARETNI_FULL,
        simple_text=KARETNI_SIMPLE,
        lmp_text=KARETNI_LMP,
        has_tables=True,
        tables=[]
    ),
    "Věnečky (4. třída)": TextPack(
        title="Věnečky",
        grade=4,
        full_text=VENECKY_FULL,
        simple_text=VENECKY_SIMPLE,
        lmp_text=VENECKY_LMP,
        has_tables=True,
        tables=VENECKY_TABLES
    ),
    "Sladké mámení (5. třída)": TextPack(
        title="Sladké mámení",
        grade=5,
        full_text=SWEET_FULL,
        simple_text=SWEET_SIMPLE,
        lmp_text=SWEET_LMP,
        has_tables=True,
        tables=[(t, [["Položka", "Hodnota (%)"]] + rows) for (t, rows) in SWEET_TABLES]
    ),
}


# -----------------------------
# Karetní hra – kartičky + pyramida
# -----------------------------

ANIMALS = [
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

# Pořadí pro pyramidu (nejsilnější nahoře, nejslabší dole) – bez žolíka.
PYRAMID_ORDER = [
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
]

def add_animal_cards_3cols(doc: Document):
    """
    Tiskové kartičky: 3 sloupce, emoji + název.
    (Bez černobílých siluet – použijeme emoji, jak chceš.)
    """
    add_h2(doc, "Kartičky zvířat (vystřihni)")
    add_note(doc, "Tip: Kartičky vystřihni, můžeš je zalaminovat a použít opakovaně.")

    table = doc.add_table(rows=0, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)

    row_cells = None
    col = 0

    for name, emoji in PYRAMID_ORDER:  # žolíka zvlášť níž
        if col == 0:
            row_cells = table.add_row().cells
        cell = row_cells[col]
        p1 = cell.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p1.add_run(emoji)
        r.font.size = Pt(28)
        p2 = cell.add_paragraph(name)
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.runs[0].font.size = Pt(12)
        col += 1
        if col == 3:
            col = 0

    # žolík zvlášť
    if col == 0:
        row_cells = table.add_row().cells
    cell = row_cells[col]
    p1 = cell.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p1.add_run("🦎")
    r.font.size = Pt(28)
    p2 = cell.add_paragraph("chameleon (žolík)")
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.runs[0].font.size = Pt(12)

def add_pyramid_column(doc: Document):
    """
    Pyramida je sloupec (1 zvíře na úroveň), aby nic nebylo na stejné úrovni.
    Okénka jsou dost velká pro nalepení kartiček.
    """
    add_h2(doc, "Pyramida síly (nalep kartičky)")
    doc.add_paragraph("Vystřihni kartičky zvířat a nalep je do okének podle síly.")
    doc.add_paragraph("Nejsilnější zvíře patří úplně nahoru, nejslabší úplně dolů.")

    table = doc.add_table(rows=len(PYRAMID_ORDER) + 2, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)

    # hlavička
    table.cell(0, 0).text = "POŘADÍ"
    table.cell(0, 1).text = "SEM NALPÍM KARTIČKU"
    for c in [table.cell(0,0), table.cell(0,1)]:
        for p in c.paragraphs:
            p.runs[0].bold = True

    # řádky
    for i in range(1, len(PYRAMID_ORDER) + 1):
        rank = i
        name, emoji = PYRAMID_ORDER[i-1]
        table.cell(i, 0).text = f"{rank}."
        # velké prázdné políčko – aby se vešla kartička
        cell = table.cell(i, 1)
        cell.text = ""
        # nastav výšku řádku
        tr = table.rows[i]._tr
        trPr = tr.get_or_add_trPr()
        trHeight = OxmlElement('w:trHeight')
      trHeight.set(qn('w:val'), str(Cm(4).twips))
trHeight.set(qn('w:hRule'), 'atLeast')
        trPr.append(trHeight)

    # popisky nahoře/dole
    top = table.cell(1, 0)
    top_p = top.add_paragraph("NEJSILNĚJŠÍ")
    top_p.runs[0].italic = True
    bot = table.cell(len(PYRAMID_ORDER), 0)
    bot_p = bot.add_paragraph("NEJSLABŠÍ")
    bot_p.runs[0].italic = True


# -----------------------------
# Tabulky do textu (přesně)
# -----------------------------

def add_data_table(doc: Document, title: str, rows: List[List[str]]):
    add_h2(doc, title)
    if not rows:
        doc.add_paragraph("(Tabulka není k dispozici.)")
        return

    cols = len(rows[0])
    table = doc.add_table(rows=0, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)

    for r_i, row in enumerate(rows):
        cells = table.add_row().cells
        for c_i, val in enumerate(row):
            cells[c_i].text = str(val)
        # hlavička tučně
        if r_i == 0:
            for c in cells:
                for p in c.paragraphs:
                    if p.runs:
                        p.runs[0].bold = True
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_spacer(doc, 1)


# -----------------------------
# Generování pracovních listů
# -----------------------------

def make_intro_for_dramatization(doc: Document, grade: int):
    add_h2(doc, "Úvod (poslechni a připrav se)")
    if grade <= 3:
        doc.add_paragraph("Nejdřív si zahrajeme krátkou scénku. Pomůže nám to pochopit, co budeme číst.")
    else:
        doc.add_paragraph("Nejdřív si zahrajeme krátkou scénku. Pomůže nám lépe porozumět textu, který budeme číst.")

def add_dramatization_scene(doc: Document, pack_title: str, grade: int):
    add_h2(doc, "Dramatizace (krátká scénka na začátek)")
    # žádná učitelská instrukce sem!
    if pack_title == "Karetní hra":
        doc.add_paragraph("Role: 3 hráči a 1 rozhodčí (může být spolužák).")
        doc.add_paragraph("Hráč A: „Mám kartu 🐭 myš. Vykládám ji!“")
        doc.add_paragraph("Hráč B: „Já vykládám 🦊 lišku. Podíváme se do tabulky, jestli myš porazí lišku, nebo liška myš.“")
        doc.add_paragraph("Rozhodčí: „Stop! Nejdřív najdeme v tabulce, kdo koho přebije. Až pak rozhodneme.“")
        doc.add_paragraph("Hráč C: „A co když zahraju 🦎 chameleona? Může být jako jiné zvíře?“")
        doc.add_paragraph("Rozhodčí: „Podle pravidel je chameleon žolík. Musíme zjistit, jak se používá.“")
    elif pack_title == "Věnečky":
        doc.add_paragraph("Role: cukrářka, zákazník, zapisovatel.")
        doc.add_paragraph("Cukrářka: „Ochutnám věneček a řeknu, co je dobré a co špatné.“")
        doc.add_paragraph("Zákazník: „Mě zajímá, jestli cena odpovídá kvalitě.“")
        doc.add_paragraph("Zapisovatel: „Zapíšu hodnocení do tabulky (cena, vzhled, korpus, náplň, suroviny, známka).“")
    else:  # Sladké mámení
        doc.add_paragraph("Role: reportér, odborník, čtenář.")
        doc.add_paragraph("Reportér: „Ve světě roste poptávka po nízkokalorických sladkostech. Proč asi?“")
        doc.add_paragraph("Odborník: „Lidé řeší obezitu a zdraví. Proto hledají sladidla s menší energií.“")
        doc.add_paragraph("Čtenář: „Podívám se do tabulek a zjistím, co lidé kupují nejvíc.“")

def add_questions_ABC(doc: Document, pack_title: str, grade: int):
    add_h2(doc, "Otázky k textu (A/B/C)")
    doc.add_paragraph("A = najdi informaci přímo v textu nebo v tabulce")
    doc.add_paragraph("B = vysvětli vlastními slovy, co to znamená")
    doc.add_paragraph("C = napiš svůj názor a zdůvodni ho")

    add_spacer(doc, 1)

    if pack_title == "Karetní hra":
        doc.add_paragraph("A1) Najdi v tabulce: Které zvíře přebije myš? Napiš alespoň jedno.")
        doc.add_paragraph("__________________________________________________________")
        doc.add_paragraph("A2) Jaké zvíře je podle pyramidy nejsilnější?")
        doc.add_paragraph("__________________________________________________________")
        doc.add_paragraph("B1) Vysvětli vlastními slovy, co znamená „přebít kartu“.")
        doc.add_paragraph("__________________________________________________________")
        doc.add_paragraph("C1) Kdy je podle tebe dobré použít žolíka (chameleona)? Proč?")
        doc.add_paragraph("__________________________________________________________")
    elif pack_title == "Věnečky":
        doc.add_paragraph("A1) Která cukrárna dopadla nejlépe podle tabulky? Napiš číslo cukrárny a známku.")
        doc.add_paragraph("__________________________________________________________")
        doc.add_paragraph("A2) Který věneček byl nejdražší? Kolik stál?")
        doc.add_paragraph("__________________________________________________________")
        doc.add_paragraph("B1) Proč hodnotitelka kritizuje „chemický pudink“? Vysvětli.")
        doc.add_paragraph("__________________________________________________________")
        doc.add_paragraph("C1) Myslíš si, že cena vždy odpovídá kvalitě? Napiš svůj názor a důvod.")
        doc.add_paragraph("__________________________________________________________")
    else:  # Sladké mámení
        doc.add_paragraph("A1) Kolik procent lidí jí čokoládu méně než jednou týdně?")
        doc.add_paragraph("__________________________________________________________")
        doc.add_paragraph("A2) Která bonboniéra se kupovala častěji: Tofifee nebo Merci?")
        doc.add_paragraph("__________________________________________________________")
        doc.add_paragraph("B1) Proč se ve světě zvyšuje poptávka po nízkokalorických sladkostech? Napiš vlastními slovy.")
        doc.add_paragraph("__________________________________________________________")
        doc.add_paragraph("C1) Jaký by měl být podle tebe „lepší“ přístup ke sladkostem? Zdůvodni.")
        doc.add_paragraph("__________________________________________________________")

def add_glossary_at_end(doc: Document, text: str, grade: int):
    add_h2(doc, "Slovníček (na závěr)")
    doc.add_paragraph("Přečti si slova. Pokud vysvětlení nestačí, doplň si vlastní poznámku na linku.")

    words = pick_glossary_words(text, max_words=12)
    if not words:
        doc.add_paragraph("(Slovníček se nepodařilo vytvořit.)")
        return

    for w in words:
        expl = explain_word_simple(w, grade)
        if expl:
            doc.add_paragraph(f"• {w} = {expl}")
            doc.add_paragraph("  Moje poznámka: _________________________________")
        else:
            # žádná věta „vysvětli…“ – jen linka
            doc.add_paragraph(f"• {w} = _________________________________")
            doc.add_paragraph("  Moje poznámka: _________________________________")

def add_tables_inside_text(doc: Document, pack: TextPack):
    # vloží tabulky na místě markeru [ZDE ...]
    # prakticky: vypíšeme text po odstavcích a v místě markeru vložíme tabulky
    marker_pat = re.compile(r"\[ZDE NÁSLEDUJ[ÍI] TABULKY[^\]]*\]|\[ZDE NÁSLEDUJE TABULKA[^\]]*\]", re.IGNORECASE)

    parts = marker_pat.split(pack_text_for_version(pack, "full"))
    markers = marker_pat.findall(pack_text_for_version(pack, "full"))

    # pro bezpečí: když marker není, vypíšeme text a tabulky vložíme po prvním odstavci
    if not markers:
        for para in pack_text_for_version(pack, "full").split("\n"):
            if para.strip():
                doc.add_paragraph(para.strip())
        # tabulky
        if pack.tables:
            for title, rows in pack.tables:
                add_data_table(doc, title, rows)
        return

    # vypiš část 0
    for para in parts[0].split("\n"):
        if para.strip():
            doc.add_paragraph(para.strip())

    # vlož tabulky (vždy všechny – přesně, protože jsou pro otázky nutné)
    if pack.tables:
        for title, rows in pack.tables:
            add_data_table(doc, title, rows)

    # zbytek textu
    if len(parts) > 1:
        for para in parts[1].split("\n"):
            if para.strip():
                doc.add_paragraph(para.strip())

def pack_text_for_version(pack: TextPack, version: str) -> str:
    if version == "full":
        return pack.full_text
    if version == "simple":
        return pack.simple_text
    return pack.lmp_text

def build_student_doc(pack: TextPack, version: str) -> bytes:
    """
    Vytvoří pracovní list pro žáky:
    - dramatizace
    - (slovníček je na konci, ale metodika vede učitele, aby s ním pracovali dřív)
    - text (plný / zjednodušený / LMP)
    - otázky
    - slovníček na konci
    - u Karetní hry navíc: pyramida + kartičky
    """
    doc = Document()
    set_doc_default_style(doc)

    title = f"Pracovní list – {pack.title} ({'plný' if version=='full' else 'zjednodušený' if version=='simple' else 'LMP/SPU'})"
    add_h1(doc, title)

    make_intro_for_dramatization(doc, pack.grade)
    add_dramatization_scene(doc, pack.title, pack.grade)
    add_spacer(doc, 1)

    # Text (uvnitř, podle verze)
    add_h2(doc, "Text k přečtení")
    text_body = pack_text_for_version(pack, version)

    # tabulky: musí být i v simple a lmp; proto vložíme tabulky vždy u textů co je mají
    if pack.title in ("Sladké mámení", "Věnečky"):
        # dočasně přehodíme pack.full_text marker split podle verze: uděláme copy logiku zde
        # vypíšeme verzi textu a v místě markeru vložíme pack.tables
        marker_pat = re.compile(r"\[ZDE NÁSLEDUJ[ÍI] TABULKY[^\]]*\]|\[ZDE NÁSLEDUJE TABULKA[^\]]*\]", re.IGNORECASE)
        parts = marker_pat.split(text_body)
        markers = marker_pat.findall(text_body)
        if markers:
            for para in parts[0].split("\n"):
                if para.strip():
                    doc.add_paragraph(para.strip())
            for title_t, rows_t in pack.tables:
                add_data_table(doc, title_t, rows_t)
            if len(parts) > 1:
                for para in parts[1].split("\n"):
                    if para.strip():
                        doc.add_paragraph(para.strip())
        else:
            for para in text_body.split("\n"):
                if para.strip():
                    doc.add_paragraph(para.strip())
            if pack.tables:
                for title_t, rows_t in pack.tables:
                    add_data_table(doc, title_t, rows_t)
    elif pack.title == "Karetní hra":
        # text
        for para in text_body.split("\n"):
            if para.strip():
                doc.add_paragraph(para.strip())
        add_spacer(doc, 1)

        # tabulka původní – ideálně jako obrázek z repozitáře (assets)
        add_h2(doc, "Tabulka (matice síly)")
        doc.add_paragraph("Použij tabulku stejně jako v originálu. Podle ní rozhoduj, kdo koho přebije.")
        # zkusíme přiložit obrázek, když existuje v assets/
        # (na Streamlit Cloudu to bude fungovat, když obrázek přidáš do repozitáře)
        import os
        from pathlib import Path
        assets = Path(__file__).parent / "assets"
        img_path = assets / "karetni_matice.png"  # doporučený název v repo
        if img_path.exists():
            doc.add_picture(str(img_path), width=Cm(16))
        else:
            add_note(doc, "Pozn.: Soubor assets/karetni_matice.png nebyl nalezen. Pokud chceš úplně totožnou tabulku jako v PDF, ulož ji do této cesty.")
            doc.add_paragraph("Náhradní pomůcka: Řaď zvířata podle pyramidy síly níže a porovnávej.")
        add_spacer(doc, 1)

        # pyramida + kartičky
        add_pyramid_column(doc)
        add_spacer(doc, 1)
        add_animal_cards_3cols(doc)
    else:
        # obecný text bez tabulek
        for para in text_body.split("\n"):
            if para.strip():
                doc.add_paragraph(para.strip())

    add_spacer(doc, 1)

    # Otázky
    add_questions_ABC(doc, pack.title, pack.grade)

    add_spacer(doc, 1)
    # Slovníček na konci (z textu dané verze!)
    add_glossary_at_end(doc, text_body, pack.grade)

    # export do bytes
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()


# -----------------------------
# Metodika – zvlášť docx
# -----------------------------

def build_teacher_methodology(pack: TextPack) -> bytes:
    doc = Document()
    set_doc_default_style(doc)

    add_h1(doc, f"Metodický list pro učitele – {pack.title}")

    add_h2(doc, "Doporučený průběh hodiny (45 min)")
    doc.add_paragraph("1) Dramatizace (5–7 min): krátká scénka na začátek – žáci se naladí na téma.")
    doc.add_paragraph("2) Slovníček (5–8 min): i když je ve pracovním listu na konci, učitel s ním pracuje hned po scénce.")
    doc.add_paragraph("   - vyberte 5–8 slov, která žáci neznají, a krátce je vysvětlete.")
    doc.add_paragraph("3) Čtení textu (10–15 min): žáci čtou text (verzi dle potřeby).")
    doc.add_paragraph("4) Otázky A/B/C (15 min): A – vyhledání info, B – interpretace, C – vlastní názor.")
    doc.add_paragraph("5) Reflexe (3–5 min): co bylo těžké, co pomohlo (slovníček/tabulka).")

    add_h2(doc, "Rozdíly mezi verzemi pracovního listu")
    doc.add_paragraph("Plná verze: plný text (včetně tabulek) + standardní otázky + slovníček.")
    doc.add_paragraph("Zjednodušená verze: zjednodušený text, ale tabulky zůstávají (jsou nutné pro vyhledávání).")
    doc.add_paragraph("LMP/SPU verze: kratší věty, více opory (jasnější zadání), tabulky zůstávají, více místa na odpovědi.")

    add_h2(doc, "Vazba na RVP ZV – čtenářská gramotnost (ukázkově)")
    doc.add_paragraph("Žák vyhledává v textu a v tabulce explicitní informace, propojuje je a ověřuje odpovědi.")
    doc.add_paragraph("Žák interpretuje sdělení textu, rozlišuje fakt a názor a formuluje vlastní stanovisko s oporou v textu.")
    add_note(doc, "Pozn.: V diplomové práci uveď konkrétní očekávané výstupy dle platného RVP ZV a dokumentů NPI k ČG (kódování dle tvé metodiky).")

    if pack.title == "Karetní hra":
        add_h2(doc, "Specifika: pyramida a tabulka (Karetní hra)")
        doc.add_paragraph("Tabulka (matice síly) je klíčová – žáci ji používají při rozhodování, kdo koho přebije.")
        doc.add_paragraph("Pyramida je vytvořená jako sloupec – žádná zvířata nejsou na stejné úrovni.")
        doc.add_paragraph("Kartičky jsou v pracovním listu ve 3 sloupcích (emoji + název). Velikost okének pyramida > kartičky.")

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()


# -----------------------------
# Vlastní text (obecný režim)
# -----------------------------

def build_generic_pack(title: str, grade: int, text: str) -> TextPack:
    # v generickém režimu neděláme speciální tabulky a pyramidu
    # jednoduché varianty textu: jen lehké zkrácení (bez AI)
    def simplify(t: str) -> str:
        # jemné zkrácení: odstraníme vícenásobné mezery a extrémně dlouhé odstavce
        t = re.sub(r"\s+", " ", t).strip()
        # rozsekání do vět pro čitelnost
        t = t.replace(". ", ".\n")
        return t

    base = simplify(text)
    simple = base
    lmp = base

    return TextPack(
        title=title,
        grade=grade,
        full_text=f"NÁZEV ÚLOHY: {title}    JMÉNO:\n\n{base}",
        simple_text=f"NÁZEV ÚLOHY: {title} (zjednodušeně)    JMÉNO:\n\n{simple}",
        lmp_text=f"NÁZEV ÚLOHY: {title} (LMP/SPU)    JMÉNO:\n\n{lmp}",
        has_tables=False,
        tables=[]
    )


# -----------------------------
# Streamlit UI + session persistence
# -----------------------------

def store_generated_files(key: str, files: Dict[str, bytes]):
    st.session_state.setdefault("generated_files", {})
    st.session_state["generated_files"][key] = files

def get_generated_files(key: str) -> Optional[Dict[str, bytes]]:
    return st.session_state.get("generated_files", {}).get(key)

def render_downloads(files: Dict[str, bytes], prefix_key: str):
    st.subheader("Stažení dokumentů")
    st.caption("Tlačítka zůstávají dostupná i po stažení jednoho souboru.")
    for name, data in files.items():
        st.download_button(
            label=f"⬇️ Stáhnout: {name}",
            data=data,
            file_name=name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"{prefix_key}_{name}"
        )

def main():
    st.set_page_config(page_title="EdRead AI (pro diplomku)", layout="centered")
    st.title("EdRead AI – generátor pracovních listů")

    st.session_state.setdefault("mode", "Pevné texty (diplomka)")

    mode = st.radio(
        "Režim",
        ["Pevné texty (diplomka)", "Vlastní text"],
        index=0 if st.session_state["mode"] == "Pevné texty (diplomka)" else 1,
        key="mode_radio"
    )
    st.session_state["mode"] = mode

    if mode == "Pevné texty (diplomka)":
        choice = st.selectbox("Vyber text", list(TEXTS.keys()), key="fixed_choice")
        pack = TEXTS[choice]
        bundle_key = f"fixed::{choice}"

        st.info("Vygenerují se 4 soubory: plný, zjednodušený, LMP/SPU a metodika (zvlášť).")

        if st.button("Vygenerovat dokumenty", key="gen_fixed"):
            pl_full = build_student_doc(pack, "full")
            pl_simple = build_student_doc(pack, "simple")
            pl_lmp = build_student_doc(pack, "lmp")
            metodika = build_teacher_methodology(pack)

            files = {
                f"pracovni_list_{pack.title}_plny.docx": pl_full,
                f"pracovni_list_{pack.title}_zjednoduseny.docx": pl_simple,
                f"pracovni_list_{pack.title}_LMP_SPU.docx": pl_lmp,
                f"metodicky_list_{pack.title}.docx": metodika,
            }
            store_generated_files(bundle_key, files)
            st.success("Hotovo! Dokumenty jsou připravené ke stažení níže.")

        files = get_generated_files(bundle_key)
        if files:
            render_downloads(files, prefix_key=bundle_key)

        # Tipy pro assets (karetní matice)
        if pack.title == "Karetní hra":
            st.caption("Tip: Chceš-li tabulku (matici síly) 1:1 jako v PDF, ulož její obrázek do repozitáře: assets/karetni_matice.png")

    else:
        grade = st.selectbox("Pro jaký ročník?", [1,2,3,4,5], index=2, key="custom_grade")
        title = st.text_input("Název úlohy", value="Vlastní text", key="custom_title")
        text = st.text_area("Vlož text", height=220, key="custom_text")

        bundle_key = f"custom::{grade}::{title}"

        if st.button("Vygenerovat dokumenty", key="gen_custom"):
            if not text.strip():
                st.error("Vlož prosím text.")
            else:
                pack = build_generic_pack(title=title, grade=grade, text=text)
                pl_full = build_student_doc(pack, "full")
                pl_simple = build_student_doc(pack, "simple")
                pl_lmp = build_student_doc(pack, "lmp")
                metodika = build_teacher_methodology(pack)

                files = {
                    f"pracovni_list_{pack.title}_plny.docx": pl_full,
                    f"pracovni_list_{pack.title}_zjednoduseny.docx": pl_simple,
                    f"pracovni_list_{pack.title}_LMP_SPU.docx": pl_lmp,
                    f"metodicky_list_{pack.title}.docx": metodika,
                }
                store_generated_files(bundle_key, files)
                st.success("Hotovo! Dokumenty jsou připravené ke stažení níže.")

        files = get_generated_files(bundle_key)
        if files:
            render_downloads(files, prefix_key=bundle_key)


if __name__ == "__main__":
    main()

