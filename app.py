# app.py — EdRead AI (prototyp pro DP)
# Streamlit + python-docx
# Vytváří: PLNY / ZJEDNODUSENY / LMP-SPU pracovní list + METODICKÝ LIST
# Speciálně pro 3 texty: Karetní hra (3. třída), Věnečky (4. třída), Sladké mámení (5. třída)

import re
from datetime import datetime

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

def add_small_note(doc: Document, text: str):
    p = doc.add_paragraph(text)
    p.runs[0].italic = True

def add_hr(doc: Document):
    doc.add_paragraph("")

def add_lines(doc: Document, count=2):
    for _ in range(count):
        doc.add_paragraph("______________________________________________")

def set_cell_shading(cell, fill_hex: str):
    """fill_hex např. 'D9D9D9'"""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tc_pr.append(shd)

def set_cell_border(cell, **kwargs):
    """
    Nastaví okraje buňky. kwargs: top/bottom/left/right = {"sz":12,"val":"single","color":"000000"}
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)

    for edge in ("left", "top", "right", "bottom", "insideH", "insideV"):
        if edge in kwargs:
            edge_data = kwargs.get(edge)
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for k, v in edge_data.items():
                element.set(qn('w:{}'.format(k)), str(v))


# ---------------------------
# Texty (plné + tabulky přesně)
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

# Sladké mámení – tabulky (přesný přepis z PDF obrázku sladke_p1)
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

Potravinářský analytik Petr Havel v zájmu zdraví doporučuje pátrat po sladkostech, které obsahují spíše složité cukry — nejlépe polysacharidy, jako je škrob, celulóza, vláknina — než jednoduché, což jsou kupříkladu glukóza — hroznový cukr, fruktóza — ovocný cukr. Ty totiž představují jen „prázdnou“, rychlou energii. „Samozřejmě záleží na tom, co chceme. Pokud to má být ,energie sbalená na cesty', pro rychlý přísun kalorií, pak jednoduché cukry poslouží výborně, ale na večerní mlsání u televize se vyplatí dát si s výběrem sladkostí trochu práci,“ míní.

Podobně se podle něho dají laskominy rozdělit na vyloženě nezdravé a zdravější podle tuků, které obsahují. „Kakaové máslo se často nahrazuje jinými tuky, hlavně kvůli ceně. Některé z nich ale lidskému — a hlavně dětskému — zdraví neprospívají. Právě naopak,“ upozorňuje Havel. Konkrétně to jsou takzvané transmastné a vyšší mastné kyseliny, jako je kyselina palmitová nebo myristová. „Palmový a kokosový tuk zvyšují riziko kardiovaskulární choroby, stejně jako méně kvalitní ztužené tuky,“ doplňuje Havel.

Jeden cukrovinářský trend je ale patrný i v našich zeměpisných šířkách. Odklon …

Zdroj: Týden, 31. října 2011, 44/2011, s. 29, upraveno. (Průzkum agentury Median v roce 2010.)
"""

# Věnečky – tabulka přesně z PDF (venecky_p2)
VENECKY_TABLE = [
    ("1", "15", "4", "5", "2", "1", "3"),
    ("2", "17", "4", "5", "5", "5", "5"),
    ("3", "11,50", "5", "5", "5", "5", "5"),
    ("4", "19", "2", "1", "2", "2", "2"),
    ("5", "20", "3", "3", "5", "5", "4"),
]

FULL_VENECKY_TEXT = """NÁZEV ÚLOHY: VĚNEČKY\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Věneček č. 2
„Vrátit výuční list!“ vykřikuje po dvou soustech z dalšího věnečku. „Tohle je špatné. Je to sražený krém. Vlastně se ani nedá říct krém, protože tohle je spíše vyšlehaný margarín. Nejenže to pudink ani vzdáleně nepřipomíná, ale navíc má chemickou pachuť, ochutnejte,“ vybízí mě. Nepříjemná stopa opravdu zůstává vzadu na patře. „Navíc tam není ani stopa rumu. A ten korpus? Buď ho tvořili podle špatného receptu, nebo recept velice ošidili. Správné odpalované těsto má mít viditelné drážky, jak se zdobícím pytlíkem stříkalo na plech. Tohle je slité, bez vzorku a tvrdé.“

Věneček č. 3
„Tady je naopak výrazně cítit rum, to je dobře. Jenže když ochutnáte, dojde vám proč. Tou vůní chtěli jen přebít absenci jakýchkoli jiných chutí,“ míní hodnotitelka. „Vůbec netuším, z čeho tohle vyrobili, možná vyšlehaný margarín nebo rostlinná šlehačka. Navíc se to srazilo! Jak si mohou dovolit tohle prodávat? Tohle je také na vrácení výučního listu. Zkuste zakrojit lžičku do korpusu — přepečená hmota, mokvavá a dole ztvrdlá. Vůbec se nevytvarovala, podobně jako u druhého věnečku.“

Věneček č. 4
„Nejhezčí věneček. Na první pohled. Krásně žlutá náplň, takhle vypadá pudink. Konečně! Jen je škoda, že tam vůbec není cítit rum. Oceňuji, že dodrželi recepturu. Ten pudink mohl být trochu více nadlehčený máslem, zdá se, že nedodrželi poměr 250 gramů másla na litr pudinku, ale to není taková tragédie. Je to dobré. A hmota se vyloženě povedla. Je světlá, zlatavá, vláčná, měkká, ale zároveň lehce křupavá, není přepečená, ani nedopečená, ani zestárlá. Tohle dělal cukrář, který své řemeslo umí.“

Věneček č. 5
„Na první pohled vypadá hezky, drážky korpusu vypadají, jak mají, ale tím to končí. Tohle je chemický pudink, s vodou smíchaný prášek, nevařilo se to s mlékem. Nejenže to nemá chuť, ale je to tou chemií cítit. Těsto je staré, ztvrdlé… Tento cukrář by u mě propadl, katastrofa.“

Než paní Fornůskové prozradím jména cukráren, přináším nesoutěžní doplňkové vzorky zákusků, kterými chci dát podnikům druhou šanci — napravit věnečkový dojem a zlomit verdikt. Podaří se to jedinému zákusku: štrúdlu s tvarohem a višněmi. „Hezky vypadá a je dobrý. Je nejspíše upečený z průmyslově vyráběného listového těsta, ale to je normální, dělá to tak většina cukráren. Vlastně spíše připomíná těsto plundrové, protože nelistuje, jak by mělo, ale nikde není psáno, že by štrúdl musel nutně být z listového těsta… Tvaroh je akorát sladký, utřený do jemna, višně chutnají jako višně. Tohle je můj vítěz druhého kola,“ pronese jednoznačně. „A o těch dalších raději pomlčme.“

Když odtajním cukrárny, které se schovávaly za čísly výrobků, vyjde najevo, že vítězný věneček i štrúdl jsou totiž z „jednoho těsta“, a to z cukrárny Mámení ve stejnojmenné pasáži. „Vida, na tuto cukrárnu bych asi vsadila předem, kdybych věděla, že jejich výrobky zde budete mít,“ říká uznale cukrářka. „Ale jinak mě věnečky zklamaly…“

Zdroj: Týden, 31. října 2011, 44/2011, s. 31, upraveno, kráceno. Hodnocení šéfkuchařky Fornůskové
"""

# Přesný seznam podniků (jako v PDF)
VENECKY_PODNIKY = [
    ("1", "Cukrárna Věnečky, Praha 5"),
    ("2", "Pekárna Krémová, Praha 1"),
    ("3", "Cukrárna Větrníček, Praha 3"),
    ("4", "Cukrárna Mámení, Praha 2"),
    ("5", "Cukrárna Dortíček, Praha 6"),
]


# ---------------------------
# Zjednodušené a LMP verze (jen text – BEZ plné verze)
# ---------------------------

SIMPLE_KARETNI_TEXT = """KARETNÍ HRA (zjednodušený text)

Ve hře je 60 karet se zvířaty. Každý hráč dostane stejné množství karet.
Cílem je zbavit se všech karet jako první.

Hráči postupně vykládají (vynášejí) karty na stůl.
Další hráč musí dát silnější zvíře, aby přebil předchozí kartu.
Někdy může přebít i stejným zvířetem, ale musí dát o jednu kartu víc.

Chameleon je žolík: může se přidat k jiné kartě a pomůže vytvořit potřebné zvíře.
Sám se hrát nesmí.

Když někdo nemůže nebo nechce přebít, řekne „pass“ a nehraje.
Vyhrává ten, kdo se první zbaví všech karet.
"""

LMP_KARETNI_TEXT = """KARETNÍ HRA (LMP/SPU)

1) Každý dostane karty.
2) Hrajeme po jednom (po řadě).
3) Chci být první, kdo už nemá žádné karty.

Když někdo dá kartu na stůl, já musím dát silnější zvíře (nebo stejné zvíře, ale o jednu kartu víc).
Když nemám, řeknu „pass“.

Chameleon je žolík. Musí být vždy s jinou kartou.
"""

SIMPLE_SLADKE_TEXT = """SLADKÉ MÁMENÍ (zjednodušený text)

Text říká, že v Evropě a Americe je problém obezita.
Proto lidé chtějí nízkokalorické (méně kalorické) sladkosti.

V Česku ale mnoho lidí nechce číst, kolik má sladkost energie.
Vědci hledají sladidlo, které bude sladké, nebude mít divnou chuť ani pach a nebude mít kalorie.

V textu se také mluví o tom, že existují jednoduché cukry (rychlá energie)
a složité cukry (lepší pro tělo, když nechci jen rychlou energii).
"""

LMP_SLADKE_TEXT = """SLADKÉ MÁMENÍ (LMP/SPU)

V textu se píše:
• Mnoho lidí má obezitu.
• Lidé proto chtějí sladkosti s méně kaloriemi.
• Vědci hledají sladidlo bez kalorií.
• Jsou jednoduché cukry (rychlá energie) a složité cukry (lepší volba).
"""

SIMPLE_VENECKY_TEXT = """VĚNEČKY (zjednodušený text)

V textu hodnotitelka ochutnává věnečky z různých cukráren.
Některé věnečky jsou špatné: krém je sražený, chutná „chemicky“ nebo je těsto tvrdé.
Jeden věneček je nejlepší: má dobrý krém i dobré těsto.

V tabulce je napsáno, kolik věneček stál a jaké dostal známky (jako ve škole).
"""

LMP_VENECKY_TEXT = """VĚNEČKY (LMP/SPU)

V textu se porovnávají věnečky z cukráren.
Některé jsou špatné (divná chuť, tvrdé těsto).
Jeden je nejlepší.
Tabulka ukazuje cenu a známku.
"""


# ---------------------------
# Dramatizace (úvodní)
# ---------------------------

DRAMA = {
    "karetni": [
        "Žák A: „Já tomu nerozumím… kdo koho přebíjí?“",
        "Žák B: „Tak si to zkusíme! Já jsem myš a ty jsi slon.“",
        "Učitel/ka: „Stop — podle pravidel může někdy myš přebít slona. Zkusíme přijít na to proč.“",
        "Učitel/ka: „Dnes budeme číst návod a zjistíme, jak to ve hře funguje.“",
    ],
    "sladke": [
        "Žák A: „Kdyby existovala čokoláda bez kalorií, jedl/a bych ji pořád!“",
        "Žák B: „A šla by vůbec udělat? Aby byla sladká a chutnala normálně?“",
        "Učitel/ka: „Dnes budeme číst text, kde vědci hledají takové sladidlo.“",
    ],
    "venecky": [
        "Žák A: „Tahle cukrárna je nejlepší, to je jasné!“",
        "Žák B: „Ne! Já myslím, že rozhoduje chuť a suroviny.“",
        "Učitel/ka: „Dnes budeme číst hodnocení zákusků a budeme hledat, co je fakt a co je názor.“",
    ],
}


# ---------------------------
# Karetní hra – tabulka „Kdo přebije koho?“ (přesná logika dle obrázku)
# ---------------------------

KARETNI_ANIMALS = ["Kosatka", "Slon", "Krokodýl", "Lední medvěd", "Lev", "Tuleň", "Liška", "Okoun", "Ježek", "Sardinky", "Myš", "Komár"]
KARETNI_ROWS = ["Kosatku", "Slona", "Krokodýla", "Ledního medvěda", "Lva", "Tuleně", "Lišku", "Okouna", "Ježka", "Sardinky", "Myš", "Komára"]

# Šedé buňky (řádek -> které sloupce jsou vybarvené)
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
    # +1 sloupec na názvy řádků
    table = doc.add_table(rows=1, cols=1 + len(KARETNI_ANIMALS))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Hlavička
    hdr = table.rows[0].cells
    hdr[0].text = ""  # levý horní roh
    for i, animal in enumerate(KARETNI_ANIMALS, start=1):
        hdr[i].text = animal

    # Řádky
    for row_name in KARETNI_ROWS:
        row_cells = table.add_row().cells
        row_cells[0].text = row_name
        for i, col_animal in enumerate(KARETNI_ANIMALS, start=1):
            # diagonála: >
            if row_name.lower().startswith(col_animal.lower()[:3].lower()):
                row_cells[i].text = ">"
            else:
                row_cells[i].text = ""

            # šedé vybarvení podle mapy
            if col_animal in KARETNI_BEATERS.get(row_name, []):
                set_cell_shading(row_cells[i], "D9D9D9")

    # rámečky
    for r in table.rows:
        for c in r.cells:
            set_cell_border(
                c,
                top={"sz": 8, "val": "single", "color": "000000"},
                bottom={"sz": 8, "val": "single", "color": "000000"},
                left={"sz": 8, "val": "single", "color": "000000"},
                right={"sz": 8, "val": "single", "color": "000000"},
            )

    doc.add_paragraph("Živočichové označení šedým políčkem daný druh přebíjejí. Symbol > znamená: lze přebít více kartami stejného druhu.")


# ---------------------------
# Karetní hra – pyramidový sloupec + kartičky (emoji)
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

# Pořadí v „pyramidě/sloupci“ — VRCH = nejsilnější, SPOD = nejslabší
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

def add_pyramid_column(doc: Document):
    add_section_header(doc, "Zvířecí „pyramida“ síly (lepení)")
    doc.add_paragraph("Vystřihni kartičky a nalep je do okýnek. Nahoře bude nejsilnější zvíře, dole nejslabší.")

    # Sloupec okýnek – velikost tak, aby se vešly kartičky (rychlé na 1 stranu)
    t = doc.add_table(rows=len(PYRAMID_ORDER_TOP_TO_BOTTOM)+1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Hlavička
    t.cell(0, 0).text = "NAHOŘE = NEJSILNĚJŠÍ"
    t.cell(0, 0).paragraphs[0].runs[0].bold = True
    t.cell(0, 0).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Okýnka
    for i, _ in enumerate(PYRAMID_ORDER_TOP_TO_BOTTOM, start=1):
        cell = t.cell(i, 0)
        cell.text = ""  # prázdné pro lepení
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        # výška okýnka
        cell.height = Cm(1.2)
        set_cell_border(
            cell,
            top={"sz": 12, "val": "single", "color": "000000"},
            bottom={"sz": 12, "val": "single", "color": "000000"},
            left={"sz": 12, "val": "single", "color": "000000"},
            right={"sz": 12, "val": "single", "color": "000000"},
        )

    doc.add_paragraph("DOLE = NEJSLABŠÍ")


def add_animal_cards_3cols(doc: Document):
    add_section_header(doc, "Kartičky zvířat (na stříhání)")
    doc.add_paragraph("Vystřihni kartičky. (3 sloupce)")

    cols = 3
    rows = (len(ANIMAL_CARDS) + cols - 1) // cols
    table = doc.add_table(rows=rows, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            set_cell_border(
                cell,
                top={"sz": 12, "val": "single", "color": "000000"},
                bottom={"sz": 12, "val": "single", "color": "000000"},
                left={"sz": 12, "val": "single", "color": "000000"},
                right={"sz": 12, "val": "single", "color": "000000"},
            )
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

            if idx < len(ANIMAL_CARDS):
                name, emoji = ANIMAL_CARDS[idx]
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run1 = p.add_run(f"{emoji}\n")
                run1.font.size = Pt(26)
                run2 = p.add_run(name)
                run2.font.size = Pt(12)
                run2.bold = True
            else:
                cell.text = ""
            idx += 1


# ---------------------------
# Tabulky pro Sladké mámení a Věnečky
# ---------------------------

def add_two_col_table(doc: Document, title: str, rows):
    add_section_header(doc, title)
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    hdr = t.rows[0].cells
    hdr[0].text = "Položka"
    hdr[1].text = "Hodnota (%)"

    for a, b in rows:
        rr = t.add_row().cells
        rr[0].text = a
        rr[1].text = b

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
    for i, c in enumerate(cols):
        t.cell(0, i).text = c

    for row in VENECKY_TABLE:
        rr = t.add_row().cells
        for i, val in enumerate(row):
            rr[i].text = val

    for r in t.rows:
        for c in r.cells:
            set_cell_border(
                c,
                top={"sz": 8, "val": "single", "color": "000000"},
                bottom={"sz": 8, "val": "single", "color": "000000"},
                left={"sz": 8, "val": "single", "color": "000000"},
                right={"sz": 8, "val": "single", "color": "000000"},
            )


# ---------------------------
# Slovníček – výběr + vysvětlení (většina slov vysvětlena)
# ---------------------------

STOPWORDS = set("""
a i o u v ve na do z ze že který která které kteří se si je jsou být bylo byla byly jsem jsme jste
když protože proto ale nebo ani jen ještě už pak také tak tedy tento tato toto
""".split())

# Slovník vysvětlení (záměrně bohatý pro 3 texty)
EXPLAIN = {
    # obecné
    "maximálně": "nejvíc (největší možné množství)",
    "vykřikuje": "říká nahlas",
    "sousto": "kousek jídla v puse",
    "sousty": "kousky jídla",
    "vyšlehaný": "hodně našlehaný, nadýchaný",
    "margarín": "tuk podobný máslu",
    "vzdáleně": "ani trochu",
    "nepřipomíná": "není to podobné",
    "chemická": "umělá, nepřirozená",
    "chemickou": "umělou, ne přírodní",
    "pachuť": "nepříjemná chuť, která zůstane",
    "korpus": "těsto (spodní část zákusku)",
    "receptura": "správný postup a poměr surovin",
    "dodrželi": "udělali přesně podle pravidel",
    "nadlehčený": "udělaný lehčí a nadýchanější",
    "poměr": "kolik čeho má být",
    "tragédie": "velmi velký problém (tady: přehnaně řečeno)",
    "vlačný": "měkký a šťavnatý",
    "křupavý": "když to při kousnutí křupne",
    "přepečený": "pečený moc dlouho",
    "ztvrdlý": "tvrdý",
    "zestárlá": "už není čerstvá",
    "na vrácení": "tak špatné, že by to neměli prodávat",
    "absence": "chybění (něčeho tam není)",
    "prodávat": "dávat do obchodu za peníze",
    "nesoutěžní": "mimo soutěž / mimo hodnocení",
    "doplňkové": "navíc, přidané",
    "podnikům": "firmám / provozovnám (tady: cukrárnám)",
    "napravit": "zlepšit, opravit",
    "dojem": "pocit",
    "verdikt": "konečné rozhodnutí",
    "průmyslově": "vyrobené ve velké výrobě (továrně)",
    "nelistuje": "netvoří vrstvy jako listové těsto",
    "upraveno": "trochu změněno",
    # Karetní
    "rovnoměrně": "stejně pro všechny",
    "kombinaci": "spojení více karet dohromady",
    "přebít": "dát silnější kartu (porazit předchozí)",
    "vynést": "položit kartu na stůl",
    "lícem": "přední stranou",
    "žolík": "karta, která může nahradit jinou",
    "obdobnou": "podobnou",
    "požadovaný": "takový, jaký je potřeba",
    "samostatně": "sám, bez jiné karty",
    # Sladké mámení
    "epidemie": "rychlé rozšíření problému",
    "obezita": "velká nadváha",
    "metabolismus": "látková výměna v těle",
    "poptávka": "zájem lidí o něco (co chtějí kupovat)",
    "nízkokalorický": "s málo kaloriemi (méně energie)",
    "energetický": "související s energií (kaloriemi)",
    "alchymisté": "lidé, kteří hledali zázračný recept (tady: přirovnání)",
    "náhražka": "něco místo původní věci",
    "sladivost": "jak moc je něco sladké",
    "kalorie": "jednotka energie v jídle",
    "polysacharidy": "složitější cukry",
    "glukóza": "hroznový cukr",
    "fruktóza": "ovocný cukr",
    "laskominy": "dobroty",
    "kardiovaskulární": "týkající se srdce a cév",
    "ztužené": "uměle upravené tuky",
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
        # vyhoď velmi časté věci typu „věneček“ atd. necháme, ale až později
        cleaned.append(wl)

    uniq = []
    for w in cleaned:
        if w not in uniq:
            uniq.append(w)

    # preferuj slova, která umíme vysvětlit (aby byl slovníček opravdu slovníček)
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
            r2 = line.add_run(EXPLAIN[w])
        else:
            # žádná věta – jen linka
            line.add_run("______________________________")

        # prostor na poznámky žáka
        doc.add_paragraph("Poznámka žáka/žákyně: _______________________________")


# ---------------------------
# Otázky A/B/C (stabilní, bez chyb typu „Věneček č.“)
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


# ---------------------------
# Vytvoření pracovních listů – vždy obsahuje odpovídající text
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
        # tabulka uvnitř textu (po části o pořadí karet)
        add_karetni_matrix_table(doc)
    elif version == "ZJEDNODUŠENÝ":
        doc.add_paragraph(SIMPLE_KARETNI_TEXT)
    else:  # LMP
        doc.add_paragraph(LMP_KARETNI_TEXT)

    add_hr(doc)

    # Aktivita pyramida jen pro 3. třídu (u všech verzí, ale s textem podle verze)
    add_pyramid_column(doc)
    add_animal_cards_3cols(doc)

    add_hr(doc)
    add_questions_karetni(doc)

    # Slovníček až na konec
    src = FULL_KARETNI_TEXT if version == "PLNÝ" else (SIMPLE_KARETNI_TEXT if version == "ZJEDNODUŠENÝ" else LMP_KARETNI_TEXT)
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
        # tabulky VLOŽENÉ „uvnitř textu“ — hned po úvodu Češi a čokoláda
        add_section_header(doc, "Češi a čokoláda (tabulky – přesný přepis)")
        for title, rows in SLADKE_TABLES.items():
            add_two_col_table(doc, title, rows)
    elif version == "ZJEDNODUŠENÝ":
        doc.add_paragraph(SIMPLE_SLADKE_TEXT)
    else:
        doc.add_paragraph(LMP_SLADKE_TEXT)

    add_hr(doc)
    add_questions_sladke(doc)

    src = FULL_SLADKE_TEXT if version == "PLNÝ" else (SIMPLE_SLADKE_TEXT if version == "ZJEDNODUŠENÝ" else LMP_SLADKE_TEXT)
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
        # podniky + tabulka přímo uvnitř (jako originál)
        add_venecky_table_and_podniky(doc)
    elif version == "ZJEDNODUŠENÝ":
        doc.add_paragraph(SIMPLE_VENECKY_TEXT)
        add_venecky_table_and_podniky(doc)  # tabulka zůstává (pracují s ní i v jednodušší verzi)
    else:
        doc.add_paragraph(LMP_VENECKY_TEXT)
        add_venecky_table_and_podniky(doc)  # tabulka zůstává

    add_hr(doc)
    add_questions_venecky(doc)

    src = FULL_VENECKY_TEXT if version == "PLNÝ" else (SIMPLE_VENECKY_TEXT if version == "ZJEDNODUŠENÝ" else LMP_VENECKY_TEXT)
    add_glossary_at_end(doc, src, max_words=12)
    return doc


# ---------------------------
# Metodický list – manuál + rozdíly mezi verzemi
# ---------------------------

def build_methodology(text_name: str, grade: str) -> Document:
    doc = Document()
    set_doc_style(doc)

    add_title(doc, "EdRead AI – Metodický list pro učitele", f"{text_name} ({grade})")
    add_hr(doc)

    add_section_header(doc, "Doporučený postup práce (45 minut)")
    doc.add_paragraph("1) Dramatizace (startovací scénka) – 3 až 7 minut.")
    doc.add_paragraph("2) Slovníček (i když je na konci pracovního listu) – učitel žáky nejprve k slovníčku NAVIGUJE, společně projdou významy.")
    doc.add_paragraph("3) Čtení textu – žáci se vrátí do textu, čtou (samostatně / po odstavcích), podtrhují klíčové informace.")
    doc.add_paragraph("4) Otázky A/B/C – nejprve A (vyhledání), potom B (interpretace), nakonec C (vlastní názor).")
    doc.add_paragraph("5) Krátké shrnutí – co nám text řekl? Co je fakt a co je názor?")

    add_hr(doc)
    add_section_header(doc, "Rozdíly mezi verzemi pracovních listů (učitel se snadno rozhodne)")
    doc.add_paragraph("PLNÝ list:")
    doc.add_paragraph("• obsahuje původní (plný) text + všechny tabulky v původní podobě; otázky jsou stejné, slovníček je na konci.")
    doc.add_paragraph("ZJEDNODUŠENÝ list:")
    doc.add_paragraph("• obsahuje kratší a jednodušší text; ponechává klíčová fakta; tabulky zůstávají, pokud jsou pro otázky potřeba.")
    doc.add_paragraph("LMP/SPU list:")
    doc.add_paragraph("• velmi jednoduché věty, jasná struktura; vhodné pro žáky se SVP; tabulky zůstávají (pracuje se s nimi i v testu).")

    add_hr(doc)
    add_section_header(doc, "Poznámka k testování (pro kvaziexperiment)")
    doc.add_paragraph("Doporučení: zachovat stejné podmínky pro všechny žáky (čas, instrukce, prostředí).")
    doc.add_paragraph("Učitel volí verzi listu podle potřeb žáka (PLNÝ / ZJEDNODUŠENÝ / LMP-SPU).")

    return doc


# ---------------------------
# Streamlit UI
# ---------------------------

st.set_page_config(page_title="EdRead AI (prototyp)", layout="centered")
st.title("EdRead AI – generátor materiálů (prototyp pro DP)")

st.write("Vyber text a stáhni pracovní listy (plný / zjednodušený / LMP) + metodický list.")

choice = st.selectbox(
    "Vyber text:",
    ["Karetní hra (3. třída)", "Věnečky (4. třída)", "Sladké mámení (5. třída)"]
)

generate = st.button("Vygenerovat dokumenty")

if generate:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")

    if choice.startswith("Karetní"):
        text_key = "karetni"
        full_doc = build_doc_karetni("PLNÝ")
        simple_doc = build_doc_karetni("ZJEDNODUŠENÝ")
        lmp_doc = build_doc_karetni("LMP/SPU")
        metod = build_methodology("Karetní hra", "3. třída")

        full_name = f"pracovni_list_Karetni_hra_plny_{stamp}.docx"
        sim_name = f"pracovni_list_Karetni_hra_zjednoduseny_{stamp}.docx"
        lmp_name = f"pracovni_list_Karetni_hra_LMP_{stamp}.docx"
        met_name = f"metodicky_list_Karetni_hra_{stamp}.docx"

    elif choice.startswith("Věnečky"):
        text_key = "venecky"
        full_doc = build_doc_venecky("PLNÝ")
        simple_doc = build_doc_venecky("ZJEDNODUŠENÝ")
        lmp_doc = build_doc_venecky("LMP/SPU")
        metod = build_methodology("Věnečky", "4. třída")

        full_name = f"pracovni_list_Venecky_plny_{stamp}.docx"
        sim_name = f"pracovni_list_Venecky_zjednoduseny_{stamp}.docx"
        lmp_name = f"pracovni_list_Venecky_LMP_{stamp}.docx"
        met_name = f"metodicky_list_Venecky_{stamp}.docx"

    else:
        text_key = "sladke"
        full_doc = build_doc_sladke("PLNÝ")
        simple_doc = build_doc_sladke("ZJEDNODUŠENÝ")
        lmp_doc = build_doc_sladke("LMP/SPU")
        metod = build_methodology("Sladké mámení", "5. třída")

        full_name = f"pracovni_list_Sladke_mameni_plny_{stamp}.docx"
        sim_name = f"pracovni_list_Sladke_mameni_zjednoduseny_{stamp}.docx"
        lmp_name = f"pracovni_list_Sladke_mameni_LMP_{stamp}.docx"
        met_name = f"metodicky_list_Sladke_mameni_{stamp}.docx"

    # Uložení do bytes pro download (bez mizícího tlačítka – každý má vlastní klíč)
    import io
    def doc_to_bytes(doc):
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf

    st.success("Hotovo. Stáhni dokumenty níže:")

    st.download_button(
        "⬇️ Stáhnout PLNOUPRAVNÝ pracovní list (DOCX)",
        data=doc_to_bytes(full_doc),
        file_name=full_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key=f"dl_full_{stamp}"
    )

    st.download_button(
        "⬇️ Stáhnout ZJEDNODUŠENÝ pracovní list (DOCX)",
        data=doc_to_bytes(simple_doc),
        file_name=sim_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key=f"dl_simple_{stamp}"
    )

    st.download_button(
        "⬇️ Stáhnout LMP/SPU pracovní list (DOCX)",
        data=doc_to_bytes(lmp_doc),
        file_name=lmp_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key=f"dl_lmp_{stamp}"
    )

    st.download_button(
        "⬇️ Stáhnout METODICKÝ LIST (DOCX)",
        data=doc_to_bytes(metod),
        file_name=met_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key=f"dl_met_{stamp}"
    )

st.caption("EdRead AI (prototyp) – generuje materiály pro testování čtenářské gramotnosti. Slovníček je záměrně na konci listu, ale metodika vede učitele k práci se slovníčkem před čtením.")
