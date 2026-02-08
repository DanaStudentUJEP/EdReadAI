import io
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import streamlit as st

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.oxml.ns import qn  # jen na font fallback, ne na emu hacky

# ----------------------------
# OPTIONAL: PDF -> image crops (exact tables)
# ----------------------------
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except Exception:
    PYMUPDF_AVAILABLE = False


# ----------------------------
# Helpers: DOCX styling
# ----------------------------
def set_doc_defaults(doc: Document, font_name="Calibri", font_size=11):
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
    p.style = doc.styles["Heading 2"]


def add_h3(doc: Document, text: str):
    p = doc.add_paragraph(text)
    p.style = doc.styles["Heading 3"]


def add_note(doc: Document, text: str):
    p = doc.add_paragraph(text)
    run = p.runs[0]
    run.italic = True


def add_spacer(doc: Document, cm=0.2):
    doc.add_paragraph("")


def doc_to_bytes(doc: Document) -> bytes:
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


# ----------------------------
# PDF crop util (exact tables)
# ----------------------------
def _pdf_page_size(pdf_path: str, page_index: int) -> Tuple[float, float]:
    with fitz.open(pdf_path) as f:
        page = f[page_index]
        r = page.rect
        return float(r.width), float(r.height)


def crop_pdf_region_to_png_bytes(
    pdf_path: str,
    page_index: int,
    clip_rel: Tuple[float, float, float, float],
    zoom: float = 2.0,
) -> Optional[bytes]:
    """
    clip_rel = (x0_rel, y0_rel, x1_rel, y1_rel) in 0..1
    Returns PNG bytes or None.
    """
    if not PYMUPDF_AVAILABLE:
        return None
    try:
        with fitz.open(pdf_path) as f:
            page = f[page_index]
            w, h = page.rect.width, page.rect.height
            x0, y0, x1, y1 = clip_rel
            clip = fitz.Rect(w * x0, h * y0, w * x1, h * y1)
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
            return pix.tobytes("png")
    except Exception:
        return None


def add_png_bytes_to_doc(doc: Document, png_bytes: bytes, width_cm: float):
    """
    Insert image into docx.
    """
    bio = io.BytesIO(png_bytes)
    doc.add_picture(bio, width=Cm(width_cm))


# ----------------------------
# Content packs (PRESET)
# ----------------------------
@dataclass
class Pack:
    key: str
    title: str
    grade: int
    pdf_path: Optional[str]  # to crop exact tables
    full_text: str
    simple_text: str
    lmp_text: str
    questions_full: List[str]
    questions_simple: List[str]
    questions_lmp: List[str]
    glossary_base: Dict[str, str]  # word -> explanation (age-appropriate)
    has_pyramid: bool


# ----------------------------
# Karetní hra — texts (you can refine wording anytime)
# The table MUST be cropped from PDF to be exact.
# ----------------------------
KARETNI_FULL = """NÁZEV ÚLOHY: KARETNÍ HRA\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

VÝCHOZÍ TEXT

1. Herní materiál
60 karet živočichů: 4 komáři, 1 chameleon (žolík), 5 karet od každého z dalších 11 druhů živočichů.

2. Popis hry
Všechny karty se rozdají mezi jednotlivé hráče. Hráči se snaží vynášet karty v souladu s pravidly tak, aby se co nejdříve zbavili všech svých karet z ruky. Zahrát lze vždy pouze silnější kombinaci živočichů, než zahrál hráč před vámi.

3. Pořadí karet
Na každé kartě je zobrazen jeden živočich. V rámečku v horní části karty jsou namalováni živočichové, kteří danou kartu přebíjí.

[KDO PŘEBIJE KOHO? – TABULKA JE VLOŽENA V TEXTU]

Živočichové, kteří daný druh přebíjí, jsou označeni vybarveným políčkem.
Symbol > označuje, že každý živočich může být přebit větším počtem karet se živočichem stejného druhu.

Příklad: Kosatku přebijí pouze dvě kosatky. Krokodýla přebijí dva krokodýli nebo jeden slon.

Chameleon má ve hře obdobnou funkci jako žolík. Lze jej zahrát spolu s libovolnou jinou kartou a počítá se jako požadovaný druh živočicha. Nelze jej hrát samostatně.

4. Průběh hry
• Karty zamíchejte a rozdělte rovnoměrně mezi všechny hráče. Každý hráč si vezme své karty do ruky a neukazuje je ostatním.
• Při hře ve třech hráčích odeberte před hrou z balíčku: 1 lva, 1 slona, 1 myš a od každého z dalších druhů živočichů 2 karty. Chameleon (žolík) zůstává ve hře.
• Hráč po levé ruce rozdávajícího hráče začíná. Zahraje (vynese na stůl lícem nahoru) jednu kartu nebo více stejných karet.
• Hráči hrají po směru hodinových ručiček a postupně se snaží přebít dříve zahrané karty.
"""

KARETNI_SIMPLE = """NÁZEV ÚLOHY: KARETNÍ HRA\tJMÉNO:

ZJEDNODUŠENÝ TEXT (pro 3. ročník)

Hrajeme karetní hru se zvířaty.
Cíl hry: zbavit se co nejdřív všech karet.

Každá karta má zvíře. Některá zvířata jsou silnější a mohou „přebít“ jiná zvířata.
Někdy můžeš přebít i tak, že zahraješ víc stejných karet.

Chameleon je žolík: může se přidat k jiné kartě a počítá se jako potřebné zvíře. Sám se hrát nesmí.

[KDO PŘEBIJE KOHO? – TABULKA JE VLOŽENA V TEXTU]
"""

KARETNI_LMP = """NÁZEV ÚLOHY: KARETNÍ HRA\tJMÉNO:

VERZE LMP / SPU

Budeme číst jednoduchá pravidla hry.
Cíl hry: nemít v ruce žádné karty.

Budeme pracovat s tabulkou „Kdo přebije koho?“
Tabulka ukazuje, které zvíře je silnější.

Chameleon je žolík: hraje se vždy s jinou kartou.

[KDO PŘEBIJE KOHO? – TABULKA JE VLOŽENA V TEXTU]
"""

KARETNI_Q_FULL = [
    "OTÁZKA 1 (1 bod): Co je cílem hry? Napiš odpověď celou větou.",
    "OTÁZKA 2 (2 body): Kolik druhů živočichů je ve hře? Uveď počet a zdůvodni.",
    "OTÁZKA 3 (2 body): Kterého živočicha je možné přebít největším počtem druhů? Napiš živočicha a počet.",
    "OTÁZKA 4 (1 bod): Kolik karet dostane každý hráč, když hrají 4 hráči?",
    "OTÁZKA 5 (1 bod): Která okolnost NEMŮŽE přispět k vítězství hráče? (A/B/C/D)",
]

KARETNI_Q_SIMPLE = [
    "OTÁZKA 1: Co je cílem hry?",
    "OTÁZKA 2: Najdi v tabulce, kdo přebije myš (napiš aspoň 2 zvířata).",
    "OTÁZKA 3: Co znamená, že chameleon je žolík?",
]

KARETNI_Q_LMP = [
    "OTÁZKA 1: Co je cílem hry? (nemít v ruce karty / mít co nejvíc karet)",
    "OTÁZKA 2: Najdi v tabulce: Kdo přebije komára? (napiš 1 zvíře)",
    "OTÁZKA 3: Co dělá chameleon? (žolík / nejsilnější zvíře)",
]

KARETNI_GLOSS = {
    "materiál": "věci, které k něčemu potřebujeme",
    "rovnoměrně": "tak, aby měl každý stejně",
    "přebít": "zahrát silnější kartu než předtím",
    "kombinace": "víc karet dohromady",
    "vynést": "položit kartu na stůl",
    "žolík": "karta, která se může tvářit jako jiné zvíře",
    "po směru": "stejným směrem jako jdou hodiny",
    "odeberte": "dej pryč (nepoužij)",
}

# ----------------------------
# Sladké mámení — keep table image exact from PDF
# ----------------------------
SLADKE_FULL = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Češi a čokoláda (všechny údaje v tabulkách jsou v procentech)
[TABULKY JSOU VLOŽENY Z PDF PŘÍMO DO TEXTU]

Následuje článek o obezitě, poptávce po nízkokalorických sladkostech
a o hledání náhražek cukru (light mlsání, sladidla apod.).
"""

SLADKE_SIMPLE = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ\tJMÉNO:

ZJEDNODUŠENÝ TEXT

V tabulkách vidíš, jak často lidé jedí čokoládu a jaké sladkosti kupují.
V článku se píše, že ve světě roste obezita, a proto lidé hledají méně kalorické sladkosti.
Vědci zkouší najít sladidlo, které sladí, ale nemá moc kalorií.

[TABULKY JSOU VLOŽENY Z PDF PŘÍMO DO TEXTU]
"""

SLADKE_LMP = """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ\tJMÉNO:

VERZE LMP / SPU

Budeme pracovat s tabulkami o čokoládě a se zkráceným textem.
Najdi v tabulkách informace a odpověz na otázky.

[TABULKY JSOU VLOŽENY Z PDF PŘÍMO DO TEXTU]
"""

SLADKE_Q_FULL = [
    "OTÁZKA 1 (1 bod): Který výrok je v rozporu s výchozím textem? (A/B/C/D)",
    "OTÁZKA 2 (1 bod): Jaké vlastnosti by podle článku nemělo mít ideální sladidlo? (A/B/C/D)",
    "OTÁZKA 3 (2 body): Proč se ve světě zvyšuje poptávka po nízkokalorických sladkostech?",
    "OTÁZKA 4 (2 body): Rozhodni ANO/NE podle tabulek (4 tvrzení).",
]

SLADKE_Q_SIMPLE = [
    "OTÁZKA 1: Co ukazují tabulky? (o čem jsou?)",
    "OTÁZKA 2: Proč lidé ve světě hledají méně kalorické sladkosti?",
    "OTÁZKA 3: Najdi v tabulce jednu čokoládovou tyčinku a napiš, kolik % lidí ji jedlo.",
]

SLADKE_Q_LMP = [
    "OTÁZKA 1: Tabulky jsou o… (čokoládě / ovoci / zelenině)",
    "OTÁZKA 2: Proč lidé hledají méně kalorické sladkosti? (kvůli obezitě / kvůli sportu)",
    "OTÁZKA 3: Najdi v tabulce slovo „Milka“ a opiš procento.",
]

SLADKE_GLOSS = {
    "epidemie": "když je nějaký problém hodně rozšířený",
    "obezita": "velká nadváha",
    "metabolismus": "to, jak tělo zpracovává jídlo a energii",
    "nízkokalorický": "má málo kalorií",
    "kalorie": "energie z jídla",
    "náhražka": "něco, co něco nahradí",
    "sladidlo": "látka, která sladí",
    "poptávka": "kolik lidí něco chce kupovat",
}

# ----------------------------
# Věnečky — table exact from PDF
# ----------------------------
VENECKY_FULL = """NÁZEV ÚLOHY: VĚNEČKY\tJMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

V článku se hodnotí několik věnečků z různých podniků.
Součástí je tabulka s cenou a známkami (jako ve škole).

[TABULKA JE VLOŽENA Z PDF PŘÍMO DO TEXTU]
"""

VENECKY_SIMPLE = """NÁZEV ÚLOHY: VĚNEČKY\tJMÉNO:

ZJEDNODUŠENÝ TEXT

Článek porovnává věnečky z několika cukráren.
Hodnotí se: vzhled, korpus, suroviny a celková známka.
Podívej se do tabulky a hledej odpovědi.

[TABULKA JE VLOŽENA Z PDF PŘÍMO DO TEXTU]
"""

VENECKY_LMP = """NÁZEV ÚLOHY: VĚNEČKY\tJMÉNO:

VERZE LMP / SPU

Budeme pracovat hlavně s tabulkou.
Najdi v tabulce ceny a známky a odpověz na otázky.

[TABULKA JE VLOŽENA Z PDF PŘÍMO DO TEXTU]
"""

VENECKY_Q_FULL = [
    "OTÁZKA 1 (1 bod): Který věneček neobsahuje pudink uvařený z mléka? (A/B/C/D)",
    "OTÁZKA 2 (1 bod): Ve kterém věnečku je rum použit, aby překryl jiné chutě? (A/B/C/D)",
    "OTÁZKA 3 (1 bod): Který věneček byl hodnocen nejlépe?",
    "OTÁZKA 4 (1 bod): Který podnik dopadl nejlépe?",
    "OTÁZKA 5 (2 body): Který věneček byl nejdražší? Cena? Kde byl zakoupen? Odpovídá cena kvalitě? Zdůvodni.",
]

VENECKY_Q_SIMPLE = [
    "OTÁZKA 1: Který podnik dopadl nejlépe? (najdi v tabulce)",
    "OTÁZKA 2: Který věneček je nejdražší? Kolik stojí?",
    "OTÁZKA 3: Co znamená „celková známka“?",
]

VENECKY_Q_LMP = [
    "OTÁZKA 1: Najdi nejnižší známku v tabulce a napiš číslo podniku.",
    "OTÁZKA 2: Najdi cenu 20 Kč. Který věneček to je?",
    "OTÁZKA 3: Co je to „podnik“? (cukrárna / zvíře)",
]

VENECKY_GLOSS = {
    "korpus": "upečená část zákusku (těsto)",
    "suroviny": "z čeho je něco vyrobené",
    "receptura": "přesný recept",
    "nadlehčený": "lehčí a nadýchanější",
    "chemický": "umělý, nepřirozený",
    "zestárlý": "už není čerstvý",
    "podnik": "místo, kde se prodává (např. cukrárna)",
}

PRESETS: Dict[str, Pack] = {
    "karetni": Pack(
        key="karetni",
        title="Karetní hra",
        grade=3,
        pdf_path="Karetní hra.pdf",
        full_text=KARETNI_FULL,
        simple_text=KARETNI_SIMPLE,
        lmp_text=KARETNI_LMP,
        questions_full=KARETNI_Q_FULL,
        questions_simple=KARETNI_Q_SIMPLE,
        questions_lmp=KARETNI_Q_LMP,
        glossary_base=KARETNI_GLOSS,
        has_pyramid=True,
    ),
    "sladke": Pack(
        key="sladke",
        title="Sladké mámení",
        grade=5,
        pdf_path="Sladké mámení.pdf",
        full_text=SLADKE_FULL,
        simple_text=SLADKE_SIMPLE,
        lmp_text=SLADKE_LMP,
        questions_full=SLADKE_Q_FULL,
        questions_simple=SLADKE_Q_SIMPLE,
        questions_lmp=SLADKE_Q_LMP,
        glossary_base=SLADKE_GLOSS,
        has_pyramid=False,
    ),
    "venecky": Pack(
        key="venecky",
        title="Věnečky",
        grade=4,
        pdf_path="Věnečky.pdf",
        full_text=VENECKY_FULL,
        simple_text=VENECKY_SIMPLE,
        lmp_text=VENECKY_LMP,
        questions_full=VENECKY_Q_FULL,
        questions_simple=VENECKY_Q_SIMPLE,
        questions_lmp=VENECKY_Q_LMP,
        glossary_base=VENECKY_GLOSS,
        has_pyramid=False,
    ),
}

# ----------------------------
# Exact table crops (relative coords)
# NOTE: These are tuned to your PDF layout screenshots.
# If you ever replace PDFs with different layout, adjust coords.
# ----------------------------
TABLE_CROPS = {
    # Karetní hra: page 0 main matrix "Kdo přebije koho?"
    ("karetni", "matrix"): dict(page=0, clip_rel=(0.12, 0.31, 0.83, 0.74), zoom=2.3),
    # Sladké mámení: page 0 has multiple tables at top; crop larger top region
    ("sladke", "tables_top"): dict(page=0, clip_rel=(0.08, 0.08, 0.92, 0.56), zoom=2.2),
    # Věnečky: page likely contains rating table; in your screenshots it’s on page 1 or 2 depending PDF
    # We'll try page 1 first; if crop empty, you can switch to page 0/2.
    ("venecky", "table"): dict(page=1, clip_rel=(0.08, 0.55, 0.92, 0.90), zoom=2.4),
}


# ----------------------------
# Pyramid + animal cards (emoji)
# ----------------------------
ANIMALS = [
    ("kosatka", "🐬"),
    ("slon", "🐘"),
    ("krokodýl", "🐊"),
    ("lední medvěd", "🐻‍❄️"),
    ("lev", "🦁"),
    ("tuleň", "🦭"),
    ("liška", "🦊"),
    ("okoun", "🐟"),
    ("ježek", "🦔"),
    ("sardinky", "🐟"),
    ("myš", "🐭"),
    ("komár", "🦟"),
    ("chameleon (žolík)", "🦎"),
]


def add_dram_intro(doc: Document, title: str):
    add_h3(doc, "Úvod (na začátek hodiny)")
    doc.add_paragraph(
        f"Dnes budeme pracovat s textem „{title}“. Nejdřív si krátce zahrajeme scénku, "
        "abychom pochopili situaci ještě před čtením. Potom si společně projdeme slovíčka "
        "(slovníček je na konci pracovního listu) a teprve pak se vrátíme k textu a otázkám."
    )


def add_dramatization_karetni(doc: Document):
    add_h3(doc, "Dramatizace (krátká scénka)")
    doc.add_paragraph("Role: hráč A, hráč B, hráč C (a vypravěč / rozhodčí).")
    doc.add_paragraph("Hráč A (dává kartu): „Vykládám myš.“")
    doc.add_paragraph("Hráč B: „Chci tě přebít… Můžu dát 2 myši?“")
    doc.add_paragraph("Hráč C (listuje tabulkou): „Podíváme se do tabulky, kdo přebije koho!“")
    doc.add_paragraph("Vypravěč / rozhodčí: „Pozor — někdy musíš dát víc stejných karet!“")
    doc.add_paragraph("Hráč B: „A co když mám chameleona?“")
    doc.add_paragraph("Hráč A: „Chameleon je žolík — ale nesmí být sám!“")
    doc.add_paragraph(
        "Krátká domluva: Ve dvojicích si pak zkuste 2–3 tahy (zvíře → pokus o přebití → kontrola v tabulce)."
    )


def add_dramatization_generic(doc: Document, title: str):
    add_h3(doc, "Dramatizace (krátká scénka)")
    doc.add_paragraph(
        f"Role: čtenář, kamarád, vypravěč. Cílem je naladit se na text „{title}“."
    )
    doc.add_paragraph("Čtenář: „V textu je něco důležitého, ale některým slovům nerozumím.“")
    doc.add_paragraph("Kamarád: „Zkusíme nejdřív slovníček. Pak to půjde líp.“")
    doc.add_paragraph("Vypravěč: „Až potom budeme hledat odpovědi přímo v textu a v tabulce.“")


def add_pyramid_column(doc: Document):
    """
    User wants column-like pyramid: strongest at top, weakest at bottom.
    Must fit the cut cards -> make cells LARGE.
    """
    add_h3(doc, "Zvířecí pyramida (nalepování kartiček)")
    doc.add_paragraph("Vystřihni kartičky zvířat a nalep je do okének podle síly ve hře:")
    doc.add_paragraph("Nahoře je nejsilnější zvíře, dole nejslabší.")

    # One-column table with 13 big slots
    rows = 13
    table = doc.add_table(rows=rows, cols=1)
    table.style = "Table Grid"

    # Make cells big enough for cards (approx)
    for i in range(rows):
        row = table.rows[i]
        row.height = Cm(1.6)  # bigger slot
        row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY
        cell = row.cells[0]
        # Label left inside cell (small)
        p = cell.paragraphs[0]
        p.text = ""
        run = p.add_run(f"{i+1}. ")
        run.bold = True
        p.add_run("")

    add_note(doc, "Tip: Kartičky lepte postupně podle tabulky „Kdo přebije koho?“")


def build_animal_cards_doc() -> Document:
    doc = Document()
    set_doc_defaults(doc, font_size=11)
    add_title(doc, "Kartičky zvířat – Karetní hra (3 sloupce)")

    doc.add_paragraph("Vystřihni kartičky. Můžeš je použít pro hru i pro nalepování do pyramidy.")

    # 3 columns grid
    cols = 3
    rows = (len(ANIMALS) + cols - 1) // cols
    table = doc.add_table(rows=rows, cols=cols)
    table.style = "Table Grid"

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.text = ""
            if idx < len(ANIMALS):
                name, emoji = ANIMALS[idx]
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run1 = p.add_run(f"{emoji}\n")
                run1.font.size = Pt(22)
                run2 = p.add_run(name)
                run2.font.size = Pt(12)
                run2.bold = True
                idx += 1

    return doc


# ----------------------------
# Glossary block (end of worksheet)
# ----------------------------
def build_glossary_block(doc: Document, glossary: Dict[str, str], max_words: int = 12):
    add_h2(doc, "Slovníček (vyplň až po dramatizaci)")
    doc.add_paragraph(
        "Nejdřív si s učitelem/učitelkou projdi slovíčka. "
        "Když něčemu nerozumíš, dopiš si vlastní poznámku."
    )

    items = list(glossary.items())[:max_words]
    for w, expl in items:
        p = doc.add_paragraph()
        r = p.add_run(f"• {w} = {expl}")
        r.bold = False
        doc.add_paragraph("Moje poznámka: ________________________________________________")


# ----------------------------
# Insert exact tables (from PDF crops)
# ----------------------------
def insert_tables_for_pack(doc: Document, pack: Pack):
    if not pack.pdf_path:
        return

    if pack.key == "karetni":
        cfg = TABLE_CROPS.get(("karetni", "matrix"))
        if cfg and PYMUPDF_AVAILABLE:
            png = crop_pdf_region_to_png_bytes(pack.pdf_path, cfg["page"], cfg["clip_rel"], cfg["zoom"])
            if png:
                add_spacer(doc)
                add_h3(doc, "Tabulka: Kdo přebije koho?")
                add_png_bytes_to_doc(doc, png, width_cm=14.5)
                add_spacer(doc)
                return
        # fallback
        add_note(doc, "Tabulku se nepodařilo vložit (zkontroluj PyMuPDF v requirements a PDF soubor).")

    if pack.key == "sladke":
        cfg = TABLE_CROPS.get(("sladke", "tables_top"))
        if cfg and PYMUPDF_AVAILABLE:
            png = crop_pdf_region_to_png_bytes(pack.pdf_path, cfg["page"], cfg["clip_rel"], cfg["zoom"])
            if png:
                add_spacer(doc)
                add_h3(doc, "Tabulky z průzkumu (převzato z originálu)")
                add_png_bytes_to_doc(doc, png, width_cm=15.5)
                add_spacer(doc)
                return
        add_note(doc, "Tabulky se nepodařilo vložit (zkontroluj PyMuPDF v requirements a PDF soubor).")

    if pack.key == "venecky":
        cfg = TABLE_CROPS.get(("venecky", "table"))
        if cfg and PYMUPDF_AVAILABLE:
            png = crop_pdf_region_to_png_bytes(pack.pdf_path, cfg["page"], cfg["clip_rel"], cfg["zoom"])
            if png:
                add_spacer(doc)
                add_h3(doc, "Tabulka hodnocení věnečků (převzato z originálu)")
                add_png_bytes_to_doc(doc, png, width_cm=15.5)
                add_spacer(doc)
                return
        add_note(doc, "Tabulku se nepodařilo vložit (zkontroluj PyMuPDF v requirements a PDF soubor).")


# ----------------------------
# Student doc builder (full / simple / lmp)
# ----------------------------
def build_student_doc(pack: Pack, variant: str) -> Document:
    doc = Document()

    # fonts per variant
    if variant == "lmp":
        set_doc_defaults(doc, font_size=13)
    else:
        set_doc_defaults(doc, font_size=11)

    add_title(doc, f"Pracovní list – {pack.title} ({variant.upper()})")

    # Intro + dramatizace
    add_dram_intro(doc, pack.title)
    if pack.key == "karetni":
        add_dramatization_karetni(doc)
    else:
        add_dramatization_generic(doc, pack.title)

    add_spacer(doc)

    # Instructions about flow (teacher will guide; here only simple student-friendly note)
    add_note(doc, "Teď přejdi na konec listu: slovníček. Pak se vrať a teprve potom čti text a dělej otázky.")

    add_spacer(doc)

    # Text (with exact tables INSIDE)
    add_h2(doc, "Text")
    if variant == "full":
        doc.add_paragraph(pack.full_text)
    elif variant == "simple":
        doc.add_paragraph(pack.simple_text)
    else:
        doc.add_paragraph(pack.lmp_text)

    # Insert exact tables where placeholder indicates
    insert_tables_for_pack(doc, pack)

    # Karetní pyramid for all variants (if pack wants)
    if pack.has_pyramid:
        add_spacer(doc)
        add_pyramid_column(doc)
        add_spacer(doc)

    # Questions
    add_h2(doc, "Otázky")
    questions = pack.questions_full if variant == "full" else pack.questions_simple if variant == "simple" else pack.questions_lmp
    for q in questions:
        doc.add_paragraph(q)
        doc.add_paragraph("Odpověď: ____________________________________________________________")
        doc.add_paragraph("")

    # Glossary at END
    add_spacer(doc)
    build_glossary_block(doc, pack.glossary_base, max_words=12)

    return doc


# ----------------------------
# Methodology doc builder
# ----------------------------
def build_method_doc(pack: Pack) -> Document:
    doc = Document()
    set_doc_defaults(doc, font_size=11)

    add_title(doc, f"Metodický list – {pack.title}")

    add_h2(doc, "Doporučený postup práce (45 minut)")
    doc.add_paragraph("1) Dramatizace (5–7 min)")
    doc.add_paragraph("   • Krátká motivační scénka (bez pomůcek navíc).")
    doc.add_paragraph("   • Cíl: naladit žáky na situaci a připravit porozumění textu.")
    doc.add_paragraph("2) Slovníček (5–10 min) – je na konci pracovního listu")
    doc.add_paragraph("   • Učitel vede žáky: nejdřív slovníček, pak návrat k textu.")
    doc.add_paragraph("3) Čtení textu (10–15 min)")
    doc.add_paragraph("   • Práce s tabulkami v textu (žáci v nich hledají informace).")
    doc.add_paragraph("4) Otázky A/B/C (15 min)")
    doc.add_paragraph("   • Vyhledání informace → interpretace → vlastní názor (dle varianty listu).")
    doc.add_paragraph("5) Krátká reflexe (3–5 min)")

    add_h2(doc, "Rozdíly mezi verzemi (manuál pro volbu verze)")
    doc.add_paragraph("PLNÁ VERZE (FULL):")
    doc.add_paragraph("• Obsahuje plný text a všechny tabulky v původní podobě.")
    doc.add_paragraph("• Otázky jsou náročnější (vyhledávání + práce s informací + zdůvodnění).")
    doc.add_paragraph("")
    doc.add_paragraph("ZJEDNODUŠENÁ VERZE (SIMPLE):")
    doc.add_paragraph("• Obsahuje zjednodušený text, ALE tabulky zůstávají zachovány.")
    doc.add_paragraph("• Otázky jsou kratší a více vedené (hledání v tabulce, vysvětlení pojmů).")
    doc.add_paragraph("")
    doc.add_paragraph("VERZE LMP / SPU:")
    doc.add_paragraph("• Větší písmo, kratší věty, více struktury.")
    doc.add_paragraph("• Tabulky zůstávají zachovány (žáci z nich čerpají odpovědi).")
    doc.add_paragraph("• Otázky jsou voleny tak, aby šly řešit s oporou v tabulce a v textu.")

    if pack.key == "karetni":
        add_h2(doc, "Specifika pro Karetní hru")
        doc.add_paragraph("• Pyramida/sloupec: nejsilnější zvíře nahoře, nejslabší dole.")
        doc.add_paragraph("• Kartičky zvířat: doporučeno vytisknout samostatně (3 sloupce).")
        doc.add_paragraph("• Tabulka „Kdo přebije koho?“ je vložena do všech verzí pracovních listů.")

    add_h2(doc, "Digitální varianta (EdRead AI)")
    doc.add_paragraph("• Učitel zvolí text a ročník, nástroj vygeneruje DOCX.")
    doc.add_paragraph("• Výstupy: plná verze, zjednodušená verze, LMP/SPU verze + metodika.")
    doc.add_paragraph("• Tabulky z PDF jsou vloženy jako přesné výřezy (identické s originálem).")

    add_h2(doc, "Poznámka k RVP ZV (čtenářská gramotnost)")
    doc.add_paragraph(
        "Aktivity podporují: vyhledávání informací v textu, porozumění, práci s nesouvislým textem (tabulky), "
        "interpretaci a vyjádření vlastního názoru. To odpovídá očekávaným výstupům v oblasti Jazyk a jazyková komunikace."
    )

    return doc


# ----------------------------
# CUSTOM TEXT support
# ----------------------------
def build_custom_pack(title: str, grade: int, text: str) -> Pack:
    # very safe default questions by grade
    q_full = [
        "OTÁZKA 1: Napiš jednou větou, o čem text je.",
        "OTÁZKA 2: Najdi v textu 2 důležité informace a opiš je.",
        "OTÁZKA 3: Co si o textu myslíš? (názor a proč)",
    ]
    q_simple = [
        "OTÁZKA 1: O čem text je? (1 věta)",
        "OTÁZKA 2: Najdi v textu jedno důležité slovo a napiš ho.",
    ]
    q_lmp = [
        "OTÁZKA 1: Zakroužkuj: Text je o… (doplň učitel s dětmi)",
        "OTÁZKA 2: Najdi v textu jedno slovo, kterému nerozumíš.",
    ]

    # pick “hard” words, but explanations left empty (teacher/child fill)
    words = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    cand = []
    for w in words:
        wl = w.lower()
        if len(wl) >= 8 and wl not in cand:
            cand.append(wl)
    gloss = {w: "______________________________" for w in cand[:12]}

    return Pack(
        key="custom",
        title=title,
        grade=grade,
        pdf_path=None,
        full_text=text,
        simple_text=text,
        lmp_text=text,
        questions_full=q_full,
        questions_simple=q_simple,
        questions_lmp=q_lmp,
        glossary_base=gloss,
        has_pyramid=False,
    )


# ----------------------------
# Streamlit UI (buttons persist)
# ----------------------------
def ensure_state():
    if "generated" not in st.session_state:
        st.session_state.generated = {}  # filename -> bytes
    if "generated_meta" not in st.session_state:
        st.session_state.generated_meta = {}  # to show what was generated


def generate_all_docs(pack: Pack):
    # Student docs
    pl_full = build_student_doc(pack, "full")
    pl_simple = build_student_doc(pack, "simple")
    pl_lmp = build_student_doc(pack, "lmp")

    # Method doc
    method = build_method_doc(pack)

    st.session_state.generated = {
        f"pracovni_list_{pack.title}_plny.docx": doc_to_bytes(pl_full),
        f"pracovni_list_{pack.title}_zjednoduseny.docx": doc_to_bytes(pl_simple),
        f"pracovni_list_{pack.title}_LMP_SPU.docx": doc_to_bytes(pl_lmp),
        f"metodicky_list_{pack.title}.docx": doc_to_bytes(method),
    }

    # extra cards for karetní
    if pack.key == "karetni":
        cards_doc = build_animal_cards_doc()
        st.session_state.generated[f"karticky_zvirat_{pack.title}.docx"] = doc_to_bytes(cards_doc)

    st.session_state.generated_meta = {
        "title": pack.title,
        "grade": pack.grade,
        "tables_exact": PYMUPDF_AVAILABLE and bool(pack.pdf_path),
    }


def main():
    st.set_page_config(page_title="EdRead AI", layout="centered")
    ensure_state()

    st.title("EdRead AI – generátor pracovních listů (DOCX)")
    st.caption("Plná / zjednodušená / LMP-SPU verze + metodický list. Tabulky z PDF jsou vkládány přesným výřezem.")

    mode = st.radio("Co chceš zpracovat?", ["Předpřipravené texty (diplomka)", "Vlastní text"], horizontal=True)

    if mode == "Předpřipravené texty (diplomka)":
        pick = st.selectbox("Vyber text", ["Karetní hra (3. třída)", "Věnečky (4. třída)", "Sladké mámení (5. třída)"])
        key = "karetni" if pick.startswith("Karetní") else "venecky" if pick.startswith("Věnečky") else "sladke"
        pack = PRESETS[key]
        st.info(f"Vybráno: **{pack.title}** (ročník: {pack.grade}).")

    else:
        title = st.text_input("Název úlohy", value="Můj text")
        grade = st.selectbox("Ročník", [3, 4, 5])
        text = st.text_area("Vlož text", height=220, placeholder="Sem vlož libovolný text…")
        if not text.strip():
            st.warning("Vlož prosím text.")
            pack = None
        else:
            pack = build_custom_pack(title=title, grade=grade, text=text)

    st.divider()

    col1, col2 = st.columns([1, 2])
    with col1:
        gen = st.button("Vygenerovat dokumenty", type="primary", disabled=(pack is None))
    with col2:
        st.write("")

    if gen and pack is not None:
        generate_all_docs(pack)
        st.success("Hotovo. Níže si stáhni všechny dokumenty — tlačítka po stažení nezmizí.")

    # Persistent download buttons (stay visible after click)
    if st.session_state.generated:
        st.subheader("Stažení dokumentů")
        meta = st.session_state.generated_meta or {}
        if meta:
            st.caption(f"Balíček: {meta.get('title','')} | ročník: {meta.get('grade','')} | tabulky z PDF: {'ANO' if meta.get('tables_exact') else 'NE'}")

        for fname, b in st.session_state.generated.items():
            st.download_button(
                label=f"⬇️ {fname}",
                data=b,
                file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"dl_{fname}",
            )

        st.info(
            "Pozn.: Pokud se tabulky nevkládají, zkontroluj, že je v repo `requirements.txt` s PyMuPDF "
            "a že PDF soubory mají přesně tyto názvy."
        )

    st.divider()
    st.caption("© EdRead AI – prototyp pro diplomovou práci (generuje DOCX).")


if __name__ == "__main__":
    main()
