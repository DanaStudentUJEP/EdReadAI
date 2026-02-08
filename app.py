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

def add_horizontal_line(doc: Document):
    p = doc.add_paragraph(" ")
    p.paragraph_format.space_after = Pt(0)

def set_cell_border(cell, **kwargs):
    """
    Nastaví okraje buňky tabulky v docx.
    kwargs např. top={"sz":12,"val":"single","color":"000000"}
    """
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
    """
    Výběr slov podobně jako původní logika: delší, méně častá, bez čísel.
    Aby se nevybíraly hlavičky typu "Správným", filtrujeme i běžné meta-terms.
    """
    stop = {
        "název", "úlohy", "jměno", "správným", "řešením", "celé", "úlohy",
        "maximálně", "bodů", "otázka", "body", "bod", "zdroj", "upraveno"
    }
    tokens = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    tokens = [t.strip() for t in tokens if len(t.strip()) >= 7]
    # zachovat původní tvar pro žáky, ale filtrovat dle lower
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

def explain_word(word: str, grade: int, glossary_map: Dict[str, str]) -> Optional[str]:
    """
    Vysvětlení:
    1) pokud je ve slovníku (ručně připravené pro daný text), použijeme
    2) jinak vrátíme None => jen linka pro poznámku
    """
    w = word.lower()
    if w in glossary_map:
        return glossary_map[w]
    return None

def add_glossary_section(doc: Document, words: List[str], grade: int, glossary_map: Dict[str, str]):
    add_section_header(doc, "SLOVNÍČEK (na konci pracovního listu)")
    add_instruction(doc, "Ke slovům si můžeš dopsat vlastní poznámku.")
    for w in words:
        expl = explain_word(w, grade, glossary_map)
        p = doc.add_paragraph()
        run = p.add_run(f"• {w}: ")
        run.bold = True
        if expl:
            doc.add_paragraph(f"  {expl}")
        # vždy ponechat prostor pro poznámku žáka
        doc.add_paragraph("  Poznámka žáka: ________________________________________________")


# -----------------------------------
# Karetní hra – pyramid + kartičky
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

def add_pyramid_template(doc: Document):
    """
    12 zvířat => pyramidová šablona 4 patra:
    1 + 2 + 3 + 6 = 12.
    Vrchol = 1 (nejsilnější), spodek = 6 (nejslabší).
    """
    add_section_header(doc, "ZVÍŘECÍ PYRAMIDA (pomůcka k porozumění pravidlům)")
    add_instruction(doc, "Vystřihni kartičky se zvířaty a nalep je do pyramidy. Nahoře bude nejsilnější, dole nejslabší.")
    add_instruction(doc, "Tip: Chameleon je žolík – do pyramidy ho nelepuj mezi sílu zvířat, patří bokem (pomocná karta).")

    # Vytvoříme tabulku 4 řádky x 6 sloupců, aby šla pěkně centrovat.
    # Řádek 1: 1 místo (merge 6 do 1)
    # Řádek 2: 2 místa (3+3)
    # Řádek 3: 3 místa (2+2+2)
    # Řádek 4: 6 míst (1+1+1+1+1+1)

    t = doc.add_table(rows=4, cols=6)
    t.style = "Table Grid"

    # nastavíme výšku řádků (vizuálně)
    for r in range(4):
        for c in range(6):
            cell = t.cell(r, c)
            cell.text = ""
            # silnější okraj
            set_cell_border(
                cell,
                top={"sz": 14, "val": "single", "color": "000000"},
                bottom={"sz": 14, "val": "single", "color": "000000"},
                left={"sz": 14, "val": "single", "color": "000000"},
                right={"sz": 14, "val": "single", "color": "000000"},
            )

    # Merge pro pyramidový tvar
    # Row 0: all merged
    top = t.cell(0, 0).merge(t.cell(0, 5))
    top.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    top.paragraphs[0].add_run("NEJSILNĚJŠÍ").bold = True

    # Row 1: 2 blocks (0-2) and (3-5)
    left2 = t.cell(1, 0).merge(t.cell(1, 2))
    right2 = t.cell(1, 3).merge(t.cell(1, 5))
    left2.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    right2.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Row 2: 3 blocks (0-1),(2-3),(4-5)
    a = t.cell(2, 0).merge(t.cell(2, 1))
    b = t.cell(2, 2).merge(t.cell(2, 3))
    c = t.cell(2, 4).merge(t.cell(2, 5))
    for cell in (a, b, c):
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Row 3: 6 single cells – dolní patro
    for col in range(6):
        t.cell(3, col).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # popisek dole
    doc.add_paragraph()
    p = doc.add_paragraph("NEJSLABŠÍ (dole)")
    p.runs[0].bold = True

def add_animal_cards_3cols(doc: Document):
    """
    Kartičky v pracovním listu – 3 sloupce, emoji + správný český název.
    Bez černých „siluet“.
    """
    add_section_header(doc, "KARTIČKY SE ZVÍŘATY (vystřihni)")
    add_instruction(doc, "Kartičky vystřihni a použij pro pyramidovou pomůcku.")

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
            cell_par = cell.paragraphs[0]
            cell_par.paragraph_format.space_after = Pt(0)
            cell_par.paragraph_format.space_before = Pt(0)
            cell_par.alignment = WD_ALIGN_PARAGRAPH.CENTER

            if idx < len(animals):
                name, emoji = animals[idx]
                # emoji
                pr = cell.add_paragraph()
                pr.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run_e = pr.add_run(emoji)
                run_e.font.size = Pt(28)
                run_e.font.name = "Segoe UI Emoji"

                # název
                pr2 = cell.add_paragraph()
                pr2.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run_n = pr2.add_run(name)
                run_n.bold = True
                run_n.font.size = Pt(12)

                # poznámka
                pr3 = cell.add_paragraph("__________")
                pr3.alignment = WD_ALIGN_PARAGRAPH.CENTER

            idx += 1


def add_karetni_strength_matrix(doc: Document):
    """
    „Kdo přebije koho?“ – matice s emoji a názvy (obrázková opora).
    V originálu jsou obrázky na kartách – zde děláme tiskově použitelnou verzi.
    Logika: sloupec = silnější než řádek.
    """
    add_section_header(doc, "KDO PŘEBIJE KOHO? (tabulka podle pravidel)")
    add_instruction(doc, "V tabulce najdeš, kdo je silnější. Pokud je v políčku tečka, zvíře ve sloupci přebíjí zvíře v řádku.")

    animals = KARETNI_ORDER_STRONG_TO_WEAK[:]  # 12 bez chameleona
    headers = [""] + [f"{emo} {name}" for name, emo in animals]

    rows = [headers]
    for r_name, r_emo in animals:
        row = [f"{r_emo} {r_name}"]
        for c_name, c_emo in animals:
            # c přebíjí r, pokud je v pořadí výš (silnější)
            r_idx = [n for n, _ in animals].index(r_name)
            c_idx = [n for n, _ in animals].index(c_name)
            row.append("●" if c_idx < r_idx else "")
        rows.append(row)

    # šířky – první sloupec širší
    table = make_table(doc, rows, col_widths_cm=[5.2] + [2.0]*len(animals), header_bold=True)
    # trochu zmenšit font v tabulce
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
    questions: List[str]  # už hotové otázky (A/B/C)
    glossary_map: Dict[str, str]
    include_tables: bool
    tables_spec: Optional[Dict[str, List[List[str]]]] = None  # marker -> rows


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

Kdo je silnější?
Silnější zvíře přebíjí slabší. Někdy můžeš přebít i stejným zvířetem, ale musíš dát o jednu kartu víc.
Chameleon je žolík: hraje se vždy s jinou kartou a může ji „změnit“ na jiné zvíře.

Když nemůžeš přebít, řekneš „pass“.
Kdo se zbaví karet jako první, vyhrává.
"""

KARETNI_LMP_TEXT = """NÁZEV ÚLOHY: KARETNÍ HRA (LMP/SPU)

1) Cíl hry:
Vyhrává ten, kdo bude mít jako první v ruce 0 karet.

2) Jak se hraje:
Hráči dávají karty na stůl. Další hráč musí dát silnější kartu (nebo více karet podle pravidel).

3) Důležité:
• Silnější zvíře přebíjí slabší.
• Stejné zvíře může přebít stejné zvíře jen tak, že dáš O JEDNU KARTU VÍCE.
• Chameleon je žolík. Hraje se vždy s jinou kartou.
• Když nemůžeš hrát, řekneš: pass.
"""

KARETNI_DRAMA = [
    "Učitel/ka: „Máme novou hru, ale pravidla jsou trochu zamotaná.“",
    "Žák A: „Já nevím, kdo je silnější… myš nebo lev?“",
    "Žák B: „Zkusme si to! Uděláme z toho pyramidovou pomůcku.“",
    "Učitel/ka: „Super. Nejdřív přečteme pravidla a potom si sílu zvířat poskládáme.“",
]

KARETNI_QUESTIONS = [
    "A) 1) Co je cílem hry?\n   A Dosáhnout nejvyššího počtu „přebití“.\n   B Nemít v ruce žádné karty jako první.\n   C Nasbírat co nejvíce karet.\n   D Získat co nejvíce karet „vyšších“ živočichů.\n   Odpověď: ________",
    "A) 2) Kolik druhů živočichů je ve hře? Napiš počet a krátce zdůvodni.\n   Počet: ________\n   Zdůvodnění: ________________________________________________",
    "B) 3) Kterého živočicha je možné přebít největším počtem druhů? Napiš živočicha a počet.\n   Živočich: _____________  Počet: ________",
    "A) 4) Kolik karet dostane každý hráč při 4 hráčích? (60 karet)\n   Výpočet: __________________  Odpověď: ________",
    "B) 5) Která okolnost NEMŮŽE přispět k vítězství?\n   A chameleon\n   B více stejných zvířat\n   C jen jedna karta každého zvířete\n   D vyšší zvířata\n   Odpověď: ________",
    "C) 6) Napiš jednou větou, proč je podle tebe pyramidová pomůcka užitečná.\n   ________________________________________________",
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
    "vzdát": "přestat, nehrát v tom kole.",
    "prostřed": "místo uprostřed stolu.",
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
    include_tables=True,
    tables_spec=None,  # tabulka pro karetní je generována funkcí (matice)
)


# -----------------------------------
# 2) Sladké mámení (5. třída)
# Tabulka je opsána 100% dle PDF (viz snímek)
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

Níže je tabulka „Češi a čokoláda“ (údaje jsou v procentech). Čti ji pozorně – budeš z ní vyvozovat odpovědi.
{{TAB_S}}
Potom si přečti výchozí článek a odpověz na otázky.

Euroamerickou civilizaci sužuje novodobá epidemie: obezita a s ní spojené choroby metabolismu, srdce a cév.
Výrobci cukrovinek po celém světě pocítili sílící poptávku po nízkokalorických čokoládách, light mlsání a dietních bonbonech.
Až na české luhy a háje. Češi podle výzkumů netouží po nízkokalorickém mlsání a nechtějí ani výrazné upozornění na energetickou hodnotu.

Novodobí „alchymisté“ v laboratořích stále hledají náhražku cukru, která by měla dobrou sladivost, neměla nepříjemnou chuť ani pach a nezásobovala tělo zbytečnými kaloriemi.
V posledních letech se používají například alditoly (např. sorbitol, xylitol, maltitol), ale často mají nižší sladivost. Jedním z objevů je i polydextróza, která má nulovou energetickou hodnotu, ale nahradit sacharózu je stále problém.

Analytik doporučuje upřednostňovat složité cukry (polysacharidy) před jednoduchými cukry, které představují „rychlou energii“.
Záleží však na situaci: pro rychlou energii mohou jednoduché cukry posloužit, ale pro večerní mlsání je lepší vybírat pečlivěji.

Důležité jsou také tuky – některé náhrady mohou být méně vhodné zejména pro dětské zdraví.
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

Důležité je i složení: jednoduché cukry dodají rychlou energii, složité cukry jsou často vhodnější.
"""

SLADKE_LMP_TEXT = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ (LMP/SPU)

1) Podívej se na tabulku „Češi a čokoláda“.
{{TAB_S}}

2) V článku:
• V Evropě a Americe je hodně obezity.
• Proto lidé chtějí sladkosti s méně kaloriemi.
• V Česku o to lidé moc nestojí.

3) Vědci hledají náhražku cukru:
Musí sladit, nesmí být nepříjemná a nesmí mít moc kalorií.
"""

SLADKE_DRAMA = [
    "Učitel/ka: „Představte si, že jste odborníci na sladkosti.“",
    "Žák A: „Já bych jedl jen čokoládu!“",
    "Žák B: „Ale co když chceme sladké a zároveň zdravější?“",
    "Učitel/ka: „Dnes budeme číst text a vyhodnocovat i data v tabulce.“",
]

SLADKE_QUESTIONS = [
    "A) 1) Který výrok je v rozporu s textem?\n   A Vědcům se podařilo nalézt výbornou náhražku cukru.\n   B Euroamerickou civilizaci trápí obezita.\n   C Ve světě roste poptávka po nízkokalorických cukrovinkách.\n   D S obezitou souvisí nemoci metabolismu, srdce a cév.\n   Odpověď: ________",
    "A) 2) Jaké vlastnosti by ideální sladidlo podle článku NEMĚLO mít?\n   A značnou sladivost\n   B příjemnou chuť\n   C intenzivní vůni\n   D nízkou energetickou hodnotu\n   Odpověď: ________",
    "B) 3) Proč se ve světě zvyšuje poptávka po nízkokalorických sladkostech?\n   ________________________________________________\n   ________________________________________________",
    "A) 4) Podle tabulky rozhodni Ano/Ne:\n   a) Více než polovina jí čokoládu méně než jednou týdně.  Ano / Ne\n   b) Merci kupují méně často než Tofifee.                 Ano / Ne\n   c) Kofilu jedlo více lidí než Milky Way.                Ano / Ne\n   d) Přesně pětina má nejraději Milku.                    Ano / Ne",
    "C) 5) Napiš, co je podle tebe lepší pro večerní mlsání – jednoduché nebo složité cukry – a proč.\n   ________________________________________________",
]

SLADKE_GLOSSARY = {
    "epidemie": "když se nějaký problém hodně rozšíří mezi lidmi.",
    "obezita": "velká nadváha, která může škodit zdraví.",
    "metabolismus": "to, jak tělo zpracovává jídlo a energii.",
    "nízkokalorický": "má málo kalorií (energie).",
    "náhražka": "něco, co nahradí původní věc.",
    "sladivost": "jak moc něco sladí.",
    "kalorie": "energie z jídla.",
    "polysacharidy": "složité cukry (např. škrob, vláknina).",
    "glukóza": "hroznový cukr – jednoduchý cukr.",
    "fruktóza": "ovocný cukr – jednoduchý cukr.",
    "ztužené": "upravené tuky, které mohou být méně vhodné.",
    "kardiovaskulární": "týká se srdce a cév.",
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
    include_tables=True,
    tables_spec={"TAB_S": SLADKE_TABLE_ROWS},
)


# -----------------------------------
# 3) Věnečky (4. třída)
# Tabulka opsaná 100% dle PDF
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

(Výchozí článek – zkráceně pro školní práci)
Věneček č. 2: Hodnotitelce vadil sražený krém, chemická pachuť a tvrdý korpus bez drážek.
Věneček č. 3: Rum je cítit, ale prý jen zakrývá, že zákusek nemá jiné chutě. Korpus je přepečený a dole ztvrdlý.
Věneček č. 4: Vypadá nejlépe. Náplň vypadá jako pudink, korpus je vláčný a lehce křupavý. Hodnotitelka říká, že cukrář své řemeslo umí.
Věneček č. 5: Vypadá hezky, ale náplň je „chemický pudink“ z prášku a vody, těsto je staré a ztvrdlé.

Nakonec se ukáže, že vítězný věneček i štrúdl jsou z cukrárny Mámení.

Níže je tabulka hodnocení (přesně podle originálu):
{{TAB_V}}
"""

VENECKY_SIMPLIFIED_TEXT = """NÁZEV ÚLOHY: VĚNEČKY (zjednodušený text)

Hodnotitelka ochutnává věnečky z různých cukráren.
Nejvíc jí chutná věneček č. 4 – má dobrý korpus i náplň.
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
    "Žák B: „A já bych koukal/a, z čeho je krém a jaké je těsto.“",
    "Učitel/ka: „Dnes budeme číst text a porovnávat i tabulku hodnocení.“",
]

VENECKY_QUESTIONS = [
    "A) 1) Který věneček neobsahuje pudink uvařený z mléka?\n   A č.2  B č.3  C č.4  D č.5\n   Odpověď: ________",
    "A) 2) Ve kterém věnečku rum zakrývá, že chybí jiné chutě?\n   A č.2  B č.3  C č.4  D č.5\n   Odpověď: ________",
    "A) 3) Který věneček byl hodnocen nejlépe? ________",
    "A) 4) Který podnik dopadl nejlépe?\n   A Pekárna Krémová  B Cukrárna Věnečky  C Cukrárna Dortíček  D Cukrárna Mámení\n   Odpověď: ________",
    "B) 5) Který věneček byl nejdražší? Kolik stál a kde byl zakoupen?\n   Nejdražší: č.___  Cena: ____ Kč  Kde: ______________________\n   Cena odpovídá kvalitě? Ano / Ne\n   Zdůvodnění: ________________________________________________",
    "C) 6) Co podle tebe rozhoduje o tom, že je věneček „poctivý“? Napiš 2 věci.\n   1) __________________________\n   2) __________________________",
]

VENECKY_GLOSSARY = {
    "sražený": "když krém není hladký a je „hrudkovitý“.",
    "pachuť": "nepříjemná chuť, která zůstává v puse.",
    "korpus": "těsto, základ zákusku.",
    "drážky": "linky na těstě, které jsou vidět po zdobení.",
    "absenci": "to, že něco chybí.",
    "přebít": "zakrýt (např. vůní zakrýt jinou chuť).",
    "průmyslově": "vyrobené ve velkém v továrně.",
    "listové": "těsto z mnoha vrstev.",
    "vláčný": "měkký a příjemný na kousnutí.",
    "křupavý": "když to při kousnutí křupne.",
    "verdikt": "výsledek rozhodnutí, konečné hodnocení.",
    "vyzdvihla": "pochválila, řekla, že je to dobré.",
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
    include_tables=True,
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
    """
    Text může obsahovat markery {{TAB_X}}.
    Vloží se tabulka přesně na místo markeru.
    """
    if not tables_spec:
        # bez tabulek
        for line in raw_text.split("\n"):
            doc.add_paragraph(line)
        return

    pattern = r"\{\{([A-Z0-9_]+)\}\}"
    parts = re.split(pattern, raw_text)

    # re.split => text, markerName, text, markerName...
    i = 0
    while i < len(parts):
        chunk = parts[i]
        doc.add_paragraph(chunk) if chunk.strip() else None
        if i + 1 < len(parts):
            marker = parts[i + 1]
            if marker in tables_spec:
                rows = tables_spec[marker]
                # tabulka s mřížkou, přesná čísla
                # pro sladké: 2 sloupce; pro věnečky: 7 sloupců
                if len(rows[0]) == 2:
                    make_table(doc, rows, col_widths_cm=[12.0, 3.0], header_bold=False)
                else:
                    make_table(doc, rows, col_widths_cm=[2.0, 2.2, 1.5, 1.5, 1.5, 1.8, 3.8], header_bold=True)
                doc.add_paragraph("")  # mezera
            i += 2
        else:
            i += 1


# -----------------------------------
# Generátor pracovních listů
# -----------------------------------
def build_workbook(pack: TextPack, version: str) -> Document:
    """
    version: 'full' | 'simplified' | 'lmp'
    """
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

    # 2) Čtený text (DŮLEŽITÉ: u každé verze jiný text)
    add_section_header(doc, "2) TEXT PRO ŽÁKY (čti pozorně)")
    if version == "full":
        add_text_with_tables(doc, pack.full_text, pack.tables_spec)
    elif version == "simplified":
        add_text_with_tables(doc, pack.simplified_text, pack.tables_spec)
    else:
        add_text_with_tables(doc, pack.lmp_text, pack.tables_spec)

    # Karetní – tabulka síly + pyramida + kartičky uvnitř pracovního listu
    if pack.key == "karetni":
        add_section_header(doc, "3) OBRÁZKOVÁ OPORA K TEXTU (pomoc při porozumění)")
        add_karetni_strength_matrix(doc)
        doc.add_paragraph("")
        add_pyramid_template(doc)
        doc.add_paragraph("")
        add_animal_cards_3cols(doc)
        q_section_no = 4
    else:
        q_section_no = 3

    # 3/4) Otázky A/B/C
    add_section_header(doc, f"{q_section_no}) OTÁZKY (A = vyhledej, B = vysvětli, C = názor)")
    for q in pack.questions:
        doc.add_paragraph(q)
        add_lines_for_answer(doc, lines=1)
        doc.add_paragraph("")

    # Slovníček až úplně na konci
    # Pro výběr použijeme text dané verze, aby to bylo věkově přiměřené.
    text_for_vocab = pack.full_text if version == "full" else pack.simplified_text if version == "simplified" else pack.lmp_text
    words = extract_candidate_words(text_for_vocab, max_words=12)
    add_glossary_section(doc, words, pack.grade, pack.glossary_map)

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
        "Podpořit rozvoj čtenářské gramotnosti na 1. stupni prostřednictvím strukturovaných pracovních listů.",
        "Rozvíjet porozumění textu, práci s informacemi, interpretaci a formulaci vlastního názoru (A/B/C).",
        "Poskytnout vizuální oporu (u 3. třídy zejména pyramidová pomůcka) bez přímé práce žáků s AI."
    ])

    add_section_header(doc, "2) Návaznost na RVP ZV (jazyk a jazyková komunikace)")
    doc.add_paragraph(
        "Materiály jsou koncipovány tak, aby podporovaly očekávané výstupy v oblasti práce s textem: "
        "vyhledávání informací, porozumění, interpretace, rozlišování faktu a názoru, formulace odpovědi a argumentace "
        "přiměřeně věku žáků. Nástroj strukturuje činnost žáků tak, aby učitel mohl sledovat proces porozumění i výsledky."
    )

    add_section_header(doc, "3) Popis výstupů EdRead AI (DOCX)")
    add_bullets(doc, [
        "Pracovní list – PLNÝ: obsahuje plný text (včetně tabulek v místě textu) + otázky A/B/C + slovníček na konci.",
        "Pracovní list – ZJEDNODUŠENÝ: obsahuje zjednodušený text (přehlednější, kratší věty) + stejné typy úloh.",
        "Pracovní list – LMP/SPU: obsahuje upravený text s vyšší strukturou, kratšími bloky a podporou orientace.",
        "Metodický list: manuál, doporučený postup hodiny, kritéria pro volbu verze a vymezení rozdílů mezi verzemi."
    ])

    add_section_header(doc, "4) Rozdíly mezi verzemi (pro výběr učitele)")
    if pack.key == "karetni":
        add_bullets(doc, [
            "PLNÝ: plná pravidla hry, kompletní informace a úkoly.",
            "ZJEDNODUŠENÝ: kratší text, explicitnější formulace pravidel (méně informací najednou).",
            "LMP/SPU: text rozdělen do číslovaných kroků, menší jazyková zátěž a jasné odrážky.",
            "Vizuální opora: tabulka síly (matice) + pyramida na lepení + kartičky (ve všech verzích).",
        ])
    else:
        add_bullets(doc, [
            "PLNÝ: delší text s plným významovým rozsahem a tabulkami uvnitř textu.",
            "ZJEDNODUŠENÝ: zkrácený a srozumitelnější text (zachovaná hlavní sdělení).",
            "LMP/SPU: nejvyšší míra strukturování, kratší bloky, jednodušší věty.",
            "Otázky A/B/C: typově stejné, aby šlo porovnávat práci žáků mezi verzemi.",
            "Slovníček je vždy na konci (umožní nepřerušovat čtení)."
        ])

    add_section_header(doc, "5) Doporučený průběh ověření (45 min)")
    add_bullets(doc, [
        "5–7 min: dramatizace (motivační scénka) – bez dalších pomůcek.",
        "10–15 min: tiché čtení / společné čtení po odstavcích, průběžné zastavení u klíčových míst.",
        "15–20 min: práce s otázkami A/B/C (individuálně, poté krátká kontrola).",
        "5 min: slovníček – doplnění poznámek žáků, krátká reflexe.",
    ])

    add_section_header(doc, "6) Kritéria pro volbu verze (orientačně)")
    add_bullets(doc, [
        "PLNÝ: běžná úroveň čtení, žák zvládá delší text a práci s informacemi.",
        "ZJEDNODUŠENÝ: žák čte pomaleji / hůře drží pozornost, ale rozumí při kratších blocích.",
        "LMP/SPU: žák potřebuje výraznou strukturu, kratší věty, častější orientační body."
    ])

    return doc


# -----------------------------------
# Streamlit UI
# -----------------------------------
st.set_page_config(page_title="EdRead AI (prototyp)", layout="wide")
st.title("EdRead AI – prototyp pro diplomovou práci")
st.caption("Generuje pracovní listy (plný / zjednodušený / LMP-SPU) + metodiku. Pro 3 texty: Karetní hra, Věnečky, Sladké mámení.")

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
