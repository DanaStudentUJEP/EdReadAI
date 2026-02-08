# app.py — EdRead AI (finální verze: tlačítka NEZMIZÍ + tabulky ve všech verzích)
# Autor: ChatGPT
# Použití: Streamlit + python-docx
#
# ✅ Download tlačítka nezmizí po kliknutí (výstupy uloženy v session_state pod stabilním klíčem)
# ✅ Zjednodušené a LMP verze u předpřipravených textů VŽDY obsahují tabulky (klíčové pro otázky)
# ✅ Slovníček je vždy na konci pracovního listu
# ✅ Metodika vede: dramatizace → slovníček → čtení → otázky

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


# ---------------------------
# DOCX helpery
# ---------------------------

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

def add_lines(doc: Document, count=2):
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

def doc_to_bytes(doc: Document) -> bytes:
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()

def set_fixed_col_width(table, col_widths_cm):
    table.autofit = False
    for row in table.rows:
        for i, w in enumerate(col_widths_cm):
            row.cells[i].width = Cm(w)

def set_cell_shading(cell, fill_hex: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tc_pr.append(shd)

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

def normalize_spaces(t: str) -> str:
    t = re.sub(r"\s+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


# ---------------------------
# Úvod + dramatizace
# ---------------------------

INTRO = {
    "karetni": "Nejdřív si zahrajeme krátkou scénku z karetní hry, abychom pochopili pravidla ještě před čtením. Potom se podíváme do slovníčku (je na konci listu), vrátíme se do textu a nakonec vyplníme otázky.",
    "sladke": "Nejdřív krátká scénka, která nás naladí na téma. Potom slovníček (na konci), čtení textu a otázky.",
    "venecky": "Nejdřív krátká scénka k tématu hodnocení. Potom slovníček (na konci), čtení textu a práce s otázkami a tabulkou.",
    "custom": "Nejdřív krátká scénka k tématu. Potom slovníček (na konci), čtení textu a otázky."
}

DRAMA = {
    "karetni": [
        "Žák A: „Zahraju komára!“",
        "Žák B: „Můžu tě přebít? Co když dám myš?“",
        "Žák C: „A co když dám dvě stejné karty? Je to silnější?“",
        "Žák D: „Mám chameleona – můžu ho hrát samotného?“",
        "Žák A: „Najdeme v pravidlech, jak se přebíjí a co umí žolík!“",
    ],
    "sladke": [
        "Žák A: „Kdyby existovala čokoláda bez kalorií, jedl/a bych ji pořád!“",
        "Žák B: „A šla by vůbec udělat, aby chutnala normálně?“",
        "Učitel/ka: „V textu zjistíme, co hledají vědci a proč.“",
    ],
    "venecky": [
        "Žák A: „Tahle cukrárna je nejlepší, to je jasné!“",
        "Žák B: „Podle mě rozhoduje chuť a suroviny.“",
        "Učitel/ka: „Dnes budeme hledat v textu fakta a názory a porovnáme je s tabulkou.“",
    ],
    "custom": [
        "Žák A: „Přečetl/a jsem to, ale nevím, co je nejdůležitější.“",
        "Žák B: „Tak budeme hledat klíčové informace a vysvětlíme je vlastními slovy.“",
        "Učitel/ka: „Půjdeme krok za krokem: slovníček – čtení – otázky.“",
    ],
}

def add_dramatization_intro(doc: Document, key: str):
    add_section_header(doc, "Úvod (co budeme dělat)")
    doc.add_paragraph(INTRO.get(key, INTRO["custom"]))

def add_dramatization(doc: Document, key: str):
    add_section_header(doc, "Dramatizace (krátká scénka)")
    for line in DRAMA[key]:
        doc.add_paragraph(line)


# ---------------------------
# Předpřipravené texty (PLNÉ)
# ---------------------------

FULL_KARETNI_TEXT = """NÁZEV ÚLOHY: KARETNÍ HRA\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

1. Herní materiál
60 karet živočichů: 4 komáři, 1 chameleon (žolík), 5 karet od každého z dalších 11 druhů živočichů.

2. Popis hry
Všechny karty se rozdají mezi jednotlivé hráče. Hráči se snaží vynášet karty v souladu s pravidly tak, aby se co nejdříve zbavili všech svých karet z ruky. Zahrát lze vždy pouze silnější kombinaci živočichů, než zahrál hráč před vámi.

3. Pořadí karet
Na každé kartě je zobrazen jeden živočich. V rámečku v horní části karty jsou namalováni živočichové, kteří danou kartu přebíjí.
Živočichové, kteří daný druh přebíjí, jsou označeni vybarveným políčkem.
Symbol > označuje, že každý živočich může být přebit větším počtem karet se živočichem stejného druhu.

Příklad: Kosatku přebijí pouze dvě kosatky. Krokodýla přebijí dva krokodýli nebo jeden slon.
Chameleon má ve hře obdobnou funkci jako žolík. Lze jej zahrát spolu s libovolnou jinou kartou a počítá se jako požadovaný druh živočicha. Nelze jej hrát samostatně.

4. Průběh hry
• Karty zamíchejte a rozdejte rovnoměrně mezi všechny hráče. Každý hráč si vezme své karty do ruky a neukazuje je ostatním.
• Při hře ve třech hráčích odeberte před hrou z balíčku: 1 lva, 1 slona, 1 myš a od každého z dalších druhů živočichů 2 karty. Chameleon (žolík) zůstává ve hře.
• Hráč po levé ruce rozdávajícího hráče začíná. Zahraje (vynese na stůl lícem nahoru) jednu kartu nebo více stejných karet.
• Hráči hrají po směru hodinových ručiček a postupně se snaží přebít dříve zahrané karty. Při tom mají dvě možnosti — buď zahrají stejný počet karet živočicha, který přebíjí před ním zahraný druh, nebo použijí stejný druh živočicha jako předchozí hráč, v tom případě zahrají o jednu kartu více.
Při přebíjení není povoleno hrát více karet, než je třeba. Vždy musí být zahráno buď přesně stejně karet „vyššího“ živočicha, nebo přesně o jednu kartu více stejného druhu.
• Hráč, který nechce nebo nemůže přebít, se může vzdát tahu slovem pass.
• Pokud se hráč dostane na řadu s tím, že nikdo z ostatních hráčů nepřebil jeho karty zahrané v minulém kole (všichni ostatní hráči „passovali“), vezme si tento hráč všechny karty, které v tu chvíli leží uprostřed stolu. Tyto karty si položí na hromádku před sebe a vynese další kartu nebo karty z ruky. S kartami, které hráči v průběhu hry sebrali, se již dále nehraje.
• Hráč, který jako první vynese svoji poslední kartu nebo karty z ruky, vítězí.

Zdroj: Bláznivá ZOO. Doris Matthäusová a Frank Nestel, Mindok, s. r. o., 1999, upraveno.
"""

SIMPLE_KARETNI_TEXT = """KARETNÍ HRA (zjednodušený text)

Ve hře jsou karty se zvířaty. Každý hráč dostane stejné množství karet.
Cílem je zbavit se všech karet jako první.

Hráči vykládají karty na stůl.
Další hráč musí dát silnější zvíře, aby přebil předchozí kartu.
Někdy může přebít i stejným zvířetem, ale musí dát o jednu kartu víc.

Chameleon je žolík: může se přidat k jiné kartě.
Sám se hrát nesmí.

Když někdo nemůže nebo nechce přebít, řekne „pass“.
Vyhrává ten, kdo se první zbaví všech karet.
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

# --- Sladké mámení (plný text + tabulky)
SLADKE_TABLES = {
    "Jak často jíte čokoládu?": [
        ("Alespoň jednou týdně", "22,7"),
        ("Více než dvakrát týdně", "6,1"),
        ("Méně než jednou týdně", "57,1"),
    ],
    "Jakou čokoládu máte nejraději?": [
        ("Studentská pečeť", "32,5"),
        ("Milka", "23,4"),
        ("Orion mléčná", "20,8"),
    ],
    "Jaké čokoládové tyčinky jste jedl v posledních 12 měsících?": [
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
    "Jak často kupujete bonboniéry?": [
        ("Dvakrát a více měsíčně", "1,7"),
        ("Jednou měsíčně", "14,9"),
        ("Jednou až dvakrát za 3 měsíce", "23,2"),
        ("Méně než jedenkrát za 3 měsíce", "54,5"),
        ("Neuvedeno", "5,7"),
    ],
    "Jaké bonboniéry jste koupili v posledních 12 měsících?": [
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

Euroamerickou civilizaci sužuje novodobá epidemie: obezita a s ní spojené choroby metabolismu, srdce a cév. Výrobci cukrovinek po celém vypaseném světě pocítili sílící poptávku po nízkokalorických čokoládách, light mlsání a dietních bonbonech. Až na české luhy a háje. „V našem rozsáhlém výzkumu se potvrdilo, že Češi netouží po nízkokalorickém mlsání, nechtějí mít dokonce ani na obalu větším písmem uvedený energetický obsah. Spotřebitelé nám v průzkumech trhu řekli, že to nechtějí slyšet: ,Vím, že hřeším, je to můj hřích a nechte mi ho,' “ říká Vašutová.

Ačkoli mnoho (převážně) hubnoucích žen tyto informace na obalech hledá, z celkové poptávky je to poměrně zanedbatelná část. „Před pár lety jsme celosvětově začali energetický obsah uvádět na přední straně výrobků. Zatímco jinde to odpovídalo přání spotřebitele, u nás to působí spíše jako rozmar výrobce,“ směje se Martin Walter, kolega Vašutové z Nestlé.

Nehledě na český nezájem, novodobí alchymisté v laboratořích stále hledají recept na zlato — náhražku rostlinného cukru, která by měla slušnou sladivost, neměla nepříjemnou chuť či pach a nezásobovala tělo zbytečnými kaloriemi. Podle expertky na cukrovinky z Vysoké školy chemicko-technologické Jany Čopíkové jsou hledači cukrovinového grálu na stopě. „V posledních letech se používají takzvané alditoly, což jsou sladidla s nižší energetickou hodnotou (např. sorbitol, xylitol, maltitol, pozn. red.). Ale pořád to není ono, protože mají zároveň nižší sladivost. Jedním z posledních objevů je však například látka zvaná polydextróza, která má skutečně nulovou energetickou hodnotu, ale nahradit sacharózu je prostě problém,“ dodává s úsměvem Jana Čopíková.

Potravinářský analytik Petr Havel v zájmu zdraví doporučuje pátrat po sladkostech, které obsahují spíše složité cukry — nejlépe polysacharidy, jako je škrob, celulóza, vláknina — než jednoduché, což jsou kupříkladu glukóza — hroznový cukr, fruktóza — ovocný cukr. Ty totiž představují jen „prázdnou“, rychlou energii. „Samozřejmě záleží na tom, co chceme. Pokud to má být ,energie sbalená na cesty', pro rychlý přísun kalorií, pak jednoduché cukry poslouží výborně, ale na večerní mlsání u televize se vyplatí dát si s výběrem sladkostí trochu práce,“ míní.

Podobně se podle něho dají laskominy rozdělit na vyloženě nezdravé a zdravější podle tuků, které obsahují. „Kakaové máslo se často nahrazuje jinými tuky, hlavně kvůli ceně. Některé z nich ale lidskému — a hlavně dětskému — zdraví neprospívají. Právě naopak,“ upozorňuje Havel.

Zdroj: Týden, 31. října 2011, 44/2011, s. 29, upraveno. (Průzkum agentury Median v roce 2010.)
"""

SIMPLE_SLADKE_TEXT = """SLADKÉ MÁMENÍ (zjednodušený text)

Text říká, že ve světě je problém obezita.
Proto lidé chtějí sladkosti s méně kaloriemi.

V Česku ale mnoho lidí nechce řešit, kolik má sladkost energie.
Vědci hledají sladidlo, které bude sladké a nebude mít kalorie.

Text také mluví o cukrech (jednoduché a složité) a o tucích.
"""

LMP_SLADKE_TEXT = """SLADKÉ MÁMENÍ (LMP/SPU)

• Ve světě je problém obezita.
• Lidé chtějí sladkosti s méně kaloriemi.
• V ČR lidé často nechtějí číst informace o kaloriích.
• Vědci hledají sladidlo bez kalorií.
"""

# --- Věnečky (plný text + tabulka + seznam podniků)
VENECKY_TABLE = [
    ("1", "15", "4", "5", "2", "1", "3"),
    ("2", "17", "4", "5", "5", "5", "5"),
    ("3", "11,50", "5", "5", "5", "5", "5"),
    ("4", "19", "2", "1", "2", "2", "2"),
    ("5", "20", "3", "3", "5", "5", "4"),
]

VENECKY_PODNIKY = [
    ("1", "Cukrárna Věnečky, Praha 5"),
    ("2", "Pekárna Krémová, Praha 1"),
    ("3", "Cukrárna Větrníček, Praha 3"),
    ("4", "Cukrárna Mámení, Praha 2"),
    ("5", "Cukrárna Dortíček, Praha 6"),
]

FULL_VENECKY_TEXT = """NÁZEV ÚLOHY: VĚNEČKY\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Věneček č. 2
„Vrátit výuční list!“ vykřikuje po dvou soustech z dalšího věnečku. „Tohle je špatné. Je to sražený krém. Vlastně se ani nedá říct krém, protože tohle je spíše vyšlehaný margarín. Nejenže to pudink ani vzdáleně nepřipomíná, ale navíc má chemickou pachuť, ochutnejte,“ vybízí mě. Nepříjemná stopa opravdu zůstává vzadu na patře. „Navíc tam není ani stopa rumu. A ten korpus? Buď ho tvořili podle špatného receptu, nebo recept velice ošidili…“

Věneček č. 3
„Tady je naopak výrazně cítit rum, to je dobře. Jenže když ochutnáte, dojde vám proč. Tou vůní chtěli jen přebít absenci jakýchkoli jiných chutí…“

Věneček č. 4
„Nejhezčí věneček… dodrželi recepturu… hmota se vyloženě povedla…“

Věneček č. 5
„…chemický pudink… nevařilo se to s mlékem… těsto je staré, ztvrdlé…“

Zdroj: Týden, 31. října 2011, 44/2011, s. 31, upraveno, kráceno.
"""

SIMPLE_VENECKY_TEXT = """VĚNEČKY (zjednodušený text)

Hodnotitelka ochutnává věnečky z různých podniků.
Některé věnečky jsou špatné, jeden je nejlepší.
V tabulce jsou ceny a známky (jako ve škole).
"""

LMP_VENECKY_TEXT = """VĚNEČKY (LMP/SPU)

• Porovnáváme věnečky z více podniků.
• Některé jsou špatné.
• Jeden je nejlepší.
• Tabulka ukazuje cenu a známku.
"""


# ---------------------------
# Karetní hra: tabulka „Kdo přebije koho?“ (zjednodušená varianta v DOCX)
# Pozn.: Tohle je pevná tabulka určená pro práci ve třídě.
# ---------------------------

KARETNI_ANIMALS = ["Kosatka", "Slon", "Krokodýl", "Lední medvěd", "Lev", "Tuleň", "Liška", "Okoun", "Ježek", "Sardinky", "Myš", "Komár"]
KARETNI_ROWS = ["Kosatku", "Slona", "Krokodýla", "Ledního medvěda", "Lva", "Tuleně", "Lišku", "Okouna", "Ježka", "Sardinky", "Myš", "Komára"]

# Logika jako v prototypu (pro školní použití).
KARETNI_BEATERS = {
    "Kosatku": [],
    "Slona": ["Myš"],
    "Krokodýla": ["Slon"],
    "Ledního medvěda": ["Kosatka", "Slon"],
    "Lva": ["Slon"],
    "Tuleně": ["Kosatka", "Lední medvěd"],
    "Lišku": ["Slon", "Krokodýl", "Lední medvěd", "Lev"],
    "Okouna": ["Kosatka", "Krokodýl", "Lední medvěd", "Tuleň"],
    "Ježka": ["Liška"],
    "Sardinky": ["Kosatka", "Krokodýl", "Tuleň", "Okoun"],
    "Myš": ["Krokodýl", "Lední medvěd", "Lev", "Tuleň", "Liška", "Ježek"],
    "Komára": ["Ježek", "Sardinky", "Myš"],
}

def add_karetni_matrix_table(doc: Document):
    add_section_header(doc, "Tabulka: Kdo přebije koho? (pro práci s pravidly)")
    table = doc.add_table(rows=1, cols=1 + len(KARETNI_ANIMALS))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_fixed_col_width(table, [3.2] + [1.2] * len(KARETNI_ANIMALS))

    hdr = table.rows[0].cells
    hdr[0].text = ""
    for i, animal in enumerate(KARETNI_ANIMALS, start=1):
        hdr[i].text = animal
        compact_cell(hdr[i])

    for row_name in KARETNI_ROWS:
        row_cells = table.add_row().cells
        row_cells[0].text = row_name
        compact_cell(row_cells[0])

        for i, col_animal in enumerate(KARETNI_ANIMALS, start=1):
            row_cells[i].text = ""
            compact_cell(row_cells[i])
            if col_animal in KARETNI_BEATERS.get(row_name, []):
                set_cell_shading(row_cells[i], "D9D9D9")

        for i, col_animal in enumerate(KARETNI_ANIMALS, start=1):
            base_row = row_name.lower()
            base_col = col_animal.lower()
            if base_col[:3] in base_row[:6]:
                row_cells[i].text = ">"
                compact_cell(row_cells[i])

    for r in table.rows:
        for c in r.cells:
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_border(
                c,
                top={"sz": 8, "val": "single", "color": "000000"},
                bottom={"sz": 8, "val": "single", "color": "000000"},
                left={"sz": 8, "val": "single", "color": "000000"},
                right={"sz": 8, "val": "single", "color": "000000"},
            )

    doc.add_paragraph("Šedé políčko = živočich ve sloupci přebíjí živočicha v řádku. Symbol >: lze přebít více kartami stejného druhu.")


# ---------------------------
# Karetní hra: kartičky + „pyramida“ (sloupec okýnek)
# ---------------------------

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
PYR_W_CM = 6.5
PYR_H_CM = 2.2

# Sloupec (nahoře nejsilnější) – pro lepení
PYRAMID_SLOTS = 13

def add_pyramid_column(doc: Document):
    add_section_header(doc, "Zvířecí „pyramida“ síly (lepení)")
    doc.add_paragraph("Vystřihni kartičky a nalep je do okýnek. Nahoře bude nejsilnější zvíře, dole nejslabší.")

    t = doc.add_table(rows=PYRAMID_SLOTS + 1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    set_fixed_col_width(t, [PYR_W_CM])

    header = t.cell(0, 0)
    header.text = "NAHOŘE = NEJSILNĚJŠÍ"
    compact_cell(header)
    header.paragraphs[0].runs[0].bold = True
    header.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    header.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    header.height = Cm(PYR_H_CM)

    for i in range(1, PYRAMID_SLOTS + 1):
        cell = t.cell(i, 0)
        cell.text = ""
        compact_cell(cell)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        cell.height = Cm(PYR_H_CM)
        set_cell_border(
            cell,
            top={"sz": 14, "val": "single", "color": "000000"},
            bottom={"sz": 14, "val": "single", "color": "000000"},
            left={"sz": 14, "val": "single", "color": "000000"},
            right={"sz": 14, "val": "single", "color": "000000"},
        )

    doc.add_paragraph("DOLE = NEJSLABŠÍ")

def add_animal_cards_3cols(doc: Document):
    add_section_header(doc, "Kartičky zvířat (na stříhání)")
    doc.add_paragraph("Vystřihni kartičky. (3 sloupce)")

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


# ---------------------------
# Tabulky pro Sladké mámení a Věnečky (vždy i ve zjednoduš./LMP)
# ---------------------------

def add_two_col_table(doc: Document, title: str, rows):
    add_section_header(doc, title)
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.autofit = False
    set_fixed_col_width(t, [12.0, 3.0])

    hdr = t.rows[0].cells
    hdr[0].text = "Položka"
    hdr[1].text = "Hodnota (%)"
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

def add_venecky_table_and_podniky(doc: Document):
    add_section_header(doc, "Kde jsme věnečky pořídili")
    for num, txt in VENECKY_PODNIKY:
        doc.add_paragraph(f"{num}. {txt}")

    add_section_header(doc, "Hodnocení (tabulka)")
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


# ---------------------------
# Slovníček (na konci)
# ---------------------------

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
    "kaloriemi": "energií v jídle",
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


# ---------------------------
# Otázky
# ---------------------------

def add_questions_karetni(doc: Document):
    add_section_header(doc, "Otázky A/B/C")
    doc.add_paragraph("A) Porozumění (najdi v textu)")
    doc.add_paragraph("1) Co je cílem hry? Napiš jednou větou.")
    add_lines(doc, 1)

    doc.add_paragraph("2) Co znamená ve hře slovo „pass“?")
    add_lines(doc, 1)

    doc.add_paragraph("B) Přemýšlení (vysvětli)")
    doc.add_paragraph("3) Proč se chameleon (žolík) nesmí hrát samostatně?")
    add_lines(doc, 2)

    doc.add_paragraph("C) Můj názor")
    doc.add_paragraph("4) Co bys poradil/a spolužákovi, aby ve hře vyhrál? (1–2 věty)")
    add_lines(doc, 2)

def add_questions_sladke(doc: Document):
    add_section_header(doc, "Otázky A/B/C")
    doc.add_paragraph("A) Porozumění (najdi v textu)")
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
    doc.add_paragraph("A) Porozumění (najdi v textu)")
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

def add_questions_generic(doc: Document, grade: int):
    add_section_header(doc, "Otázky A/B/C")
    doc.add_paragraph("A) Porozumění")
    doc.add_paragraph("1) O čem text je? Napiš jednou větou.")
    add_lines(doc, 1)
    doc.add_paragraph("B) Práce s textem")
    doc.add_paragraph("2) Najdi v textu dvě důležité informace.")
    add_lines(doc, 2)
    doc.add_paragraph("C) Můj názor")
    doc.add_paragraph("3) Co si o tom myslíš? Proč?")
    add_lines(doc, 2)


# ---------------------------
# Jednoduché zjednodušení pro vlastní text
# ---------------------------

def simple_simplify(text: str, grade: int) -> str:
    t = normalize_spaces(text)
    paras = [p.strip() for p in t.split("\n\n") if p.strip()]
    if grade <= 3:
        paras = paras[:4]
    elif grade == 4:
        paras = paras[:6]
    else:
        paras = paras[:8]
    return "\n\n".join(paras)

def lmp_simplify(text: str) -> str:
    t = normalize_spaces(text)
    sents = re.split(r"(?<=[\.\!\?])\s+", t)
    sents = [s.strip() for s in sents if s.strip()][:6]
    out = ["LMP/SPU verze (zjednodušeně):", ""]
    for s in sents:
        if len(s) > 140:
            s = s[:140].rstrip() + "…"
        out.append(f"• {s}")
    return "\n".join(out)


# ---------------------------
# Stavba pracovních listů (PLNÝ / ZJEDNODUŠENÝ / LMP)
# ✅ DŮLEŽITÉ: tabulky vkládáme do všech verzí u předpřipravených textů
# ---------------------------

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
        doc.add_paragraph(FULL_KARETNI_TEXT)
    elif version == "ZJEDNODUŠENÝ":
        src = SIMPLE_KARETNI_TEXT
        doc.add_paragraph(SIMPLE_KARETNI_TEXT)
    else:
        src = LMP_KARETNI_TEXT
        doc.add_paragraph(LMP_KARETNI_TEXT)

    # ✅ tabulka vždy (klíčová pro rozhodování v otázkách)
    add_karetni_matrix_table(doc)

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
        doc.add_paragraph(FULL_SLADKE_TEXT)
    elif version == "ZJEDNODUŠENÝ":
        src = SIMPLE_SLADKE_TEXT
        doc.add_paragraph(SIMPLE_SLADKE_TEXT)
    else:
        src = LMP_SLADKE_TEXT
        doc.add_paragraph(LMP_SLADKE_TEXT)

    # ✅ tabulky vždy (klíčové pro otázky)
    add_section_header(doc, "Tabulky (pro práci s daty) — přesný přepis")
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
        doc.add_paragraph(FULL_VENECKY_TEXT)
    elif version == "ZJEDNODUŠENÝ":
        src = SIMPLE_VENECKY_TEXT
        doc.add_paragraph(SIMPLE_VENECKY_TEXT)
    else:
        src = LMP_VENECKY_TEXT
        doc.add_paragraph(LMP_VENECKY_TEXT)

    # ✅ tabulka + seznam podniků vždy (klíčové pro otázky)
    add_venecky_table_and_podniky(doc)

    add_hr(doc)
    add_questions_venecky(doc)
    add_glossary_at_end(doc, src, max_words=12)
    return doc

def build_doc_custom(version: str, title: str, grade: int, full_text: str) -> Document:
    doc = Document()
    set_doc_style(doc)
    add_title(doc, "EdRead AI – Pracovní list", f"{title} (třída: {grade}) — verze: {version}")
    add_hr(doc)

    add_dramatization_intro(doc, "custom")
    add_hr(doc)
    add_dramatization(doc, "custom")
    add_hr(doc)

    add_section_header(doc, "Text k přečtení")
    full_text = normalize_spaces(full_text)

    if version == "PLNÝ":
        src = full_text
        doc.add_paragraph(full_text)
    elif version == "ZJEDNODUŠENÝ":
        src = simple_simplify(full_text, grade)
        doc.add_paragraph(src)
    else:
        src = lmp_simplify(full_text)
        doc.add_paragraph(src)

    add_hr(doc)
    add_questions_generic(doc, grade)
    add_glossary_at_end(doc, src, max_words=12)
    return doc


# ---------------------------
# Metodika (učitel) — manuál + rozdíly verzí
# ---------------------------

def build_methodology(text_name: str, grade: str, has_pyramid: bool = False) -> Document:
    doc = Document()
    set_doc_style(doc)

    add_title(doc, "EdRead AI – Metodický list pro učitele", f"{text_name} ({grade})")
    add_hr(doc)

    add_section_header(doc, "Doporučený postup práce (45 minut)")
    doc.add_paragraph("1) Úvodní naladění + dramatizace (3–7 min).")
    doc.add_paragraph("2) Slovníček (je na konci listu): učitel žáky ke slovníčku nejprve navede a významy projde.")
    doc.add_paragraph("3) Čtení textu: žáci se vrátí do textu, čtou, podtrhují klíčové informace.")
    doc.add_paragraph("4) Otázky A/B/C: nejprve A (vyhledání), potom B (interpretace/práce s tabulkou), nakonec C (vlastní názor).")
    doc.add_paragraph("5) Shrnutí: co bylo v textu fakt a co názor?")

    add_hr(doc)
    add_section_header(doc, "Rozdíly mezi verzemi pracovních listů")
    doc.add_paragraph("PLNÝ list:")
    doc.add_paragraph("• původní (plný) text + tabulky + úkoly; nejvyšší náročnost čtení.")
    doc.add_paragraph("ZJEDNODUŠENÝ list:")
    doc.add_paragraph("• kratší a jazykově jednodušší text; tabulky zůstávají, pokud jsou potřeba pro otázky.")
    doc.add_paragraph("LMP/SPU list:")
    doc.add_paragraph("• velmi jednoduché věty a jasná struktura; tabulky zůstávají (kvůli odpovědím); slovníček má i prostor na poznámky.")

    if has_pyramid:
        add_hr(doc)
        add_section_header(doc, "Specifická aktivita: Karetní hra (pyramida + kartičky)")
        doc.add_paragraph("• Žáci vystřihnou kartičky (3 sloupce) a lepí je do sloupce okýnek.")
        doc.add_paragraph("• Okýnka jsou větší než kartičky, aby se vešly bez přehýbání.")
        doc.add_paragraph("• Tabulka „Kdo přebije koho?“ je přiložena ve všech verzích (plný / zjednodušený / LMP), protože je klíčová.")

    return doc


# ---------------------------
# Session storage: ukládáme výstupy PODLE KONKRÉTNÍ SÁDY (např. preset_karetni)
# Tím tlačítka zůstanou stále, i po kliknutí na download.
# ---------------------------

def store_outputs(keybase: str, full_doc: Document, simple_doc: Document, lmp_doc: Document, metod_doc: Document,
                  full_name: str, simp_name: str, lmp_name: str, met_name: str):
    st.session_state[f"{keybase}_ready"] = True
    st.session_state[f"{keybase}_full_bytes"] = doc_to_bytes(full_doc)
    st.session_state[f"{keybase}_simp_bytes"] = doc_to_bytes(simple_doc)
    st.session_state[f"{keybase}_lmp_bytes"] = doc_to_bytes(lmp_doc)
    st.session_state[f"{keybase}_met_bytes"] = doc_to_bytes(metod_doc)

    st.session_state[f"{keybase}_full_name"] = full_name
    st.session_state[f"{keybase}_simp_name"] = simp_name
    st.session_state[f"{keybase}_lmp_name"] = lmp_name
    st.session_state[f"{keybase}_met_name"] = met_name

def render_downloads(keybase: str, label_prefix: str = ""):
    if st.session_state.get(f"{keybase}_ready", False):
        st.success("Dokumenty jsou připravené ke stažení (tlačítka zůstávají viditelná).")

        st.download_button(
            f"⬇️ {label_prefix}PLNÝ pracovní list (DOCX)",
            data=st.session_state[f"{keybase}_full_bytes"],
            file_name=st.session_state[f"{keybase}_full_name"],
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"{keybase}_dl_full"
        )
        st.download_button(
            f"⬇️ {label_prefix}ZJEDNODUŠENÝ pracovní list (DOCX)",
            data=st.session_state[f"{keybase}_simp_bytes"],
            file_name=st.session_state[f"{keybase}_simp_name"],
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"{keybase}_dl_simp"
        )
        st.download_button(
            f"⬇️ {label_prefix}LMP/SPU pracovní list (DOCX)",
            data=st.session_state[f"{keybase}_lmp_bytes"],
            file_name=st.session_state[f"{keybase}_lmp_name"],
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"{keybase}_dl_lmp"
        )
        st.download_button(
            f"⬇️ {label_prefix}METODICKÝ LIST (DOCX)",
            data=st.session_state[f"{keybase}_met_bytes"],
            file_name=st.session_state[f"{keybase}_met_name"],
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"{keybase}_dl_met"
        )


# ---------------------------
# Streamlit UI
# ---------------------------

st.set_page_config(page_title="EdRead AI (prototyp)", layout="centered")
st.title("EdRead AI – generátor materiálů (prototyp)")

mode = st.radio("Režim:", ["Předpřipravené texty (3)", "Vlastní text"], horizontal=True)

if mode == "Předpřipravené texty (3)":
    choice = st.selectbox("Vyber text:", ["Karetní hra (3. třída)", "Věnečky (4. třída)", "Sladké mámení (5. třída)"])

    # stabilní keybase podle volby (tím tlačítka drží i po stažení)
    if choice.startswith("Karetní"):
        keybase = "preset_karetni"
        label = "Karetní hra – "
    elif choice.startswith("Věnečky"):
        keybase = "preset_venecky"
        label = "Věnečky – "
    else:
        keybase = "preset_sladke"
        label = "Sladké mámení – "

    with st.form("gen_preset_form", clear_on_submit=False):
        submitted = st.form_submit_button("Vygenerovat dokumenty")

    if submitted:
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")

        if keybase == "preset_karetni":
            full_doc = build_doc_karetni("PLNÝ")
            simp_doc = build_doc_karetni("ZJEDNODUŠENÝ")
            lmp_doc = build_doc_karetni("LMP/SPU")
            metod = build_methodology("Karetní hra", "3. třída", has_pyramid=True)

            store_outputs(
                keybase,
                full_doc, simp_doc, lmp_doc, metod,
                f"pracovni_list_Karetni_hra_plny_{stamp}.docx",
                f"pracovni_list_Karetni_hra_zjednoduseny_{stamp}.docx",
                f"pracovni_list_Karetni_hra_LMP_{stamp}.docx",
                f"metodicky_list_Karetni_hra_{stamp}.docx",
            )

        elif keybase == "preset_venecky":
            full_doc = build_doc_venecky("PLNÝ")
            simp_doc = build_doc_venecky("ZJEDNODUŠENÝ")
            lmp_doc = build_doc_venecky("LMP/SPU")
            metod = build_methodology("Věnečky", "4. třída", has_pyramid=False)

            store_outputs(
                keybase,
                full_doc, simp_doc, lmp_doc, metod,
                f"pracovni_list_Venecky_plny_{stamp}.docx",
                f"pracovni_list_Venecky_zjednoduseny_{stamp}.docx",
                f"pracovni_list_Venecky_LMP_{stamp}.docx",
                f"metodicky_list_Venecky_{stamp}.docx",
            )

        else:
            full_doc = build_doc_sladke("PLNÝ")
            simp_doc = build_doc_sladke("ZJEDNODUŠENÝ")
            lmp_doc = build_doc_sladke("LMP/SPU")
            metod = build_methodology("Sladké mámení", "5. třída", has_pyramid=False)

            store_outputs(
                keybase,
                full_doc, simp_doc, lmp_doc, metod,
                f"pracovni_list_Sladke_mameni_plny_{stamp}.docx",
                f"pracovni_list_Sladke_mameni_zjednoduseny_{stamp}.docx",
                f"pracovni_list_Sladke_mameni_LMP_{stamp}.docx",
                f"metodicky_list_Sladke_mameni_{stamp}.docx",
            )

    # ✅ tlačítka se vykreslí vždy, pokud už někdy byly vygenerované
    render_downloads(keybase, label_prefix=label)

    st.info("Tip: můžeš přepnout na jiný text – pokud už byl dříve vygenerovaný, jeho tlačítka zůstanou připravená také.")

else:
    st.subheader("Vlastní text")
    custom_title = st.text_input("Název:", value=st.session_state.get("custom_title", "Vlastní text"))
    grade = st.selectbox("Pro jakou třídu?", [1, 2, 3, 4, 5], index=2)
    custom_text = st.text_area("Vlož text:", value=st.session_state.get("custom_text", ""), height=260)

    st.session_state["custom_title"] = custom_title
    st.session_state["custom_text"] = custom_text

    # klíč pro vlastní text — stabilní (poslední generace)
    keybase = "custom_last"

    with st.form("gen_custom_form", clear_on_submit=False):
        submitted = st.form_submit_button("Vygenerovat dokumenty")

    if submitted:
        if not custom_text.strip():
            st.error("Vlož prosím text.")
        else:
            stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            safe = re.sub(r"[^A-Za-z0-9ÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž_\- ]+", "", custom_title).strip().replace(" ", "_") or "Vlastni_text"

            full_doc = build_doc_custom("PLNÝ", custom_title, grade, custom_text)
            simp_doc = build_doc_custom("ZJEDNODUŠENÝ", custom_title, grade, custom_text)
            lmp_doc = build_doc_custom("LMP/SPU", custom_title, grade, custom_text)
            metod = build_methodology(custom_title, f"{grade}. třída", has_pyramid=False)

            store_outputs(
                keybase,
                full_doc, simp_doc, lmp_doc, metod,
                f"pracovni_list_{safe}_plny_{stamp}.docx",
                f"pracovni_list_{safe}_zjednoduseny_{stamp}.docx",
                f"pracovni_list_{safe}_LMP_{stamp}.docx",
                f"metodicky_list_{safe}_{stamp}.docx",
            )

    render_downloads(keybase, label_prefix="Vlastní text – ")

st.caption("Pozn.: U předpřipravených textů jsou tabulky vkládány do všech verzí (plný / zjednodušený / LMP), protože jsou potřebné pro odpovědi.")
