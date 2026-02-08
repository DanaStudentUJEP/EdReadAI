import re
import io
from datetime import datetime
import streamlit as st

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


# =========================================================
# 1) ZÁKLADNÍ NASTAVENÍ + HELPERY
# =========================================================

def doc_to_bytes(doc: Document) -> bytes:
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()

def set_doc_style(doc: Document):
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

def add_title(doc: Document, title: str, subtitle: str = ""):
    p = doc.add_paragraph()
    run = p.add_run(title)
    run.bold = True
    run.font.size = Pt(16)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if subtitle:
        p2 = doc.add_paragraph(subtitle)
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

def add_section_header(doc: Document, text: str):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(12)

def add_hr(doc: Document):
    doc.add_paragraph("")

def add_lines(doc: Document, count=1):
    for _ in range(count):
        doc.add_paragraph("______________________________________________")

def compact_paragraph(p):
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0

def compact_cell(cell):
    for p in cell.paragraphs:
        compact_paragraph(p)

def set_fixed_col_width(table, col_widths_cm):
    table.autofit = False
    for row in table.rows:
        for i, w in enumerate(col_widths_cm):
            row.cells[i].width = Cm(w)

def set_cell_border(cell, **kwargs):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)

    for edge in ("left", "top", "right", "bottom"):
        if edge in kwargs:
            edge_data = kwargs.get(edge)
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for k, v in edge_data.items():
                element.set(qn('w:{}'.format(k)), str(v))

def set_cell_shading(cell, fill_hex: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tc_pr.append(shd)

def normalize_spaces(t: str) -> str:
    t = re.sub(r"\s+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


# =========================================================
# 2) DRAMATIZACE – bez věty, která patří jen do metodiky
# =========================================================

INTRO = {
    "karetni": "Dnes si nejdřív zahrajeme krátkou scénku z karetní hry, abychom rychle pochopili, o co ve hře jde. Potom se podíváme do slovníčku (je až na konci pracovního listu), vrátíme se k textu a nakonec vyplníme otázky.",
    "sladke": "Nejdřív krátká scénka, která nás naladí na téma. Potom slovníček (na konci), čtení textu a otázky.",
    "venecky": "Nejdřív krátká scénka k tématu hodnocení. Potom slovníček (na konci), čtení textu a práce s otázkami a tabulkou.",
    "custom": "Nejdřív krátká scénka k tématu. Potom slovníček (na konci), čtení textu a otázky."
}

DRAMA = {
    "karetni": [
        "Žák A: „Mám komára. Je slabý, ale co když dám víc komárů?“",
        "Žák B: „Já mám myš. Přebije komára? A co přebije myš?“",
        "Žák C: „Když dám dvě stejné karty, je to silnější?“",
        "Žák D: „Mám chameleona. Můžu ho přidat k jiné kartě?“",
        "Žák A: „Přečteme pravidla a ověříme si to podle tabulky!“",
    ],
    "sladke": [
        "Žák A: „Proč jsou některé sladkosti ‚light‘?“",
        "Žák B: „A chtěli by to lidé opravdu kupovat?“",
        "Učitel/ka: „V textu zjistíme, proč se to řeší a co lidé chtějí.“",
    ],
    "venecky": [
        "Žák A: „Tenhle věneček určitě vyhrál!“",
        "Žák B: „Podle mě rozhoduje chuť a suroviny.“",
        "Učitel/ka: „Dnes budeme hledat v textu fakta a názory a porovnáme je s tabulkou.“",
    ],
    "custom": [
        "Žák A: „Nevím, co je v textu nejdůležitější.“",
        "Žák B: „Tak budeme hledat klíčové informace a vysvětlíme je vlastními slovy.“",
        "Učitel/ka: „Půjdeme krok za krokem.“",
    ],
}

def add_dramatization_intro(doc: Document, key: str):
    add_section_header(doc, "Úvod (co budeme dělat)")
    doc.add_paragraph(INTRO.get(key, INTRO["custom"]))

def add_dramatization(doc: Document, key: str):
    add_section_header(doc, "Dramatizace (krátká scénka)")
    for line in DRAMA[key]:
        doc.add_paragraph(line)


# =========================================================
# 3) PŘEDPŘIPRAVENÉ TEXTY (PLNÝ / ZJEDNODUŠENÝ / LMP)
#    + TABULKY vždy i v ZJED a LMP
# =========================================================

# --- Karetní hra
FULL_KARETNI_TEXT = """NÁZEV ÚLOHY: KARETNÍ HRA\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

(… zde je plný text Karetní hry …)
"""

SIMPLE_KARETNI_TEXT = """KARETNÍ HRA (zjednodušený text)

Ve hře jsou karty se zvířaty. Každý hráč dostane karty.
Cílem je zbavit se všech karet jako první.

Hráči vykládají karty na stůl.
Další hráč musí dát silnější zvíře, aby přebil předchozí kartu.
Někdy může přebít i stejným zvířetem, ale musí dát o jednu kartu víc.

Chameleon je žolík: může se přidat k jiné kartě.
Sám se hrát nesmí.
"""

LMP_KARETNI_TEXT = """KARETNÍ HRA (LMP/SPU)

1) Každý dostane karty.
2) Hrajeme po řadě.
3) Vyhrává ten, kdo už nemá žádné karty.

Když někdo dá kartu na stůl, já musím dát silnější zvíře
(nebo stejné zvíře, ale o jednu kartu víc).
Když nemám, řeknu „pass“.

Chameleon je žolík. Musí být vždy s jinou kartou.
"""

# --- Sladké mámení + tabulky (přepis)
SLADKE_TABLES = {
    "Jak často jíte čokoládu? (v %)": [
        ("Alespoň jednou týdně", "22,7"),
        ("Více než dvakrát týdně", "6,1"),
        ("Méně než jednou týdně", "57,1"),
    ],
    "Jakou čokoládu máte nejraději? (v %)": [
        ("Studentská pečeť", "32,5"),
        ("Milka", "23,4"),
        ("Orion mléčná", "20,8"),
    ],
    "Jaké čokoládové tyčinky jste jedl v posledních 12 měsících? (v %)": [
        ("Margot", "29,9"),
        ("Ledové kaštany", "29,2"),
        ("Banán v čokoládě", "27,9"),
        ("Deli", "27,0"),
        ("Kofila", "24,8"),
        ("Milena", "22,4"),
        ("3 BIT", "19,5"),
        ("Studentská pečeť", "19,4"),
        ("Geisha", "15,0"),
        ("Mars", "13,6"),
    ],
    "Jak často kupujete bonboniéry? (v %)": [
        ("Dvakrát a více měsíčně", "1,7"),
        ("Jednou měsíčně", "14,9"),
        ("Jednou až dvakrát za 3 měsíce", "23,2"),
        ("Méně než jedenkrát za 3 měsíce", "54,5"),
        ("Neuvedeno", "5,7"),
    ],
    "Jaké bonboniéry jste koupili v posledních 12 měsících? (v %)": [
        ("Laguna — mořské plody", "31,9"),
        ("Figaro — Tatiana", "25,6"),
        ("Figaro — Zlaťouš", "21,6"),
        ("Tofifee", "19,6"),
        ("Orion — Modré z nebe", "19,4"),
        ("Nugeta — dezert", "17,6"),
        ("Ferrero Rocher", "16,2"),
        ("Merci", "15,7"),
        ("Raffaello", "13,9"),
        ("Mon Chéri", "13,5"),
    ],
}

FULL_SLADKE_TEXT = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Češi a čokoláda
(Všechny údaje v tabulkách jsou v procentech.)

(… zde je plný text Sladkého mámení …)

Zdroj: Týden, 31. října 2011, 44/2011, s. 29, upraveno.
"""

SIMPLE_SLADKE_TEXT = """SLADKÉ MÁMENÍ (zjednodušený text)

Text říká, že ve světě je problém obezita.
Proto lidé chtějí sladkosti s méně kaloriemi.

V Česku ale mnoho lidí nechce řešit, kolik má sladkost energie.
Vědci hledají sladidlo, které bude sladké a nebude mít kalorie.
"""

LMP_SLADKE_TEXT = """SLADKÉ MÁMENÍ (LMP/SPU)

• Ve světě je problém obezita.
• Lidé chtějí sladkosti s méně kaloriemi.
• V ČR lidé často nechtějí číst informace o kaloriích.
• Vědci hledají sladidlo bez kalorií.
"""

# --- Věnečky + tabulka (přepis)
VENECKY_PODNIKY = [
    ("1", "Cukrárna Věnečky, Praha 5"),
    ("2", "Pekárna Krémová, Praha 1"),
    ("3", "Cukrárna Větrníček, Praha 3"),
    ("4", "Cukrárna Mámení, Praha 2"),
    ("5", "Cukrárna Dortíček, Praha 6"),
]

VENECKY_TABLE = [
    ("1", "15", "4", "5", "2", "1", "3"),
    ("2", "17", "4", "5", "5", "5", "5"),
    ("3", "11,50", "5", "5", "5", "5", "5"),
    ("4", "19", "2", "1", "2", "2", "2"),
    ("5", "20", "3", "3", "5", "5", "4"),
]

FULL_VENECKY_TEXT = """NÁZEV ÚLOHY: VĚNEČKY\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

(… zde je plný text Věnečků …)

Zdroj: Týden, 31. října 2011, 44/2011, s. 31, upraveno, kráceno.
"""

SIMPLE_VENECKY_TEXT = """VĚNEČKY (zjednodušený text)

Hodnotitelka ochutnává věnečky z různých podniků.
Některé věnečky jsou špatné, jeden je nejlepší.
V tabulce jsou ceny a známky (jako ve škole).
"""

LMP_VENECKY_TEXT = """VĚNEČKY (LMP/SPU)

• Porovnáváme věnečky z více podniků.
• Jeden je nejlepší.
• Tabulka ukazuje cenu a známku.
"""


def add_two_col_table(doc: Document, title: str, rows):
    add_section_header(doc, title)
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.autofit = False
    set_fixed_col_width(t, [12.0, 3.0])

    hdr = t.rows[0].cells
    hdr[0].text = "Položka"
    hdr[1].text = "Hodnota"
    compact_cell(hdr[0]); compact_cell(hdr[1])

    for a, b in rows:
        rr = t.add_row().cells
        rr[0].text = a
        rr[1].text = b
        compact_cell(rr[0]); compact_cell(rr[1])

    for r in t.rows:
        for c in r.cells:
            set_cell_border(
                c,
                top={"sz": 8, "val": "single", "color": "000000"},
                bottom={"sz": 8, "val": "single", "color": "000000"},
                left={"sz": 8, "val": "single", "color": "000000"},
                right={"sz": 8, "val": "single", "color": "000000"},
            )

def add_venecky_table_inside(doc: Document):
    add_section_header(doc, "Kde jsme věnečky pořídili (přesný přepis)")
    for num, txt in VENECKY_PODNIKY:
        doc.add_paragraph(f"{num}. {txt}")

    add_section_header(doc, "Hodnocení (přesná tabulka)")
    cols = ["Cukrárna", "Cena v Kč", "Vzhled", "Korpus", "Náplň", "Suroviny", "Celková známka"]
    t = doc.add_table(rows=1, cols=len(cols))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    set_fixed_col_width(t, [2.0, 2.0, 1.4, 1.4, 1.4, 1.6, 2.5])

    for i, c in enumerate(cols):
        t.cell(0, i).text = c
        compact_cell(t.cell(0, i))

    for row in VENECKY_TABLE:
        rr = t.add_row().cells
        for i, val in enumerate(row):
            rr[i].text = val
            compact_cell(rr[i])

    for r in t.rows:
        for c in r.cells:
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_border(
                c,
                top={"sz": 8, "val": "single", "color": "000000"},
                bottom={"sz": 8, "val": "single", "color": "000000"},
                left={"sz": 8, "val": "single", "color": "000000"},
                right={"sz": 8, "val": "single", "color": "000000"},
            )


# =========================================================
# 4) KARETNÍ HRA – PYRAMIDA + KARTIČKY (EMOJI)
# =========================================================

ANIMAL_CARDS = [
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

CARD_W_CM = 5.6
CARD_H_CM = 1.85
SLOT_W_CM = 7.2     # větší než kartičky
SLOT_H_CM = 2.15    # větší než kartičky
SLOTS = 13

def add_pyramid_column(doc: Document):
    add_section_header(doc, "„Pyramida“ síly (sloupec okýnek na lepení)")
    doc.add_paragraph("Nahoře nalep nejsilnější zvíře, dole nejslabší. Každé zvíře má vlastní úroveň.")

    t = doc.add_table(rows=SLOTS + 1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    set_fixed_col_width(t, [SLOT_W_CM])

    header = t.cell(0, 0)
    header.text = "NAHOŘE = NEJSILNĚJŠÍ"
    compact_cell(header)
    header.paragraphs[0].runs[0].bold = True
    header.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    header.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    header.height = Cm(SLOT_H_CM)

    for i in range(1, SLOTS + 1):
        cell = t.cell(i, 0)
        cell.text = ""
        compact_cell(cell)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        cell.height = Cm(SLOT_H_CM)
        set_cell_border(
            cell,
            top={"sz": 14, "val": "single", "color": "000000"},
            bottom={"sz": 14, "val": "single", "color": "000000"},
            left={"sz": 14, "val": "single", "color": "000000"},
            right={"sz": 14, "val": "single", "color": "000000"},
        )

    doc.add_paragraph("DOLE = NEJSLABŠÍ")

def add_animal_cards_3cols(doc: Document):
    add_section_header(doc, "Kartičky zvířat (3 sloupce, na stříhání)")
    cols = 3
    rows = (len(ANIMAL_CARDS) + cols - 1) // cols

    table = doc.add_table(rows=rows, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_fixed_col_width(table, [CARD_W_CM, CARD_W_CM, CARD_W_CM])

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.height = Cm(CARD_H_CM)

            set_cell_border(
                cell,
                top={"sz": 14, "val": "single", "color": "000000"},
                bottom={"sz": 14, "val": "single", "color": "000000"},
                left={"sz": 14, "val": "single", "color": "000000"},
                right={"sz": 14, "val": "single", "color": "000000"},
            )

            if idx < len(ANIMAL_CARDS):
                name, emoji = ANIMAL_CARDS[idx]
                p = cell.paragraphs[0]
                compact_paragraph(p)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run1 = p.add_run(f"{emoji} ")
                run1.font.size = Pt(18)
                run2 = p.add_run(name)
                run2.bold = True
                run2.font.size = Pt(10)
            else:
                cell.text = ""
                compact_cell(cell)
            idx += 1


# =========================================================
# 5) SLOVNÍČEK – vždy na konci (s možností poznámky)
# =========================================================

STOPWORDS = set("""
a i o u v ve na do z ze že který která které kteří se si je jsou být bylo byla byly jsem jsme jste
když protože proto ale nebo ani jen ještě už pak také tak tedy tento tato toto
""".split())

EXPLAIN = {
    "maximálně": "nejvíc (největší možné množství)",
    "vykřikuje": "říká nahlas",
    "soustech": "kouscích jídla",
    "vyšlehaný": "nadýchaný (hodně našlehaný)",
    "margarín": "tuk podobný máslu",
    "vzdáleně": "ani trochu",
    "nepřipomíná": "není to podobné",
    "chemickou": "umělou, ne přírodní",
    "pachuť": "nepříjemná chuť, která zůstane",
    "korpus": "těsto (spodní část zákusku)",
    "dodrželi": "udělali přesně podle pravidel",
    "upraveno": "trochu změněno",
    "obezita": "velká nadváha",
    "kaloriemi": "energie v jídle",
    "sladivost": "jak moc je něco sladké",
    "přebít": "porazit (dát silnější kartu)",
    "samostatně": "sám, bez jiné karty",
    "rovnoměrně": "stejně pro všechny",
}

def pick_glossary_words(text: str, max_words=12):
    words = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž\-]+", text)
    cleaned = []
    for w in words:
        wl = w.lower().strip("-")
        if len(wl) < 6:
            continue
        if wl in STOPWORDS:
            continue
        cleaned.append(wl)

    uniq = []
    for w in cleaned:
        if w not in uniq:
            uniq.append(w)

    known = [w for w in uniq if w in EXPLAIN]
    unknown = [w for w in uniq if w not in EXPLAIN]

    out = []
    for w in known:
        out.append(w)
        if len(out) >= max_words:
            break
    if len(out) < max_words:
        for w in unknown:
            out.append(w)
            if len(out) >= max_words:
                break
    return out[:max_words]

def add_glossary_at_end(doc: Document, source_text: str, max_words=12):
    add_hr(doc)
    add_section_header(doc, "Slovníček (na konec pracovního listu)")
    words = pick_glossary_words(source_text, max_words=max_words)

    for w in words:
        p = doc.add_paragraph()
        r1 = p.add_run(f"• {w} = ")
        r1.bold = True
        if w in EXPLAIN:
            p.add_run(EXPLAIN[w])
        else:
            p.add_run("______________________________")
        doc.add_paragraph("Poznámka žáka/žákyně: _______________________________")


# =========================================================
# 6) OTÁZKY
# =========================================================

def add_questions_karetni(doc: Document):
    add_section_header(doc, "Otázky A/B/C")
    doc.add_paragraph("A) Najdi v textu")
    doc.add_paragraph("1) Co je cílem hry? Napiš jednou větou.")
    add_lines(doc, 1)

    doc.add_paragraph("2) Co znamená ve hře slovo „pass“?")
    add_lines(doc, 1)

    doc.add_paragraph("B) Vysvětli vlastními slovy")
    doc.add_paragraph("3) Proč se chameleon (žolík) nesmí hrát samostatně?")
    add_lines(doc, 2)

    doc.add_paragraph("C) Můj názor")
    doc.add_paragraph("4) Co bys poradil/a spolužákovi, aby ve hře vyhrál? (1–2 věty)")
    add_lines(doc, 2)

def add_questions_sladke(doc: Document):
    add_section_header(doc, "Otázky A/B/C")
    doc.add_paragraph("A) Najdi v textu")
    doc.add_paragraph("1) Proč roste ve světě poptávka po nízkokalorických sladkostech?")
    add_lines(doc, 2)

    doc.add_paragraph("B) Práce s tabulkami")
    doc.add_paragraph("2) Podle tabulek: Kterou bonboniéru koupilo více lidí – Tofifee nebo Merci? Napiš i procenta.")
    add_lines(doc, 2)

    doc.add_paragraph("C) Můj názor")
    doc.add_paragraph("3) Myslíš, že lidé v ČR nechtějí číst informace o kaloriích? Proč ano/ne?")
    add_lines(doc, 2)

def add_questions_venecky(doc: Document):
    add_section_header(doc, "Otázky A/B/C")
    doc.add_paragraph("A) Najdi v textu")
    doc.add_paragraph("1) Který věneček neobsahuje pudink uvařený z mléka? Napiš číslo a proč.")
    add_lines(doc, 2)

    doc.add_paragraph("B) Práce s tabulkou")
    doc.add_paragraph("2) Který podnik dopadl nejlépe? (podle tabulky) Napiš název.")
    add_lines(doc, 1)

    doc.add_paragraph("3) Který věneček byl nejdražší? Uveď cenu a kde byl koupen.")
    add_lines(doc, 2)

    doc.add_paragraph("C) Můj názor")
    doc.add_paragraph("4) Souhlasíš s hodnocením? Vyber jeden věneček a vysvětli proč.")
    add_lines(doc, 2)


# =========================================================
# 7) STAVBA PRACOVNÍCH LISTŮ – KLÍČ: každý list obsahuje svůj text
#    + tabulky jsou i v ZJED a LMP
# =========================================================

def build_doc_karetni(version: str) -> Document:
    doc = Document()
    set_doc_style(doc)
    add_title(doc, "EdRead AI – Pracovní list", f"Karetní hra (3. třída) — verze: {version}")
    add_hr(doc)

    add_dramatization_intro(doc, "karetni")
    add_hr(doc)
    add_dramatization(doc, "karetni")
    add_hr(doc)

    add_section_header(doc, "Text k přečtení")
    if version == "PLNÝ":
        src = FULL_KARETNI_TEXT
    elif version == "ZJEDNODUŠENÝ":
        src = SIMPLE_KARETNI_TEXT
    else:
        src = LMP_KARETNI_TEXT
    doc.add_paragraph(src)

    add_hr(doc)
    add_pyramid_column(doc)
    add_animal_cards_3cols(doc)

    add_hr(doc)
    add_questions_karetni(doc)

    add_glossary_at_end(doc, src, max_words=12)
    return doc

def build_doc_sladke(version: str) -> Document:
    doc = Document()
    set_doc_style(doc)
    add_title(doc, "EdRead AI – Pracovní list", f"Sladké mámení (5. třída) — verze: {version}")
    add_hr(doc)

    add_dramatization_intro(doc, "sladke")
    add_hr(doc)
    add_dramatization(doc, "sladke")
    add_hr(doc)

    add_section_header(doc, "Text k přečtení")
    if version == "PLNÝ":
        src = FULL_SLADKE_TEXT
    elif version == "ZJEDNODUŠENÝ":
        src = SIMPLE_SLADKE_TEXT
    else:
        src = LMP_SLADKE_TEXT
    doc.add_paragraph(src)

    # ✅ Tabulky vždy – i v ZJED a LMP
    add_hr(doc)
    add_section_header(doc, "Tabulky (přesný přepis z originálu)")
    for title, rows in SLADKE_TABLES.items():
        add_two_col_table(doc, title, rows)

    add_hr(doc)
    add_questions_sladke(doc)

    add_glossary_at_end(doc, src, max_words=12)
    return doc

def build_doc_venecky(version: str) -> Document:
    doc = Document()
    set_doc_style(doc)
    add_title(doc, "EdRead AI – Pracovní list", f"Věnečky (4. třída) — verze: {version}")
    add_hr(doc)

    add_dramatization_intro(doc, "venecky")
    add_hr(doc)
    add_dramatization(doc, "venecky")
    add_hr(doc)

    add_section_header(doc, "Text k přečtení")
    if version == "PLNÝ":
        src = FULL_VENECKY_TEXT
    elif version == "ZJEDNODUŠENÝ":
        src = SIMPLE_VENECKY_TEXT
    else:
        src = LMP_VENECKY_TEXT
    doc.add_paragraph(src)

    # ✅ Tabulka vždy – i v ZJED a LMP
    add_hr(doc)
    add_venecky_table_inside(doc)

    add_hr(doc)
    add_questions_venecky(doc)

    add_glossary_at_end(doc, src, max_words=12)
    return doc


# =========================================================
# 8) METODIKA – manuál + postup (dramatizace → slovníček → čtení → otázky)
# =========================================================

def build_methodology(text_name: str, grade: str, has_pyramid: bool = False) -> Document:
    doc = Document()
    set_doc_style(doc)
    add_title(doc, "EdRead AI – Metodický list pro učitele", f"{text_name} ({grade})")
    add_hr(doc)

    add_section_header(doc, "Doporučený postup práce (45 minut)")
    doc.add_paragraph("1) Úvod + dramatizace (3–7 min): scénka slouží k motivaci a rychlému porozumění situaci.")
    doc.add_paragraph("2) Slovníček (na konci pracovního listu): učitel žáky navede na konec listu, vyjasní významy a teprve potom je vrátí k textu.")
    doc.add_paragraph("3) Čtení textu: žáci se vrátí do části „Text k přečtení“, čtou, podtrhují důležité informace.")
    doc.add_paragraph("4) Otázky A/B/C: A = vyhledání informace; B = práce s tabulkou / interpretace; C = vlastní názor.")
    doc.add_paragraph("5) Shrnutí: rozlišení faktu a názoru, krátká reflexe.")

    add_hr(doc)
    add_section_header(doc, "Rozdíly mezi verzemi")
    doc.add_paragraph("PLNÝ list: plný text + všechny části (nejvyšší náročnost čtení).")
    doc.add_paragraph("ZJEDNODUŠENÝ list: kratší a jednodušší text; tabulky zůstávají, pokud jsou potřeba pro odpovědi.")
    doc.add_paragraph("LMP/SPU list: velmi jednoduché věty a jasná struktura; tabulky zůstávají; slovníček obsahuje i prostor na poznámky.")

    if has_pyramid:
        add_hr(doc)
        add_section_header(doc, "Karetní hra – pyramida a kartičky")
        doc.add_paragraph("• Žáci vystřihnou kartičky (3 sloupce) a lepí je do sloupce okýnek.")
        doc.add_paragraph("• Okýnka jsou zvětšená tak, aby se kartičky pohodlně vešly.")
        doc.add_paragraph("• Každé zvíře má vlastní úroveň (žádná dvě zvířata nejsou na stejné úrovni).")

    return doc


# =========================================================
# 9) ULOŽENÍ VÝSTUPŮ DO SESSION_STATE – trvalé tlačítka i po stažení
# =========================================================

def store_bundle(bundle_key: str, files: dict):
    """
    files: { 'label': (bytes, filename, mime) }
    """
    st.session_state[f"{bundle_key}_files"] = files
    st.session_state[f"{bundle_key}_ready"] = True

def render_bundle(bundle_key: str):
    """
    Vykreslí stažení – NEZMIZÍ, protože je to čistě ze session_state
    """
    if not st.session_state.get(f"{bundle_key}_ready", False):
        return

    files = st.session_state.get(f"{bundle_key}_files", {})
    if not files:
        return

    st.success("Dokumenty jsou připravené. Po stažení jednoho zůstávají ostatní tlačítka viditelná.")

    # Stabilní layout: 2 sloupce, aby to bylo přehledné
    items = list(files.items())
    cols = st.columns(2)
    for i, (label, (data, fname, mime)) in enumerate(items):
        with cols[i % 2]:
            st.download_button(
                label=f"⬇️ {label}",
                data=data,
                file_name=fname,
                mime=mime,
                key=f"{bundle_key}_{label}_{fname}"  # stabilní a unikátní
            )


# =========================================================
# 10) STREAMLIT UI
# =========================================================

st.set_page_config(page_title="EdRead AI (prototyp)", layout="centered")
st.title("EdRead AI – generátor materiálů (prototyp)")

choices = ["Karetní hra (3. třída)", "Věnečky (4. třída)", "Sladké mámení (5. třída)"]
default_choice = st.session_state.get("last_choice", choices[0])
index = choices.index(default_choice) if default_choice in choices else 0

choice = st.selectbox("Vyber text:", choices, index=index)
st.session_state["last_choice"] = choice

if choice.startswith("Karetní"):
    bundle_key = "bundle_karetni"
elif choice.startswith("Věnečky"):
    bundle_key = "bundle_venecky"
else:
    bundle_key = "bundle_sladke"

# Tlačítko generování (NE form – form někdy komplikuje rerun)
if st.button("Vygenerovat dokumenty", key=f"gen_{bundle_key}"):
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")

    if bundle_key == "bundle_karetni":
        full_doc = build_doc_karetni("PLNÝ")
        simp_doc = build_doc_karetni("ZJEDNODUŠENÝ")
        lmp_doc  = build_doc_karetni("LMP/SPU")
        met_doc  = build_methodology("Karetní hra", "3. třída", has_pyramid=True)

        files = {
            "PLNÝ pracovní list (DOCX)": (doc_to_bytes(full_doc), f"pracovni_list_Karetni_hra_plny_{stamp}.docx",
                                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "ZJEDNODUŠENÝ pracovní list (DOCX)": (doc_to_bytes(simp_doc), f"pracovni_list_Karetni_hra_zjednoduseny_{stamp}.docx",
                                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "LMP/SPU pracovní list (DOCX)": (doc_to_bytes(lmp_doc), f"pracovni_list_Karetni_hra_LMP_{stamp}.docx",
                                             "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "METODICKÝ LIST (DOCX)": (doc_to_bytes(met_doc), f"metodicky_list_Karetni_hra_{stamp}.docx",
                                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        }
        store_bundle(bundle_key, files)

    elif bundle_key == "bundle_venecky":
        full_doc = build_doc_venecky("PLNÝ")
        simp_doc = build_doc_venecky("ZJEDNODUŠENÝ")
        lmp_doc  = build_doc_venecky("LMP/SPU")
        met_doc  = build_methodology("Věnečky", "4. třída", has_pyramid=False)

        files = {
            "PLNÝ pracovní list (DOCX)": (doc_to_bytes(full_doc), f"pracovni_list_Venecky_plny_{stamp}.docx",
                                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "ZJEDNODUŠENÝ pracovní list (DOCX)": (doc_to_bytes(simp_doc), f"pracovni_list_Venecky_zjednoduseny_{stamp}.docx",
                                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "LMP/SPU pracovní list (DOCX)": (doc_to_bytes(lmp_doc), f"pracovni_list_Venecky_LMP_{stamp}.docx",
                                             "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "METODICKÝ LIST (DOCX)": (doc_to_bytes(met_doc), f"metodicky_list_Venecky_{stamp}.docx",
                                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        }
        store_bundle(bundle_key, files)

    else:
        full_doc = build_doc_sladke("PLNÝ")
        simp_doc = build_doc_sladke("ZJEDNODUŠENÝ")
        lmp_doc  = build_doc_sladke("LMP/SPU")
        met_doc  = build_methodology("Sladké mámení", "5. třída", has_pyramid=False)

        files = {
            "PLNÝ pracovní list (DOCX)": (doc_to_bytes(full_doc), f"pracovni_list_Sladke_mameni_plny_{stamp}.docx",
                                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "ZJEDNODUŠENÝ pracovní list (DOCX)": (doc_to_bytes(simp_doc), f"pracovni_list_Sladke_mameni_zjednoduseny_{stamp}.docx",
                                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "LMP/SPU pracovní list (DOCX)": (doc_to_bytes(lmp_doc), f"pracovni_list_Sladke_mameni_LMP_{stamp}.docx",
                                             "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "METODICKÝ LIST (DOCX)": (doc_to_bytes(met_doc), f"metodicky_list_Sladke_mameni_{stamp}.docx",
                                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        }
        store_bundle(bundle_key, files)

# ✅ KLÍČ: render bundle je vždy mimo kliknutí, takže po stažení tlačítka zůstávají
render_bundle(bundle_key)

st.caption("Pozn.: Tabulky jsou vložené i do zjednodušené a LMP verze, protože jsou nutné pro hledání odpovědí.")
