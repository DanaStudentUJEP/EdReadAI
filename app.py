import io
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import streamlit as st
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Cm, Pt


# ============================================================
# CONFIG
# ============================================================

ASSETS_DIR = "assets"
ASSET_TABLES = {
    "karetni_hra": os.path.join(ASSETS_DIR, "karetni_table.png"),
    "sladke_mameni": os.path.join(ASSETS_DIR, "sladke_table.png"),
    "venecky": os.path.join(ASSETS_DIR, "venecky_table.png"),
}

APP_TITLE = "EdRead AI – prototyp (diplomová práce)"
APP_SUB = "Generátor pracovních listů (plný / zjednodušený / LMP-SPU) + metodika"


# ============================================================
# HELPERS – Czech text utilities
# ============================================================

def normalize_spaces(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def safe_filename(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^\w\- ]+", "", name, flags=re.UNICODE)
    name = name.replace(" ", "_")
    return name or "edread_ai"

def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M")


# ============================================================
# DATA PACKS (predefined texts)
# ============================================================

@dataclass
class Pack:
    key: str
    title: str
    grade: int
    full_text: str
    simple_text: str
    lmp_text: str
    # Optional: special features
    has_pyramid: bool = False
    has_animal_cards: bool = False
    table_asset_key: Optional[str] = None


# NOTE: Zde nechávám texty tak, jak je běžně vkládáš do EdRead AI.
# Pokud chceš 100% shodu s originálem, vlož sem vždy celé originální znění (nebo jejich zjednodušené varianty).
# Tabulky řešíme přes assets/*.png (nejpřesnější).

KARETNI_FULL = normalize_spaces("""
NÁZEV ÚLOHY: KARETNÍ HRA\tJMÉNO:

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
""")

# Zjednodušené – musí stále obsahovat tabulku (vložíme obrázek tabulky stejně jako ve full)
KARETNI_SIMPLE = normalize_spaces("""
NÁZEV ÚLOHY: KARETNÍ HRA\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Ve hře rozdáte všechny karty. Cíl je zbavit se karet z ruky jako první.
Přebíjíš jen silnější kombinací.

Chameleon je žolík: hraje se vždy s jinou kartou, nikdy ne sám.
Když nechceš nebo nemůžeš přebít, řekneš „pass“.

(Podle pravidel hry Bláznivá ZOO, upraveno.)
""")

# LMP – jednoduchý jazyk, ale tabulka musí být také
KARETNI_LMP = normalize_spaces("""
NÁZEV ÚLOHY: KARETNÍ HRA\tJMÉNO:

Cíl hry: být první bez karet.
Když máš silnější kartu, přebiješ soupeře.
Když nechceš hrát, řekneš „pass“.

Chameleon je žolík. Musí být vždy s jinou kartou.
""")

SLADKE_FULL = normalize_spaces("""
NÁZEV ÚLOHY: SLADKÉ MÁMENÍ\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

(Text + tabulka z průzkumu – tabulku vložíme jako obrázek přes assets/sladke_table.png.)
""")

SLADKE_SIMPLE = normalize_spaces("""
NÁZEV ÚLOHY: SLADKÉ MÁMENÍ\tJMÉNO:

Budeme číst článek o sladkostech a o tom, proč lidé hledají „lehčí“ (nízkokalorické) výrobky.
V textu jsou i výsledky průzkumu (tabulka).
""")

SLADKE_LMP = normalize_spaces("""
NÁZEV ÚLOHY: SLADKÉ MÁMENÍ\tJMÉNO:

Text je o sladkostech a o tom, co lidé kupují.
V tabulce jsou čísla z průzkumu.
""")

VENECKY_FULL = normalize_spaces("""
NÁZEV ÚLOHY: VĚNEČKY\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

(Text + tabulka hodnocení – tabulku vložíme jako obrázek přes assets/venecky_table.png.)
""")

VENECKY_SIMPLE = normalize_spaces("""
NÁZEV ÚLOHY: VĚNEČKY\tJMÉNO:

Čteme text o tom, jak odbornice hodnotila věnečky v několika cukrárnách.
V textu je i tabulka se známkami.
""")

VENECKY_LMP = normalize_spaces("""
NÁZEV ÚLOHY: VĚNEČKY\tJMÉNO:

Text je o věnečcích a o tom, který byl nejlepší.
V tabulce jsou známky.
""")

PACKS: Dict[str, Pack] = {
    "karetni_hra": Pack(
        key="karetni_hra",
        title="Karetní hra",
        grade=3,
        full_text=KARETNI_FULL,
        simple_text=KARETNI_SIMPLE,
        lmp_text=KARETNI_LMP,
        has_pyramid=True,
        has_animal_cards=True,
        table_asset_key="karetni_hra",
    ),
    "sladke_mameni": Pack(
        key="sladke_mameni",
        title="Sladké mámení",
        grade=5,
        full_text=SLADKE_FULL,
        simple_text=SLADKE_SIMPLE,
        lmp_text=SLADKE_LMP,
        table_asset_key="sladke_mameni",
    ),
    "venecky": Pack(
        key="venecky",
        title="Věnečky",
        grade=4,
        full_text=VENECKY_FULL,
        simple_text=VENECKY_SIMPLE,
        lmp_text=VENECKY_LMP,
        table_asset_key="venecky",
    ),
}


# ============================================================
# CONTENT GENERATORS
# ============================================================

ANIMALS = [
    ("🦟", "komár"),
    ("🐭", "myš"),
    ("🐟", "sardinka"),
    ("🦔", "ježek"),
    ("🐟", "okoun"),
    ("🦊", "liška"),
    ("🦭", "tuleň"),
    ("🦁", "lev"),
    ("🐻‍❄️", "lední medvěd"),
    ("🐊", "krokodýl"),
    ("🐘", "slon"),
    ("🐬", "kosatka"),
    ("🦎", "chameleon (žolík)"),
]

# Logická pyramida (shora nejsilnější → dolů nejslabší) podle pořadí v tabulce (kosatka nejsilnější, komár nejslabší).
PYRAMID_ORDER = [
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
    "chameleon (žolík)",  # žolík – dáš klidně mimo, ale pokud chceš v pyramidě, nechávám jako poslední
]

def set_default_style(doc: Document):
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

def add_heading(doc: Document, text: str, level: int = 1):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14 if level == 1 else 12)
    return p

def add_subheading(doc: Document, text: str):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(12)
    return p

def add_par(doc: Document, text: str):
    return doc.add_paragraph(text)

def insert_table_image(doc: Document, asset_path: str, width_cm: float = 16.0) -> bool:
    if not asset_path or not os.path.exists(asset_path):
        return False
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(asset_path, width=Cm(width_cm))
    return True


# ------------------------
# Pyramid and animal cards
# ------------------------

def add_pyramid_column(doc: Document):
    """
    Sloupcová pyramida (13 řádků). Okénka jsou velká, aby se kartičky vešly.
    """
    add_subheading(doc, "Zvířecí „pyramida“ síly (lepení)")
    add_par(doc, "Vystřihni kartičky a nalep je do okýnek. Nahoře je nejsilnější zvíře, dole nejslabší.")

    # 1 sloupec, 13 řádků
    rows = len(PYRAMID_ORDER)
    table = doc.add_table(rows=rows + 2, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Nahoře/dole popisek
    table.cell(0, 0).text = "NAHOŘE = NEJSILNĚJŠÍ"
    table.cell(0, 0).paragraphs[0].runs[0].bold = True

    # Okénka
    for i in range(1, rows + 1):
        cell = table.cell(i, 0)
        cell.text = ""
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        # bezpečné nastavení výšky řádku (bez _emu)
        row = table.rows[i]
        row.height = Cm(1.6)           # okénko výška
        row.height_rule = 2            # EXACTLY (interně)
        # a šířka buňky
        cell.width = Cm(8.5)

    table.cell(rows + 1, 0).text = "DOLE = NEJSLABŠÍ"
    table.cell(rows + 1, 0).paragraphs[0].runs[0].bold = True


def add_animal_cards(doc: Document):
    """
    Kartičky na stříhání – 3 sloupce, emoji + český název.
    """
    add_subheading(doc, "Kartičky zvířat (na stříhání)")
    add_par(doc, "Vystřihni kartičky. (3 sloupce)")

    cols = 3
    rows = (len(ANIMALS) + cols - 1) // cols
    table = doc.add_table(rows=rows, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.width = Cm(6.0)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if idx < len(ANIMALS):
                emoji, name = ANIMALS[idx]
                run1 = p.add_run(f"{emoji}\n")
                run1.font.size = Pt(22)
                run2 = p.add_run(name)
                run2.bold = True
                run2.font.size = Pt(12)
            else:
                p.add_run("")
            idx += 1

        # řádek výška, aby kartičky byly “rychlé” na jednu A4 (typicky vyjde)
        table.rows[r].height = Cm(3.2)
        table.rows[r].height_rule = 2


# ------------------------
# Dramatizations
# ------------------------

def dramatization_intro_for_students(grade: int) -> str:
    if grade <= 3:
        return "Za chvíli si zahrajeme krátkou scénku. Pomůže nám to pochopit pravidla dřív, než začneme číst."
    if grade == 4:
        return "Zahrajeme krátkou scénku, aby se nám lépe četlo a rozuměli jsme tomu, o čem text je."
    return "Na začátku uděláme krátkou scénku, která nás naladí na téma textu."

def dramatization_scene(pack_key: str) -> List[str]:
    if pack_key == "karetni_hra":
        # bez věty učitel/ka s plánem – ta patří do metodiky, ne do PL
        return [
            "Žák A: „Zahraju komára!“",
            "Žák B: „Já dám myš. Přebiju tě?“",
            "Žák C: „Co když zahraju dvě stejné karty?“",
            "Žák D: „Mám chameleona – můžu ho dát samotného?“",
            "Společně: „Najdeme v textu pravidlo, kdo koho přebíjí a jak se hraje žolík.“",
        ]
    if pack_key == "sladke_mameni":
        return [
            "Žákyně A: „Já mám sladké ráda, ale proč někdo chce light čokoládu?“",
            "Žák B: „V textu je napsáno něco o obezitě…“",
            "Žákyně C: „A tabulka ukazuje, co lidé nejčastěji jedí.“",
            "Společně: „Přečteme text a zjistíme, proč se hledají nízkokalorické sladkosti.“",
        ]
    if pack_key == "venecky":
        return [
            "Žák A: „Já myslím, že nejlepší je ten nejdražší.“",
            "Žákyně B: „To nemusí být pravda. Podíváme se na tabulku se známkami.“",
            "Žák C: „A v textu je, co hodnotitelka chválí a co kritizuje.“",
            "Společně: „Najdeme v textu a tabulce důkazy a odpovíme na otázky.“",
        ]
    return [
        "Společně: „Krátká scénka a pak čtení textu.“",
    ]


# ------------------------
# Questions A/B/C – age-adapted but stable and correct
# ------------------------

def build_questions(pack_key: str, grade: int) -> List[Tuple[str, str]]:
    """
    Vrací seznam (nadpis sekce, text otázky s linkami).
    Držíme stabilní, bez “halucinací”.
    """
    if pack_key == "karetni_hra":
        return [
            ("A) Porozumění (najdi v textu)", 
             "1) Co je cílem hry? (1 věta)\n______________________________________________\n\n"
             "2) Co znamená ve hře slovo „pass“?\n______________________________________________\n"),
            ("B) Přemýšlení (vysvětli)", 
             "3) Proč se chameleon (žolík) nesmí hrát samostatně?\n"
             "______________________________________________\n______________________________________________\n"),
            ("C) Můj názor", 
             "4) Co bys poradil/a spolužákovi, aby ve hře vyhrál? (1–2 věty)\n"
             "______________________________________________\n______________________________________________\n"),
        ]

    if pack_key == "sladke_mameni":
        return [
            ("A) Porozumění (najdi v textu / tabulce)",
             "1) Proč se ve světě zvyšuje poptávka po nízkokalorických sladkostech?\n"
             "______________________________________________\n______________________________________________\n\n"
             "2) Najdi v tabulce jednu sladkost (tyčinku nebo bonboniéru) a napiš, kolik procent lidí ji uvedlo.\n"
             "Sladkost: ____________________  Procenta: ________ %\n"),
            ("B) Přemýšlení (vysvětli)",
             "3) Co znamená v textu přirovnání „novodobí alchymisté hledají recept na zlato“?\n"
             "______________________________________________\n______________________________________________\n"),
            ("C) Můj názor",
             "4) Myslíš, že je dobré mít na obalu velkým písmem energii (kalorie)? Proč ano/ne?\n"
             "______________________________________________\n______________________________________________\n"),
        ]

    if pack_key == "venecky":
        return [
            ("A) Porozumění (najdi v textu / tabulce)",
             "1) Který věneček byl hodnocen nejlépe?\n"
             "______________________________________________\n\n"
             "2) Který podnik dopadl v testu nejlépe?\n"
             "______________________________________________\n"),
            ("B) Přemýšlení (pracuj s tabulkou)",
             "3) Který věneček byl nejdražší? Kolik stál a kde byl koupen?\n"
             "Věneček č.: ____  Cena: ______ Kč  Kde: __________________________\n\n"
             "4) Myslíš, že cena odpovídala kvalitě? Zakroužkuj a zdůvodni.\n"
             "ANO / NE\n"
             "Zdůvodnění: ______________________________________________\n"
             "__________________________________________________________\n"),
            ("C) Můj názor",
             "5) Co je podle tebe při hodnocení zákusku nejdůležitější? (1–2 věty)\n"
             "______________________________________________\n______________________________________________\n"),
        ]

    # generic
    if grade <= 3:
        return [
            ("A) Najdi v textu", "1) Napiš jednu důležitou informaci z textu.\n______________________________________________\n"),
            ("B) Vysvětli", "2) Vysvětli vlastními slovy, o čem text je.\n______________________________________________\n"),
            ("C) Můj názor", "3) Co se ti na textu líbilo nebo nelíbilo?\n______________________________________________\n"),
        ]
    return [
        ("A) Najdi v textu", "1) Najdi v textu hlavní myšlenku.\n______________________________________________\n"),
        ("B) Přemýšlení", "2) Najdi jednu větu, která je názor, a jednu, která je fakt.\nNÁZOR: ____________________\nFAKT: ____________________\n"),
        ("C) Můj názor", "3) Souhlasíš s autorem? Proč?\n______________________________________________\n"),
    ]


# ------------------------
# Vocabulary – robust explanations + student note line
# ------------------------

def pick_vocab_words(text: str, max_words: int = 12) -> List[str]:
    """
    Vybere kandidáty podobně jako dřív (delší slova), ale filtruje běžné/nevhodné.
    """
    words = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    words = [w.strip().lower() for w in words]
    stop = {
        "který", "která", "které", "kterého", "kterou",
        "protože", "aby", "nebo", "jako", "také", "tuhle", "tento",
        "správným", "řešením", "získat", "maximálně", "název", "úlohy", "jmÉno".lower(),
        "text", "tabulka", "otázka", "otázky"
    }
    uniq = []
    for w in words:
        if len(w) < 7:
            continue
        if w in stop:
            continue
        if w not in uniq:
            uniq.append(w)
    return uniq[:max_words]

def explain_word_simple(word: str, grade: int) -> Optional[str]:
    """
    Ručně připravené vysvětlení pro často se vyskytující slova.
    Když není, vrátí None (a v PL bude jen linka pro žáka).
    """
    base = {
        "rovnoměrně": "stejně pro všechny",
        "samostatně": "sám / bez jiné věci",
        "kombinaci": "spojení více věcí dohromady",
        "přebít": "dát silnější kartu (porazit předchozí)",
        "vynese": "položí kartu na stůl",
        "upravene": "trochu změněné",
        "upraveno": "trochu změněno",
        "absenci": "to, že něco chybí",
        "chemický": "umělý (ne z přírodních surovin)",
        "chemickou": "umělou (ne přírodní)",
        "korpus": "spodní těsto zákusku",
        "pudink": "sladký krém z mléka",
        "margarín": "tuk podobný máslu",
        "odpalované": "druh těsta, které se peče do kroužků (věnečků)",
        "recepturu": "přesný postup a složení",
        "dodrželi": "udělali přesně tak, jak se má",
        "napravit": "opravit to, aby to bylo lepší",
        "zestárlá": "už není čerstvá",
        "vyráběného": "udělaného (vyrobeného)",
        "jedinému": "jen jednomu",
        "podnikům": "firmám / cukrárnám / pekárnám",
    }
    w = word.lower()
    if w in base:
        return base[w]

    # drobná úprava pro děti
    if grade <= 3:
        # pro 3. třídu raději vysvětluj jen když je to opravdu vhodné
        return base.get(w)

    return base.get(w)


def add_vocab_section(doc: Document, text_source: str, grade: int, forced_words: Optional[List[str]] = None):
    """
    Slovníček vždy na konec pracovního listu.
    - Pokud existuje vysvětlení: uvede se.
    - Pokud ne: jen prázdná linka (bez nevhodných vět).
    + vždy linka pro poznámku žáka.
    """
    doc.add_page_break()
    add_subheading(doc, "Slovníček (na konec pracovního listu)")

    words = forced_words if forced_words else pick_vocab_words(text_source, max_words=12)

    # když je výběr slabý, doplň pár bezpečných pojmů (jen u presetů)
    if len(words) < 10:
        for extra in ["rovnoměrně", "samostatně", "kombinaci", "dodrželi", "napravit", "zestárlá"]:
            if extra not in words:
                words.append(extra)
            if len(words) >= 12:
                break

    for w in words:
        expl = explain_word_simple(w, grade)
        if expl:
            add_par(doc, f"• {w} = {expl}")
        else:
            add_par(doc, f"• {w} = ______________________________")
        add_par(doc, "Poznámka žáka/žákyně: _______________________________")


# ============================================================
# DOC BUILDERS
# ============================================================

def build_student_doc(pack: Pack, variant: str, custom_text: Optional[str] = None, custom_grade: Optional[int] = None) -> bytes:
    """
    variant: 'full' | 'simple' | 'lmp'
    """
    doc = Document()
    set_default_style(doc)

    grade = custom_grade if custom_grade else pack.grade

    # Header
    add_heading(doc, f"{pack.title} ({grade}. třída) — verze: {variant.upper()}")
    doc.add_paragraph("")

    # Úvod + dramatizace
    add_subheading(doc, "Úvod (co budeme dělat)")
    add_par(doc, dramatization_intro_for_students(grade))

    add_subheading(doc, "Dramatizace (zahájení hodiny – krátká scénka)")
    for line in dramatization_scene(pack.key):
        doc.add_paragraph(line, style="List Bullet")

    doc.add_paragraph("")

    # Text k přečtení (každá verze má svůj text!)
    add_subheading(doc, "Text k přečtení")

    if custom_text:
        text_for_version = normalize_spaces(custom_text)
    else:
        if variant == "full":
            text_for_version = pack.full_text
        elif variant == "simple":
            text_for_version = pack.simple_text
        else:
            text_for_version = pack.lmp_text

    for para in text_for_version.split("\n\n"):
        doc.add_paragraph(para)

    doc.add_paragraph("")

    # Tabulka – musí být ve všech verzích, pokud je to preset s tabulkou
    if pack.table_asset_key:
        add_subheading(doc, "Tabulka (z výchozího textu)")
        ok = insert_table_image(doc, ASSET_TABLES.get(pack.table_asset_key, ""), width_cm=16.0)
        if not ok:
            # Fallback – upozornění do dokumentu (bez „chyby“, ale jasné)
            add_par(doc, "⚠ Tabulka nebyla nalezena jako obrázek v assets/. Přidej prosím správný PNG soubor pro 100% shodu s PDF.")

    # Karetní hra: pyramida + kartičky (ve všech verzích, protože práce s tabulkou/oporou je klíčová)
    if pack.has_pyramid:
        doc.add_page_break()
        add_pyramid_column(doc)

    if pack.has_animal_cards:
        doc.add_page_break()
        add_animal_cards(doc)

    # Otázky
    doc.add_page_break()
    add_subheading(doc, "Otázky A/B/C")
    for section, qtext in build_questions(pack.key, grade):
        add_subheading(doc, section)
        doc.add_paragraph(qtext)

    # Slovníček vždy na konec
    add_vocab_section(doc, text_for_version, grade)

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def build_teacher_doc(pack: Pack, custom_mode: bool = False, custom_grade: Optional[int] = None) -> bytes:
    doc = Document()
    set_default_style(doc)

    grade = custom_grade if custom_grade else pack.grade

    add_heading(doc, f"Metodický list – {pack.title} ({grade}. třída)")
    doc.add_paragraph("")

    add_subheading(doc, "Doporučený průběh hodiny (45 min)")
    doc.add_paragraph("1) Dramatizace (5–7 min): krátká scénka pro naladění a motivaci.", style="List Number")
    doc.add_paragraph("2) Slovníček (5 min): učitel vede žáky na konec pracovního listu a projde klíčová slova.", style="List Number")
    doc.add_paragraph("   Žáci si mohou dopsat vlastní poznámky, pokud vysvětlení nestačí.", style="List Bullet")
    doc.add_paragraph("3) Čtení textu (10–15 min): návrat do textu, společné / tiché čtení, práce s tabulkou.", style="List Number")
    doc.add_paragraph("4) Otázky A/B/C (15 min): A = vyhledání informace, B = vysvětlení/interpretace, C = vlastní názor.", style="List Number")
    doc.add_paragraph("5) Krátká reflexe (3 min): co bylo těžké, co pomohlo.", style="List Number")

    doc.add_paragraph("")
    add_subheading(doc, "Rozdíly mezi verzemi (pro rozhodnutí učitele)")
    doc.add_paragraph("PLNÝ pracovní list:", style="List Bullet")
    doc.add_paragraph("– plné znění textu (originál / plná verze), tabulka uvnitř textu, plná sada otázek.", style="List Bullet")
    doc.add_paragraph("ZJEDNODUŠENÝ pracovní list:", style="List Bullet")
    doc.add_paragraph("– zjednodušený text, ale tabulka zůstává (je nutná pro odpovědi). Otázky jsou stejného typu, jazyk je jednodušší.", style="List Bullet")
    doc.add_paragraph("LMP/SPU pracovní list:", style="List Bullet")
    doc.add_paragraph("– nejjednodušší jazyk, kratší věty, více prostoru pro odpovědi. Tabulka zůstává (opora).", style="List Bullet")

    doc.add_paragraph("")
    add_subheading(doc, "Poznámka k etice a bezpečnosti (AI v 1. stupni)")
    doc.add_paragraph("Žáci přímo nekomunikují s AI. AI slouží učiteli jako nástroj pro tvorbu materiálů (pracovní listy, metodika), "
                      "čímž se minimalizují etická rizika práce dětí s generativní AI.")

    doc.add_paragraph("")
    add_subheading(doc, "RVP ZV – napojení na čtenářskou gramotnost (obecně)")
    doc.add_paragraph("Materiály podporují porozumění textu, vyhledávání informací, interpretaci a formulaci vlastního názoru. "
                      "U práce s tabulkou a vizuální oporou dochází k propojování souvislého a nesouvislého textu.")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


# ============================================================
# STREAMLIT UI
# ============================================================

def init_state():
    if "outputs" not in st.session_state:
        st.session_state.outputs = {}  # key -> (filename, bytes)
    if "last_pack" not in st.session_state:
        st.session_state.last_pack = None

def persist_output(key: str, filename: str, data: bytes):
    st.session_state.outputs[key] = (filename, data)

def render_download_buttons():
    if not st.session_state.outputs:
        return
    st.subheader("Stažení vygenerovaných souborů")
    for k, (fname, data) in st.session_state.outputs.items():
        st.download_button(
            label=f"⬇️ Stáhnout: {fname}",
            data=data,
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"dl_{k}_{fname}",
        )

def main():
    st.set_page_config(page_title=APP_TITLE, layout="centered")
    init_state()

    st.title(APP_TITLE)
    st.caption(APP_SUB)

    mode = st.radio(
        "Co chceš generovat?",
        ["Předpřipravené texty (Karetní hra / Věnečky / Sladké mámení)", "Vlastní text"],
        index=0,
    )

    custom_text = None
    custom_grade = None

    if mode.startswith("Předpřipravené"):
        pack_key = st.selectbox("Vyber text", list(PACKS.keys()), format_func=lambda k: PACKS[k].title)
        pack = PACKS[pack_key]
        st.info(f"Vybráno: **{pack.title}** (doporučený ročník: {pack.grade}.)")
    else:
        pack_key = "custom"
        pack = Pack(
            key="custom",
            title="Vlastní text",
            grade=3,
            full_text="",
            simple_text="",
            lmp_text="",
            table_asset_key=None,
        )
        custom_grade = st.selectbox("Pro jaký ročník?", [1,2,3,4,5], index=2)
        custom_text = st.text_area("Vlož text", height=260, placeholder="Sem vlož libovolný text...")
        st.warning("U vlastního textu se nevkládají speciální tabulky/pyramida (to je jen pro předpřipravené 3 texty).")

    st.divider()

    # Generování
    if st.button("🛠️ Vygenerovat dokumenty", type="primary"):
        st.session_state.outputs = {}  # přegenerovat čistě

        if mode.startswith("Předpřipravené"):
            base = safe_filename(PACKS[pack_key].title)
            grade = PACKS[pack_key].grade
        else:
            base = "vlastni_text"
            grade = custom_grade

        # Student docs
        pl_full = build_student_doc(pack, "full", custom_text=custom_text, custom_grade=custom_grade)
        pl_simple = build_student_doc(pack, "simple", custom_text=custom_text, custom_grade=custom_grade)
        pl_lmp = build_student_doc(pack, "lmp", custom_text=custom_text, custom_grade=custom_grade)

        # Teacher
        metodika = build_teacher_doc(pack, custom_mode=bool(custom_text), custom_grade=custom_grade)

        stamp = now_stamp()
        persist_output("pl_full", f"pracovni_list_{base}_plny_{stamp}.docx", pl_full)
        persist_output("pl_simple", f"pracovni_list_{base}_zjednoduseny_{stamp}.docx", pl_simple)
        persist_output("pl_lmp", f"pracovni_list_{base}_LMP_SPU_{stamp}.docx", pl_lmp)
        persist_output("metodika", f"metodicky_list_{base}_{stamp}.docx", metodika)

        st.success("Hotovo. Dokumenty jsou připravené ke stažení níže.")

    # Download buttons must persist across reruns
    render_download_buttons()

    st.divider()
    st.caption(
        "Pozn.: Pro 100% přesné tabulky jako v PDF vlož do složky assets/ obrázky: "
        "karetni_table.png, sladke_table.png, venecky_table.png."
    )


if __name__ == "__main__":
    main()
