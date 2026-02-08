# app.py — EdRead AI (opravená verze dle posledních připomínek)
# ✅ ODSTRANĚNA věta z dramatizace: „Nejdřív krátká scénka, pak slovníček...“
# ✅ PYRAMIDA (sloupec okýnek) = VĚTŠÍ okýnka než kartičky, aby se kartičky vždy vešly
# ✅ Zůstává: 4 DOCX výstupy (PLNÝ / ZJEDNODUŠENÝ / LMP-SPU / METODIKA)
# ✅ Zůstává: režim „Vlastní text“ + volba ročníku (1–5)

import re
from datetime import datetime
import io

import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


# ---------------------------
# Pomocné funkce (DOCX)
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

def set_fixed_col_width(table, col_widths_cm):
    table.autofit = False
    for row in table.rows:
        for i, w in enumerate(col_widths_cm):
            row.cells[i].width = Cm(w)

def doc_to_bytes(doc):
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def compact_paragraph(p):
    """Zmenší mezery v odstavci (hlavně pro buňky tabulek)."""
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0

def compact_cell(cell):
    for p in cell.paragraphs:
        compact_paragraph(p)


# ---------------------------
# Předpřipravené texty (plné + tabulky)
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

Podobně se podle něho dají laskominy rozdělit na vyloženě nezdravé a zdravější podle tuků, které obsahují. „Kakaové máslo se často nahrazuje jinými tuky, hlavně kvůli ceně. Některé z nich ale lidskému — a hlavně dětskému — zdraví neprospívají. Právě naopak,“ upozorňuje Havel. Konkrétně to jsou takzvané transmastné a vyšší mastné kyseliny, jako je kyselina palmitová nebo myristová. „Palmový a kokosový tuk zvyšují riziko kardiovaskulární choroby, stejně jako méně kvalitní ztužené tuky,“ doplňuje Havel.

Jeden cukrovinářský trend je ale patrný i v našich zeměpisných šířkách. Odklon …

Zdroj: Týden, 31. října 2011, 44/2011, s. 29, upraveno. (Průzkum agentury Median v roce 2010.)
"""

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
„Vrátit výuční list!“ vykřikuje po dvou soustech z dalšího věnečku. „Tohle je špatné. Je to sražený krém. Vlastně se ani nedá říct krém, protože tohle je spíše vyšlehaný margarín. Nejenže to pudink ani vzdáleně nepřipomíná, ale navíc má chemickou pachuť, ochutnejte,“ vybízí mě. Nepříjemná stopa opravdu zůstává vzadu na patře. „Navíc tam není ani stopa rumu. A ten korpus? Buď ho tvořili podle špatného receptu, nebo recept velice ošidili. Správné odpalované těsto má mít viditelné drážky, jak se zdobícím pytlíkem stříkalo na plech. Tohle je slité, bez vzorku a tvrdé.“

Věneček č. 3
„Tady je naopak výrazně cítit rum, to je dobře. Jenže když ochutnáte, dojde vám proč. Tou vůní chtěli jen přebít absenci jakýchkoli jiných chutí,“ míní hodnotitelka. „Vůbec netouším, z čeho tohle vyrobili, možná vyšlehaný margarín nebo rostlinná šlehačka. Navíc se to srazilo! Jak si mohou dovolit tohle prodávat? Tohle je také na vrácení výučního listu. Zkuste zakrojit lžičku do korpusu — přepečená hmota, mokvavá a dole ztvrdlá. Vůbec se nevytvarovala, podobně jako u druhého věnečku.“

Věneček č. 4
„Nejhezčí věneček. Na první pohled. Krásně žlutá náplň, takhle vypadá pudink. Konečně! Jen je škoda, že tam vůbec není cítit rum. Oceňuji, že dodrželi recepturu. Ten pudink mohl být trochu více nadlehčený máslem, zdá se, že nedodrželi poměr 250 gramů másla na litr pudinku, ale to není taková tragédie. Je to dobré. A hmota se vyloženě povedla. Je světlá, zlatavá, vláčná, měkká, ale zároveň lehce křupavá, není přepečená, ani nedopečená, ani zestárlá. Tohle dělal cukrář, který své řemeslo umí.“

Věneček č. 5
„Na první pohled vypadá hezky, drážky korpusu vypadají, jak mají, ale tím to končí. Tohle je chemický pudink, s vodou smíchaný prášek, nevařilo se to s mlékem. Nejenže to nemá chuť, ale je to tou chemií cítit. Těsto je staré, ztvrdlé… Tento cukrář by u mě propadl, katastrofa.”

Než paní Fornůskové prozradím jména cukráren, přináším nesoutěžní doplňkové vzorky zákusků, kterými chci dát podnikům druhou šanci — napravit věnečkový dojem a zlomit verdikt. Podaří se to jedinému zákusku: štrúdlu s tvarohem a višněmi. „Hezky vypadá a je dobrý. Je nejspíše upečený z průmyslově vyráběného listového těsta, ale to je normální, dělá to tak většina cukráren. Vlastně spíše připomíná těsto plundrové, protože nelistuje, jak by mělo… Tvaroh je akorát sladký, utřený do jemna, višně chutnají jako višně. Tohle je můj vítěz druhého kola,“ pronese jednoznačně. „A o těch dalších raději pomlčme.“

Když odtajním cukrárny, které se schovávaly za čísly výrobků, vyjde najevo, že vítězný věneček i štrúdl jsou totiž z „jednoho těsta“, a to z cukrárny Mámení ve stejnojmenné pasáži. „Vida, na tuto cukrárnu bych asi vsadila předem, kdybych věděla, že jejich výrobky zde budete mít,“ říká uznale cukrářka. „Ale jinak mě věnečky zklamaly…“

Zdroj: Týden, 31. října 2011, 44/2011, s. 31, upraveno, kráceno. Hodnocení šéfkuchařky Fornůskové
"""

SIMPLE_KARETNI_TEXT = """KARETNÍ HRA (zjednodušený text)

Ve hře je 60 karet se zvířaty. Každý hráč dostane stejné množství karet.
Cílem je zbavit se všech karet jako první.

Hráči postupně vykládají karty na stůl.
Další hráč musí dát silnější zvíře, aby přebil předchozí kartu.
Někdy může přebít i stejným zvířetem, ale musí dát o jednu kartu víc.

Chameleon je žolík: může se přidat k jiné kartě a pomůže vytvořit potřebné zvíře.
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

SIMPLE_SLADKE_TEXT = """SLADKÉ MÁMENÍ (zjednodušený text)

Text říká, že ve světě je problém obezita.
Proto lidé chtějí sladkosti s méně kaloriemi.

V Česku ale mnoho lidí nechce řešit, kolik má sladkost energie.
Vědci hledají sladidlo, které bude sladké a nebude mít kalorie.

V textu se mluví o jednoduchých cukrech (rychlá energie)
a složitých cukrech (lepší volba, když nechci jen rychlou energii).
"""

LMP_SLADKE_TEXT = """SLADKÉ MÁMENÍ (LMP/SPU)

V textu se píše:
• Mnoho lidí má obezitu.
• Lidé chtějí sladkosti s méně kaloriemi.
• Vědci hledají sladidlo bez kalorií.
• Jsou jednoduché cukry a složité cukry.
"""

SIMPLE_VENECKY_TEXT = """VĚNEČKY (zjednodušený text)

Hodnotitelka ochutnává věnečky z různých cukráren.
Některé věnečky jsou špatné: divná chuť, tvrdé těsto nebo špatný krém.
Jeden věneček je nejlepší: má dobrý krém i dobré těsto.

V tabulce je cena a známky (jako ve škole).
"""

LMP_VENECKY_TEXT = """VĚNEČKY (LMP/SPU)

V textu se porovnávají věnečky z cukráren.
Některé jsou špatné.
Jeden je nejlepší.
Tabulka ukazuje cenu a známku.
"""


# ---------------------------
# Dramatizace – OPRAVA: žádná věta o pořadí kroků
# ---------------------------

DRAMA = {
    "karetni": [
        "Žák A: „Mám komára. Tak ho zahraju!“",
        "Žák B: „Já dám myš. Přebil/a jsem tě?“",
        "Žák C: „A co když zahraju dvě stejné karty? Je to silnější?“",
        "Žák D: „Mám chameleona – můžu ho hrát samotného?“",
        "Žák A: „Kdo najde v pravidlech, jak přesně se přebíjí a co umí žolík?“",
    ],
    "sladke": [
        "Žák A: „Kdyby existovala čokoláda bez kalorií, jedl/a bych ji pořád!“",
        "Žák B: „A šla by vůbec udělat? Aby byla sladká a chutnala normálně?“",
        "Učitel/ka: „Dnes budeme číst text, kde vědci hledají takové sladidlo.“",
    ],
    "venecky": [
        "Žák A: „Tahle cukrárna je nejlepší, to je jasné!“",
        "Žák B: „Ne! Podle mě rozhoduje chuť a suroviny.“",
        "Učitel/ka: „Dnes budeme číst hodnocení a hledat, co je fakt a co je názor.“",
    ],
    "custom": [
        "Žák A: „Já jsem si to přečetl/a, ale nejsem si jistý/á, co je hlavní.“",
        "Žák B: „Tak budeme hledat důležité informace a pak je vysvětlíme vlastními slovy.“",
        "Učitel/ka: „Dnes budeme pracovat s textem krok za krokem.“",
    ],
}


# ---------------------------
# Karetní hra – tabulka „Kdo přebije koho?“
# ---------------------------

KARETNI_ANIMALS = ["Kosatka", "Slon", "Krokodýl", "Lední medvěd", "Lev", "Tuleň", "Liška", "Okoun", "Ježek", "Sardinky", "Myš", "Komár"]
KARETNI_ROWS = ["Kosatku", "Slona", "Krokodýla", "Ledního medvěda", "Lva", "Tuleně", "Lišku", "Okouna", "Ježka", "Sardinky", "Myš", "Komára"]

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
    add_section_header(doc, "Kdo přebije koho? (tabulka z pravidel hry)")
    table = doc.add_table(rows=1, cols=1 + len(KARETNI_ANIMALS))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    col_widths = [3.2] + [1.2] * len(KARETNI_ANIMALS)
    set_fixed_col_width(table, col_widths)

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
            base_row = row_name.lower().replace("ého", "").replace("a", "")
            base_col = col_animal.lower()
            if base_col[:3] in base_row[:5]:
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

    doc.add_paragraph("Šedé políčko = daný živočich přebíjí živočicha v řádku. Symbol > znamená: lze přebít více kartami stejného druhu.")


# ---------------------------
# Karetní hra – kartičky (3 sloupce) + pyramida (větší okýnka)
# OPRAVA: pyramidová okýnka jsou VĚTŠÍ než kartičky, aby se kartičky vždy vešly.
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

# Kartička (na stříhání)
CARD_W_CM = 5.6          # 3 sloupce se vejdou na A4
CARD_H_CM = 1.85         # kartička

# Okýnko pyramidy (na lepení) — VĚTŠÍ než kartička
PYR_W_CM = 6.0           # o něco širší
PYR_H_CM = 2.25          # výrazně vyšší (hlavní důvod, proč se kartičky nevešly)

def add_pyramid_column(doc: Document):
    add_section_header(doc, "Zvířecí „pyramida“ síly (lepení)")
    doc.add_paragraph("Vystřihni kartičky a nalep je do okýnek. Nahoře bude nejsilnější zvíře, dole nejslabší.")

    t = doc.add_table(rows=len(PYRAMID_ORDER_TOP_TO_BOTTOM) + 1, cols=1)
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

    for i in range(1, len(PYRAMID_ORDER_TOP_TO_BOTTOM) + 1):
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
# Tabulky pro Sladké mámení a Věnečky
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
    cols = ["Cukrárna", "Cena v Kč", "Vzhled", "Korpus", "Náplň", "Suroviny", "Celková známka (jako ve škole)"]
    t = doc.add_table(rows=1, cols=len(cols))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    set_fixed_col_width(t, [2.0, 2.0, 1.4, 1.4, 1.4, 1.6, 2.6])

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
# Slovníček – výběr + vysvětlení
# ---------------------------

STOPWORDS = set("""
a i o u v ve na do z ze že který která které kteří se si je jsou být bylo byla byly jsem jsme jste
když protože proto ale nebo ani jen ještě už pak také tak tedy tento tato toto
""".split())

EXPLAIN = {
    "maximálně": "nejvíc (největší možné množství)",
    "vykřikuje": "říká nahlas",
    "sousto": "kousek jídla v puse",
    "sousty": "kousky jídla",
    "vyšlehaný": "hodně našlehaný, nadýchaný",
    "margarín": "tuk podobný máslu",
    "vzdáleně": "ani trochu",
    "nepřipomíná": "není to podobné",
    "chemickou": "umělou, ne přírodní",
    "pachuť": "nepříjemná chuť, která zůstane",
    "korpus": "těsto (spodní část zákusku)",
    "receptura": "správný postup a poměr surovin",
    "dodrželi": "udělali přesně podle pravidel",
    "nadlehčený": "udělaný lehčí a nadýchanější",
    "poměr": "kolik čeho má být",
    "vlačný": "měkký a šťavnatý",
    "křupavý": "když to při kousnutí křupne",
    "přepečená": "upečená moc dlouho",
    "ztvrdlá": "tvrdá",
    "zestárlá": "už není čerstvá",
    "absence": "chybění (něčeho tam není)",
    "doplňkové": "navíc, přidané",
    "podnikům": "provozovnám (tady: cukrárnám)",
    "napravit": "zlepšit, opravit",
    "verdikt": "konečné rozhodnutí",
    "průmyslově": "vyrobené ve velké výrobě (továrně)",
    "nelistuje": "netvoří vrstvy jako listové těsto",
    "upraveno": "trochu změněno",
    "rovnoměrně": "stejně pro všechny",
    "kombinaci": "spojení více karet dohromady",
    "přebít": "dát silnější kartu (porazit předchozí)",
    "vynese": "položí kartu na stůl",
    "žolík": "karta, která může nahradit jinou",
    "samostatně": "sám, bez jiné karty",
    "obezita": "velká nadváha",
    "poptávku": "zájem lidí o něco (co chtějí kupovat)",
    "nízkokalorických": "s málo kaloriemi (méně energie)",
    "kaloriemi": "energie v jídle",
    "sladivost": "jak moc je něco sladké",
    "laskominy": "dobroty",
    "kardiovaskulární": "týkající se srdce a cév",
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
        if wl.isdigit():
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
        line = doc.add_paragraph()
        r1 = line.add_run(f"• {w} = ")
        r1.bold = True

        if w in EXPLAIN:
            line.add_run(EXPLAIN[w])
        else:
            line.add_run("______________________________")

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

    doc.add_paragraph("2) Najdi v textu dvě vlastnosti ideálního sladidla.")
    add_lines(doc, 2)

    doc.add_paragraph("B) Práce s daty / interpretace")
    doc.add_paragraph("3) Podle tabulek: Kterou bonboniéru koupilo více lidí – Tofifee nebo Merci? Napiš i procenta.")
    add_lines(doc, 2)

    doc.add_paragraph("C) Kritické čtení / můj názor")
    doc.add_paragraph("4) Myslíš, že lidé v ČR opravdu nechtějí číst informace o kaloriích? Proč ano/ne?")
    add_lines(doc, 2)

def add_questions_venecky(doc: Document):
    add_section_header(doc, "Otázky A/B/C")
    doc.add_paragraph("A) Porozumění (najdi v textu)")
    doc.add_paragraph("1) Který věneček neobsahuje pudink uvařený z mléka? Napiš číslo věnečku a proč.")
    add_lines(doc, 2)

    doc.add_paragraph("2) Ve kterém věnečku je vůně rumu použita k zakrytí chybějících chutí? (číslo věnečku)")
    add_lines(doc, 1)

    doc.add_paragraph("B) Práce s tabulkou / interpretace")
    doc.add_paragraph("3) Který podnik dopadl nejlépe? (podle tabulky) Napiš název.")
    add_lines(doc, 1)

    doc.add_paragraph("4) Který věneček byl nejdražší? Uveď cenu a kde byl koupen (podnik).")
    add_lines(doc, 2)

    doc.add_paragraph("C) Kritické čtení / můj názor")
    doc.add_paragraph("5) Souhlasíš s hodnocením? Vyber jeden věneček a vysvětli proč.")
    add_lines(doc, 2)

def add_questions_generic(doc: Document, grade: int):
    add_section_header(doc, "Otázky A/B/C")
    doc.add_paragraph("A) Porozumění (najdi v textu)")
    doc.add_paragraph("1) O čem text je? Napiš jednou větou.")
    add_lines(doc, 1)

    if grade <= 3:
        doc.add_paragraph("2) Najdi v textu dvě důležité informace a napiš je.")
        add_lines(doc, 2)
    else:
        doc.add_paragraph("2) Najdi v textu dvě důležité informace a vysvětli, proč jsou důležité.")
        add_lines(doc, 2)

    doc.add_paragraph("B) Práce s textem (vysvětli)")
    doc.add_paragraph("3) Vyber jednu větu z textu a vysvětli ji vlastními slovy.")
    add_lines(doc, 2)

    doc.add_paragraph("C) Můj názor")
    doc.add_paragraph("4) Souhlasíš s tím, co text říká? Proč ano/ne?")
    add_lines(doc, 2)


# ---------------------------
# Vlastní text – úpravy podle ročníku (heuristika)
# ---------------------------

REPL = {
    "absenci": "chybění",
    "obdobnou": "podobnou",
    "samostatně": "sám",
    "maximálně": "nejvíc",
    "metabolismus": "látková výměna v těle",
}

def normalize_spaces(t: str) -> str:
    t = re.sub(r"\s+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()

def simple_simplify(text: str, grade: int) -> str:
    t = normalize_spaces(text)
    if grade <= 3:
        t = re.sub(r"„[^“]{80,}“", "„…“", t)
    for k, v in REPL.items():
        t = re.sub(rf"\b{k}\b", v, t, flags=re.IGNORECASE)
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
    sents = [s.strip() for s in sents if len(s.strip()) > 0][:6]
    out = ["LMP/SPU verze (zjednodušeně):", ""]
    for s in sents:
        if len(s) > 140:
            s = s[:140].rstrip() + "…"
        out.append(f"• {s}")
    return "\n".join(out)


# ---------------------------
# Stavba pracovních listů
# ---------------------------

def add_dramatization(doc: Document, key: str):
    add_section_header(doc, "Dramatizace (zahájení hodiny – krátká scénka)")
    for line in DRAMA[key]:
        doc.add_paragraph(line)

def build_doc_karetni(version: str) -> Document:
    doc = Document()
    set_doc_style(doc)

    add_title(doc, "EdRead AI – Pracovní list", f"Karetní hra (3. třída) — verze: {version}")
    add_hr(doc)
    add_dramatization(doc, "karetni")
    add_hr(doc)

    add_section_header(doc, "Text k přečtení")
    if version == "PLNÝ":
        doc.add_paragraph(FULL_KARETNI_TEXT)
        add_karetni_matrix_table(doc)
        src = FULL_KARETNI_TEXT
    elif version == "ZJEDNODUŠENÝ":
        doc.add_paragraph(SIMPLE_KARETNI_TEXT)
        src = SIMPLE_KARETNI_TEXT
    else:
        doc.add_paragraph(LMP_KARETNI_TEXT)
        src = LMP_KARETNI_TEXT

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
    add_dramatization(doc, "sladke")
    add_hr(doc)

    add_section_header(doc, "Text k přečtení")
    if version == "PLNÝ":
        doc.add_paragraph(FULL_SLADKE_TEXT)
        add_section_header(doc, "Češi a čokoláda (tabulky – přesný přepis)")
        for title, rows in SLADKE_TABLES.items():
            add_two_col_table(doc, title, rows)
        src = FULL_SLADKE_TEXT
    elif version == "ZJEDNODUŠENÝ":
        doc.add_paragraph(SIMPLE_SLADKE_TEXT)
        src = SIMPLE_SLADKE_TEXT
    else:
        doc.add_paragraph(LMP_SLADKE_TEXT)
        src = LMP_SLADKE_TEXT

    add_hr(doc)
    add_questions_sladke(doc)
    add_glossary_at_end(doc, src, max_words=12)
    return doc

def build_doc_venecky(version: str) -> Document:
    doc = Document()
    set_doc_style(doc)

    add_title(doc, "EdRead AI – Pracovní list", f"Věnečky (4. třída) — verze: {version}")
    add_hr(doc)
    add_dramatization(doc, "venecky")
    add_hr(doc)

    add_section_header(doc, "Text k přečtení")
    if version == "PLNÝ":
        doc.add_paragraph(FULL_VENECKY_TEXT)
        add_venecky_table_and_podniky(doc)
        src = FULL_VENECKY_TEXT
    elif version == "ZJEDNODUŠENÝ":
        doc.add_paragraph(SIMPLE_VENECKY_TEXT)
        add_venecky_table_and_podniky(doc)
        src = SIMPLE_VENECKY_TEXT
    else:
        doc.add_paragraph(LMP_VENECKY_TEXT)
        add_venecky_table_and_podniky(doc)
        src = LMP_VENECKY_TEXT

    add_hr(doc)
    add_questions_venecky(doc)
    add_glossary_at_end(doc, src, max_words=12)
    return doc

def build_doc_custom(version: str, title: str, grade: int, full_text: str) -> Document:
    doc = Document()
    set_doc_style(doc)

    add_title(doc, "EdRead AI – Pracovní list", f"{title} (třída: {grade}) — verze: {version}")
    add_hr(doc)
    add_dramatization(doc, "custom")
    add_hr(doc)

    add_section_header(doc, "Text k přečtení")
    full_text = normalize_spaces(full_text)

    if version == "PLNÝ":
        doc.add_paragraph(full_text)
        src = full_text
    elif version == "ZJEDNODUŠENÝ":
        simp = simple_simplify(full_text, grade)
        doc.add_paragraph(simp)
        src = simp
    else:
        lmp = lmp_simplify(full_text)
        doc.add_paragraph(lmp)
        src = lmp

    add_hr(doc)
    add_questions_generic(doc, grade)
    add_glossary_at_end(doc, src, max_words=12)
    return doc


# ---------------------------
# Metodika – pořadí kroků je jen zde
# ---------------------------

def build_methodology(text_name: str, grade: str, has_pyramid: bool = False) -> Document:
    doc = Document()
    set_doc_style(doc)

    add_title(doc, "EdRead AI – Metodický list pro učitele", f"{text_name} ({grade})")
    add_hr(doc)

    add_section_header(doc, "Doporučený postup práce (45 minut)")
    doc.add_paragraph("1) Dramatizace (startovací scénka) – 3 až 7 minut.")
    doc.add_paragraph("2) Slovníček – i když je na konci pracovního listu: učitel žáky nejprve ke slovníčku NAVIGUJE a významy projde společně.")
    doc.add_paragraph("3) Čtení textu – žáci se vrátí do textu, čtou (samostatně / po odstavcích), podtrhují klíčové informace.")
    doc.add_paragraph("4) Otázky A/B/C – nejprve A (vyhledání), potom B (interpretace), nakonec C (vlastní názor).")
    doc.add_paragraph("5) Shrnutí – co je fakt a co je názor? Co je hlavní sdělení?")

    if has_pyramid:
        add_hr(doc)
        add_section_header(doc, "Specifická aktivita (Karetní hra – pyramida)")
        doc.add_paragraph("Žáci vystřihnou kartičky (3 sloupce) a lepí je do sloupce okýnek.")
        doc.add_paragraph("Okýnka jsou velikostně nastavena větší než kartičky, aby se kartičky vešly bez přehýbání.")
        doc.add_paragraph("Pořadí: nahoře nejsilnější, dole nejslabší. Každé zvíře má vlastní úroveň.")

    add_hr(doc)
    add_section_header(doc, "Rozdíly mezi verzemi pracovních listů")
    doc.add_paragraph("PLNÝ list:")
    doc.add_paragraph("• obsahuje původní (plný) text; u předpřipravených textů obsahuje i tabulky; otázky a slovníček jsou přiměřené ročníku.")
    doc.add_paragraph("ZJEDNODUŠENÝ list:")
    doc.add_paragraph("• obsahuje kratší a jazykově jednodušší text; ponechává klíčová fakta; tabulky zůstávají, pokud jsou potřeba pro otázky.")
    doc.add_paragraph("LMP/SPU list:")
    doc.add_paragraph("• obsahuje velmi jednoduché věty a jasnou strukturu; vhodné pro žáky se SVP; slovníček je vždy na konci a má i prostor na poznámky.")

    return doc


# ---------------------------
# Streamlit UI
# ---------------------------

st.set_page_config(page_title="EdRead AI (prototyp)", layout="centered")
st.title("EdRead AI – generátor materiálů (prototyp)")

st.write("Můžeš použít předpřipravené texty (DP) nebo vložit vlastní text a zvolit ročník (1–5).")

mode = st.radio("Režim:", ["Předpřipravené texty (3)", "Vlastní text"], horizontal=True)

if mode == "Předpřipravené texty (3)":
    choice = st.selectbox(
        "Vyber text:",
        ["Karetní hra (3. třída)", "Věnečky (4. třída)", "Sladké mámení (5. třída)"]
    )
    if st.button("Vygenerovat dokumenty"):
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")

        if choice.startswith("Karetní"):
            full_doc = build_doc_karetni("PLNÝ")
            simple_doc = build_doc_karetni("ZJEDNODUŠENÝ")
            lmp_doc = build_doc_karetni("LMP/SPU")
            metod = build_methodology("Karetní hra", "3. třída", has_pyramid=True)

            full_name = f"pracovni_list_Karetni_hra_plny_{stamp}.docx"
            sim_name  = f"pracovni_list_Karetni_hra_zjednoduseny_{stamp}.docx"
            lmp_name  = f"pracovni_list_Karetni_hra_LMP_{stamp}.docx"
            met_name  = f"metodicky_list_Karetni_hra_{stamp}.docx"

        elif choice.startswith("Věnečky"):
            full_doc = build_doc_venecky("PLNÝ")
            simple_doc = build_doc_venecky("ZJEDNODUŠENÝ")
            lmp_doc = build_doc_venecky("LMP/SPU")
            metod = build_methodology("Věnečky", "4. třída", has_pyramid=False)

            full_name = f"pracovni_list_Venecky_plny_{stamp}.docx"
            sim_name  = f"pracovni_list_Venecky_zjednoduseny_{stamp}.docx"
            lmp_name  = f"pracovni_list_Venecky_LMP_{stamp}.docx"
            met_name  = f"metodicky_list_Venecky_{stamp}.docx"

        else:
            full_doc = build_doc_sladke("PLNÝ")
            simple_doc = build_doc_sladke("ZJEDNODUŠENÝ")
            lmp_doc = build_doc_sladke("LMP/SPU")
            metod = build_methodology("Sladké mámení", "5. třída", has_pyramid=False)

            full_name = f"pracovni_list_Sladke_mameni_plny_{stamp}.docx"
            sim_name  = f"pracovni_list_Sladke_mameni_zjednoduseny_{stamp}.docx"
            lmp_name  = f"pracovni_list_Sladke_mameni_LMP_{stamp}.docx"
            met_name  = f"metodicky_list_Sladke_mameni_{stamp}.docx"

        st.success("Hotovo. Stáhni dokumenty:")

        st.download_button("⬇️ PLNÝ pracovní list (DOCX)", doc_to_bytes(full_doc), full_name,
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           key=f"dl_full_{stamp}")
        st.download_button("⬇️ ZJEDNODUŠENÝ pracovní list (DOCX)", doc_to_bytes(simple_doc), sim_name,
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           key=f"dl_simple_{stamp}")
        st.download_button("⬇️ LMP/SPU pracovní list (DOCX)", doc_to_bytes(lmp_doc), lmp_name,
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           key=f"dl_lmp_{stamp}")
        st.download_button("⬇️ METODICKÝ LIST (DOCX)", doc_to_bytes(metod), met_name,
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           key=f"dl_met_{stamp}")

else:
    st.subheader("Vlastní text")
    custom_title = st.text_input("Název (např. téma / text):", value="Vlastní text")
    grade = st.selectbox("Pro jakou třídu?", [1, 2, 3, 4, 5], index=2)
    custom_text = st.text_area("Vlož text (žáci s ním budou pracovat):", height=250)

    if st.button("Vygenerovat dokumenty pro vlastní text"):
        if not custom_text.strip():
            st.error("Vlož prosím text.")
        else:
            stamp = datetime.now().strftime("%Y-%m-%d_%H%M")

            full_doc = build_doc_custom("PLNÝ", custom_title, grade, custom_text)
            simple_doc = build_doc_custom("ZJEDNODUŠENÝ", custom_title, grade, custom_text)
            lmp_doc = build_doc_custom("LMP/SPU", custom_title, grade, custom_text)
            metod = build_methodology(custom_title, f"{grade}. třída", has_pyramid=False)

            safe = re.sub(r"[^A-Za-z0-9ÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž_\- ]+", "", custom_title).strip().replace(" ", "_")
            full_name = f"pracovni_list_{safe}_plny_{stamp}.docx"
            sim_name  = f"pracovni_list_{safe}_zjednoduseny_{stamp}.docx"
            lmp_name  = f"pracovni_list_{safe}_LMP_{stamp}.docx"
            met_name  = f"metodicky_list_{safe}_{stamp}.docx"

            st.success("Hotovo. Stáhni dokumenty:")

            st.download_button("⬇️ PLNÝ pracovní list (DOCX)", doc_to_bytes(full_doc), full_name,
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               key=f"dl_cfull_{stamp}")
            st.download_button("⬇️ ZJEDNODUŠENÝ pracovní list (DOCX)", doc_to_bytes(simple_doc), sim_name,
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               key=f"dl_csimple_{stamp}")
            st.download_button("⬇️ LMP/SPU pracovní list (DOCX)", doc_to_bytes(lmp_doc), lmp_name,
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               key=f"dl_clmp_{stamp}")
            st.download_button("⬇️ METODICKÝ LIST (DOCX)", doc_to_bytes(metod), met_name,
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               key=f"dl_cmet_{stamp}")

st.caption("Pozn.: Slovníček je v pracovním listu na konci, ale metodika vede učitele: dramatizace → slovníček → čtení → otázky.")
