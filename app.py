# app.py
# EdRead AI – prototyp pro diplomovou práci (1. stupeň ZŠ)
# Streamlit + python-docx
# Generuje DOCX: pracovní list (plný), zjednodušený, LMP/SPU + metodiku
# Pro Karetní hru navíc: kartičky zvířat (emoji) + pyramida (podklad pro lepení)

import io
import math
import re
from datetime import date

import streamlit as st
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, Cm


# ---------------------------
# Nastavení Streamlit stránky
# ---------------------------
st.set_page_config(page_title="EdRead AI (prototyp)", page_icon="📘", layout="centered")


# ---------------------------
# Obsahy (v praxi je můžeš upravit dle originálů PDF)
# ---------------------------

# KARETNÍ HRA – pořadí síly (od nejslabšího po nejsilnější) podle tvého zadání
# (komár je nejslabší, kosatka nejsilnější; chameleon je žolík mimo pořadí)
KARETNI_PORADI = [
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

ANIMALS_CARDS = [
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

# Pozn.: Tady jsou texty zkrácené tak, aby to šlo rozumně testovat.
# Pokud chceš 100% doslovné převzetí včetně tabulek a formátu, nejlepší je vložit text ručně do konstant.
TEXTS = {
    "Karetní hra (3. třída)": {
        "rocnik": 3,
        "tag_rvp": "CJ_OZ_1_2",
        "text_full": """NÁZEV ÚLOHY: KARETNÍ HRA

Herní materiál: 60 karet živočichů (4 komáři, 1 chameleon – žolík, 5 karet od každého z dalších 11 druhů).

Cíl hry: Hráči se snaží zbavit všech karet z ruky jako první. Zahrát lze vždy pouze silnější kombinaci než předchozí hráč.

Pravidla přebíjení:
- Hraje se po směru hodinových ručiček.
- Buď zahraješ stejný počet karet „vyššího“ zvířete,
  nebo stejné zvíře, ale o 1 kartu více.
- Kdo nechce/nemůže, řekne pass.
- Chameleon funguje jako žolík, nelze ho hrát samostatně.

(Zdroj: Bláznivá ZOO, upraveno.)
""",
        "text_simple": """KARETNÍ HRA – ZJEDNODUŠENĚ

Hraje se s kartami zvířat.
Cíl je: zbavit se karet jako první.

Když někdo vyloží kartu (nebo více stejných karet), další hráč ji musí přebít:
- buď stejným počtem silnějších zvířat,
- nebo stejným zvířetem, ale o jednu kartu víc.

Kdo nemůže, řekne PASS.

Chameleon je žolík: pomůže ti jako jakékoli zvíře, ale sám hrát nesmí.
""",
        "text_lmp": """KARETNÍ HRA – PRO SNADNÉ ČTENÍ (LMP/SPU)

Hraje se s kartami zvířat.
Vyhrává ten, kdo nemá žádné karty.

Když někdo dá kartu na stůl, další hráč ji musí přebít.
Kdo nemůže, řekne PASS.

Chameleon je žolík. Pomůže ti, ale sám hrát nejde.
""",
        "drama": [
            "Učitelka: „Dnes budeme detektivové pravidel. Máme novou hru a musíme přijít na to, jak se hraje.“",
            "Žák 1: „Já nerozumím, co znamená přebít kartu.“",
            "Žák 2: „To je asi jako být silnější!“",
            "Učitelka: „Přesně. Nejdřív si to zahrajeme na zvířata – kdo je slabší a kdo silnější – a pak teprve budeme číst.“",
        ],
        "slovicka_hint": [
            "kombinace",
            "přebít",
            "pravidla",
            "žolík",
            "rovnoměrně",
            "připevnit",
            "vzdát",
            "kolo",
            "prostřed",
            "vyložit",
        ],
    },

    "Věnečky (4. třída)": {
        "rocnik": 4,
        "tag_rvp": "CJ_OZ_1_2",
        "text_full": """NÁZEV ÚLOHY: VĚNEČKY

Text popisuje hodnocení několika věnečků z různých cukráren.
Hodnotitelka si všímá chuti, vůně rumu, pudinku a kvality těsta.

Věneček č. 2: špatný krém, chemická pachuť, tvrdé těsto.
Věneček č. 3: rum cítit, ale jen aby zakryl chybějící chuť; těsto špatné.
Věneček č. 4: nejlepší, dobrý pudink a povedené těsto.
Věneček č. 5: chemický pudink z prášku, staré tvrdé těsto.

Součástí je i tabulka s cenou a hodnocením.

(Zdroj: Týden, upraveno.)
""",
        "text_simple": """VĚNEČKY – ZJEDNODUŠENĚ

Hodnotitelka zkoušela věnečky z pěti cukráren.
Nejlepší byl věneček č. 4. Nejhorší byly č. 2 a č. 3.
U některých byl krém „chemický“ a těsto tvrdé.
""",
        "text_lmp": """VĚNEČKY – PRO SNADNÉ ČTENÍ (LMP/SPU)

Paní hodnotila několik věnečků.
Dívala se, jestli je dobrý krém a těsto.
Nejlepší byl věneček č. 4.
""",
        "drama": [
            "Učitelka: „Dnes budeme hodnotitelé. Co všechno se dá poznat podle chuti a vůně?“",
            "Žák 1: „Třeba jestli je něco z pravých surovin.“",
            "Žák 2: „A jestli to není chemické!“",
            "Učitelka: „Skvělé. Než začneme číst, řekněte: co by měl mít opravdu dobrý věneček?“",
        ],
        "slovicka_hint": [
            "odpalované",
            "korpus",
            "pachuť",
            "absenci",
            "receptura",
            "nadlehčený",
            "poměr",
            "průmyslově",
            "verdikt",
            "vyzdvihla",
        ],
    },

    "Sladké mámení (5. třída)": {
        "rocnik": 5,
        "tag_rvp": "CJ_OZ_1_2",
        "text_full": """NÁZEV ÚLOHY: SLADKÉ MÁMENÍ

Text vysvětluje, že ve světě roste poptávka po nízkokalorických sladkostech kvůli obezitě,
ale v ČR lidé často o „light“ sladkosti nestojí.

V článku se mluví o hledání náhražek cukru (alditoly, polydextróza),
a o rozdílu mezi jednoduchými a složitými cukry.

Součástí je i tabulka s údaji o tom, jak často lidé jedí čokoládu a bonboniéry.

(Zdroj: Týden + Median, upraveno.)
""",
        "text_simple": """SLADKÉ MÁMENÍ – ZJEDNODUŠENĚ

Ve světě je hodně lidí s nadváhou, proto se hledají sladkosti s méně kaloriemi.
V ČR lidé často „light“ sladkosti neřeší.
V textu se vysvětluje rozdíl mezi cukry a proč záleží na složení.
""",
        "text_lmp": """SLADKÉ MÁMENÍ – PRO SNADNÉ ČTENÍ (LMP/SPU)

Lidé jedí sladkosti.
Některé sladkosti mají hodně cukru.
V textu se říká, že je důležité dívat se na složení.
""",
        "drama": [
            "Učitelka: „Představte si, že jste výrobci čokolády. Co by lidé chtěli – a co by měli chtít?“",
            "Žák 1: „Lidi chtějí, aby to bylo dobré.“",
            "Žák 2: „Ale aby to nebylo tak nezdravé.“",
            "Učitelka: „Přesně. A teď zjistíme, co říká článek – a co říkají čísla v tabulce.“",
        ],
        "slovicka_hint": [
            "epidemie",
            "metabolismus",
            "nízkokalorický",
            "náhražka",
            "sladivost",
            "energetický",
            "polysacharidy",
            "fruktóza",
            "kardiovaskulární",
            "ztužené",
        ],
    },
}


# ---------------------------
# Pomocné funkce pro DOCX
# ---------------------------

def set_doc_defaults(doc: Document, font_name="Calibri", font_size=11):
    style = doc.styles["Normal"]
    style.font.name = font_name
    style.font.size = Pt(font_size)
    # pro češtinu:
    style._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)


def add_title(doc: Document, text: str):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(16)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_h2(doc: Document, text: str):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(13)


def add_spacer(doc: Document, n=1):
    for _ in range(n):
        doc.add_paragraph("")


def add_box_hint(doc: Document, text: str):
    t = doc.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.cell(0, 0)
    cell.paragraphs[0].add_run(text).bold = True


def safe_explain_word(word: str, grade: int) -> str:
    """
    Jednoduchá (a bezpečná) vysvětlovací logika bez internetů.
    Není vševědoucí — ale dává smysluplná vysvětlení pro školní slovníček.
    Když si nejsme jistí, vrátíme prázdný string a necháme linku pro žáka.
    """
    w = word.lower()

    # ručně doladěné časté školní pojmy (můžeš rozšířit)
    dict_base = {
        "korpus": "spodní část zákusku, těsto",
        "pachuť": "nepříjemná chuť, která zůstane v puse",
        "receptura": "přesný recept a postup",
        "poměr": "kolik čeho má být (např. 1:2)",
        "průmyslově": "vyrobené ve velké továrně",
        "verdikt": "konečný názor, rozhodnutí",
        "epidemie": "když se něco šíří u hodně lidí",
        "metabolismus": "co se děje v těle s jídlem (přeměna)",
        "náhražka": "něco místo něčeho jiného",
        "sladivost": "jak moc něco sladí",
        "energetický": "spojený s energií (kalorie)",
        "nízkokalorický": "má málo kalorií",
        "odpalované": "druh těsta, které se nejdřív zahřeje v hrnci a pak peče",
        "absenci": "chybění něčeho",
        "nadlehčený": "lehčí a nadýchanější",
        "polysacharidy": "složitější cukry (např. škrob, vláknina)",
        "fruktóza": "ovocný cukr",
        "ztužené": "zpevněné (tuk je tvrdší)",
        "kardiovaskulární": "souvisí se srdcem a cévami",
        "přebít": "zahrát silnější kartu a porazit předchozí",
        "žolík": "speciální karta, která může nahradit jinou",
        "kombinace": "skupina karet zahraná spolu",
    }

    if w in dict_base:
        return dict_base[w]

    # lehká „jazyková“ vysvětlení (bez rizika halucinace)
    if w.endswith("li"):
        return "udělali to (např. dodrželi = drželi se pravidel)"
    if w.endswith("o") and len(w) > 6:
        return ""

    # raději prázdné (žák doplní s učitelem)
    return ""


def build_glossary(doc: Document, words: list[str], grade: int):
    add_h2(doc, "Slovníček (pomáhá porozumět textu)")
    doc.add_paragraph("Dopiš si poznámky. Když vysvětlení nestačí, doplň vlastními slovy.")
    add_spacer(doc)

    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text = "Slovo"
    hdr[1].text = "Vysvětlení (EdRead AI)"
    hdr[2].text = "Moje poznámka"

    for w in words:
        row = table.add_row().cells
        row[0].text = w
        explanation = safe_explain_word(w, grade)
        row[1].text = explanation if explanation else ""
        row[2].text = "_____________________________"


def pick_glossary_words(text: str, max_words: int, preferred: list[str]) -> list[str]:
    """
    Kombinace:
    - vezmeme 'preferred' (které jsi chtěla pedagogicky)
    - doplníme automaticky z textu (delší slova, bez čísel), a vyhodíme duplicity
    """
    found = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    found = [f.strip() for f in found if len(f.strip()) >= 8]
    merged = []

    for w in preferred:
        if w not in merged:
            merged.append(w)

    for w in found:
        lw = w.lower()
        # nechceme „správným“, „maximálně“ apod. (bez užitku)
        if lw in {"správným", "maximálně"}:
            continue
        if w not in merged:
            merged.append(w)

    return merged[:max_words]


def build_questions_abc(doc: Document, title: str, grade: int):
    """
    Šablonové otázky A/B/C – stabilní (nebude se ti rozbíjet jako předtím).
    U každého textu se drží čtenářských strategií: vyhledání – interpretace – názor.
    """
    add_h2(doc, "Otázky A/B/C")
    doc.add_paragraph("A = najdi v textu • B = přemýšlej a vysvětli • C = můj názor")
    add_spacer(doc)

    add_box_hint(doc, "A) Porozumění textu (najdi v textu)")
    doc.add_paragraph("1) Najdi v textu větu, která říká, co bylo nejlepší / nejdůležitější.")
    doc.add_paragraph("Odpověď: ________________________________________________")
    doc.add_paragraph("2) Najdi dvě informace, které jsou přímo napsané v textu.")
    doc.add_paragraph("Odpověď: ________________________________________________")
    add_spacer(doc)

    add_box_hint(doc, "B) Přemýšlení o textu (vysvětli)")
    doc.add_paragraph("3) Proč si myslíš, že autor/hodnotitel došel k takovému závěru? Napiš důvod.")
    doc.add_paragraph("Odpověď: ________________________________________________")
    doc.add_paragraph("4) Najdi v textu jednu větu – NÁZOR a jednu větu – FAKT.")
    doc.add_paragraph("NÁZOR: _________________________________________________")
    doc.add_paragraph("FAKT: _________________________________________________")
    add_spacer(doc)

    add_box_hint(doc, "C) Můj názor")
    doc.add_paragraph("5) Souhlasíš s tím, co text říká? Proč ano / proč ne?")
    doc.add_paragraph("Odpověď: ________________________________________________")
    add_spacer(doc)

    add_h2(doc, "Sebehodnocení")
    doc.add_paragraph("Označ: 😃 / 🙂 / 😐")
    doc.add_paragraph("Rozuměl/a jsem textu:  😃  🙂  😐")
    doc.add_paragraph("Uměl/a jsem najít odpovědi v textu:  😃  🙂  😐")
    doc.add_paragraph("Umím to vysvětlit vlastními slovy:  😃  🙂  😐")


def build_drama(doc: Document, lines: list[str]):
    add_h2(doc, "Dramatizace (motivační začátek hodiny)")
    for line in lines:
        doc.add_paragraph(f"• {line}")
    add_spacer(doc)


def build_pyramid_template_docx() -> bytes:
    """
    Podklad pro lepení pyramidy (3. třída – Karetní hra).
    Vytvoří velkou tabulku s řádky, kam se lepí kartičky.
    """
    doc = Document()
    set_doc_defaults(doc, font_size=12)
    add_title(doc, "Pyramida síly zvířat (podklad pro lepení)")
    doc.add_paragraph("Nalep kartičky do pyramidy: dole nejslabší, nahoře nejsilnější.")
    add_spacer(doc)

    # pyramid: 12 úrovní (kosatka nahoře)
    levels = len(KARETNI_PORADI)
    table = doc.add_table(rows=levels, cols=1)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # nahoře nejsilnější => kosatka
    for i in range(levels):
        animal = KARETNI_PORADI[-1 - i]  # shora dolů
        cell = table.cell(i, 0)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"{i+1}. místo: {animal}")
        run.bold = True
        # prostor pro nalepení
        cell.add_paragraph("\n\n\n").alignment = WD_ALIGN_PARAGRAPH.CENTER

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def build_animal_cards_docx() -> bytes:
    """
    Kartičky zvířat (emoji) – 3 sloupce – tisk.
    Emoji font nastavíme na Segoe UI Emoji.
    """
    doc = Document()
    set_doc_defaults(doc, font_size=11)

    add_title(doc, "Kartičky zvířat (emoji) – Karetní hra")
    doc.add_paragraph("Vystřihni kartičky. Použij je pro pyramidu a pro práci s pravidly.")
    add_spacer(doc)

    cols = 3
    rows = math.ceil(len(ANIMALS_CARDS) / cols)
    table = doc.add_table(rows=rows, cols=cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            cell = table.cell(r, c)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            if idx >= len(ANIMALS_CARDS):
                continue

            name_cz, emoji = ANIMALS_CARDS[idx]

            run1 = p.add_run(emoji)
            run1.font.name = "Segoe UI Emoji"
            run1._element.rPr.rFonts.set(qn("w:eastAsia"), "Segoe UI Emoji")
            run1.font.size = Pt(34)

            p.add_run("\n")

            run2 = p.add_run(name_cz)
            run2.bold = True
            run2.font.size = Pt(12)

            # trochu prostoru
            cell.add_paragraph("")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def build_work_sheet(doc_title: str, cfg: dict, variant: str) -> bytes:
    """
    variant: "full" | "simple" | "lmp"
    """
    doc = Document()
    set_doc_defaults(doc, font_size=11)
    add_title(doc, f"EdRead AI – Pracovní list ({variant.upper()})")
    doc.add_paragraph(f"Název textu: {doc_title}    |    Ročník: {cfg['rocnik']}    |    Tag RVP: {cfg['tag_rvp']}")
    doc.add_paragraph(f"Datum: {date.today().isoformat()}")
    add_spacer(doc)

    # dramatizace
    build_drama(doc, cfg["drama"])

    # text pro žáky (plný / zjednodušený / LMP)
    add_h2(doc, "Text pro žáky")
    if variant == "full":
        doc.add_paragraph(cfg["text_full"])
    elif variant == "simple":
        doc.add_paragraph(cfg["text_simple"])
    else:
        doc.add_paragraph(cfg["text_lmp"])
    add_spacer(doc)

    # speciální část pro Karetní hru: pyramida instrukce
    if doc_title.startswith("Karetní hra"):
        add_h2(doc, "Pyramida síly (pomůcka k porozumění pravidlům)")
        doc.add_paragraph("1) Vystřihni kartičky zvířat (emoji).")
        doc.add_paragraph("2) Nalep je do pyramidy: dole nejslabší, nahoře nejsilnější.")
        doc.add_paragraph("3) Pak zkus vysvětlit pravidlo: kdo může koho „přebít“.")
        add_spacer(doc)
        add_box_hint(doc, "📌 DŮLEŽITÉ: Pyramida (podklad pro lepení) je v samostatném souboru.")

    # slovníček
    words = pick_glossary_words(
        cfg["text_full"],
        max_words=12 if cfg["rocnik"] >= 4 else 10,
        preferred=cfg["slovicka_hint"],
    )
    build_glossary(doc, words, cfg["rocnik"])
    add_spacer(doc)

    # otázky
    build_questions_abc(doc, doc_title, cfg["rocnik"])

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def build_methodical(doc_title: str, cfg: dict) -> bytes:
    doc = Document()
    set_doc_defaults(doc, font_size=11)
    add_title(doc, "📘 Metodický list pro učitele (EdRead AI)")
    doc.add_paragraph(f"Téma: {doc_title} | Ročník: {cfg['rocnik']} | Tag RVP: {cfg['tag_rvp']}")
    doc.add_paragraph(f"Datum: {date.today().isoformat()}")
    add_spacer(doc)

    add_h2(doc, "Cíl")
    doc.add_paragraph("Rozvoj čtenářské gramotnosti: porozumění textu, práce s informací, interpretace a argumentace.")
    doc.add_paragraph("Podpora je založena na pracovních listech (ne na přímé komunikaci žáků s AI).")

    add_spacer(doc)
    add_h2(doc, "Propojení s RVP ZV (Jazyk a jazyková komunikace – ČJL)")
    doc.add_paragraph("Žák vyhledává informace v textu, rozlišuje podstatné informace, interpretuje a hodnotí obsah.")
    doc.add_paragraph("Žák formuluje odpovědi, vyjadřuje vlastní názor a zdůvodňuje ho.")

    add_spacer(doc)
    add_h2(doc, "Doporučený průběh (45 minut)")
    doc.add_paragraph("1) Motivační dramatizace (5–7 min) – krátká scénka k tématu.")
    doc.add_paragraph("2) Čtení textu (10–15 min) – po odstavcích, práce s podtrháváním.")
    doc.add_paragraph("3) Slovníček (5–8 min) – vysvětlení slov, doplnění poznámek.")
    doc.add_paragraph("4) Otázky A/B/C (15 min) – vyhledání → interpretace → názor.")
    doc.add_paragraph("5) Sebehodnocení (3–5 min).")

    if doc_title.startswith("Karetní hra"):
        add_spacer(doc)
        add_h2(doc, "Specifická pomůcka: pyramida síly")
        doc.add_paragraph("Žáci lepí kartičky zvířat do pyramidy (dole nejslabší, nahoře nejsilnější).")
        doc.add_paragraph("Cíl: vizuální opora pro pochopení logiky pravidel (přebíjení).")

    add_spacer(doc)
    add_h2(doc, "Digitální varianta (EdRead AI)")
    doc.add_paragraph("Učitel vygeneruje 3 varianty pracovního listu (plný / zjednodušený / LMP) + metodiku.")
    doc.add_paragraph("Materiály lze tisknout nebo používat na interaktivní tabuli.")
    if doc_title.startswith("Karetní hra"):
        doc.add_paragraph("Navíc se generují kartičky zvířat (emoji) a podklad pro pyramidu (lepení).")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


# ---------------------------
# Streamlit UI
# ---------------------------

st.title("📘 EdRead AI – prototyp")
st.write("Generátor pracovních listů a metodiky (DOCX) pro 1. stupeň ZŠ.")

choice = st.selectbox("Vyber text:", list(TEXTS.keys()))
cfg = TEXTS[choice]

st.info("Klikni na **Vygenerovat**. Poté se objeví tlačítka ke stažení (nezmizí).")

if st.button("✅ Vygenerovat materiály", type="primary"):
    # uložíme do session_state, aby download tlačítka nezmizela
    st.session_state["full_doc"] = build_work_sheet(choice, cfg, "full")
    st.session_state["simple_doc"] = build_work_sheet(choice, cfg, "simple")
    st.session_state["lmp_doc"] = build_work_sheet(choice, cfg, "lmp")
    st.session_state["method_doc"] = build_methodical(choice, cfg)

    if choice.startswith("Karetní hra"):
        st.session_state["cards_doc"] = build_animal_cards_docx()
        st.session_state["pyramid_doc"] = build_pyramid_template_docx()
    else:
        st.session_state["cards_doc"] = None
        st.session_state["pyramid_doc"] = None

    st.success("Hotovo. Níže stáhni potřebné soubory.")

st.subheader("⬇️ Ke stažení (DOCX)")

def dl(key, filename, label):
    if key in st.session_state and st.session_state[key]:
        st.download_button(
            label=label,
            data=st.session_state[key],
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

dl("full_doc", f"pracovni_list_{choice}_PLNY.docx", "📄 Pracovní list – plný")
dl("simple_doc", f"pracovni_list_{choice}_ZJEDNODUSENY.docx", "📄 Pracovní list – zjednodušený")
dl("lmp_doc", f"pracovni_list_{choice}_LMP_SPU.docx", "📄 Pracovní list – LMP/SPU")
dl("method_doc", f"metodicky_list_{choice}.docx", "📘 Metodický list pro učitele")

if choice.startswith("Karetní hra"):
    dl("cards_doc", "karty_zvirat_emoji_Karetni_hra.docx", "🃏 Kartičky zvířat (emoji) – 3 sloupce")
    dl("pyramid_doc", "pyramida_podklad_Karetni_hra.docx", "🔺 Pyramida (podklad pro lepení)")

st.caption("EdRead AI (prototyp) – generuje materiály pro testování čtenářské gramotnosti.")
