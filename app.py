# app.py
# EdRead AI – prototyp pro DP (Streamlit + python-docx)
# Generuje: pracovní list (plný / zjednodušený / LMP), kartičky (3. třída), metodický list
# Všechny verze obsahují text k přečtení a tabulky jsou uvnitř textu.

import io
import re
import datetime
import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn


# -----------------------------
# ZÁKLADNÍ NASTAVENÍ DOKUMENTU
# -----------------------------
def set_doc_style(doc: Document):
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    section = doc.sections[0]
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)


def add_title(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(16)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT


def add_subtitle(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(12)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT


def add_hr(doc):
    p = doc.add_paragraph("—" * 42)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT


def add_note_box(doc, lines=2):
    # „linka“ pro odpověď
    for _ in range(lines):
        doc.add_paragraph("_______________________________________________")


def doc_to_bytes(doc: Document) -> bytes:
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


# -----------------------------
# POMOCNÉ: TABULKY DO DOCX
# -----------------------------
def add_two_col_table(doc, rows, col1="Položka", col2="Hodnota"):
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text = col1
    hdr[1].text = col2
    for a, b in rows:
        r = table.add_row().cells
        r[0].text = str(a)
        r[1].text = str(b)
    doc.add_paragraph("")


def add_venecky_tables(doc):
    # Tabulka 1: kde jsme věnečky pořídili
    add_subtitle(doc, "Hodnocení šéfkuchařky Fornůskové – kde jsme věnečky pořídili")
    rows = [
        ("1", "Cukrárna Věnečky, Praha 5"),
        ("2", "Pekárna Krémová, Praha 1"),
        ("3", "Cukrárna Větrníček, Praha 3"),
        ("4", "Cukrárna Mámení, Praha 2"),
        ("5", "Cukrárna Dortíček, Praha 6"),
    ]
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.rows[0].cells[0].text = "Číslo"
    table.rows[0].cells[1].text = "Podnik"
    for a, b in rows:
        r = table.add_row().cells
        r[0].text = a
        r[1].text = b

    doc.add_paragraph("")

    # Tabulka 2: známkování
    add_subtitle(doc, "Tabulka hodnocení věnečků (jako ve škole)")
    cols = ["Cukrárna", "Cena v Kč", "Vzhled", "Korpus", "Náplň", "Suroviny", "Celková známka (jako ve škole)"]
    data = [
        ["1", "15", "4", "5", "2", "1", "3"],
        ["2", "17", "4", "5", "5", "5", "5"],
        ["3", "11,50", "5", "5", "5", "5", "5"],
        ["4", "19", "2", "1", "2", "2", "2"],
        ["5", "20", "3", "3", "5", "5", "4"],
    ]
    table2 = doc.add_table(rows=1, cols=len(cols))
    table2.style = "Table Grid"
    for i, c in enumerate(cols):
        table2.rows[0].cells[i].text = c
    for row in data:
        r = table2.add_row().cells
        for i, val in enumerate(row):
            r[i].text = val
    doc.add_paragraph("")


def add_sladke_mameni_tables(doc):
    add_subtitle(doc, "Češi a čokoláda (všechny údaje v druhém sloupci jsou v procentech)")

    add_subtitle(doc, "Jak často jíte čokoládu?")
    add_two_col_table(doc, [
        ("Alespoň jednou týdně", "22,7"),
        ("Více než dvakrát týdně", "6,1"),
        ("Méně než jednou týdně", "57,1"),
    ])

    add_subtitle(doc, "Jakou čokoládu máte nejraději?")
    add_two_col_table(doc, [
        ("Studentská pečeť", "32,5"),
        ("Milka", "23,4"),
        ("Orion mléčná", "20,8"),
    ])

    add_subtitle(doc, "Jaké čokoládové tyčinky jste jedl v posledních 12 měsících?")
    add_two_col_table(doc, [
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
    ])

    add_subtitle(doc, "Jak často kupujete bonboniéry?")
    add_two_col_table(doc, [
        ("Dvakrát a více měsíčně", "1,7"),
        ("Jednou měsíčně", "14,9"),
        ("Jednou až dvakrát za 3 měsíce", "23,2"),
        ("Méně než jedenkrát za 3 měsíce", "54,5"),
        ("Neuvedeno", "5,7"),
    ])

    add_subtitle(doc, "Jaké bonboniéry jste koupili v posledních 12 měsících?")
    add_two_col_table(doc, [
        ("Laguna – mořské lodě", "31,9"),
        ("Figaro – Tatiana", "25,6"),
        ("Figaro – Zlatý nuget", "21,6"),
        ("Tofifee", "19,6"),
        ("Orion – Modré z nebe", "19,4"),
        ("Nugátový dezert", "17,6"),
        ("Ferrero Rocher", "16,2"),
        ("Merci", "15,7"),
        ("Raffaello", "13,9"),
        ("Mon Chéri", "13,5"),
    ])

    doc.add_paragraph("Zdroj: Průzkum agentury Median v roce 2010.")


# -----------------------------
# KARETNÍ HRA – PYRAMIDA + KARTIČKY
# -----------------------------
KARETNI_ZVIRATA_ORDER_WEAK_TO_STRONG = [
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
]
KARETNI_JOKER = ("chameleon (žolík)", "🦎")


def add_pyramid_template(doc):
    add_subtitle(doc, "Zvířecí pyramida síly (vizuální opora)")
    doc.add_paragraph("Vystřihni kartičky zvířat a nalep je do pyramidy podle síly ve hře.")
    doc.add_paragraph("Dole je nejslabší zvíře, nahoře je nejsilnější. Chameleona (žolíka) nech stranou.")

    # 6 řad = 12 míst (1+1+2+2+3+3 = 12) – jednoduché na lepení
    # Uděláme tabulku 6x6 a budeme slučovat buňky tak, aby vznikla pyramida.
    table = doc.add_table(rows=6, cols=6)
    table.style = "Table Grid"

    # vyčistit text
    for r in table.rows:
        for c in r.cells:
            c.text = ""

    # Helper: merge range in a row
    def merge_row(row_idx, start_col, end_col, label=""):
        cell = table.cell(row_idx, start_col)
        for col in range(start_col + 1, end_col + 1):
            cell = cell.merge(table.cell(row_idx, col))
        if label:
            cell.text = label
        return cell

    # Pyramida (shora dolů):
    # ř0: 1 pole uprostřed (sloupec 2-3)
    merge_row(0, 2, 3, "⬜")
    # ř1: 1 pole uprostřed (2-3)
    merge_row(1, 2, 3, "⬜")
    # ř2: 2 pole (1-2) a (3-4)
    merge_row(2, 1, 2, "⬜")
    merge_row(2, 3, 4, "⬜")
    # ř3: 2 pole (1-2) a (3-4)
    merge_row(3, 1, 2, "⬜")
    merge_row(3, 3, 4, "⬜")
    # ř4: 3 pole (0-1), (2-3), (4-5)
    merge_row(4, 0, 1, "⬜")
    merge_row(4, 2, 3, "⬜")
    merge_row(4, 4, 5, "⬜")
    # ř5: 3 pole (0-1), (2-3), (4-5)
    merge_row(5, 0, 1, "⬜")
    merge_row(5, 2, 3, "⬜")
    merge_row(5, 4, 5, "⬜")

    doc.add_paragraph("")
    doc.add_paragraph("Tip: Pokud si nejsi jistý/á, podívej se do části textu „Pořadí karet“.")
    doc.add_paragraph("")


def build_animal_cards_doc():
    doc = Document()
    set_doc_style(doc)
    add_title(doc, "KARETNÍ HRA – Kartičky zvířat (pro vystřižení)")
    doc.add_paragraph("Vystřihni kartičky a použij je k lepení do pyramidy.")
    doc.add_paragraph("")

    animals = [(n, e) for (n, e) in KARETNI_ZVIRATA_ORDER_WEAK_TO_STRONG] + [KARETNI_JOKER]

    # 3 sloupce, tolik řad, kolik je třeba
    cols = 3
    rows = (len(animals) + cols - 1) // cols
    table = doc.add_table(rows=rows, cols=cols)
    table.style = "Table Grid"

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.text = ""
            if idx < len(animals):
                name, emoji = animals[idx]
                p = cell.paragraphs[0]
                run = p.add_run(f"{emoji}\n{name}")
                run.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            idx += 1

    doc.add_paragraph("")
    doc.add_paragraph("Pozn.: Chameleon je žolík – ve hře se počítá jako požadované zvíře, ale sám se nehraje.")
    return doc


# -----------------------------
# SLOVNÍČEK (vysvětlit co nejvíc)
# -----------------------------
def explain_word(word: str, grade: int) -> str:
    # Malá „mini-databáze“ – aby to bylo stabilní a bez chyb.
    # Když něco neznáme, vracíme prázdný řetězec (a do PL půjde jen linka).
    w = word.lower().strip()

    simple = {
        "odpalované": "těsto, které se nejdřív zahřeje v hrnci a pak se peče",
        "podnikům": "cukrárnám nebo pekárnám (místům, kde se to prodává)",
        "vyráběného": "udělaného, vyrobeného",
        "jedinému": "jen jednomu (pouze jednomu)",
        "dodrželi": "udělali to podle pravidel / receptu",
        "napravit": "spravit, zlepšit",
        "upraveno": "trochu změněno (zkráceno nebo přepracováno)",
        "zestárlá": "už není čerstvá",
        "nelistuje": "netvoří vrstvy jako listové těsto",
        "korpus": "těsto zákusku (spodní část)",
        "receptura": "přesný recept, podle kterého se něco dělá",
        "pachuť": "chuť, která není příjemná a zůstává v puse",
        "absenci": "to, že něco chybí",
        "nadlehčený": "udělaný víc lehký a nadýchaný",
        "pudink": "sladký krém uvařený z mléka",
        "margarín": "tuk podobný máslu",
        "přebít": "zahrát silnější kartu / být silnější",
        "kombinace": "víc karet dohromady",
        "rovnoměrně": "stejně pro všechny",
        "žolík": "speciální karta, která může nahradit jinou",
        "distraktor": "schválně špatná odpověď v testu",
    }

    if w in simple:
        return simple[w]

    return ""


def add_glossary(doc, words, grade: int):
    add_subtitle(doc, "Slovníček pojmů")
    doc.add_paragraph("Doplň vlastními slovy. Můžeš si připsat i poznámku.")
    doc.add_paragraph("")

    for w in words:
        expl = explain_word(w, grade)
        p = doc.add_paragraph()
        run = p.add_run(f"• {w} = ")
        run.bold = True
        if expl:
            doc.add_paragraph(f"{expl}")
        else:
            # jen linka – žádná rušivá věta
            doc.add_paragraph("_______________________________________________")

        # místo pro poznámku žáka vždy
        doc.add_paragraph("Poznámka žáka: ______________________________________")
        doc.add_paragraph("")


# -----------------------------
# OBSAH – TEXTY (plný / zjednodušený / LMP)
# -----------------------------
# Pozn.: pro stabilitu jsou texty uložené natvrdo.
# Zjednodušení a LMP jsou záměrně kratší a s kratšími větami.

KARETNI_FULL_TEXT = """NÁZEV ÚLOHY: KARETNÍ HRA\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

1. Herní materiál
60 karet živočichů: 4 komáři, 1 chameleon (žolík), 5 karet od každého z dalších 11 druhů živočichů.

2. Popis hry
Všechny karty se rozdají mezi jednotlivé hráče. Hráči se snaží vynášet karty v souladu s pravidly tak, aby se co nejdříve zbavili všech svých karet z ruky. Zahrát lze vždy pouze silnější kombinaci živočichů, než zahrál hráč před vámi.

3. Pořadí karet
Na každé kartě je zobrazen jeden živočich. V rámečku v horní části karty jsou namalováni živočichové, kteří danou kartu přebíjí.

Kdo přebije koho?
Kosatku
Slona
Krokodýla
Ledního medvěda
Lva
Tuleně
Lišku
Okouna
Ježka
Sardinku
Myš
Komára

Symbol > označuje, že každý živočich může být přebit větším počtem karet se živočichem stejného druhu.
Příklad: Kosatku přebijí pouze dvě kosatky. Krokodýla přebijí dva krokodýli nebo jeden slon.

Chameleon má ve hře obdobnou funkci jako žolík. Lze jej zahrát spolu s libovolnou jinou kartou a počítá se jako požadovaný druh živočicha. Nelze jej hrát samostatně.

4. Průběh hry
• Karty zamíchejte a rozdejte rovnoměrně mezi všechny hráče.
• Hráč po levé ruce rozdávajícího hráče začíná. Zahraje jednu kartu nebo více stejných karet.
• Hráči se snaží přebít dříve zahrané karty buď stejným počtem karet „vyššího“ živočicha, nebo o jednu kartu více stejného druhu.
• Kdo nechce nebo nemůže přebít, řekne pass.
• Hráč, který jako první vynese poslední kartu, vítězí.

Zdroj: Bláznivá ZOO. Doris Matthäusová a Frank Nestel, Mindok, 1999, upraveno.
"""

KARETNI_SIMPLE_TEXT = """KARETNÍ HRA (zjednodušený text)

Ve hře je 60 karet zvířat. Některá zvířata jsou silnější než jiná.

Cíl hry: co nejdříve se zbavit všech karet v ruce.

Hráči hrají postupně. Kdo chce, může přebít kartu na stole:
- buď stejným počtem karet silnějšího zvířete,
- nebo o jednu kartu více stejného zvířete.

Kdo nemůže, řekne „pass“.

Pořadí zvířat (od nejsilnějšího):
Kosatka, slon, krokodýl, lední medvěd, lev, tuleň, liška, okoun, ježek, sardinka, myš, komár.

Chameleon je žolík – hraje se vždy s jinou kartou.

Zdroj: upraveno podle pravidel hry.
"""

KARETNI_LMP_TEXT = """KARETNÍ HRA (LMP / SPU)

Ve hře jsou karty zvířat.
Některá zvířata jsou silnější.

Cíl: nemít v ruce žádnou kartu jako první.

Když je na stole karta, můžeš ji přebít silnější kartou.
Když nemůžeš, řekni „pass“.

Pořadí zvířat (od nejsilnějšího):
Kosatka – slon – krokodýl – lední medvěd – lev – tuleň – liška – okoun – ježek – sardinka – myš – komár.

Chameleon je žolík. Hraje se s jinou kartou.
"""

SLADEK_FULL_TEXT = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Euroamerickou civilizaci sužuje novodobá epidemie: obezita a s ní spojené choroby metabolismu, srdce a cév.
Výrobci cukrovinek po celém světě pocítili sílící poptávku po nízkokalorických čokoládách, light mlsání a dietních bonbonech.
Češi však podle výzkumů často netouží po nízkokalorickém mlsání a nechtějí mít ani na obalu velkým písmem uvedený energetický obsah.

Novodobí „alchymisté“ v laboratořích hledají náhražku cukru, která by měla dobrou sladivost, neměla nepříjemnou chuť či pach a nezásobovala tělo zbytečnými kaloriemi.
V posledních letech se používají například alditoly (sorbitol, xylitol, maltitol).
Jedním z posledních objevů je polydextróza, která má nulovou energetickou hodnotu, ale nahradit sacharózu je problém.

Analytik doporučuje vybírat sladkosti s vyšším podílem složitých cukrů (např. polysacharidy).
Jednoduché cukry jsou rychlá „prázdná“ energie, a proto je lepší je omezovat při večerním mlsání.

Zdroj: Týden, 31. října 2011, 44/2011, upraveno.
"""

SLADEK_SIMPLE_TEXT = """SLADKÉ MÁMENÍ (zjednodušený text)

V Americe a Evropě je hodně lidí, kteří mají obezitu.
Proto roste zájem o nízkokalorické sladkosti.

Vědci hledají nové sladidlo:
- aby dobře sladilo,
- nemělo divnou chuť nebo pach,
- a nemělo moc kalorií.

Odborníci říkají, že je lepší vybírat sladkosti se složitými cukry (např. vláknina),
protože jednoduché cukry jsou rychlá energie.

Zdroj: upraveno podle článku.
"""

SLADEK_LMP_TEXT = """SLADKÉ MÁMENÍ (LMP / SPU)

Lidé v Evropě a Americe mají často obezitu.
Proto chtějí sladkosti, které mají méně kalorií.

Vědci hledají sladidlo, které:
- sladí,
- nemá divnou chuť,
- nemá moc kalorií.

Odborníci říkají: jednoduché cukry jsou rychlá energie.
"""

VENECKY_FULL_TEXT = """NÁZEV ÚLOHY: VĚNEČKY\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Text popisuje ochutnávku věnečků v několika pražských cukrárnách.
Hodnotitelka kritizuje některé věnečky za špatný krém, chemickou pachuť, tvrdý korpus nebo ošizený recept.
Naopak jeden věneček hodnotí velmi dobře: má správný pudink, dobré těsto a odpovídá receptuře.

Zdroj: Týden, 31. října 2011, 44/2011, upraveno, kráceno.
"""

VENECKY_SIMPLE_TEXT = """VĚNEČKY (zjednodušený text)

Hodnotitelka ochutnává věnečky z několika cukráren.
Některé jsou špatné: mají divnou chuť, špatný krém nebo tvrdé těsto.
Jeden věneček je nejlepší: má dobrý krém i těsto.

Zdroj: upraveno podle článku.
"""

VENECKY_LMP_TEXT = """VĚNEČKY (LMP / SPU)

Hodnotitelka ochutnává věnečky.
Některé jsou špatné.
Jeden je nejlepší.

Použij i tabulky, abys našel/našla odpovědi.
"""


# -----------------------------
# OTÁZKY A/B/C – stabilní (bez rozpadů typu „Věneček č.“)
# -----------------------------
def add_questions_karetni(doc):
    add_subtitle(doc, "Otázky A/B/C")

    doc.add_paragraph("A) Najdi v textu (vyhledání informace)")
    doc.add_paragraph("1) Co je cílem hry Karetní hra?")
    doc.add_paragraph("Odpověď:")
    add_note_box(doc, 2)

    doc.add_paragraph("2) Co udělá hráč, který nemůže přebít?")
    doc.add_paragraph("Odpověď:")
    add_note_box(doc, 2)

    doc.add_paragraph("B) Přemýšlej (interpretace)")
    doc.add_paragraph("3) Proč je chameleon (žolík) ve hře výhodný?")
    add_note_box(doc, 3)

    doc.add_paragraph("C) Můj názor")
    doc.add_paragraph("4) Bavil/a by tě tenhle typ hry? Proč?")
    add_note_box(doc, 3)


def add_questions_sladke(doc):
    add_subtitle(doc, "Otázky A/B/C")

    doc.add_paragraph("A) Najdi v textu (vyhledání informace)")
    doc.add_paragraph("1) Proč roste ve světě zájem o nízkokalorické sladkosti?")
    add_note_box(doc, 3)

    doc.add_paragraph("2) Najdi v tabulkách jednu čokoládovou tyčinku a napiš, kolik % lidí ji jedlo.")
    add_note_box(doc, 2)

    doc.add_paragraph("B) Přemýšlej (interpretace)")
    doc.add_paragraph("3) Co znamená výraz „novodobí alchymisté“ v textu?")
    add_note_box(doc, 3)

    doc.add_paragraph("C) Můj názor")
    doc.add_paragraph("4) Je podle tebe dobré mít na obalu potravin energetickou hodnotu? Proč?")
    add_note_box(doc, 3)


def add_questions_venecky(doc):
    add_subtitle(doc, "Otázky A/B/C")

    doc.add_paragraph("A) Najdi v textu / tabulkách (vyhledání informace)")
    doc.add_paragraph("1) Která cukrárna dopadla nejlépe podle celkové známky?")
    add_note_box(doc, 1)

    doc.add_paragraph("2) Který věneček byl nejdražší? Kolik stál a kde byl pořízen?")
    add_note_box(doc, 3)

    doc.add_paragraph("B) Přemýšlej (interpretace)")
    doc.add_paragraph("3) Proč může být drahý věneček i přesto nekvalitní? Napiš vlastními slovy.")
    add_note_box(doc, 3)

    doc.add_paragraph("C) Můj názor")
    doc.add_paragraph("4) Podle čeho ty posuzuješ, jestli je zákusek „dobrý“? Napiš 2–3 kritéria.")
    add_note_box(doc, 3)


# -----------------------------
# DRAMATIZACE (vždy konkrétní)
# -----------------------------
def add_dramatization(doc, kind: str):
    add_subtitle(doc, "Dramatizace – krátká motivace na začátek hodiny (2–3 min)")

    if kind == "karetni":
        doc.add_paragraph("Učitel/ka: „Dnes máme pravidla nové hry. Kdo z vás už někdy četl pravidla a úplně se v nich ztratil?“")
        doc.add_paragraph("Žák A: „Já! Je tam moc informací.“")
        doc.add_paragraph("Žák B: „A hlavně kdo přebíjí koho…“")
        doc.add_paragraph("Učitel/ka: „Tak si to nejdřív ukážeme. Každý si vybere jedno zvíře a zkusíme zjistit, kdo je silnější.“")
        doc.add_paragraph("Učitel/ka: „Až pak budeme číst text a ověříme si to podle pravidel.“")

    elif kind == "sladke":
        doc.add_paragraph("Učitel/ka: „Představte si, že firma chce vyrobit čokoládu, která bude sladká, ale nebude mít skoro žádné kalorie.“")
        doc.add_paragraph("Žák A: „To by bylo super!“")
        doc.add_paragraph("Žák B: „Ale jde to vůbec?“")
        doc.add_paragraph("Učitel/ka: „V textu zjistíme, co vědci hledají a proč. A podíváme se i na čísla z průzkumu.“")

    elif kind == "venecky":
        doc.add_paragraph("Učitel/ka: „Představte si, že jste porotci, kteří mají rozhodnout: který věneček je nejlepší.“")
        doc.add_paragraph("Žák A: „Já bych hodnotil/a podle chuti.“")
        doc.add_paragraph("Žák B: „A podle vzhledu.“")
        doc.add_paragraph("Učitel/ka: „V textu uvidíme, jak hodnotí odborník. A tabulky nám pomůžou porovnat výsledky.“")

    doc.add_paragraph("")


# -----------------------------
# PRACOVNÍ LISTY – GENERÁTORY
# -----------------------------
def build_workbook(text_name: str, variant: str) -> Document:
    """
    text_name: 'Karetní hra' | 'Sladké mámení' | 'Věnečky'
    variant: 'plny' | 'zjednoduseny' | 'lmp'
    """
    doc = Document()
    set_doc_style(doc)

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Titul
    add_title(doc, f"EdRead AI – pracovní list ({text_name})")
    doc.add_paragraph(f"Verze: {variant.upper()}   |   Datum: {today}")
    doc.add_paragraph("Jméno: ____________________________   Třída: ________")
    add_hr(doc)

    # Dramatizace
    if text_name == "Karetní hra":
        add_dramatization(doc, "karetni")
    elif text_name == "Sladké mámení":
        add_dramatization(doc, "sladke")
    else:
        add_dramatization(doc, "venecky")

    # TEXT PRO ŽÁKY (správná verze podle varianty)
    add_subtitle(doc, "Text pro žáky (čtení)")
    if text_name == "Karetní hra":
        if variant == "plny":
            doc.add_paragraph(KARETNI_FULL_TEXT)
        elif variant == "zjednoduseny":
            doc.add_paragraph(KARETNI_SIMPLE_TEXT)
        else:
            doc.add_paragraph(KARETNI_LMP_TEXT)

        # Pyramida jen pro 3. třídu (karetní hra) – uvnitř pracovního listu
        add_hr(doc)
        add_pyramid_template(doc)

    elif text_name == "Sladké mámení":
        if variant == "plny":
            doc.add_paragraph(SLADEK_FULL_TEXT)
        elif variant == "zjednoduseny":
            doc.add_paragraph(SLADEK_SIMPLE_TEXT)
        else:
            doc.add_paragraph(SLADEK_LMP_TEXT)

        add_hr(doc)
        add_sladke_mameni_tables(doc)

    elif text_name == "Věnečky":
        if variant == "plny":
            doc.add_paragraph(VENECKY_FULL_TEXT)
        elif variant == "zjednoduseny":
            doc.add_paragraph(VENECKY_SIMPLE_TEXT)
        else:
            doc.add_paragraph(VENECKY_LMP_TEXT)

        add_hr(doc)
        add_venecky_tables(doc)

    add_hr(doc)

    # Slovníček – pro každé téma zvolíme smysluplná slova, ale vysvětlení se doplňuje automaticky (kde umíme).
    if text_name == "Karetní hra":
        words = ["přebít", "kombinace", "rovnoměrně", "žolík", "vynést", "pravidla", "pořadí", "pass", "příklad", "silnější"]
        grade = 3
    elif text_name == "Sladké mámení":
        words = ["epidemie", "obezita", "poptávka", "nízkokalorické", "alchymisté", "náhražka", "sladivost", "polydextróza", "sacharóza", "polysacharidy"]
        grade = 5
    else:
        words = ["odpalované", "korpus", "pachuť", "receptura", "dodrželi", "zestárlá", "nelistuje", "upraveno", "napravit", "jedinému"]
        grade = 4

    add_glossary(doc, words, grade)

    # Otázky
    add_hr(doc)
    if text_name == "Karetní hra":
        add_questions_karetni(doc)
    elif text_name == "Sladké mámení":
        add_questions_sladke(doc)
    else:
        add_questions_venecky(doc)

    # Sebehodnocení
    add_hr(doc)
    add_subtitle(doc, "Sebehodnocení")
    doc.add_paragraph("Označ: 😃 / 🙂 / 😐")
    doc.add_paragraph("Rozuměl/a jsem textu:  😃  🙂  😐")
    doc.add_paragraph("Našel/la jsem odpovědi v textu / tabulkách:  😃  🙂  😐")
    doc.add_paragraph("Umím vysvětlit některá slova ze slovníčku:  😃  🙂  😐")

    return doc


def build_methodology(text_name: str) -> Document:
    doc = Document()
    set_doc_style(doc)

    add_title(doc, f"EdRead AI – metodický list (pro učitele): {text_name}")
    doc.add_paragraph("Určeno pro ověření v rámci diplomové práce (kvaziexperiment).")
    add_hr(doc)

    add_subtitle(doc, "Cíl aktivity")
    doc.add_paragraph("• Rozvoj čtenářské gramotnosti: práce s informací, porozumění, interpretace a vyjádření názoru.")
    doc.add_paragraph("• Podpora slovní zásoby (slovníček) a práce se strukturou textu (otázky A/B/C).")
    if text_name == "Karetní hra":
        doc.add_paragraph("• Vizuální opora (pyramida síly) – propojení textu s obrazovým schématem.")

    add_subtitle(doc, "Propojení s RVP ZV (jazyk a jazyková komunikace – čtenářství)")
    doc.add_paragraph("Žák vyhledává informace v textu, rozumí jim, propojuje je a dokáže je využít při řešení úloh.")
    doc.add_paragraph("Žák formuluje odpovědi vlastními slovy a rozlišuje fakt a názor.")
    doc.add_paragraph("Pozn.: Formulace je záměrně obecná, aby byla použitelná napříč ŠVP škol a odpovídala principům RVP ZV.")

    add_subtitle(doc, "Doporučený průběh (45 min)")
    doc.add_paragraph("1) Motivační dramatizace (2–3 min) – naladění na téma.")
    doc.add_paragraph("2) Čtení textu (10–15 min) – tiché čtení / střídání po odstavcích.")
    doc.add_paragraph("3) Práce se slovníčkem (5–8 min) – společné objasnění, doplnění poznámek.")
    doc.add_paragraph("4) Otázky A/B/C (15–20 min) – A vyhledávání, B interpretace, C názor.")
    if text_name == "Karetní hra":
        doc.add_paragraph("5) Pyramida síly (7–10 min) – lepení kartiček, kontrola podle textu.")

    add_subtitle(doc, "Hodnocení a záznam")
    doc.add_paragraph("• Doporučeno zaznamenat: počet správných odpovědí, typ chyby (vyhledání / interpretace / názor), práci se slovníkem.")
    doc.add_paragraph("• Pro žáky se SVP využít variantu LMP/SPU (kratší věty, přehlednější struktura).")

    add_subtitle(doc, "Digitální varianta (EdRead AI)")
    doc.add_paragraph("Aplikace generuje dokumenty jako výstup (DOCX). Žáci nepracují přímo s AI – minimalizují se etická rizika.")

    return doc


# -----------------------------
# STREAMLIT APP
# -----------------------------
st.set_page_config(page_title="EdRead AI (prototyp)", layout="centered")
st.title("EdRead AI – generátor pracovních listů (prototyp)")
st.write("Vyber text a vytvoř pracovní listy (plný / zjednodušený / LMP) + metodiku. U Karetní hry se generují i kartičky zvířat.")

text_name = st.selectbox("Vyber text:", ["Karetní hra", "Sladké mámení", "Věnečky"])

if "generated" not in st.session_state:
    st.session_state.generated = {}

if st.button("Vygenerovat dokumenty", type="primary"):
    # Pracovní listy
    doc_full = build_workbook(text_name, "plny")
    doc_simple = build_workbook(text_name, "zjednoduseny")
    doc_lmp = build_workbook(text_name, "lmp")
    doc_met = build_methodology(text_name)

    # Kartičky pro karetní hru navíc
    cards_doc = None
    if text_name == "Karetní hra":
        cards_doc = build_animal_cards_doc()

    st.session_state.generated = {
        "full": doc_to_bytes(doc_full),
        "simple": doc_to_bytes(doc_simple),
        "lmp": doc_to_bytes(doc_lmp),
        "met": doc_to_bytes(doc_met),
        "cards": doc_to_bytes(cards_doc) if cards_doc else None,
    }

    st.success("Hotovo. Teď můžeš stáhnout dokumenty níže (tlačítka nezmizí).")

if st.session_state.generated:
    st.subheader("Stažení")

    st.download_button(
        "⬇️ Pracovní list – PLNÝ (DOCX)",
        data=st.session_state.generated["full"],
        file_name=f"pracovni_list_{text_name}_plny.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key="dl_full",
    )

    st.download_button(
        "⬇️ Pracovní list – ZJEDNODUŠENÝ (DOCX)",
        data=st.session_state.generated["simple"],
        file_name=f"pracovni_list_{text_name}_zjednoduseny.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key="dl_simple",
    )

    st.download_button(
        "⬇️ Pracovní list – LMP/SPU (DOCX)",
        data=st.session_state.generated["lmp"],
        file_name=f"pracovni_list_{text_name}_LMP.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key="dl_lmp",
    )

    st.download_button(
        "⬇️ Metodický list pro učitele (DOCX)",
        data=st.session_state.generated["met"],
        file_name=f"metodicky_list_{text_name}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key="dl_met",
    )

    if st.session_state.generated.get("cards"):
        st.download_button(
            "⬇️ Kartičky zvířat (3 sloupce, DOCX)",
            data=st.session_state.generated["cards"],
            file_name="karticky_zvirat_karetni_hra.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="dl_cards",
        )

st.caption("EdRead AI – prototyp pro ověření v diplomové práci. Výstupy: DOCX.")
