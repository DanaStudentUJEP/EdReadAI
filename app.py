# app.py
# EdRead AI – stabilní prototyp pro diplomovou práci (3 texty)
# Výstupy:
# 1) Pracovní list – PLNY (DOCX)
# 2) Pracovní list – ZJEDNODUSENY (DOCX)
# 3) Pracovní list – LMP/SPU (DOCX)
# 4) Metodický list pro učitele (DOCX)
# 5) (Karetní hra) Kartičky se zvířaty (DOCX) – 3 sloupce, emoji, tisk

import io
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn


# -----------------------------
# Pomocné funkce – DOCX styling
# -----------------------------
def set_doc_defaults(doc: Document, base_font_size: int = 11):
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(base_font_size)

def add_title(doc: Document, title: str, subtitle: Optional[str] = None):
    p = doc.add_paragraph()
    run = p.add_run(title)
    run.bold = True
    run.font.size = Pt(16)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if subtitle:
        p2 = doc.add_paragraph(subtitle)
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

def add_name_line(doc: Document):
    p = doc.add_paragraph("JMÉNO: ________________________________   DATUM: ________________")
    p.paragraph_format.space_after = Pt(8)

def add_section_header(doc: Document, text: str):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(12)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)

def add_instruction(doc: Document, text: str):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(6)

def add_bullets(doc: Document, items: List[str]):
    for it in items:
        p = doc.add_paragraph(it, style="List Bullet")
        p.paragraph_format.space_after = Pt(0)

def set_cell_border(cell, **kwargs):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders")
        tcPr.append(tcBorders)
    for edge in ("top", "left", "bottom", "right"):
        if edge in kwargs:
            edge_data = kwargs[edge]
            tag = "w:" + edge
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for k, v in edge_data.items():
                element.set(qn("w:" + k), str(v))

def make_table(doc: Document, rows: List[List[str]], col_widths_cm: Optional[List[float]] = None, header_bold=True):
    table = doc.add_table(rows=0, cols=len(rows[0]))
    table.style = "Table Grid"
    for r_i, row in enumerate(rows):
        cells = table.add_row().cells
        for c_i, val in enumerate(row):
            cells[c_i].text = val
            if r_i == 0 and header_bold:
                for run in cells[c_i].paragraphs[0].runs:
                    run.bold = True
            cells[c_i].paragraphs[0].paragraph_format.space_after = Pt(0)
            cells[c_i].paragraphs[0].paragraph_format.space_before = Pt(0)
        if col_widths_cm:
            for c_i, w in enumerate(col_widths_cm):
                cells[c_i].width = Cm(w)
    return table

def add_lines_for_answer(doc: Document, lines: int = 2):
    for _ in range(lines):
        doc.add_paragraph("__________________________________________________________________")

def doc_to_bytes(doc: Document) -> bytes:
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# -----------------------------------
# Slovníček – výběr + vysvětlení
# -----------------------------------
def extract_candidate_words(text: str, max_words: int = 12) -> List[str]:
    stop = {
        "název", "úlohy", "jměno", "správným", "řešením", "celé", "úlohy",
        "maximálně", "bodů", "otázka", "body", "bod", "zdroj"
    }
    tokens = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    tokens = [t.strip() for t in tokens if len(t.strip()) >= 7]
    uniq = []
    seen = set()
    for t in tokens:
        tl = t.lower()
        if tl in stop:
            continue
        if tl not in seen:
            seen.add(tl)
            uniq.append(t)
    return uniq[:max_words]

def explain_word(word: str, glossary_map: Dict[str, str]) -> Optional[str]:
    w = word.lower()
    return glossary_map.get(w)

def add_glossary_section(doc: Document, words: List[str], glossary_map: Dict[str, str]):
    add_section_header(doc, "SLOVNÍČEK (na konci pracovního listu)")
    add_instruction(doc, "Nejdřív si slovníček projdi s učitelem/učitelkou. Ke slovům si můžeš dopsat poznámku.")
    for w in words:
        expl = explain_word(w, glossary_map)
        p = doc.add_paragraph()
        run = p.add_run(f"• {w}: ")
        run.bold = True
        if expl:
            doc.add_paragraph(f"  {expl}")
        # vždy prostor na poznámku – bez rušivých vět
        doc.add_paragraph("  Poznámka žáka: ________________________________________________")


# -----------------------------------
# Karetní hra – sloupec síly + kartičky
# -----------------------------------
KARETNI_ORDER_STRONG_TO_WEAK = [
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
KARETNI_CHAMELEON = ("chameleon (žolík)", "🦎")


def add_strength_column_template(doc: Document):
    """
    Místo pyramidy: sloupec 12 úrovní (každé zvíře je na jiné úrovni).
    Velikost okének odpovídá kartičkám (vystřižené kartičky se musí vejít).
    """
    add_section_header(doc, "SLOUPEC SÍLY ZVÍŘAT (pomůcka k porozumění pravidlům)")
    add_instruction(doc, "Vystřihni kartičky se zvířaty a nalep je do sloupce podle síly.")
    add_instruction(doc, "Úplně nahoře bude nejsilnější zvíře, úplně dole nejslabší.")
    add_instruction(doc, "Chameleon je žolík – nelepuj ho do sloupce síly. Použiješ ho jen jako speciální kartu ve hře.")

    # 12 řádků, 1 sloupec – velká okénka
    t = doc.add_table(rows=12, cols=1)
    t.style = "Table Grid"

    # šířka okénka – aby se vešla kartička (emoji + název)
    # (tahle hodnota funguje spolehlivě pro tisk na A4)
    for r in range(12):
        cell = t.cell(r, 0)
        cell.text = ""
        cell.width = Cm(16.5)
        # okraje
        set_cell_border(
            cell,
            top={"sz": 14, "val": "single", "color": "000000"},
            bottom={"sz": 14, "val": "single", "color": "000000"},
            left={"sz": 14, "val": "single", "color": "000000"},
            right={"sz": 14, "val": "single", "color": "000000"},
        )
        # centrování + popisek úrovně
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("Sem nalep kartičku")
        run.font.size = Pt(10)

    # štítky nahoře/dole
    doc.add_paragraph("")
    p_top = doc.add_paragraph("⬆️ Nahoře = NEJSILNĚJŠÍ")
    p_top.runs[0].bold = True
    p_bottom = doc.add_paragraph("⬇️ Dole = NEJSLABŠÍ")
    p_bottom.runs[0].bold = True


def add_animal_cards_3cols(doc: Document):
    """
    Kartičky: 3 sloupce, emoji + správný český název.
    Bez siluet, bez internetu, tiskově použitelné.
    """
    add_section_header(doc, "KARTIČKY SE ZVÍŘATY (vystřihni)")
    add_instruction(doc, "Kartičky vystřihni a použij je pro sloupec síly (a později při práci se hrou).")

    animals = [
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

    cols = 3
    rows = (len(animals) + cols - 1) // cols
    table = doc.add_table(rows=rows, cols=cols)
    table.style = "Table Grid"

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.text = ""
            cell.width = Cm(6.0)

            if idx < len(animals):
                name, emoji = animals[idx]

                pr = cell.paragraphs[0]
                pr.alignment = WD_ALIGN_PARAGRAPH.CENTER

                p1 = cell.add_paragraph()
                p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run_e = p1.add_run(emoji)
                run_e.font.size = Pt(26)
                run_e.font.name = "Segoe UI Emoji"

                p2 = cell.add_paragraph()
                p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run_n = p2.add_run(name)
                run_n.bold = True
                run_n.font.size = Pt(12)

                p3 = cell.add_paragraph("__________")
                p3.alignment = WD_ALIGN_PARAGRAPH.CENTER

            idx += 1


def add_karetni_strength_matrix(doc: Document):
    """
    Matice síly (vizuální tabulka): emoji + názvy, tečka = silnější přebíjí slabší.
    """
    add_section_header(doc, "KDO PŘEBIJE KOHO? (tabulka podle pravidel)")
    add_instruction(doc, "● = zvíře ve sloupci přebíjí zvíře v řádku.")

    animals = KARETNI_ORDER_STRONG_TO_WEAK[:]  # 12 bez chameleona
    headers = [""] + [f"{emo} {name}" for name, emo in animals]

    rows = [headers]
    names = [n for n, _ in animals]

    for r_name, r_emo in animals:
        row = [f"{r_emo} {r_name}"]
        r_idx = names.index(r_name)
        for c_name, c_emo in animals:
            c_idx = names.index(c_name)
            row.append("●" if c_idx < r_idx else "")
        rows.append(row)

    table = make_table(doc, rows, col_widths_cm=[5.2] + [2.0]*len(animals), header_bold=True)
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9)


# -----------------------------
# Datové struktury pro texty
# -----------------------------
@dataclass
class TextPack:
    key: str
    title: str
    grade: int
    points_max: int
    full_text: str
    simplified_text: str
    lmp_text: str
    dramatization: List[str]
    questions: List[str]
    glossary_map: Dict[str, str]
    tables_spec: Optional[Dict[str, List[List[str]]]] = None


# -----------------------------------
# 1) Karetní hra (3. třída)
# -----------------------------------
KARETNI_FULL_TEXT = """NÁZEV ÚLOHY: KARETNÍ HRA

Správným řešením celé úlohy lze získat maximálně 12 bodů.

1. Herní materiál
60 karet živočichů: 4 komáři, 1 chameleon (žolík), 5 karet od každého z dalších 11 druhů živočichů.

2. Popis hry
Všechny karty se rozdají mezi jednotlivé hráče. Hráči se snaží vynášet karty v souladu s pravidly tak, aby se co nejdříve zbavili všech svých karet z ruky. Zahrát lze vždy pouze silnější kombinaci živočichů, než zahrál hráč před vámi.

3. Pořadí karet
Na každé kartě je zobrazen jeden živočich. V rámečku v horní části karty jsou namalováni živočichové, kteří danou kartu přebíjí.
Symbol > označuje, že každý živočich může být přebit větším počtem karet se živočichem stejného druhu.
Příklad: Kosatku přebijí pouze dvě kosatky. Krokodýla přebijí dva krokodýli nebo jeden slon.
Chameleon má ve hře obdobnou funkci jako žolík. Lze jej zahrát spolu s libovolnou jinou kartou a počítá se jako požadovaný druh živočicha. Nelze jej hrát samostatně.

4. Průběh hry
• Karty zamíchejte a rozdejte rovnoměrně mezi všechny hráče. Každý hráč si vezme své karty do ruky a neukazuje je ostatním.
• Hráč po levé ruce rozdávajícího hráče začíná. Zahraje (vynese na stůl lícem nahoru) jednu kartu nebo více stejných karet.
• Hráči hrají po směru hodinových ručiček a postupně se snaží přebít dříve zahrané karty.
• Hráč, který nechce nebo nemůže přebít, se může vzdát tahu slovem pass.
• Pokud se hráč dostane na řadu s tím, že nikdo z ostatních hráčů nepřebil jeho karty, vezme si tento hráč všechny karty, které leží uprostřed stolu. Tyto karty si položí před sebe a vynese další kartu nebo karty z ruky.
• Hráč, který jako první vynese svoji poslední kartu nebo karty z ruky, vítězí.
"""

KARETNI_SIMPLIFIED_TEXT = """NÁZEV ÚLOHY: KARETNÍ HRA (zjednodušený text)

Cílem hry je zbavit se jako první všech karet z ruky.
Hráči hrají po směru hodinových ručiček a snaží se přebít kartu nebo karty, které leží na stole.

Silnější zvíře přebíjí slabší.
Někdy můžeš přebít i stejným zvířetem, ale musíš dát o jednu kartu víc.

Chameleon je žolík:
hraje se vždy s jinou kartou a může se počítat jako jiné zvíře.
Nemůže se hrát sám.

Když nemůžeš přebít, řekneš „pass“.
Kdo se zbaví karet jako první, vyhrává.
"""

KARETNI_LMP_TEXT = """NÁZEV ÚLOHY: KARETNÍ HRA (LMP/SPU)

1) Cíl hry:
Vyhrává ten, kdo bude mít jako první v ruce 0 karet.

2) Jak se hraje:
Hráč dá jednu kartu (nebo více stejných).
Další hráč musí dát silnější kartu (nebo správný počet karet).

3) Důležité:
• Silnější zvíře přebíjí slabší.
• Stejné zvíře přebije stejné zvíře jen tak, že dáš O JEDNU KARTU VÍCE.
• Chameleon je žolík. Hraje se vždy s jinou kartou.
• Když nemůžeš hrát, řekneš: pass.
"""

KARETNI_DRAMA = [
    "Učitel/ka: „Máme novou hru, ale pravidla jsou trochu zamotaná.“",
    "Žák A: „Já nevím, kdo je silnější… myš nebo lev?“",
    "Žák B: „Zkusme si udělat pomůcku – sloupec síly zvířat.“",
    "Učitel/ka: „Nejdřív krátká scénka, pak slovníček, a potom se pustíme do čtení pravidel.“",
]

KARETNI_QUESTIONS = [
    "A) 1) Co je cílem hry?\n   A Nasbírat co nejvíce karet.\n   B Nemít v ruce žádné karty jako první.\n   C Vyhrát co nejvíce kol.\n   D Získat nejvíce silných zvířat.\n   Odpověď: ________",
    "A) 2) Kolik karet je celkem ve hře?\n   Odpověď: ________",
    "B) 3) Vysvětli vlastními slovy, co znamená „přebít kartu“.\n   ________________________________________________",
    "A) 4) Kdy hráč řekne „pass“?\n   ________________________________________________",
    "C) 5) K čemu pomáhá sloupec síly zvířat? Napiš jednou větou.\n   ________________________________________________",
]

KARETNI_GLOSSARY = {
    "kombinace": "víc karet dohromady (např. dvě stejné).",
    "pravidla": "to, co se musí ve hře dodržovat.",
    "přebít": "dát silnější kartu (nebo správný počet karet).",
    "vynést": "položit karty na stůl.",
    "rovnoměrně": "stejně pro každého.",
    "obdobnou": "podobnou.",
    "funkci": "úkol, použití.",
    "požadovaný": "takový, který je potřeba.",
    "samostatně": "sám, bez jiné karty.",
    "postupně": "po jednom, krok za krokem.",
    "vzdát": "nehrát v tom kole.",
}

KARETNI_PACK = TextPack(
    key="karetni",
    title="Karetní hra",
    grade=3,
    points_max=12,
    full_text=KARETNI_FULL_TEXT,
    simplified_text=KARETNI_SIMPLIFIED_TEXT,
    lmp_text=KARETNI_LMP_TEXT,
    dramatization=KARETNI_DRAMA,
    questions=KARETNI_QUESTIONS,
    glossary_map=KARETNI_GLOSSARY,
    tables_spec=None,
)


# -----------------------------------
# 2) Sladké mámení (5. třída) – tabulka 100% dle PDF
# -----------------------------------
SLADKE_TABLE_ROWS = [
    ["Češi a čokoláda (v %)", ""],
    ["Jak často jíte čokoládu?", ""],
    ["Alespoň jednou týdně", "22,7"],
    ["Více než dvakrát týdně", "6,1"],
    ["Méně než jednou týdně", "57,1"],
    ["Jakou čokoládu máte nejraději?", ""],
    ["Studentská pečeť", "32,5"],
    ["Milka", "23,4"],
    ["Orion mléčná", "20,8"],
    ["Jaké čokoládové tyčinky jste jedl v posledních 12 měsících?", ""],
    ["Margot", "29,9"],
    ["Ledové kaštany", "29,2"],
    ["Banán v čokoládě", "27,9"],
    ["Deli", "27,0"],
    ["Kofila", "24,8"],
    ["Milena", "22,4"],
    ["3 BIT", "19,5"],
    ["Studentská pečeť (tyčinka)", "19,4"],
    ["Geisha", "15,0"],
    ["Mars", "13,6"],
    ["Jak často kupujete bonboniéry?", ""],
    ["Dvakrát a více měsíčně", "1,7"],
    ["Jednou měsíčně", "14,9"],
    ["Jednou až dvakrát za 3 měsíce", "23,2"],
    ["Méně než jedenkrát za 3 měsíce", "54,5"],
    ["Neuvedeno", "5,7"],
    ["Jaké bonboniéry jste koupili v posledních 12 měsících?", ""],
    ["Laguna – mořské plody", "31,9"],
    ["Figaro – Tatiana", "25,6"],
    ["Figaro – Zlatý nugát", "21,6"],
    ["Tofifee", "19,6"],
    ["Orion – Modré z nebe", "19,4"],
    ["Nugátový dezert", "17,6"],
    ["Ferrero Rocher", "16,2"],
    ["Merci", "15,7"],
    ["Raffaello", "13,9"],
    ["Mon Chéri", "13,5"],
]

SLADKE_FULL_TEXT = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Níže je tabulka „Češi a čokoláda“ (údaje jsou v procentech).
Čti ji pozorně – budeš z ní vyvozovat odpovědi.
{{TAB_S}}

Potom si přečti výchozí článek a odpověz na otázky.

Euroamerickou civilizaci sužuje novodobá epidemie: obezita a s ní spojené choroby metabolismu, srdce a cév.
Výrobci cukrovinek po celém světě pocítili sílící poptávku po nízkokalorických čokoládách, light mlsání a dietních bonbonech.
Až na české luhy a háje. Češi podle výzkumů netouží po nízkokalorickém mlsání a nechtějí ani výrazné upozornění na energetickou hodnotu.

Novodobí „alchymisté“ v laboratořích stále hledají náhražku cukru, která by měla dobrou sladivost, neměla nepříjemnou chuť ani pach a nezásobovala tělo zbytečnými kaloriemi.
V posledních letech se používají například alditoly, ale často mají nižší sladivost.
Nahradit sacharózu je stále problém.

Analytik doporučuje upřednostňovat složité cukry před jednoduchými cukry.
Záleží však na situaci: pro rychlou energii mohou jednoduché cukry posloužit, ale pro večerní mlsání je lepší vybírat pečlivěji.
"""

SLADKE_SIMPLIFIED_TEXT = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ (zjednodušený text)

Podívej se na tabulku „Češi a čokoláda“. Ukazuje, jak často lidé jedí čokoládu a co si kupují.
{{TAB_S}}

V článku se píše, že v Evropě a Americe je hodně obezity. Proto roste zájem o nízkokalorické sladkosti.
V Česku ale lidé většinou light sladkosti moc nechtějí.

Vědci hledají náhražku cukru, která:
• sladí dobře,
• nebude mít nepříjemnou chuť ani pach,
• nebude mít moc kalorií.
"""

SLADKE_LMP_TEXT = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ (LMP/SPU)

1) Tabulka „Češi a čokoláda“:
{{TAB_S}}

2) Co je důležité v textu:
• Ve světě je hodně obezity.
• Proto lidé chtějí sladkosti s méně kaloriemi.
• V Česku o to lidé často nestojí.
"""

SLADKE_DRAMA = [
    "Učitel/ka: „Představte si, že jste odborníci na sladkosti.“",
    "Žák A: „Já bych jedl jen čokoládu!“",
    "Žák B: „A co kdybychom chtěli sladké, ale zdravější?“",
    "Učitel/ka: „Nejdřív krátká scénka, potom slovníček, a pak budeme číst text i tabulku.“",
]

SLADKE_QUESTIONS = [
    "A) 1) Který výrok je v rozporu s textem?\n   A Vědcům se podařilo najít ideální náhražku cukru.\n   B Obezita souvisí s nemocemi.\n   C Ve světě roste poptávka po nízkokalorických sladkostech.\n   D V Česku lidé většinou light sladkosti moc nechtějí.\n   Odpověď: ________",
    "A) 2) Podle tabulky: Je správně, že více než polovina jí čokoládu méně než jednou týdně? Ano / Ne",
    "B) 3) Proč je těžké najít dobrou náhražku cukru? Napiš vlastními slovy.\n   ________________________________________________",
    "C) 4) Myslíš, že je dobré řešit „light“ sladkosti? Proč ano/ne?\n   ________________________________________________",
]

SLADKE_GLOSSARY = {
    "epidemie": "když se nějaký problém hodně rozšíří mezi lidmi.",
    "obezita": "velká nadváha, která může škodit zdraví.",
    "metabolismus": "to, jak tělo zpracovává jídlo a energii.",
    "nízkokalorický": "má málo kalorií (energie).",
    "náhražka": "něco, co nahradí původní věc.",
    "sladivost": "jak moc něco sladí.",
    "kalorie": "energie z jídla.",
    "alchymisté": "lidé, kteří něco „zázračně“ hledají – tady vědci v laboratoři.",
    "upřednostňovat": "vybírat raději než něco jiného.",
}

SLADKE_PACK = TextPack(
    key="sladke",
    title="Sladké mámení",
    grade=5,
    points_max=12,
    full_text=SLADKE_FULL_TEXT,
    simplified_text=SLADKE_SIMPLIFIED_TEXT,
    lmp_text=SLADKE_LMP_TEXT,
    dramatization=SLADKE_DRAMA,
    questions=SLADKE_QUESTIONS,
    glossary_map=SLADKE_GLOSSARY,
    tables_spec={"TAB_S": SLADKE_TABLE_ROWS},
)


# -----------------------------------
# 3) Věnečky (4. třída) – tabulka 100% dle PDF
# -----------------------------------
VENECKY_TABLE_ROWS = [
    ["Cukrárna", "Cena v Kč", "Vzhled", "Korpus", "Náplň", "Suroviny", "Celková známka (jako ve škole)"],
    ["1", "15", "4", "5", "2", "1", "3"],
    ["2", "17", "4", "5", "5", "5", "5"],
    ["3", "11,50", "5", "5", "5", "5", "5"],
    ["4", "19", "2", "1", "2", "2", "2"],
    ["5", "20", "3", "3", "5", "5", "4"],
]

VENECKY_FULL_TEXT = """NÁZEV ÚLOHY: VĚNEČKY

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Přečti si text a všímej si, jak hodnotitelka popisuje chuť, krém a těsto.

Věneček č. 2: Hodnotitelce vadil sražený krém, chemická pachuť a tvrdý korpus bez drážek.
Věneček č. 3: Rum je cítit, ale prý jen zakrývá, že zákusek nemá jiné chutě. Korpus je přepečený a dole ztvrdlý.
Věneček č. 4: Vypadá nejlépe. Náplň vypadá jako pudink, korpus je vláčný a lehce křupavý.
Věneček č. 5: Vypadá hezky, ale náplň je „chemický pudink“ z prášku a vody, těsto je staré a ztvrdlé.

Níže je tabulka hodnocení (přesně podle originálu):
{{TAB_V}}
"""

VENECKY_SIMPLIFIED_TEXT = """NÁZEV ÚLOHY: VĚNEČKY (zjednodušený text)

Hodnotitelka ochutnává věnečky z různých cukráren.
Nejvíc jí chutná věneček č. 4.
Některé věnečky jsou špatné: krém je sražený nebo „chemický“ a těsto tvrdé.

Tabulka hodnocení:
{{TAB_V}}
"""

VENECKY_LMP_TEXT = """NÁZEV ÚLOHY: VĚNEČKY (LMP/SPU)

Čteme o tom, jak paní hodnotí věnečky.
• Věneček č. 4 je nejlepší.
• Některé věnečky jsou tvrdé nebo „chemické“.

Tabulka hodnocení:
{{TAB_V}}
"""

VENECKY_DRAMA = [
    "Učitel/ka: „Představte si, že jste ochutnávači v cukrárně.“",
    "Žák A: „Já hodnotím hlavně chuť!“",
    "Žák B: „A já bych koukal/a, jaké je těsto a krém.“",
    "Učitel/ka: „Nejdřív scénka, potom slovníček a pak se vrátíme do textu a tabulky.“",
]

VENECKY_QUESTIONS = [
    "A) 1) Který věneček neobsahuje pudink uvařený z mléka?\n   A č.2  B č.3  C č.4  D č.5\n   Odpověď: ________",
    "A) 2) Ve kterém věnečku rum zakrývá, že chybí jiné chutě?\n   A č.2  B č.3  C č.4  D č.5\n   Odpověď: ________",
    "A) 3) Který věneček je podle textu nejlepší? ________",
    "B) 4) Který věneček je nejdražší a jakou má známku?\n   ________________________________________________",
    "C) 5) Co je podle tebe důležité, aby byl zákusek „poctivý“? Napiš 2 věci.\n   1) __________________________\n   2) __________________________",
]

VENECKY_GLOSSARY = {
    "sražený": "když krém není hladký a je „hrudkovitý“.",
    "pachuť": "nepříjemná chuť, která zůstává v puse.",
    "korpus": "těsto, základ zákusku.",
    "drážky": "linky na těstě, které jsou vidět po zdobení.",
    "zakrývá": "schovává, aby to nebylo poznat.",
    "přepečený": "upečený moc – je tvrdý nebo suchý.",
    "vláčný": "měkký a příjemný na kousnutí.",
    "křupavý": "když to při kousnutí křupne.",
}

VENECKY_PACK = TextPack(
    key="venecky",
    title="Věnečky",
    grade=4,
    points_max=12,
    full_text=VENECKY_FULL_TEXT,
    simplified_text=VENECKY_SIMPLIFIED_TEXT,
    lmp_text=VENECKY_LMP_TEXT,
    dramatization=VENECKY_DRAMA,
    questions=VENECKY_QUESTIONS,
    glossary_map=VENECKY_GLOSSARY,
    tables_spec={"TAB_V": VENECKY_TABLE_ROWS},
)


PACKS: Dict[str, TextPack] = {
    "Karetní hra (3. třída)": KARETNI_PACK,
    "Věnečky (4. třída)": VENECKY_PACK,
    "Sladké mámení (5. třída)": SLADKE_PACK,
}


# -----------------------------------
# Vkládání tabulek do textu (MARKERY)
# -----------------------------------
def add_text_with_tables(doc: Document, raw_text: str, tables_spec: Optional[Dict[str, List[List[str]]]]):
    if not tables_spec:
        for line in raw_text.split("\n"):
            if line.strip():
                doc.add_paragraph(line)
        return

    pattern = r"\{\{([A-Z0-9_]+)\}\}"
    parts = re.split(pattern, raw_text)

    i = 0
    while i < len(parts):
        chunk = parts[i]
        if chunk.strip():
            for line in chunk.split("\n"):
                if line.strip():
                    doc.add_paragraph(line)
        if i + 1 < len(parts):
            marker = parts[i + 1]
            if marker in tables_spec:
                rows = tables_spec[marker]
                if len(rows[0]) == 2:
                    make_table(doc, rows, col_widths_cm=[12.0, 3.0], header_bold=False)
                else:
                    make_table(doc, rows, col_widths_cm=[2.0, 2.2, 1.5, 1.5, 1.5, 1.8, 3.8], header_bold=True)
                doc.add_paragraph("")
            i += 2
        else:
            i += 1


# -----------------------------------
# Generátor pracovních listů
# -----------------------------------
def build_workbook(pack: TextPack, version: str) -> Document:
    doc = Document()
    set_doc_defaults(doc, base_font_size=11)

    title_map = {
        "full": f"EdRead AI – PRACOVNÍ LIST (PLNÝ) – {pack.title}",
        "simplified": f"EdRead AI – PRACOVNÍ LIST (ZJEDNODUŠENÝ) – {pack.title}",
        "lmp": f"EdRead AI – PRACOVNÍ LIST (LMP/SPU) – {pack.title}",
    }
    add_title(doc, title_map[version], f"Ročník: {pack.grade}. třída | Max.: {pack.points_max} bodů")
    add_name_line(doc)

    # 1) Dramatizace
    add_section_header(doc, "1) ÚVODNÍ DRAMATIZACE (motivace – začátek hodiny)")
    add_bullets(doc, pack.dramatization)

    # 2) Text pro žáky
    add_section_header(doc, "2) TEXT PRO ŽÁKY (čti pozorně)")
    if version == "full":
        add_text_with_tables(doc, pack.full_text, pack.tables_spec)
    elif version == "simplified":
        add_text_with_tables(doc, pack.simplified_text, pack.tables_spec)
    else:
        add_text_with_tables(doc, pack.lmp_text, pack.tables_spec)

    # Karetní – vizuální opora + sloupec síly + kartičky
    if pack.key == "karetni":
        add_section_header(doc, "3) OBRÁZKOVÁ OPORA K PRAVIDLŮM HRY")
        add_karetni_strength_matrix(doc)
        doc.add_paragraph("")
        add_strength_column_template(doc)
        doc.add_paragraph("")
        add_animal_cards_3cols(doc)
        q_section_no = 4
    else:
        q_section_no = 3

    # Otázky
    add_section_header(doc, f"{q_section_no}) OTÁZKY (A = vyhledej, B = vysvětli, C = názor)")
    for q in pack.questions:
        doc.add_paragraph(q)
        add_lines_for_answer(doc, lines=1)
        doc.add_paragraph("")

    # Slovníček až na konci
    text_for_vocab = pack.full_text if version == "full" else pack.simplified_text if version == "simplified" else pack.lmp_text
    words = extract_candidate_words(text_for_vocab, max_words=12)
    add_glossary_section(doc, words, pack.glossary_map)

    return doc


# -----------------------------------
# Metodický list pro učitele (zvlášť)
# -----------------------------------
def build_methodology(pack: TextPack) -> Document:
    doc = Document()
    set_doc_defaults(doc, base_font_size=11)

    add_title(doc, f"EdRead AI – METODICKÝ LIST PRO UČITELE – {pack.title}", f"Ročník: {pack.grade}. třída")
    doc.add_paragraph("Tento metodický list slouží jako manuál pro učitele, který bude realizovat ověření materiálů ve třídě.")
    doc.add_paragraph("")

    add_section_header(doc, "1) Cíl didaktického zásahu")
    add_bullets(doc, [
        "Podpora čtenářské gramotnosti prostřednictvím strukturované práce s textem.",
        "Rozvoj porozumění, práce s informacemi, interpretace a formulace názoru (A/B/C).",
        "Vizuální opory jsou součástí materiálu (učitel nemusí nic dohledávat)."
    ])

    add_section_header(doc, "2) Návaznost na RVP ZV (jazyk a jazyková komunikace)")
    doc.add_paragraph(
        "Materiály vedou žáka k vyhledávání informací, porozumění textu, interpretaci a formulaci odpovědi. "
        "Úlohy A/B/C podporují postup od práce s explicitní informací přes výklad až po vlastní stanovisko."
    )

    add_section_header(doc, "3) Výstupy EdRead AI (DOCX)")
    add_bullets(doc, [
        "Pracovní list – PLNÝ: plný text + tabulky v místě textu + otázky + slovníček na konci.",
        "Pracovní list – ZJEDNODUŠENÝ: zjednodušený text + tabulky + stejné typy úloh.",
        "Pracovní list – LMP/SPU: nejvyšší míra struktury a srozumitelnosti, kratší bloky textu.",
        "Metodický list: jasný postup hodiny + přehled rozdílů mezi verzemi."
    ])

    add_section_header(doc, "4) Rozdíly mezi verzemi (pro rychlý výběr učitele)")
    if pack.key == "karetni":
        add_bullets(doc, [
            "PLNÝ: kompletní pravidla hry (více informací, delší text).",
            "ZJEDNODUŠENÝ: kratší a přímější formulace pravidel, méně zátěže najednou.",
            "LMP/SPU: text rozdělen do kroků, odrážky, zjednodušené věty.",
            "Vizuální opory: matice síly + sloupec síly (šablona) + kartičky (ve všech verzích)."
        ])
    else:
        add_bullets(doc, [
            "PLNÝ: širší významový rozsah textu, plnější formulace.",
            "ZJEDNODUŠENÝ: kratší a srozumitelnější verze při zachování hlavních sdělení.",
            "LMP/SPU: nejvyšší struktura – krátké úseky, odrážky, orientační body.",
            "Slovníček je fyzicky na konci pracovního listu (neruší čtení)."
        ])

    add_section_header(doc, "5) Doporučený průběh hodiny (DŮLEŽITÉ – pořadí práce)")
    add_bullets(doc, [
        "1) Dramatizace (5–7 min): krátká scénka bez pomůcek.",
        "2) Slovníček (5–8 min): i když je na konci pracovního listu, učitel žáky záměrně vede nejprve ke slovníčku. "
        "Žáci si slovníček projdou, případně si doplní poznámky ke slovům.",
        "3) Čtení textu (10–15 min): teprve po slovníčku se žáci vrátí do textu a čtou s lepším porozuměním.",
        "4) Otázky (15–20 min): vyplňování úloh A/B/C; učitel sleduje práci s textem a argumentaci.",
        "5) Krátká reflexe (2–3 min): co bylo nejtěžší, co pomohlo (slovníček, tabulka, vizuální opora)."
    ])

    add_section_header(doc, "6) Kritéria pro volbu verze (orientačně)")
    add_bullets(doc, [
        "PLNÝ: běžná úroveň čtení, žák zvládá delší text.",
        "ZJEDNODUŠENÝ: žák potřebuje kratší text a jasnější formulace.",
        "LMP/SPU: žák potřebuje výraznou strukturu, kratší věty, více podpory v orientaci."
    ])

    return doc


# -----------------------------------
# Streamlit UI
# -----------------------------------
st.set_page_config(page_title="EdRead AI (prototyp)", layout="wide")
st.title("EdRead AI – prototyp pro diplomovou práci")
st.caption("Generuje pracovní listy (plný / zjednodušený / LMP-SPU) + metodiku. Texty: Karetní hra, Věnečky, Sladké mámení.")

text_choice = st.selectbox("Vyber text:", list(PACKS.keys()))
pack = PACKS[text_choice]

st.markdown("---")
st.subheader("Generování výstupů")

if "bytes_full" not in st.session_state:
    st.session_state.bytes_full = None
    st.session_state.bytes_simpl = None
    st.session_state.bytes_lmp = None
    st.session_state.bytes_meto = None

colA, colB, colC, colD = st.columns(4)

with colA:
    if st.button("Vygenerovat PLNÝ list", use_container_width=True):
        doc = build_workbook(pack, "full")
        st.session_state.bytes_full = doc_to_bytes(doc)

with colB:
    if st.button("Vygenerovat ZJEDNODUŠENÝ list", use_container_width=True):
        doc = build_workbook(pack, "simplified")
        st.session_state.bytes_simpl = doc_to_bytes(doc)

with colC:
    if st.button("Vygenerovat LMP/SPU list", use_container_width=True):
        doc = build_workbook(pack, "lmp")
        st.session_state.bytes_lmp = doc_to_bytes(doc)

with colD:
    if st.button("Vygenerovat METODIKU", use_container_width=True):
        doc = build_methodology(pack)
        st.session_state.bytes_meto = doc_to_bytes(doc)

st.markdown("---")
st.subheader("Stažení souborů (DOCX)")

d1, d2, d3, d4 = st.columns(4)

with d1:
    if st.session_state.bytes_full:
        st.download_button(
            "Stáhnout PLNÝ list",
            data=st.session_state.bytes_full,
            file_name=f"pracovni_list_{pack.title}_plny.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="dl_full",
            use_container_width=True
        )
    else:
        st.info("Nejdřív vygeneruj PLNÝ list.")

with d2:
    if st.session_state.bytes_simpl:
        st.download_button(
            "Stáhnout ZJEDNODUŠENÝ list",
            data=st.session_state.bytes_simpl,
            file_name=f"pracovni_list_{pack.title}_zjednoduseny.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="dl_simpl",
            use_container_width=True
        )
    else:
        st.info("Nejdřív vygeneruj zjednodušený list.")

with d3:
    if st.session_state.bytes_lmp:
        st.download_button(
            "Stáhnout LMP/SPU list",
            data=st.session_state.bytes_lmp,
            file_name=f"pracovni_list_{pack.title}_LMP_SPU.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="dl_lmp",
            use_container_width=True
        )
    else:
        st.info("Nejdřív vygeneruj LMP/SPU list.")

with d4:
    if st.session_state.bytes_meto:
        st.download_button(
            "Stáhnout METODIKU",
            data=st.session_state.bytes_meto,
            file_name=f"metodicky_list_{pack.title}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="dl_meto",
            use_container_width=True
        )
    else:
        st.info("Nejdřív vygeneruj metodiku.")
