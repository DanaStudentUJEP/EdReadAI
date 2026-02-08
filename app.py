# app.py
# EdRead AI – prototyp pro DP (Streamlit + python-docx)
# Autor: Dana Křivakovská (koncept), implementace: ChatGPT
# Pozn.: Tabulky jsou vkládány jako obrázek z PDF (100% přesnost dat).

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import streamlit as st

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


# =========================
# 1) KONFIG / DATA
# =========================

ASSETS = {
    "karetni_table": "assets/karetni_table.png",
    "sladke_table": "assets/sladke_table.png",
    "venecky_table": "assets/venecky_table.png",
}

# Zvířata pro Karetní hru – český název + slug + emoji (použijeme emoji jako „ikonku“)
ANIMALS: List[Tuple[str, str, str]] = [
    ("komár", "komar", "🦟"),
    ("myš", "mys", "🐭"),
    ("sardinka", "sardinka", "🐟"),
    ("ježek", "jezek", "🦔"),
    ("okoun", "okoun", "🐟"),
    ("liška", "liska", "🦊"),
    ("tuleň", "tulen", "🦭"),
    ("lev", "lev", "🦁"),
    ("lední medvěd", "ledni_medved", "🐻‍❄️"),
    ("krokodýl", "krokodyl", "🐊"),
    ("slon", "slon", "🐘"),
    ("kosatka", "kosatka", "🐬"),
    ("chameleon (žolík)", "chameleon_zolik", "🦎"),
]

# Logika pyramidy = řazení nejslabší -> nejsilnější (nahoře nejsilnější)
# V textu je příklad: kosatku přebijí jen 2 kosatky, krokodýla přebije slon atd.
# Zjednodušená pyramida pro podporu porozumění pravidlům:
# nejslabší dole, nejsilnější nahoře:
PYRAMID_ORDER_WEAK_TO_STRONG = [
    "komár",
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
    "myš",  # ve hře „přebíjí“ některé velké – děti to řeší přes tabulku
]
# Chameleon je žolík → nepatří do pyramidy jako síla (řeší se pravidlem)
# Pokud chceš myš držet podle tabulky jinak, můžeš pořadí upravit ručně.


# =========================
# 2) PŘEDNASTAVENÉ TEXTY (PLNÉ)
#    (zde jsou jen zkrácené ukázky – DOPLŇ si plné texty,
#     nebo vlož text přes „Vlastní text“)
# =========================

PRESETS = {
    "Karetní hra (3. třída)": {
        "grade": 3,
        "type": "navod",
        "title": "KARETNÍ HRA",
        "table_asset_key": "karetni_table",
        "full_text": (
            "NÁZEV ÚLOHY: KARETNÍ HRA\n\n"
            "1. Herní materiál\n"
            "60 karet živočichů: 4 komáři, 1 chameleon (žolík), 5 karet od každého z dalších 11 druhů živočichů.\n\n"
            "2. Popis hry\n"
            "Všechny karty se rozdají mezi hráče. Hráči se snaží vynášet karty podle pravidel tak, aby se co nejdříve zbavili všech karet v ruce.\n"
            "Zahrát lze vždy pouze silnější kombinaci živočichů, než zahrál hráč před vámi.\n\n"
            "3. Pořadí karet\n"
            "Na každé kartě je zobrazen jeden živočich. V rámečku jsou namalováni živočichové, kteří danou kartu přebíjí.\n"
            "(V textu je tabulka „Kdo přebije koho?“ – viz vložený obrázek.)\n\n"
            "Chameleon má funkci žolíka. Lze ho zahrát spolu s jinou kartou a počítá se jako požadovaný druh.\n"
            "Nelze ho hrát samostatně.\n\n"
            "4. Průběh hry\n"
            "Karty zamíchejte a rozdejte rovnoměrně. Hráč po levé ruce rozdávajícího začíná...\n"
        ),
    },
    "Sladké mámení (5. třída)": {
        "grade": 5,
        "type": "argumentace+tabulka",
        "title": "SLADKÉ MÁMENÍ",
        "table_asset_key": "sladke_table",
        "full_text": (
            "NÁZEV ÚLOHY: SLADKÉ MÁMENÍ\n\n"
            "Češi a čokoláda (výsledky průzkumu agentury Median v roce 2010 – tabulka je vložena jako obrázek).\n\n"
            "Euroamerickou civilizaci sužuje novodobá epidemie: obezita a s ní spojené choroby metabolismu, srdce a cév...\n"
            "Text pokračuje...\n"
        ),
    },
    "Věnečky (4. třída)": {
        "grade": 4,
        "type": "reportáž+tabulka",
        "title": "VĚNEČKY",
        "table_asset_key": "venecky_table",
        "full_text": (
            "NÁZEV ÚLOHY: VĚNEČKY\n\n"
            "Reportáž o hodnocení věnečků. Součástí je tabulka s cenou, vzhledem, korpusem, surovinami a celkovou známkou.\n"
            "(Tabulka je vložena jako obrázek.)\n\n"
            "Věneček č. 2...\n"
            "Věneček č. 3...\n"
            "Věneček č. 4...\n"
            "Věneček č. 5...\n"
            "Text pokračuje...\n"
        ),
    },
}


# =========================
# 3) POMOCNÉ FUNKCE – DOCX STYL
# =========================

def set_doc_style(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

def add_h1(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(16)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

def add_h2(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(13)

def add_note(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    p.runs[0].italic = True

def add_spacer(doc: Document, cm: float = 0.2) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(int(cm * 28.35))  # approx

def add_table_image(doc: Document, asset_path: str, width_cm: float = 16.0) -> None:
    try:
        doc.add_picture(asset_path, width=Cm(width_cm))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    except Exception:
        add_note(doc, f"(Tabulka nebyla nalezena: {asset_path}. Zkontroluj složku assets/.)")

def add_line(doc: Document) -> None:
    doc.add_paragraph("______________________________________________________________")

def add_lines(doc: Document, count: int = 2) -> None:
    for _ in range(count):
        add_line(doc)

def doc_to_bytes(doc: Document) -> bytes:
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


# =========================
# 4) TEXT – ZJEDNODUŠENÍ / LMP (PRAGMATICKÉ, BEZ AI)
# =========================

def simplify_text(text: str, grade: int) -> str:
    """
    Jednoduché zjednodušení bez AI:
    - zkrátí dlouhé věty,
    - odstraní některé vsuvky,
    - zjednoduší interpunkci.
    """
    t = text.strip()
    # odstraň dvojité mezery
    t = re.sub(r"[ \t]+", " ", t)
    # zkracuj extrémně dlouhé věty
    sentences = re.split(r"(?<=[\.\!\?])\s+", t)
    out = []
    max_len = 160 if grade >= 5 else 120
    for s in sentences:
        s = s.strip()
        if len(s) > max_len:
            # rozsekni podle čárek
            parts = [p.strip() for p in s.split(",") if p.strip()]
            if parts:
                out.extend([parts[0] + "."] + [p + "." for p in parts[1:3]])
            else:
                out.append(s)
        else:
            out.append(s)
    return "\n".join(out).strip()

def lmp_text(text: str, grade: int) -> str:
    """
    LMP/SPU verze – kratší, čitelnější:
    - kratší odstavce,
    - jednoduché věty,
    - více řádků.
    """
    t = simplify_text(text, grade)
    # rozděl po odstavcích a udělej více řádků
    t = re.sub(r"\n{3,}", "\n\n", t)
    # lehké „odlehčení“
    return t


# =========================
# 5) SLOVNÍČEK – VÝBĚR SLOV + VYSVĚTLENÍ
# =========================

def pick_vocab_words(text: str, max_words: int = 12) -> List[str]:
    words = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž\-]+", text)
    # kandidáti: delší slova, ne příliš běžná
    cand = []
    for w in words:
        w0 = w.strip(" -–—").lower()
        if len(w0) < 7:
            continue
        if w0.isdigit():
            continue
        cand.append(w0)

    # unikátní v pořadí výskytu
    uniq = []
    for w in cand:
        if w not in uniq:
            uniq.append(w)

    return uniq[:max_words]

def explain_word(word: str, grade: int, context_title: str) -> str:
    """
    Ručně pravidla + bezpečné vysvětlení (bez halucinací).
    Pokud si nejsme jistí → dáme krátké, obecné vysvětlení.
    """
    w = word.lower()

    # pár užitečných jistých map
    base = {
        "odpalované": "těsto, které se nejdřív zahřeje (odpálí) v hrnci a pak se peče",
        "korpus": "upečená část zákusku (těsto), která drží tvar",
        "receptura": "přesný postup a poměry surovin",
        "přebít": "zahrát silnější kartu (nebo více karet) než předchozí hráč",
        "žolík": "karta, která se může počítat jako jiné zvíře",
        "absence": "když něco chybí",
        "chemická": "umělá, nepřirozená (není to z běžných surovin)",
        "nadlehčený": "jemnější a nadýchanější",
        "zestárlá": "není čerstvá, je už starší",
        "nelistuje": "těsto se nerozpadá na tenké vrstvy, jak by mělo",
        "upraveno": "text byl trochu změněn (zkrácen nebo přepsán)",
        "dodrželi": "udělali to přesně tak, jak se má",
        "jedinému": "jen jednomu (a žádnému jinému)",
        "napravit": "spravit, zlepšit",
        "podnikům": "firmám / cukrárnám / místům, kde se prodává",
        "vyráběného": "udělaného, vyrobeného",
        "pachuť": "chuť, která zůstane v puse a není příjemná",
        "sražený": "krém se nepovedl a je hrudkovitý / oddělený",
        "výuční": "týká se učení řemesla (např. cukrář)",
        "verdikt": "konečné rozhodnutí",
        "kritérii": "podle čeho se něco hodnotí (pravidla hodnocení)",
        "procent": "část ze sta (např. 20 % = 20 ze 100)",
        "metabolismus": "děje v těle, které zpracovávají energii z jídla",
    }

    if w in base:
        return base[w]

    # fallback – věkově přiměřené, ale ne „hloupé“
    if grade <= 3:
        return "slovo, které je dobré vysvětlit vlastními slovy (zkus příklad)"
    if grade <= 5:
        return "slovo, které může znamenat něco odbornějšího – zkus ho vysvětlit jednoduše"
    return "méně běžné slovo – zkus ho vysvětlit a najdi v textu, co naznačuje"

def add_vocab_section(doc: Document, text: str, grade: int, context_title: str) -> None:
    add_h2(doc, "SLOVNÍČEK (na konec pracovního listu)")
    doc.add_paragraph("Vyber si slovo, přečti vysvětlení a doplň svou poznámku, pokud je potřeba.")
    words = pick_vocab_words(text, max_words=12)

    for w in words:
        exp = explain_word(w, grade, context_title)
        p = doc.add_paragraph()
        r1 = p.add_run(f"• {w} – ")
        r1.bold = True
        p.add_run(exp)
        # prostor pro vlastní poznámku
        p2 = doc.add_paragraph("Moje poznámka: ________________________________________________")


# =========================
# 6) KARETNÍ HRA – PYRAMIDA + KARTIČKY (3 sloupce)
# =========================

def set_row_height(row, cm: float) -> None:
    """
    Nastaví výšku řádku v tabulce (Word).
    """
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    trHeight = OxmlElement('w:trHeight')
    trHeight.set(qn('w:val'), str(Cm(cm).twips))
    trHeight.set(qn('w:hRule'), 'atLeast')
    trPr.append(trHeight)

def add_pyramid_column(doc: Document, card_box_cm: float = 2.2, width_cm: float = 8.0) -> None:
    add_h2(doc, "PYRAMIDA SÍLY ZVÍŘAT (lepení kartiček)")
    doc.add_paragraph("Nalep kartičky do okének: nahoře je nejsilnější zvíře, dole nejslabší.")
    doc.add_paragraph("Chameleon (žolík) do pyramidy nelep – je to zvláštní pravidlo (žolík).")

    # „pyramida“ jako sloupec – každé zvíře vlastní řádek, velké okénko
    table = doc.add_table(rows=len(PYRAMID_ORDER_WEAK_TO_STRONG), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # šířky
    for row in table.rows:
        row.cells[0].width = Cm(2.0)   # popisek (nahoře/dole)
        row.cells[1].width = Cm(width_cm)

    # plnění – odshora nejsilnější
    strong_to_weak = list(reversed(PYRAMID_ORDER_WEAK_TO_STRONG))

    for i, animal in enumerate(strong_to_weak):
        row = table.rows[i]
        set_row_height(row, card_box_cm)

        label = "NEJSILNĚJŠÍ" if i == 0 else ("NEJSLABŠÍ" if i == len(strong_to_weak)-1 else "")
        row.cells[0].text = label
        row.cells[1].text = ""  # prázdné okénko
        # zarovnání
        row.cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

def add_animal_cards(doc: Document) -> None:
    add_h2(doc, "KARTIČKY ZVÍŘAT (vystřihni)")
    doc.add_paragraph("Vystřihni kartičky a nalep je do pyramidy podle síly.")

    # 3 sloupce – tabulka 3xN
    cards = [a for a in ANIMALS if not a[0].startswith("chameleon")] + [("chameleon (žolík)", "chameleon_zolik", "🦎")]

    cols = 3
    rows = (len(cards) + cols - 1) // cols

    table = doc.add_table(rows=rows, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    for r in range(rows):
        set_row_height(table.rows[r], 2.6)
        for c in range(cols):
            cell = table.cell(r, c)
            cell.width = Cm(6.0)

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            if idx >= len(cards):
                cell.text = ""
                continue
            name, _, emoji = cards[idx]
            idx += 1

            # obsah kartičky
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(f"{emoji}\n{name}")
            run.bold = True
            run.font.size = Pt(12)

            # řádek na poznámku
            p2 = cell.add_paragraph("______________")
            p2.alignment = WD_ALIGN_PARAGRAPH.CENTER


# =========================
# 7) DRAMATIZACE – ÚVOD + SCÉNKA
# =========================

def drama_intro(doc: Document, grade: int) -> None:
    add_h2(doc, "1) KRÁTKÁ DRAMATIZACE (na začátku)")
    if grade <= 3:
        doc.add_paragraph(
            "Teď si zahrajeme krátkou scénku. Pomůže nám to pochopit text ještě před čtením."
        )
    else:
        doc.add_paragraph(
            "Nejdřív krátká scénka. Pomůže nám naladit se na text a pochopit, o co v něm jde."
        )

def drama_scene_for_pack(title: str, grade: int) -> List[str]:
    if "KARETNÍ HRA" in title:
        return [
            "Hráč 1: „Jdu první. Vykládám lišku!“",
            "Hráč 2: „Chci tě přebít. Kdo přebije lišku? Podívám se do tabulky.“",
            "Hráč 3: „Já mám tuleně. Ten je silnější než liška. Vykládám tuleně!“",
            "Hráč 1: „A co když nemám silnější zvíře? Můžu říct pass?“",
            "Hráč 2: „A co chameleon? Když ho přidám ke kosatce, počítá se jako druhá kosatka!“",
        ]
    if "SLADKÉ MÁMENÍ" in title:
        return [
            "Žák A: „Podívej, tady jsou procenta. Co znamená 57,1 %?“",
            "Žák B: „To je víc než polovina. Takže víc než polovina lidí jí čokoládu méně než jednou týdně.“",
            "Žák C: „A text mluví o obezitě. Proč se hledají nízkokalorické sladkosti?“",
        ]
    if "VĚNEČKY" in title:
        return [
            "Žák A (hodnotitel): „Tenhle věneček vypadá hezky, ale má divnou pachuť.“",
            "Žák B: „A co říká tabulka? Jakou dostal známku za suroviny a za korpus?“",
            "Žák C: „Takže někdy cena neznamená kvalitu. Musíme číst text i tabulku.“",
        ]
    return [
        "Žák A: „Co je hlavní informace v textu?“",
        "Žák B: „Zkus ji najít a podtrhnout.“",
    ]


def add_dramatization(doc: Document, title: str, grade: int) -> None:
    drama_intro(doc, grade)
    lines = drama_scene_for_pack(title, grade)
    for ln in lines:
        doc.add_paragraph(f"• {ln}")


# =========================
# 8) OTÁZKY A/B/C – BEZ NESMYSLŮ
# =========================

def add_questions_abc(doc: Document, title: str, grade: int) -> None:
    add_h2(doc, "3) OTÁZKY A/B/C (pracovní část)")

    # A – vyhledání informací
    add_h2(doc, "A) Najdi v textu (vyhledej informaci)")
    if grade <= 3:
        doc.add_paragraph("1. Co je cílem hry? Napiš jednou větou.")
        add_lines(doc, 2)
        doc.add_paragraph("2. Co znamená, že hráč řekne „pass“?")
        add_lines(doc, 2)
    else:
        doc.add_paragraph("1. Najdi v textu jednu důležitou informaci a napiš ji vlastními slovy.")
        add_lines(doc, 2)
        doc.add_paragraph("2. Vyhledej v textu (nebo tabulce) údaj, který se ti zdá nejdůležitější, a napiš ho.")
        add_lines(doc, 2)

    # B – interpretace
    add_h2(doc, "B) Přemýšlej o textu (interpretace)")
    if "SLADKÉ MÁMENÍ" in title:
        doc.add_paragraph("3. Proč se ve světě zvyšuje poptávka po nízkokalorických sladkostech?")
        add_lines(doc, 3)
        doc.add_paragraph("4. Rozliš FAKT vs. NÁZOR: napiš jeden fakt a jeden názor z textu.")
        doc.add_paragraph("FAKT: ________________________________________________")
        doc.add_paragraph("NÁZOR: _______________________________________________")
    elif "VĚNEČKY" in title:
        doc.add_paragraph("3. Proč hodnotitelce u některých věnečků vadí rumová vůně?")
        add_lines(doc, 3)
        doc.add_paragraph("4. Najdi v textu, podle čeho pozná, že je věneček kvalitní (uveď aspoň 2 věci).")
        add_lines(doc, 3)
    else:
        doc.add_paragraph("3. Proč je v této hře důležité vědět, kdo přebije koho?")
        add_lines(doc, 2)
        doc.add_paragraph("4. Co znamená, že chameleon je žolík? Vysvětli.")
        add_lines(doc, 2)

    # C – vlastní názor
    add_h2(doc, "C) Můj názor (hodnocení / argument)")
    doc.add_paragraph("5. Co bylo v textu nejzajímavější? Proč?")
    add_lines(doc, 2)


# =========================
# 9) STUDENTSKÝ DOC – FULL / EASY / LMP
# =========================

@dataclass
class Pack:
    title: str
    grade: int
    full_text: str
    table_asset_key: Optional[str]
    pack_type: str

def build_student_doc(pack: Pack, variant: str) -> Document:
    """
    variant: 'full' | 'easy' | 'lmp'
    """
    doc = Document()
    set_doc_style(doc)

    add_h1(doc, f"PRACOVNÍ LIST – {pack.title}")
    doc.add_paragraph("Jméno: ____________________________   Třída: ________   Datum: __________")

    add_spacer(doc, 0.2)

    # 1) DRAMA
    add_dramatization(doc, pack.title, pack.grade)
    add_spacer(doc, 0.2)

    # 2) TEXT (správně podle varianty)
    add_h2(doc, "2) TEXT K PŘEČTENÍ")

    if variant == "full":
        text_for_variant = pack.full_text
    elif variant == "easy":
        text_for_variant = simplify_text(pack.full_text, pack.grade)
    else:
        text_for_variant = lmp_text(pack.full_text, pack.grade)

    # vlož text po odstavcích
    for para in text_for_variant.split("\n"):
        para = para.strip()
        if not para:
            doc.add_paragraph("")
        else:
            doc.add_paragraph(para)

    # tabulka uvnitř textu (přesný originál z PDF jako obrázek)
    if pack.table_asset_key:
        add_spacer(doc, 0.2)
        add_note(doc, "TABULKA (přesný originál z PDF):")
        add_table_image(doc, ASSETS[pack.table_asset_key], width_cm=16.5)
        add_spacer(doc, 0.2)

    # Karetní hra – pyramida + kartičky (jen pro 3. třídu)
    if pack.title == "KARETNÍ HRA" and pack.grade == 3:
        add_spacer(doc, 0.2)
        add_pyramid_column(doc, card_box_cm=2.6, width_cm=9.0)  # velké okénko
        add_spacer(doc, 0.2)
        add_animal_cards(doc)
        add_spacer(doc, 0.2)

    # 3) OTÁZKY
    add_questions_abc(doc, pack.title, pack.grade)

    # 4) SLOVNÍČEK AŽ NA KONEC
    doc.add_page_break()
    add_vocab_section(doc, text_for_variant, pack.grade, pack.title)

    return doc


# =========================
# 10) METODICKÝ LIST – ZVLÁŠŤ
# =========================

def build_methodology_doc(pack: Pack) -> Document:
    doc = Document()
    set_doc_style(doc)

    add_h1(doc, f"METODICKÝ LIST – {pack.title}")
    doc.add_paragraph("Určeno pro učitele. Slouží k jednotnému ověření práce žáků s textem.")
    add_spacer(doc, 0.2)

    add_h2(doc, "Cíl (čtenářská gramotnost)")
    doc.add_paragraph("• porozumění textu (vyhledání informace)")
    doc.add_paragraph("• interpretace (vysvětlení vlastními slovy, práce s tabulkou)")
    doc.add_paragraph("• kritické čtení (fakt × názor, argumentace)")

    add_spacer(doc, 0.2)
    add_h2(doc, "Doporučený postup hodiny (45 min)")
    doc.add_paragraph("1) Dramatizace (5–7 min) – žáci se naladí na situaci z textu.")
    doc.add_paragraph("2) Slovníček (5 min) – i když je na konci pracovního listu, učitel žáky nejdřív k němu vede.")
    doc.add_paragraph("3) Čtení textu (10–15 min) – žáci čtou a podtrhují klíčové informace.")
    doc.add_paragraph("4) Otázky A/B/C (15 min) – A: vyhledání, B: interpretace, C: názor.")
    doc.add_paragraph("5) Krátká reflexe (3 min).")

    add_spacer(doc, 0.2)
    add_h2(doc, "Rozdíly mezi verzemi pracovních listů")
    doc.add_paragraph("• Plná verze: plný text + originální tabulka z PDF + kompletní otázky.")
    doc.add_paragraph("• Zjednodušená verze: zkrácené a přehlednější věty, ale stále obsahuje tabulku (originál z PDF).")
    doc.add_paragraph("• LMP/SPU verze: kratší odstavce, více řádkování, jednodušší formulace; tabulka je zachována.")

    if pack.title == "KARETNÍ HRA" and pack.grade == 3:
        add_spacer(doc, 0.2)
        add_h2(doc, "Specifická podpora: pyramida zvířat")
        doc.add_paragraph("• Žáci vystřihnou kartičky a lepí do pyramidy/sloupce podle síly.")
        doc.add_paragraph("• Okénka jsou navržena tak, aby se kartičky vešly bez zmenšování.")
        doc.add_paragraph("• Chameleon (žolík) se do pyramidy nelepí – vysvětluje se pravidlem.")

    add_spacer(doc, 0.2)
    add_h2(doc, "Poznámka k tabulkám")
    doc.add_paragraph("Tabulky jsou vloženy jako obrázek z originálního PDF, aby byla zajištěna 100% shoda údajů.")

    add_spacer(doc, 0.2)
    add_h2(doc, "RVP ZV – návaznost (obecně)")
    doc.add_paragraph("• práce s informací v textu, porozumění, interpretace, vyjadřování vlastního názoru")
    doc.add_paragraph("• práce s nesouvislým textem (tabulka) – vyhledávání a porovnávání údajů")

    return doc


# =========================
# 11) STREAMLIT UI + SESSION STATE (tlačítka nezmizí)
# =========================

def get_pack_from_ui() -> Pack:
    mode = st.radio("Zdroj textu", ["Předpřipravené (DP)", "Vlastní text"], horizontal=True)

    if mode == "Předpřipravené (DP)":
        preset_name = st.selectbox("Vyber text", list(PRESETS.keys()))
        preset = PRESETS[preset_name]
        return Pack(
            title=preset["title"],
            grade=preset["grade"],
            full_text=preset["full_text"],
            table_asset_key=preset.get("table_asset_key"),
            pack_type=preset["type"],
        )

    # Vlastní text
    grade = st.selectbox("Pro jaký ročník?", [3, 4, 5])
    title = st.text_input("Název úlohy", value="MŮJ TEXT")
    text = st.text_area("Vlož text", height=280, placeholder="Sem vlož celý text…")
    table_choice = st.selectbox(
        "Tabulka (volitelně jako obrázek v assets/)",
        ["Bez tabulky", "karetni_table.png", "sladke_table.png", "venecky_table.png"],
    )
    table_asset_key = None
    if table_choice != "Bez tabulky":
        # mapneme na klíč
        if "karetni" in table_choice:
            table_asset_key = "karetni_table"
        elif "sladke" in table_choice:
            table_asset_key = "sladke_table"
        else:
            table_asset_key = "venecky_table"

    return Pack(
        title=title.strip() or "MŮJ TEXT",
        grade=int(grade),
        full_text=text.strip(),
        table_asset_key=table_asset_key,
        pack_type="vlastni",
    )


def main():
    st.set_page_config(page_title="EdRead AI", layout="wide")
    st.title("EdRead AI – generátor pracovních listů (pro DP)")

    st.info(
        "Vygeneruje 3 varianty pracovního listu (plný / zjednodušený / LMP) + metodický list.\n"
        "Tabulky jsou vloženy jako obrázek z PDF, aby byly 100% přesné."
    )

    pack = get_pack_from_ui()

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("Nastavení")
        st.write(f"**Téma:** {pack.title}")
        st.write(f"**Ročník:** {pack.grade}")
        if pack.table_asset_key:
            st.write(f"**Tabulka:** {ASSETS[pack.table_asset_key]}")
        else:
            st.write("**Tabulka:** žádná (nebo nebyla vybrána)")

        generate = st.button("Vygenerovat dokumenty", type="primary")

    if "generated_docs" not in st.session_state:
        st.session_state.generated_docs = {}

    if generate:
        if not pack.full_text.strip():
            st.error("Chybí text. Vlož text, aby šlo dokumenty vygenerovat.")
        else:
            # vytvoř všechny dokumenty a ulož do session_state
            docs = {}

            pl_full = build_student_doc(pack, "full")
            docs["Pracovní list – plný.docx"] = doc_to_bytes(pl_full)

            pl_easy = build_student_doc(pack, "easy")
            docs["Pracovní list – zjednodušený.docx"] = doc_to_bytes(pl_easy)

            pl_lmp = build_student_doc(pack, "lmp")
            docs["Pracovní list – LMP-SPU.docx"] = doc_to_bytes(pl_lmp)

            met = build_methodology_doc(pack)
            docs["Metodický list.docx"] = doc_to_bytes(met)

            st.session_state.generated_docs = docs
            st.success("Hotovo. Dokumenty jsou připravené ke stažení níže.")

    with col2:
        st.subheader("Stažení")
        if st.session_state.generated_docs:
            st.write("Klikni postupně na všechny soubory — tlačítka zůstanou dostupná.")
            for fname, fbytes in st.session_state.generated_docs.items():
                st.download_button(
                    label=f"⬇️ {fname}",
                    data=fbytes,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"dl_{fname}",  # unikátní klíč → tlačítka nemizí
                )
        else:
            st.write("Nejdřív vygeneruj dokumenty.")


if __name__ == "__main__":
    main()
