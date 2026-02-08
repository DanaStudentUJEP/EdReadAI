# app.py
# EdRead AI – stabilní prototyp pro diplomovou práci (3 texty) – Streamlit + python-docx
# Generuje: plný PL, zjednodušený PL, LMP/SPU PL, metodický list
# Pro 3. třídu navíc: pyramida (šablona k lepení) + kartičky zvířat (3 sloupce, černobílé siluety)

import re
import io
import math
import tempfile
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

import streamlit as st
from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENTATION

from PIL import Image, ImageDraw

# -----------------------------
# 1) KONFIG
# -----------------------------

APP_TITLE = "EdRead AI – prototyp (diplomová práce)"
APP_SUBTITLE = "Generátor pracovních listů + metodiky (3 texty: Karetní hra / Sladké mámení / Věnečky)"

# Stabilní ročníky pro texty (jak máš ve výzkumu)
TEXT_META = {
    "Karetní hra (3. třída)": {"grade": 3, "key": "karetni_hra"},
    "Věnečky (4. třída)": {"grade": 4, "key": "venecky"},
    "Sladké mámení (5. třída)": {"grade": 5, "key": "sladke_mameni"},
}

# -----------------------------
# 2) ORIGINÁLNÍ TEXTY + TABULKY (pevně, aby nic nechybělo a tabulky byly tabulkami)
# -----------------------------

KARETNI_HRA_TEXT_FULL = """NÁZEV ÚLOHY: KARETNÍ HRA\t\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

1. Herní materiál
60 karet živočichů: 4 komáři, 1 chameleon (žolík), 5 karet od každého z dalších 11 druhů živočichů

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
• Při přebíjení není povoleno hrát více karet, než je třeba. Vždy musí být zahráno buď přesně stejně karet „vyššího“ živočicha, nebo přesně o jednu kartu více stejného druhu.
• Hráč, který nechce nebo nemůže přebít, se může vzdát tahu slovem pass. V tuto chvíli nezahraje žádné karty, ale později může ještě hrát, když se dostane znovu na řadu.
• Pokud se hráč dostane na řadu s tím, že nikdo z ostatních hráčů nepřebil jeho karty zahrané v minulém kole (všichni ostatní hráči „passovali“), vezme si tento hráč všechny karty, které v tu chvíli leží uprostřed stolu. Tyto karty si položí na hromádku před sebe a vynese další kartu nebo karty z ruky. S kartami, které hráči v průběhu hry sebrali, se již dále nehraje.
• Hráč, který jako první vynese svoji poslední kartu nebo karty z ruky, vítězí.

Zdroj: Bláznivá ZOO. Doris Matthäusová a Frank Nestel, Mindok, s. r. o., 1999, upraveno.
"""

# Pořadí síly (logika pyramidy)
# nejslabší -> nejsilnější
KARETNI_ORDER_WEAK_TO_STRONG = [
    "komár",
    "myš",
    "sardinka",
    "ježek",
    "okoun",
    "liška",
    "tuleň",
    "lev",
    "lední medvěd",
    "krokodýl",
    "slon",
    "kosatka",
]
KARETNI_JOKER = "chameleon (žolík)"

# Tabulka „Kdo přebije koho?“ – uděláme jako tabulku v docx (2 sloupce)
KARETNI_PREBIJI_LIST_STRONG_TO_WEAK = [
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
]
# Pozn.: chameleon je žolík

KARETNI_HRA_QUESTIONS = [
    ("1) Co je cílem hry?", ["A) Dosáhnout nejvyššího počtu „přebití“ ostatních hráčů.",
                             "B) Nemít v ruce žádné karty jako první.",
                             "C) Nasbírat v průběhu hry co nejvíce karet.",
                             "D) Získat co nejvíce karet „vyšších“ živočichů."], "B"),
    ("2) Kolik druhů živočichů je ve hře? Uveď počet a krátce zdůvodni.", [], None),
    ("3) Kterého živočicha lze přebít největším počtem druhů? Uveď živočicha a počet.", [], None),
    ("4) Kolik karet obdrží každý hráč, pokud se hry zúčastní 4 hráči?", [], None),
    ("5) Která okolnost NEMŮŽE přispět k vítězství hráče?", ["A) Hráč při rozdávání získal kartu chameleona.",
                                                             "B) Hráč při rozdávání získal více karet stejného živočicha.",
                                                             "C) Hráč při rozdávání získal pouze jednu kartu každého živočicha.",
                                                             "D) Hráč při rozdávání získal karty tzv. „vyšších“ živočichů."], "C"),
]

# -----------------------------
# SLADKÉ MÁMENÍ – tabulky + text (zkráceně, ale kompletně pro test)
# Pozn.: zachováme i tabulky jako tabulky.
# -----------------------------

SLADKE_MAMENI_TABLE_1 = [
    ["Jak často jíte čokoládu?", ""],
    ["Alespoň jednou týdně", "22,7"],
    ["Více než dvakrát týdně", "6,1"],
    ["Méně než jednou týdně", "57,1"],
]

SLADKE_MAMENI_TABLE_2 = [
    ["Jakou čokoládu máte nejraději?", ""],
    ["Studentská pečeť", "32,5"],
    ["Milka", "23,4"],
    ["Orion mléčná", "20,8"],
]

SLADKE_MAMENI_TABLE_3 = [
    ["Jaké čokoládové tyčinky jste jedl(a) v posledních 12 měsících?", ""],
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
]

SLADKE_MAMENI_TABLE_4 = [
    ["Jak často kupujete bonboniéru?", ""],
    ["Jednou měsíčně", "14,9"],
    ["Jednou až dvakrát za 3 měsíce", "23,2"],
    ["Méně než jedenkrát za 3 měsíce", "54,5"],
]

SLADKE_MAMENI_TABLE_5 = [
    ["Jaké bonboniéry jste koupili v posledních 12 měsících?", ""],
    ["La Panna – mořské plody", "31,9"],
    ["Figaro – Tatiana", "25,6"],
    ["Figaro – Zlatý nuget", "21,6"],
    ["Tofifee", "19,6"],
    ["Orion – Modré z nebe", "19,4"],
    ["Nugátový dezert", "17,6"],
    ["Ferrero Rocher", "16,2"],
    ["Merci", "15,7"],
    ["Raffaello", "13,9"],
    ["Mon Chéri", "13,5"],
]

SLADKE_MAMENI_TEXT_FULL = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ\t\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Euroamerickou civilizaci sužuje novodobá epidemie: obezita a s ní spojené choroby metabolismu, srdce a cév. Výrobci cukrovinek po celém vypaseném světě pocítili sílící poptávku po nízkokalorických čokoládách, light mlsání a dietních bonbonech. Až na české luhy a háje. „V našem rozsáhlém výzkumu se potvrdilo, že Češi netouží po nízkokalorickém mlsání, nechtějí mít dokonce ani na obalu větším písmem uvedený energetický obsah…“ říká Vašutová.

Nehledě na český nezájem, novodobí alchymisté v laboratořích stále hledají recept na „zlato“ – náhražku rostlinného cukru, která by měla slušnou sladivost, neměla nepříjemnou chuť či pach a nezásobovala tělo zbytečnými kaloriemi. Podle odborníků se používají sladidla s nižší energetickou hodnotou (např. sorbitol, xylitol, maltitol), ale pořád to není ideální.

Analytik Petr Havel doporučuje kvůli zdraví dávat přednost sladkostem se složitějšími cukry (např. polysacharidy – škrob, celulóza, vláknina) před jednoduchými cukry (glukóza, fruktóza), které dodají „rychlou energii“. Upozorňuje také na kvalitu tuků – některé tuky mohou zdraví škodit.

Zdroj: Týden, 31. října 2011, 44/2011, upraveno.
"""

SLADKE_MAMENI_QUESTIONS = [
    ("1) Které tvrzení je v rozporu s textem?", [
        "A) Vědcům se podařilo nalézt výbornou náhražku rostlinného cukru bez problémů.",
        "B) Euroamerickou civilizaci trápí problém obezity.",
        "C) Ve světě roste poptávka po nízkokalorických cukrovinkách.",
        "D) S obezitou souvisí nemoci metabolismu, srdce a cév."
    ], "A"),
    ("2) Jakou vlastnost by ideální sladidlo podle textu NEMĚLO mít?", [
        "A) Značnou sladivost.",
        "B) Příjemnou chuť.",
        "C) Intenzivní (nepříjemnou) vůni/pach.",
        "D) Nízkou energetickou hodnotu."
    ], "C"),
    ("3) Proč se ve světě zvyšuje poptávka po nízkokalorických sladkostech? (2–3 věty)", [], None),
    ("4) Rozhodni Ano/Ne podle tabulek (Median 2010):", [], None),
    ("5) Co je hlavním smyslem textu?", [
        "A) Vyvolat chuť na čokoládu.",
        "B) Informovat čtenáře.",
        "C) Odradit od sladkostí.",
        "D) Pobavit čtenáře.",
        "E) Udělat reklamu."
    ], "B"),
]

# -----------------------------
# VĚNEČKY – tabulka + text (kompletní pro test)
# -----------------------------

VENECKY_TEXT_FULL = """NÁZEV ÚLOHY: VĚNEČKY\t\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Věneček č. 2
„Vrátit výuční list!“ vykřikuje po dvou soustech z dalšího věnečku. „Tohle je špatné. Je to sražený krém… vlastně se ani nedá říct krém, protože tohle je spíše vyšlehaný margarín… Navíc tam není ani stopa rumu… Tohle je slité, bez vzorku a tvrdé.“

Věneček č. 3
„Tady je naopak výrazně cítit rum… Tou vůní chtěli jen přebít absenci jakýchkoli jiných chutí… Navíc se to srazilo… Zkuste zakrojit lžičku do korpusu — přepečená hmota, mokvavá a dole ztvrdlá.“

Věneček č. 4
„Nejhezčí věneček. Na první pohled… Krásně žlutá náplň, takhle vypadá pudink… Hmota se vyloženě povedla… Tohle dělal cukrář, který své řemeslo umí.“

Věneček č. 5
„Na první pohled vypadá hezky… Tohle je chemický pudink, s vodou smíchaný prášek, nevařilo se to s mlékem… Těsto je staré, ztvrdlé… katastrofa.“

Doplňkové vzorky: štrúdl s tvarohem a višněmi dopadl nejlépe; vítězný věneček i štrúdl jsou z cukrárny Mámení.

Zdroj: Týden, 31. října 2011, 44/2011, upraveno, kráceno.
"""

VENECKY_TABLE_KDE = [
    ["Kde jsme věnečky pořídili", ""],
    ["1", "Cukrárna Věnečky, Praha 5"],
    ["2", "Pekárna Krémová, Praha 1"],
    ["3", "Cukrárna Větrníček, Praha 3"],
    ["4", "Cukrárna Mámení, Praha 2"],
    ["5", "Cukrárna Dortíček, Praha 6"],
]

VENECKY_TABLE_HODNOCENI = [
    ["Cukrárna", "Cena v Kč", "Vzhled", "Korpus", "Náplň", "Suroviny", "Celková známka (jako ve škole)"],
    ["1", "15", "4", "5", "2", "1", "3"],
    ["2", "17", "4", "5", "5", "5", "5"],
    ["3", "11,50", "5", "5", "5", "5", "5"],
    ["4", "19", "2", "1", "2", "2", "2"],
    ["5", "20", "3", "3", "5", "5", "4"],
]

VENECKY_QUESTIONS = [
    ("1) Který z věnečků neobsahuje pudink uvařený přímo z mléka?", [
        "A) Věneček č. 2", "B) Věneček č. 3", "C) Věneček č. 4", "D) Věneček č. 5"
    ], "D"),
    ("2) Ve kterém věnečku je použita vůně rumu proto, aby zakryla nepřítomnost jiných chutí?", [
        "A) Věneček č. 2", "B) Věneček č. 3", "C) Věneček č. 4", "D) Věneček č. 5"
    ], "B"),
    ("3) Který věneček byl hodnocen nejlépe? (napiš číslo)", [], None),
    ("4) Který podnik dopadl v testu nejlépe?", [
        "A) Pekárna Krémová", "B) Cukrárna Věnečky", "C) Cukrárna Dortíček", "D) Cukrárna Mámení"
    ], "D"),
    ("5) Který věneček byl nejdražší? Kolik stál a kde byl koupen? Odpovídá cena kvalitě? Zdůvodni.", [], None),
]

# -----------------------------
# 3) ZJEDNODUŠENÉ TEXTY (pro žáky) – aby vždy existovaly
# -----------------------------

KARETNI_HRA_TEXT_SIMPLE = """KARETNÍ HRA – zjednodušený text

Hraje se s kartami zvířat. Každý hráč dostane stejně karet. Cílem je zbavit se karet co nejrychleji.

Karty mají sílu. Některá zvířata jsou „silnější“ než jiná. Silnější karta přebije slabší.
Když chceš přebít stejný druh zvířete, musíš dát o jednu kartu víc.
Chameleon je žolík: může pomoci, ale sám se hrát nesmí.

Vyhrává ten, kdo se jako první zbaví všech karet.
"""

SLADKE_MAMENI_TEXT_SIMPLE = """SLADKÉ MÁMENÍ – zjednodušený text

V Evropě a Americe je hodně lidí s obezitou. Proto se ve světě více kupují nízkokalorické sladkosti.
V textu se píše, že v Česku lidé většinou nechtějí řešit, kolik má sladkost energie.

Vědci hledají náhradu cukru, která by dobře sladila a neměla zbytečné kalorie.
Odborníci také upozorňují, že je rozdíl mezi jednoduchými a složitými cukry
a že některé tuky ve sladkostech mohou být nezdravé.

Součástí úlohy jsou i tabulky z průzkumu (co lidé kupují a jedí).
"""

VENECKY_TEXT_SIMPLE = """VĚNEČKY – zjednodušený text

V textu někdo ochutnává věnečky z různých cukráren a hodnotí je.
U některých věnečků kritizuje krém (například že je „chemický“ nebo sražený),
u jiných chválí dobrý pudink a povedené těsto.

Nejlépe dopadl věneček č. 4. Vítězný věneček i štrúdl jsou z cukrárny Mámení.
V tabulce je cena a známky (jako ve škole).
"""

# LMP/SPU verze (ještě jednodušší, kratší věty)
KARETNI_HRA_TEXT_LMP = """KARETNÍ HRA – text pro LMP/SPU

Hraje se s kartami zvířat.
Cíl: zbavit se karet jako první.

Každé zvíře má sílu.
Silnější zvíře přebije slabší.

Chameleon je žolík.
Pomůže, ale sám se hrát nesmí.
"""

SLADKE_MAMENI_TEXT_LMP = """SLADKÉ MÁMENÍ – text pro LMP/SPU

Ve světě je více lidí s obezitou.
Proto lidé chtějí sladkosti s méně kaloriemi.

Vědci hledají náhradu cukru.
V tabulkách je průzkum, co lidé jedí a kupují.
"""

VENECKY_TEXT_LMP = """VĚNEČKY – text pro LMP/SPU

Někdo ochutnává věnečky z různých cukráren.
Hodnotí krém a těsto.
Nejlépe dopadl věneček č. 4.
V tabulce jsou ceny a známky.
"""

# -----------------------------
# 4) DRAMATIZACE (úvodní motivační scénky)
# -----------------------------

DRAMA = {
    "karetni_hra": [
        ("Učitel/ka", "Dnes budeme číst pravidla jedné hry. Ale nejdřív si to zkusíme jako scénku!"),
        ("Žák A", "Já mám kartu komára. Jsem slabý!"),
        ("Žák B", "Já mám myš. Přebiju tě?"),
        ("Učitel/ka", "Podle pravidel zjistíme, kdo koho přebije. A pak z toho uděláme pyramidu síly."),
    ],
    "sladke_mameni": [
        ("Učitel/ka", "Dnes budeme číst článek o sladkostech. Nejdřív krátká scénka z obchodu."),
        ("Žák A", "Já bych chtěl sladkost na rychlou energii, třeba na výlet!"),
        ("Žák B", "A já chci něco, co je trochu zdravější. Co mám vybrat?"),
        ("Učitel/ka", "V textu i v tabulkách najdeme, co se doporučuje a proč."),
    ],
    "venecky": [
        ("Učitel/ka", "Dnes budeme jako hodnotitelé zákusků. Krátká scénka: cukrárna a porota!"),
        ("Žák A (porotce)", "Tenhle věneček vypadá hezky, ale co chuť?"),
        ("Žák B (porotce)", "Cítím rum… ale možná jen maskuje jiné chutě."),
        ("Učitel/ka", "Budeme číst text a porovnáme ho s tabulkou hodnocení."),
    ],
}

# -----------------------------
# 5) SLOVNÍČEK – automatický výběr + vysvětlení podle ročníku
# -----------------------------

STOPWORDS = set("""
a i v ve na do z ze s se o u k že je jsou byl byla byli být jak když aby nebo ale protože proto
tady tam tento tato toto který která které kteří kdo co kde kdy
""".split())

# Vysvětlení slov podle textu a ročníku (rozšiřitelné; cílem je mít většinu)
VOCAB_EXPLAIN = {
    "karetni_hra": {
        3: {
            "přebít": "zahrát silnější kartu než předchozí hráč",
            "kombinace": "víc karet stejného zvířete najednou",
            "rovnoměrně": "stejně pro všechny",
            "vynést": "položit kartu na stůl",
            "průběh": "jak to jde krok za krokem",
            "povolené": "dovolené",
            "vzdát": "nehrát teď, říct „pass“",
            "žolík": "karta, která může nahradit jiné zvíře",
            "libovolný": "jakýkoliv",
            "vítězí": "vyhraje",
        }
    },
    "sladke_mameni": {
        5: {
            "epidemie": "něco, co se rychle šíří a je toho hodně",
            "obezita": "velká nadváha",
            "metabolismus": "jak tělo zpracovává jídlo a energii",
            "nízkokalorický": "málo kalorií (energie)",
            "poptávka": "co lidé chtějí a kupují",
            "náhražka": "něco místo něčeho jiného",
            "alchymisté": "tady obrazně: lidé, co hledají něco „zázračného“",
            "sladivost": "jak moc to sladí",
            "polysacharidy": "složitější cukry (např. škrob)",
            "fruktóza": "ovocný cukr",
            "glukóza": "hroznový cukr",
            "kalorie": "energie z jídla",
            "analytik": "odborník, který zkoumá a hodnotí",
        }
    },
    "venecky": {
        4: {
            "sražený": "krém se pokazil a není hladký",
            "margarín": "tuk podobný máslu",
            "pachuť": "nepříjemná chuť, která zůstane v puse",
            "korpus": "těsto (základ) zákusku",
            "odpalované": "druh těsta na věnečky a větrníky",
            "drážky": "rýhy, proužky na těstě",
            "absence": "chybění něčeho",
            "přebít": "překrýt (tady vůní zakrýt jinou chuť)",
            "přepečený": "moc upečený",
            "ztvrdlý": "moc tvrdý",
            "průmyslově": "vyrobené ve velké výrobě",
            "receptura": "správný recept / postup a poměry",
            "nadlehčený": "lehčí, vzdušnější",
            "vyvodit": "dojít k závěru",
        }
    }
}

def normalize_word(w: str) -> str:
    return w.strip().lower()

def pick_vocab_words(text: str, max_words: int = 10) -> List[str]:
    # Vybereme kandidáty podobně jako dřív: delší slova, bez čísel, bez stop slov, bez čistě velkých zkratek
    words = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    cand = []
    for w in words:
        lw = normalize_word(w)
        if len(lw) < 7:
            continue
        if lw in STOPWORDS:
            continue
        if lw.isupper():
            continue
        cand.append(lw)
    # unikátně, v pořadí výskytu
    uniq = []
    for w in cand:
        if w not in uniq:
            uniq.append(w)
    return uniq[:max_words]

def explain_word(text_key: str, grade: int, word: str) -> Optional[str]:
    m = VOCAB_EXPLAIN.get(text_key, {}).get(grade, {})
    return m.get(word)

# -----------------------------
# 6) DOCX STYL
# -----------------------------

def set_doc_defaults(doc: Document, font_name: str = "Calibri", font_size: int = 11):
    style = doc.styles["Normal"]
    style.font.name = font_name
    style._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
    style.font.size = Pt(font_size)

def add_title(doc: Document, title: str):
    p = doc.add_paragraph(title)
    p.style = doc.styles["Title"]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

def add_h2(doc: Document, text: str):
    p = doc.add_paragraph(text)
    p.runs[0].bold = True
    p.runs[0].font.size = Pt(14)

def add_h3(doc: Document, text: str):
    p = doc.add_paragraph(text)
    p.runs[0].bold = True
    p.runs[0].font.size = Pt(12)

def add_spacer(doc: Document, lines: int = 1):
    for _ in range(lines):
        doc.add_paragraph("")

def add_table(doc: Document, data: List[List[str]], col_widths_cm: Optional[List[float]] = None):
    rows = len(data)
    cols = len(data[0])
    table = doc.add_table(rows=rows, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for r in range(rows):
        for c in range(cols):
            table.cell(r, c).text = str(data[r][c])
    if col_widths_cm and len(col_widths_cm) == cols:
        for c in range(cols):
            for r in range(rows):
                table.cell(r, c).width = Cm(col_widths_cm[c])
    return table

def add_answer_lines(doc: Document, n: int = 2):
    for _ in range(n):
        doc.add_paragraph("______________________________________________________________")

# -----------------------------
# 7) PYRAMIDA + KARTIČKY (černobílé siluety, bez internetu)
# -----------------------------

def draw_silhouette(animal: str, size: int = 240) -> Image.Image:
    """
    Jednoduché, rozpoznatelné černobílé siluety (piktogramy).
    Cílem je tisková použitelnost (černá výplň, bílý podklad).
    """
    img = Image.new("RGB", (size, size), "white")
    d = ImageDraw.Draw(img)

    def ellipse(x0, y0, x1, y1): d.ellipse([x0, y0, x1, y1], fill="black")
    def rect(x0, y0, x1, y1): d.rectangle([x0, y0, x1, y1], fill="black")
    def poly(points): d.polygon(points, fill="black")

    a = animal.lower()

    # společné proporce
    cx, cy = size//2, size//2

    if a == "komár":
        # tělo + křídla + sosák
        ellipse(cx-20, cy-10, cx+20, cy+30)
        poly([(cx-10, cy+5), (cx-90, cy-40), (cx-20, cy+25)])
        poly([(cx+10, cy+5), (cx+90, cy-40), (cx+20, cy+25)])
        rect(cx-2, cy-30, cx+2, cy-5)
        rect(cx-2, cy+30, cx+2, cy+70)
    elif a == "myš":
        ellipse(cx-55, cy-10, cx+55, cy+70)      # tělo
        ellipse(cx-65, cy-45, cx-20, cy)         # ucho 1
        ellipse(cx+20, cy-45, cx+65, cy)         # ucho 2
        rect(cx+55, cy+35, cx+110, cy+45)        # ocásek
        ellipse(cx-10, cy+40, cx+10, cy+60)      # čumák
    elif a == "sardinka":
        # rybka
        ellipse(cx-90, cy-20, cx+60, cy+60)
        poly([(cx+60, cy+20), (cx+110, cy-10), (cx+110, cy+50)])
        poly([(cx-20, cy), (cx+10, cy-40), (cx+25, cy)])
    elif a == "ježek":
        ellipse(cx-70, cy+10, cx+70, cy+90)
        # ostny
        for i in range(10):
            x = cx-75 + i*15
            poly([(x, cy+30), (x+10, cy-10), (x+20, cy+30)])
        ellipse(cx+40, cy+45, cx+75, cy+75)  # čumák
    elif a == "okoun":
        ellipse(cx-90, cy-10, cx+70, cy+70)
        poly([(cx+70, cy+30), (cx+120, cy), (cx+120, cy+60)])
        poly([(cx-30, cy+5), (cx, cy-60), (cx+30, cy+5)])  # hřbetní ploutev
    elif a == "liška":
        ellipse(cx-60, cy+20, cx+60, cy+110)  # tělo
        poly([(cx-60, cy+30), (cx-90, cy-10), (cx-30, cy+20)])  # ucho L
        poly([(cx+60, cy+30), (cx+90, cy-10), (cx+30, cy+20)])  # ucho P
        poly([(cx+20, cy+110), (cx+120, cy+140), (cx+40, cy+70)])  # ocas
    elif a == "tuleň":
        ellipse(cx-90, cy+30, cx+90, cy+140)
        ellipse(cx-30, cy-10, cx+50, cy+70)   # hlava
        poly([(cx-20, cy+140), (cx-80, cy+180), (cx-40, cy+120)])  # ploutev
    elif a == "lev":
        ellipse(cx-60, cy+40, cx+70, cy+140)  # tělo
        ellipse(cx-80, cy-10, cx+10, cy+70)   # hlava
        ellipse(cx-95, cy-25, cx+25, cy+90)   # hříva
        rect(cx+70, cy+90, cx+130, cy+100)    # ocas
        poly([(cx+130, cy+95), (cx+155, cy+80), (cx+155, cy+110)])
    elif a == "lední medvěd":
        ellipse(cx-90, cy+40, cx+90, cy+150)
        ellipse(cx-120, cy, cx-30, cy+80)     # hlava
        rect(cx+70, cy+90, cx+120, cy+110)    # čumák část
        ellipse(cx-110, cy-20, cx-80, cy+10)  # ucho
    elif a == "krokodýl":
        rect(cx-120, cy+70, cx+120, cy+110)   # tělo
        poly([(cx+120, cy+70), (cx+170, cy+90), (cx+120, cy+110)])  # tlama
        for i in range(8):
            poly([(cx-100+i*25, cy+70), (cx-90+i*25, cy+50), (cx-80+i*25, cy+70)])  # hřbet
        poly([(cx-120, cy+70), (cx-170, cy+90), (cx-120, cy+110)])  # ocas
    elif a == "slon":
        ellipse(cx-90, cy+40, cx+80, cy+160)
        ellipse(cx-120, cy, cx-20, cy+90)     # hlava
        poly([(cx-20, cy+40), (cx+40, cy+60), (cx-20, cy+80)])      # chobot základ
        rect(cx+20, cy+60, cx+60, cy+120)     # chobot dolů
        ellipse(cx-150, cy+20, cx-70, cy+100) # ucho
    elif a == "kosatka":
        ellipse(cx-110, cy+30, cx+110, cy+150)
        poly([(cx+110, cy+80), (cx+170, cy+50), (cx+170, cy+110)])  # ocas
        poly([(cx-10, cy+50), (cx+10, cy-40), (cx+30, cy+55)])      # ploutev hřbetní
    elif a.startswith("chameleon"):
        ellipse(cx-70, cy+60, cx+70, cy+140)
        ellipse(cx-110, cy+40, cx-40, cy+100)  # hlava
        poly([(cx+70, cy+110), (cx+120, cy+130), (cx+80, cy+80)])  # ocas
        # spirála ocasu (jednoduchá)
        d.arc([cx+70, cy+80, cx+150, cy+160], start=0, end=300, fill="black", width=8)
    else:
        # fallback
        ellipse(cx-70, cy-70, cx+70, cy+70)

    return img

def image_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def make_animal_card_images() -> Dict[str, bytes]:
    animals = KARETNI_ORDER_WEAK_TO_STRONG + [KARETNI_JOKER]
    out = {}
    for a in animals:
        img = draw_silhouette(a)
        out[a] = image_to_bytes(img)
    return out

def build_animal_cards_docx() -> bytes:
    # 3 sloupce, řádky podle počtu kartiček
    animals = KARETNI_ORDER_WEAK_TO_STRONG + [KARETNI_JOKER]
    imgs = make_animal_card_images()

    doc = Document()
    set_doc_defaults(doc, font_size=11)
    add_title(doc, "Kartičky zvířat – Karetní hra (pro vystřižení)")
    doc.add_paragraph("Vystřihni kartičky. Na každé je název zvířete a černobílá silueta.").alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_spacer(doc)

    cols = 3
    rows = math.ceil(len(animals) / cols)
    table = doc.add_table(rows=rows, cols=cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # rozměry kartičky
    # (Word to snese; případně si to učitel doladí tiskem)
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            cell = table.cell(r, c)
            cell_par = cell.paragraphs[0]
            cell_par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if idx >= len(animals):
                cell.text = ""
                continue
            name = animals[idx]
            # vlož obrázek
            img_bytes = imgs[name]
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name
            run = cell_par.add_run()
            run.add_picture(tmp_path, width=Cm(3.5))
            cell_par.add_run("\n")
            t = cell_par.add_run(name)
            t.bold = True
    # výstup
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def build_pyramid_template_docx() -> bytes:
    """
    Pyramida k lepení: 12 pater (slabý dole, silný nahoře) + box pro žolíka.
    """
    doc = Document()
    set_doc_defaults(doc, font_size=12)

    # na šířku
    section = doc.sections[0]
    section.orientation = WD_ORIENTATION.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)

    add_title(doc, "Pyramida síly zvířat – Karetní hra (šablona k lepení)")
    doc.add_paragraph("Nalep zvířata do pyramidy podle síly ve hře. Nejslabší je dole, nejsilnější nahoře.").alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_spacer(doc)

    # vytvoříme tabulku jako pyramidu: 12 řádků, 12 sloupců
    # každé patro bude mít 1 "slot" uprostřed, o patro níž 2 sloty atd.
    levels = len(KARETNI_ORDER_WEAK_TO_STRONG)
    cols = levels  # 12
    table = doc.add_table(rows=levels, cols=cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # popisky: nahoře nejsilnější (kosatka), dole nejslabší (komár)
    strong_to_weak = list(reversed(KARETNI_ORDER_WEAK_TO_STRONG))  # top -> bottom
    for row in range(levels):
        # kolik slotů v daném patře: 1 nahoře, roste směrem dolů
        slots = row + 1
        start = (cols - slots) // 2
        for c in range(cols):
            cell = table.cell(row, c)
            cell.text = ""
            # vyplň jen sloty
            if start <= c < start + slots:
                # necháme prázdné okénko k nalepení
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(" ")
            else:
                # "vymažeme" rámeček tím, že necháme prázdno – grid zůstane, ale je to v pohodě pro tisk
                pass

        # do prvního slotu v řádku dáme malý popisek úrovně (nenápadný)
        label_cell = table.cell(row, start)
        p = label_cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run("\n")
        r = p.add_run(f"({strong_to_weak[row]})")
        r.font.size = Pt(8)

    add_spacer(doc, 1)
    add_h3(doc, "Žolík")
    doc.add_paragraph("Chameleon je žolík – nenalepuj ho do pyramidy. Vlož ho sem:").alignment = WD_ALIGN_PARAGRAPH.LEFT
    joker_table = doc.add_table(rows=1, cols=1)
    joker_table.style = "Table Grid"
    joker_cell = joker_table.cell(0, 0)
    joker_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    joker_cell.paragraphs[0].add_run("CHAMELEON (ŽOLÍK)")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# -----------------------------
# 8) GENERÁTORY DOCX
# -----------------------------

def build_vocab_block(doc: Document, text_key: str, grade: int, base_text: str):
    add_h2(doc, "Slovníček")
    words = pick_vocab_words(base_text, max_words=10)
    # aby to nebyla prázdná sada, přidej ještě pár „typických“ z mapy (když algoritmus nevybere)
    fixed = list(VOCAB_EXPLAIN.get(text_key, {}).get(grade, {}).keys())
    for w in fixed:
        if w not in words:
            words.append(w)
        if len(words) >= 12:
            break

    # Výpis: slovo – vysvětlení (pokud máme) + linka pro poznámku žáka vždy
    for w in words[:12]:
        expl = explain_word(text_key, grade, w)
        p = doc.add_paragraph()
        run = p.add_run(f"• {w} = ")
        run.bold = True
        if expl:
            doc.add_paragraph(f"{expl}")
        # poznámka žáka (vždy)
        doc.add_paragraph("Poznámka / moje vysvětlení: _____________________________________________")

def build_drama_block(doc: Document, text_key: str):
    add_h2(doc, "Krátká dramatizace (zahájení hodiny)")
    for speaker, line in DRAMA[text_key]:
        p = doc.add_paragraph()
        p.add_run(f"{speaker}: ").bold = True
        p.add_run(line)

def build_questions_block(doc: Document, questions: List[Tuple[str, List[str], Optional[str]]], add_space: bool = True):
    add_h2(doc, "Otázky A/B/C")
    add_h3(doc, "A) Najdu informaci v textu")
    # první 2
    for i, (q, options, _) in enumerate(questions[:2], start=1):
        doc.add_paragraph(f"{i}. {q}").runs[0].bold = True
        for opt in options:
            doc.add_paragraph(opt)
        add_answer_lines(doc, 2)

    add_h3(doc, "B) Přemýšlím a vysvětluji")
    for i, (q, options, _) in enumerate(questions[2:4], start=3):
        doc.add_paragraph(f"{i}. {q}").runs[0].bold = True
        for opt in options:
            doc.add_paragraph(opt)
        add_answer_lines(doc, 3)

    add_h3(doc, "C) Můj názor (s oporou v textu)")
    if len(questions) >= 5:
        q, options, _ = questions[4]
        doc.add_paragraph(f"5. {q}").runs[0].bold = True
        for opt in options:
            doc.add_paragraph(opt)
        add_answer_lines(doc, 3)

def build_self_reflection(doc: Document):
    add_h2(doc, "Sebehodnocení")
    doc.add_paragraph("Označ: 😃 / 🙂 / 😐")
    doc.add_paragraph("• Rozuměl/a jsem textu:  😃  🙂  😐")
    doc.add_paragraph("• Uměl/a jsem najít informace:  😃  🙂  😐")
    doc.add_paragraph("• Uměl/a jsem vysvětlit vlastními slovy:  😃  🙂  😐")

def build_full_workbook(text_choice_key: str) -> bytes:
    meta = TEXT_META[text_choice_key]
    grade = meta["grade"]
    key = meta["key"]

    doc = Document()
    set_doc_defaults(doc, font_size=11)

    add_title(doc, f"EdRead AI – Pracovní list (PLNÁ VERZE) – {text_choice_key}")
    doc.add_paragraph("Jméno: ____________________________   Datum: _______________")

    add_spacer(doc)
    build_drama_block(doc, key)
    add_spacer(doc)

    add_h2(doc, "Text pro žáky (originální)")
    if key == "karetni_hra":
        doc.add_paragraph(KARETNI_HRA_TEXT_FULL)
        add_h3(doc, "Tabulka: Kdo přebije koho?")
        # uděláme 2sloupcovou tabulku: pořadí (silnější nahoře)
        data = [["Pořadí (od nejsilnějšího)", "Poznámka"]]
        for i, a in enumerate(KARETNI_PREBIJI_LIST_STRONG_TO_WEAK, start=1):
            data.append([f"{i}. {a}", ""])
        data.append(["Chameleon", "žolík – hraje se s jinou kartou"])
        add_table(doc, data, col_widths_cm=[9.0, 9.0])

        add_spacer(doc)
        add_h2(doc, "Aktivita: Pyramida síly (práce s pravidly)")
        doc.add_paragraph("1) Přečti si popis hry (výše).")
        doc.add_paragraph("2) Potom si vystřihni kartičky zvířat a nalep je do pyramidy podle síly ve hře.")
        doc.add_paragraph("Nejslabší zvíře je dole, nejsilnější nahoře. Chameleon je žolík (není v pyramidě).")

    elif key == "sladke_mameni":
        doc.add_paragraph(SLADKE_MAMENI_TEXT_FULL)
        add_spacer(doc)
        add_h3(doc, "Tabulky z průzkumu (Median 2010)")
        add_table(doc, SLADKE_MAMENI_TABLE_1, col_widths_cm=[12.0, 4.0])
        add_spacer(doc)
        add_table(doc, SLADKE_MAMENI_TABLE_2, col_widths_cm=[12.0, 4.0])
        add_spacer(doc)
        add_table(doc, SLADKE_MAMENI_TABLE_3, col_widths_cm=[12.0, 4.0])
        add_spacer(doc)
        add_table(doc, SLADKE_MAMENI_TABLE_4, col_widths_cm=[12.0, 4.0])
        add_spacer(doc)
        add_table(doc, SLADKE_MAMENI_TABLE_5, col_widths_cm=[12.0, 4.0])

    elif key == "venecky":
        doc.add_paragraph(VENECKY_TEXT_FULL)
        add_spacer(doc)
        add_h3(doc, "Tabulka: Kde jsme věnečky pořídili")
        add_table(doc, VENECKY_TABLE_KDE, col_widths_cm=[3.0, 15.0])
        add_spacer(doc)
        add_h3(doc, "Tabulka: Hodnocení")
        add_table(doc, VENECKY_TABLE_HODNOCENI, col_widths_cm=[2.0, 2.5, 2.2, 2.2, 2.2, 2.2, 4.2])

    add_spacer(doc)

    # Slovníček
    base_text = {
        "karetni_hra": KARETNI_HRA_TEXT_FULL,
        "sladke_mameni": SLADKE_MAMENI_TEXT_FULL,
        "venecky": VENECKY_TEXT_FULL
    }[key]
    build_vocab_block(doc, key, grade, base_text)
    add_spacer(doc)

    # Otázky
    questions = {
        "karetni_hra": KARETNI_HRA_QUESTIONS,
        "sladke_mameni": SLADKE_MAMENI_QUESTIONS,
        "venecky": VENECKY_QUESTIONS
    }[key]
    build_questions_block(doc, questions)
    add_spacer(doc)
    build_self_reflection(doc)

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def build_simple_workbook(text_choice_key: str) -> bytes:
    meta = TEXT_META[text_choice_key]
    grade = meta["grade"]
    key = meta["key"]

    doc = Document()
    set_doc_defaults(doc, font_size=12)

    add_title(doc, f"EdRead AI – Pracovní list (ZJEDNODUŠENÁ VERZE) – {text_choice_key}")
    doc.add_paragraph("Jméno: ____________________________   Datum: _______________")

    add_spacer(doc)
    build_drama_block(doc, key)
    add_spacer(doc)

    add_h2(doc, "Text pro žáky (zjednodušený)")
    if key == "karetni_hra":
        doc.add_paragraph(KARETNI_HRA_TEXT_SIMPLE)
    elif key == "sladke_mameni":
        doc.add_paragraph(SLADKE_MAMENI_TEXT_SIMPLE)
        add_spacer(doc)
        add_h3(doc, "Tabulky – zůstávají stejné (práce s daty)")
        add_table(doc, SLADKE_MAMENI_TABLE_1, col_widths_cm=[12.0, 4.0])
    elif key == "venecky":
        doc.add_paragraph(VENECKY_TEXT_SIMPLE)
        add_spacer(doc)
        add_h3(doc, "Tabulka – zůstává stejná (hodnocení)")
        add_table(doc, VENECKY_TABLE_HODNOCENI, col_widths_cm=[2.0, 2.5, 2.2, 2.2, 2.2, 2.2, 4.2])

    add_spacer(doc)
    base_text = {
        "karetni_hra": KARETNI_HRA_TEXT_SIMPLE,
        "sladke_mameni": SLADKE_MAMENI_TEXT_SIMPLE,
        "venecky": VENECKY_TEXT_SIMPLE
    }[key]
    build_vocab_block(doc, key, grade, base_text)
    add_spacer(doc)

    # zjednodušené otázky: vždy A/B/C, ale méně náročné formulace
    add_h2(doc, "Otázky")
    doc.add_paragraph("A) Najdi odpověď v textu.")
    add_answer_lines(doc, 2)
    doc.add_paragraph("B) Vysvětli vlastními slovy, co je v textu důležité.")
    add_answer_lines(doc, 3)
    doc.add_paragraph("C) Napiš svůj názor a opři se o text nebo tabulku.")
    add_answer_lines(doc, 3)

    add_spacer(doc)
    build_self_reflection(doc)

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def build_lmp_workbook(text_choice_key: str) -> bytes:
    meta = TEXT_META[text_choice_key]
    grade = meta["grade"]
    key = meta["key"]

    doc = Document()
    set_doc_defaults(doc, font_size=14)

    add_title(doc, f"EdRead AI – Pracovní list (LMP/SPU) – {text_choice_key}")
    doc.add_paragraph("Jméno: ____________________________   Datum: _______________")

    add_spacer(doc)
    add_h2(doc, "Motivace (scénka)")
    # kratší verze scénky (2–3 repliky)
    drama = DRAMA[key][:3]
    for speaker, line in drama:
        p = doc.add_paragraph()
        p.add_run(f"{speaker}: ").bold = True
        p.add_run(line)

    add_spacer(doc)
    add_h2(doc, "Text (krátký)")
    if key == "karetni_hra":
        doc.add_paragraph(KARETNI_HRA_TEXT_LMP)
    elif key == "sladke_mameni":
        doc.add_paragraph(SLADKE_MAMENI_TEXT_LMP)
        add_spacer(doc)
        add_h3(doc, "Tabulka (krátká práce s daty)")
        add_table(doc, SLADKE_MAMENI_TABLE_1, col_widths_cm=[12.0, 4.0])
    elif key == "venecky":
        doc.add_paragraph(VENECKY_TEXT_LMP)
        add_spacer(doc)
        add_h3(doc, "Tabulka (hodnocení)")
        add_table(doc, VENECKY_TABLE_HODNOCENI, col_widths_cm=[2.0, 2.5, 2.2, 2.2, 2.2, 2.2, 4.2])

    add_spacer(doc)
    add_h2(doc, "Slovníček (pomocná slova)")
    base_text = {
        "karetni_hra": KARETNI_HRA_TEXT_LMP,
        "sladke_mameni": SLADKE_MAMENI_TEXT_LMP,
        "venecky": VENECKY_TEXT_LMP
    }[key]
    build_vocab_block(doc, key, grade, base_text)

    add_spacer(doc)
    add_h2(doc, "Otázky (jednodušší)")
    doc.add_paragraph("1) Napiš, co je cílem / o čem text je.")
    add_answer_lines(doc, 3)
    doc.add_paragraph("2) Najdi v textu jednu důležitou informaci.")
    add_answer_lines(doc, 2)
    doc.add_paragraph("3) Co bylo pro tebe těžké? (můžeš napsat jedno slovo)")
    add_answer_lines(doc, 2)

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def build_methodology_doc(text_choice_key: str) -> bytes:
    meta = TEXT_META[text_choice_key]
    grade = meta["grade"]
    key = meta["key"]

    doc = Document()
    set_doc_defaults(doc, font_size=11)

    add_title(doc, f"EdRead AI – Metodický list pro učitele – {text_choice_key}")
    add_spacer(doc)

    add_h2(doc, "1. Charakteristika materiálu")
    doc.add_paragraph(f"Ročník: {grade}.")
    doc.add_paragraph("Materiál je součástí prototypu EdRead AI. Žáci nepracují přímo s AI; AI slouží učiteli k přípravě výukových materiálů (pracovní listy, slovníček, metodika).")

    add_spacer(doc)
    add_h2(doc, "2. Cíle a dovednosti čtenářské gramotnosti")
    doc.add_paragraph("Cíl: rozvoj porozumění textu, práce s informacemi, interpretace a základní kritické čtení.")
    doc.add_paragraph("Dílčí dovednosti: vyhledání explicitní informace; propojení textu s tabulkou/obrazovou oporou; formulace odpovědi vlastními slovy; rozlišení faktu a názoru (zejména 4.–5. ročník).")

    add_spacer(doc)
    add_h2(doc, "3. Vazba na RVP ZV (jazyk a jazyková komunikace – ČJL)")
    doc.add_paragraph("Nástroj je navržen tak, aby podporoval práci s textem v souladu s požadavky na porozumění, vyhledávání informací, interpretaci a formulaci odpovědí.")
    doc.add_paragraph("Pozn.: V praxi učitel doplní vazbu na ŠVP školy (konkrétní tematický celek, průřezová témata).")

    add_spacer(doc)
    add_h2(doc, "4. Doporučený průběh hodiny (45 min)")
    doc.add_paragraph("1) Motivace (3–5 min) – krátká dramatizace z listu.")
    doc.add_paragraph("2) Čtení textu (10–15 min) – tiché čtení / společné čtení po odstavcích.")
    doc.add_paragraph("3) Slovníček (5–8 min) – vysvětlit klíčová slova; žák doplní vlastní poznámky.")
    doc.add_paragraph("4) Otázky A/B/C (15–20 min) – A: vyhledání, B: interpretace, C: názor s oporou v textu.")
    doc.add_paragraph("5) Sebehodnocení (2–3 min).")

    if key == "karetni_hra":
        add_spacer(doc)
        add_h2(doc, "5. Specifika pro Karetní hru (3. třída)")
        doc.add_paragraph("Vizuální opora: pyramida síly zvířat (zvířata od nejslabšího po nejsilnější).")
        doc.add_paragraph("Doporučení: nejprve krátce vysvětlit, že pořadí síly je součást pravidel. Poté žáci lepí kartičky do pyramidy a teprve následně odpovídají na otázky.")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# -----------------------------
# 9) STREAMLIT UI – downloady nesmí mizet
# -----------------------------

def store_bytes(name: str, data: bytes):
    st.session_state[name] = data

def get_bytes(name: str) -> Optional[bytes]:
    return st.session_state.get(name)

def main():
    st.set_page_config(page_title=APP_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)

    st.divider()

    choice = st.selectbox("Vyber text / ročník:", list(TEXT_META.keys()))
    meta = TEXT_META[choice]
    key = meta["key"]

    st.info("Vygenerují se samostatné DOCX soubory (plný / zjednodušený / LMP-SPU / metodika). Pro Karetní hru navíc pyramida + kartičky.")

    if st.button("Vygenerovat materiály", type="primary"):
        full_doc = build_full_workbook(choice)
        simple_doc = build_simple_workbook(choice)
        lmp_doc = build_lmp_workbook(choice)
        meth_doc = build_methodology_doc(choice)

        store_bytes("full_doc", full_doc)
        store_bytes("simple_doc", simple_doc)
        store_bytes("lmp_doc", lmp_doc)
        store_bytes("meth_doc", meth_doc)

        # pro 3. třídu přidej pyramidy a kartičky
        if key == "karetni_hra":
            pyramid = build_pyramid_template_docx()
            cards = build_animal_cards_docx()
            store_bytes("pyramid_doc", pyramid)
            store_bytes("cards_doc", cards)
        else:
            store_bytes("pyramid_doc", None)
            store_bytes("cards_doc", None)

        st.success("Hotovo. Teď si stáhni soubory níže (tlačítka zůstanou aktivní).")

    st.divider()
    st.subheader("Stažení souborů")

    full_doc = get_bytes("full_doc")
    simple_doc = get_bytes("simple_doc")
    lmp_doc = get_bytes("lmp_doc")
    meth_doc = get_bytes("meth_doc")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Stáhnout pracovní list – PLNÝ (DOCX)",
            data=full_doc if full_doc else b"",
            file_name=f"pracovni_list_{key}_plny.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            disabled=(not full_doc),
            key="dl_full"
        )
        st.download_button(
            "⬇️ Stáhnout pracovní list – ZJEDNODUŠENÝ (DOCX)",
            data=simple_doc if simple_doc else b"",
            file_name=f"pracovni_list_{key}_zjednoduseny.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            disabled=(not simple_doc),
            key="dl_simple"
        )

    with col2:
        st.download_button(
            "⬇️ Stáhnout pracovní list – LMP/SPU (DOCX)",
            data=lmp_doc if lmp_doc else b"",
            file_name=f"pracovni_list_{key}_lmp_spu.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            disabled=(not lmp_doc),
            key="dl_lmp"
        )
        st.download_button(
            "⬇️ Stáhnout metodický list (DOCX)",
            data=meth_doc if meth_doc else b"",
            file_name=f"metodicky_list_{key}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            disabled=(not meth_doc),
            key="dl_meth"
        )

    # Extra pro Karetní hru
    if TEXT_META[choice]["key"] == "karetni_hra":
        pyramid = get_bytes("pyramid_doc")
        cards = get_bytes("cards_doc")
        st.divider()
        st.subheader("Karetní hra – doplňky pro 3. třídu")
        st.download_button(
            "⬇️ Stáhnout pyramidu (šablona k lepení) – DOCX",
            data=pyramid if pyramid else b"",
            file_name="karetni_hra_pyramida_sablona.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            disabled=(not pyramid),
            key="dl_pyramid"
        )
        st.download_button(
            "⬇️ Stáhnout kartičky zvířat (3 sloupce, siluety) – DOCX",
            data=cards if cards else b"",
            file_name="karetni_hra_karticky_zvirat.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            disabled=(not cards),
            key="dl_cards"
        )

if __name__ == "__main__":
    main()
