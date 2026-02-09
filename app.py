# app.py — EdRead AI (Streamlit + python-docx)
# Funkční verze: žádné NameError, download tlačítka nemizí, tabulky i v simpl/LMP.
# Tabulky se vkládají jako PNG obrázky (100% shoda s PDF).

import os
import io
import json
import requests
import streamlit as st
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn


# =========================
# OpenAI helpers (nepadá)
# =========================
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

def get_openai_key() -> str:
    # Streamlit Cloud secrets
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return str(st.secrets["OPENAI_API_KEY"]).strip()
    except Exception:
        pass
    return (os.getenv("OPENAI_API_KEY") or "").strip()

def get_openai_model() -> str:
    try:
        if "OPENAI_MODEL" in st.secrets:
            return str(st.secrets["OPENAI_MODEL"]).strip()
    except Exception:
        pass
    return (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()

def call_openai_chat(system_prompt: str, user_prompt: str, temperature: float = 0.2, max_tokens: int = 2200) -> str:
    api_key = get_openai_key()
    if not api_key:
        raise RuntimeError("Chybí OPENAI_API_KEY (Streamlit Cloud → Settings → Secrets).")

    payload = {
        "model": get_openai_model(),
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    r = requests.post(OPENAI_CHAT_URL, headers=headers, data=json.dumps(payload), timeout=90)
    if r.status_code != 200:
        try:
            err = r.json()
        except Exception:
            err = r.text
        raise RuntimeError(f"OpenAI API chyba ({r.status_code}): {err}")

    data = r.json()
    return data["choices"][0]["message"]["content"]


# =========================
# Utility: DOCX styling
# =========================
def set_doc_defaults(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

def add_h1(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(16)
    p.space_after = Pt(6)

def add_h2(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(13)
    p.space_before = Pt(8)
    p.space_after = Pt(4)

def add_note(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    p.runs[0].italic = True

def add_spacer(doc: Document, cm: float = 0.3) -> None:
    p = doc.add_paragraph("")
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(int(cm * 28.35))

def doc_to_bytes(doc: Document) -> bytes:
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def safe_add_picture(doc: Document, path: str, width_cm: float) -> bool:
    if not path:
        return False
    if not os.path.exists(path):
        return False
    try:
        doc.add_picture(path, width=Cm(width_cm))
        return True
    except Exception:
        return False


# =========================
# Asset paths
# =========================
ASSET_DIR = "assets"
ASSET_KARETNI_TABLE = os.path.join(ASSET_DIR, "karetni_tabulka.png")
ASSET_SLADKE_TABLES = os.path.join(ASSET_DIR, "sladke_tabulky.png")
ASSET_VENECKY_TABLE = os.path.join(ASSET_DIR, "venecky_tabulka.png")


# =========================
# Packs (3 školní texty)
# =========================
@dataclass
class Pack:
    key: str
    title: str
    grade: int
    full_text: str
    # tabulky jako PNG (100% shoda s PDF)
    tables_png: Optional[str]
    # dramatizace (záměrně bez věty „Učitel/ka: ...“ – ta patří jen do metodiky)
    drama_intro: str
    drama_scene: List[Tuple[str, str]]
    # otázky (A/B/C)
    questions_A: List[str]
    questions_B: List[str]
    questions_C: List[str]
    # slovníček: pro školní texty může být předpřipravený; jinak generujeme AI
    glossary_seed: List[str]
    # jen pro karetní hru
    include_pyramid: bool = False


# Pozn.: plné texty si sem dej přesně – já tu držím kratší zástupné, aby soubor nebyl nekonečný.
# Ve tvém projektu už ty texty máš; stačí je sem vložit (plná verze).
# Pokud je nechceš duplikovat, můžeš je načítat ze souborů – ale teď dávám „samostatný app.py“.

KARETNI_FULL = """(SEM VLOŽ PLNÝ TEXT „Karetní hra“ tak, jak ho používáš v plné verzi.)
POZN.: Tabulka „Kdo přebije koho?“ bude vložena jako PNG do všech verzí.
"""

SLADKE_FULL = """(SEM VLOŽ PLNÝ TEXT „Sladké mámení“ včetně navazujícího zadání, stejně jako v originálu.)
POZN.: Tabulky budou vloženy jako PNG do všech verzí.
"""

VENECKY_FULL = """(SEM VLOŽ PLNÝ TEXT „Věnečky“ včetně zadání, stejně jako v originálu.)
POZN.: Tabulka bude vložena jako PNG do všech verzí.
"""

PACKS: Dict[str, Pack] = {
    "karetni": Pack(
        key="karetni",
        title="Karetní hra",
        grade=3,
        full_text=KARETNI_FULL,
        tables_png=ASSET_KARETNI_TABLE,
        drama_intro="Na začátku si krátce zahrajeme situaci z karetní hry. Pomůže nám to pochopit pravidla dřív, než je budeme číst.",
        drama_scene=[
            ("Žák A (Má kartu)", "„Mám zvíře. Myslíš, že tě přebiju?“"),
            ("Žák B (Má kartu)", "„Nevím. Zkus to. Podíváme se do tabulky, kdo koho přebije.“"),
            ("Žák C (Rozhodčí)", "„Stop! Než zahrajete kolo, řekněte nahlas: Kdo přebíjí koho a proč.“"),
            ("Všichni", "„Hrajeme férově: nejdřív pravidlo, potom tah!“"),
        ],
        questions_A=[
            "Najdi v pravidlech, kdy hráč vyhrává kolo. Odpověz celou větou.",
            "Jak se pozná, že je nějaké zvíře „žolík“? Najdi to v textu.",
            "Kde v pravidlech je napsáno, co se děje po odehrání karty?"
        ],
        questions_B=[
            "Proč je užitečná tabulka „Kdo přebije koho?“ Vysvětli vlastními slovy.",
            "Co by se stalo, kdyby tabulka neexistovala? Jak by se hra změnila?",
        ],
        questions_C=[
            "Líbí se ti, že hra má žolíka? Proč ano / ne?",
            "Napiš jedno pravidlo, které bys do hry přidal/a, aby byla ještě spravedlivější.",
        ],
        glossary_seed=["přebít", "žolík", "tah", "pravidla", "férově", "rozhodčí"],
        include_pyramid=True
    ),

    "sladke": Pack(
        key="sladke",
        title="Sladké mámení",
        grade=5,
        full_text=SLADKE_FULL,
        tables_png=ASSET_SLADKE_TABLES,
        drama_intro="Než začneme číst, krátce si zahrajeme rozhovor „novinář × odborník“. Pomůže nám to poznat, o čem text bude.",
        drama_scene=[
            ("Novinář/ka", "„Proč dnes lidé řeší, kolik má sladkost energie?“"),
            ("Odborník/ice", "„Protože přibývá obezita a s ní i další nemoci.“"),
            ("Novinář/ka", "„A co chtějí zákazníci v Česku?“"),
            ("Odborník/ice", "„Často nechtějí, aby jim to někdo připomínal. Chtějí si prostě zamlsat.“"),
        ],
        questions_A=[
            "Které tvrzení je v rozporu s výchozím textem? Vypiš písmeno a jednu větu vysvětlení.",
            "Jaké vlastnosti by podle článku nemělo mít ideální sladidlo?",
        ],
        questions_B=[
            "Proč se ve světě zvyšuje poptávka po nízkokalorických sladkostech? Odpověz vlastními slovy.",
            "Vysvětli přirovnání „novodobí alchymisté hledají recept na zlato“.",
        ],
        questions_C=[
            "Myslíš, že je lepší, když je energetická hodnota na přední straně obalu? Proč?",
            "Jaký typ sladkostí bys doporučil/a na „energii na cesty“ a proč?",
        ],
        glossary_seed=["obezita", "poptávka", "energetický", "sladidlo", "náhražka", "kalorie", "polysacharidy", "transmastné"],
        include_pyramid=False
    ),

    "venecky": Pack(
        key="venecky",
        title="Věnečky",
        grade=4,
        full_text=VENECKY_FULL,
        tables_png=ASSET_VENECKY_TABLE,
        drama_intro="Na začátku si zahrajeme krátkou „degustaci“. Cílem je pochopit, že hodnotitelka posuzuje více věcí najednou (chuť, vůni, suroviny, těsto).",
        drama_scene=[
            ("Hodnotitel/ka", "„Podívám se na vzhled. A teď vůně…“"),
            ("Pomocník/ice", "„A co suroviny? Je to poctivé, nebo chemické?“"),
            ("Hodnotitel/ka", "„A ještě korpus: je křupavý, měkký, nebo tvrdý?“"),
            ("Pomocník/ice", "„Takže nestačí, že to vypadá hezky!“"),
        ],
        questions_A=[
            "Který věneček neobsahuje pudink uvařený z mléka?",
            "Ve kterém věnečku je rum použitý hlavně proto, aby zakryl jiné nedostatky?",
            "Který podnik dopadl v testu nejlépe?",
        ],
        questions_B=[
            "Co všechno podle textu potřebuje cukrář k výrobě poctivého věnečku? Vypiš.",
            "Proč nestačí hodnotit jen „vzhled“?",
        ],
        questions_C=[
            "Souhlasíš s tím, že nejdražší věneček nemusel být nejlepší? Proč?",
            "Podle čeho bys ty hodnotil/a zákusek? Napiš 3 kritéria.",
        ],
        glossary_seed=["degustace", "korpus", "pudink", "suroviny", "receptura", "poměr", "chemický", "verdikt"],
        include_pyramid=False
    ),
}


# =========================
# AI: zjednodušení + LMP/SPU + slovníček
# =========================
def ai_generate_variants(full_text: str, grade: int, title: str) -> Dict[str, str]:
    """
    Vrací dict: {"simpl": ..., "lmp": ...}
    Pokud není API key, vrátí fallback (jen plný text).
    """
    if not get_openai_key():
        return {"simpl": full_text, "lmp": full_text}

    system = (
        "Jsi odborník na český jazyk, didaktiku čtenářské gramotnosti na 1. stupni ZŠ a tvorbu didaktických textů. "
        "Piš česky, bez chyb, bez odrážek v samotném textu pro žáky. "
        "Zachovej význam, ale přizpůsob jazyk věku. Nevymýšlej fakta."
    )

    user = f"""
Uprav následující text pro žáky {grade}. ročníku ZŠ.
Text se jmenuje: {title}.

Vygeneruj 2 verze:
1) ZJEDNODUŠENÁ verze (pro běžné žáky): kratší věty, jednodušší slovní zásoba, zachovej klíčové informace.
2) LMP/SPU verze: ještě jednodušší, velmi krátké věty, jasná struktura, odstranění metafor a složitých souvětí.

DŮLEŽITÉ:
- Nepřidávej žádné nové informace, jen zjednodušuj.
- Zachovej vlastní jména, čísla a data.
- Výstup vrať POUZE jako JSON v tomto formátu:
{{
  "simpl": "...",
  "lmp": "..."
}}

TEXT:
\"\"\"{full_text}\"\"\"
"""
    out = call_openai_chat(system, user, temperature=0.15, max_tokens=2600)

    try:
        data = json.loads(out)
        simpl = str(data.get("simpl", full_text)).strip()
        lmp = str(data.get("lmp", full_text)).strip()
        if not simpl:
            simpl = full_text
        if not lmp:
            lmp = full_text
        return {"simpl": simpl, "lmp": lmp}
    except Exception:
        # fallback při rozbitém JSONu
        return {"simpl": full_text, "lmp": full_text}


def ai_explain_glossary(words: List[str], grade: int) -> Dict[str, str]:
    """
    Vrátí mapu slovo->vysvětlení. Když není API key, vrátí prázdné.
    """
    if not get_openai_key():
        return {}

    system = (
        "Jsi učitel českého jazyka na 1. stupni. Vysvětluješ slova krátce, věcně a dětsky, bez chyb. "
        "Vysvětlení mají být max. 10 slov, bez uvozovek."
    )
    user = f"""
Vysvětli stručně pro žáka {grade}. ročníku tato slova.
Vrať POUZE jako JSON slovník: {{ "slovo": "vysvětlení", ... }}.
Slova:
{", ".join(words)}
"""
    out = call_openai_chat(system, user, temperature=0.1, max_tokens=1200)
    try:
        data = json.loads(out)
        # očista
        cleaned = {}
        for k, v in data.items():
            kk = str(k).strip()
            vv = str(v).strip()
            if kk and vv:
                cleaned[kk] = vv
        return cleaned
    except Exception:
        return {}


# =========================
# Karetní hra: pyramid + kartičky (emoji)
# =========================
ANIMALS_ORDER_STRONG_TO_WEAK = [
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
    ("chameleon (žolík)", "🦎"),
]

def add_pyramid_column(doc: Document) -> None:
    """
    Sloupec (ne pyramidové patro) – každé zvíře má vlastní úroveň.
    Buňky velké, aby se vešly kartičky.
    """
    add_h2(doc, "Pyramida síly (nalepování)")
    doc.add_paragraph("Vystřihni kartičky zvířat a nalep je do sloupce: nahoře nejsilnější, dole nejslabší.")
    doc.add_paragraph("Žádné dvě kartičky nejsou na stejné úrovni.")

    rows = len(ANIMALS_ORDER_STRONG_TO_WEAK)
    table = doc.add_table(rows=rows, cols=1)
    table.autofit = False

    # šířka sloupce
    for row in table.rows:
        row.cells[0].width = Cm(8.5)

    # výška buněk – bezpečně bez XML triků (Word si to drží)
    # Uděláme prázdné řádky a větší odsazení
    for i in range(rows):
        cell = table.cell(i, 0)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"{i+1}. ________________________________")
        run.font.size = Pt(10)
        # přidáme „vzduch“: prázdné odstavce v buňce
        for _ in range(2):
            cell.add_paragraph("")

    doc.add_paragraph("Tip: Začni nalepovat shora (nejsilnější) a postupuj dolů.")


def build_animal_cards_doc() -> Document:
    """
    Kartičky 3 sloupce: emoji + český název.
    Bez „siluet“ – jen hezké emoji a text, bezpečné pro tisk.
    """
    doc = Document()
    set_doc_defaults(doc)
    add_h1(doc, "Kartičky zvířat – Karetní hra (k vystřižení)")
    doc.add_paragraph("Vystřihni kartičky. Slouží k nalepení do sloupce (pyramidy síly).")

    cols = 3
    items = ANIMALS_ORDER_STRONG_TO_WEAK[:]  # strong->weak
    rows = (len(items) + cols - 1) // cols

    table = doc.add_table(rows=rows, cols=cols)
    table.autofit = False
    for c in range(cols):
        for r in range(rows):
            table.cell(r, c).width = Cm(6.0)

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.text = ""
            if idx < len(items):
                name, emoji = items[idx]
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run1 = p.add_run(f"{emoji}\n")
                run1.font.size = Pt(28)
                run2 = p.add_run(name)
                run2.bold = True
                run2.font.size = Pt(12)
            idx += 1

    doc.add_paragraph("Poznámka: „chameleon (žolík)“ je speciální karta.")
    return doc


# =========================
# Slovníček (na konci)
# =========================
def add_glossary_block(doc: Document, grade: int, seed_words: List[str], text_for_pick: str) -> None:
    add_h2(doc, "Slovníček pojmů (na závěr pracovního listu)")
    doc.add_paragraph("Nejdřív si slovíčka projdete společně s učitelem/kou. Pak se vrátíte k textu a budete číst snadněji.")

    # vybereme „logicky“: seed + pár dalších delších slov z textu
    words = []
    for w in seed_words:
        if w not in words:
            words.append(w)

    # doplň z textu (bez délkového filtru jako „8+“, ale jemně: unikátní slova 6+ písmen)
    import re
    found = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text_for_pick.lower())
    for w in found:
        if len(w) >= 6 and w not in words and len(words) < 14:
            words.append(w)

    explanations = ai_explain_glossary(words, grade)  # může být prázdné

    # formát: slovo — vysvětlení + linka na poznámku
    for w in words:
        p = doc.add_paragraph()
        runw = p.add_run(f"• {w} — ")
        runw.bold = True
        expl = explanations.get(w, "").strip()
        if expl:
            p.add_run(expl)
            p.add_run("  | Poznámka: ________________________________")
        else:
            # bez otravné věty – jen linka na dopsání
            p.add_run("_______________________________  | Poznámka: ________________________________")


# =========================
# Student doc builder
# =========================
def build_student_doc(pack: Pack, variant: str, text_variant: str) -> Document:
    """
    variant: "full" | "simpl" | "lmp"
    text_variant: text, který patří do dané verze
    """
    doc = Document()
    set_doc_defaults(doc)

    # Titulek
    add_h1(doc, f"NÁZEV ÚLOHY: {pack.title} — {variant.upper()}")
    doc.add_paragraph("JMÉNO: ________________________________    DATUM: _______________")

    add_spacer(doc, 0.2)

    # 1) Dramatizace – jen intro + role, bez věty pro učitele
    add_h2(doc, "1) Krátká dramatizace (začátek hodiny)")
    doc.add_paragraph(pack.drama_intro)
    for role, line in pack.drama_scene:
        doc.add_paragraph(f"{role}: {line}")

    add_spacer(doc, 0.2)

    # 2) Text + tabulky uvnitř bloku pro čtení
    add_h2(doc, "2) Text pro čtení")
    doc.add_paragraph(text_variant)

    # Tabulky vždy i v simpl a lmp
    if pack.tables_png:
        add_spacer(doc, 0.2)
        add_h2(doc, "Tabulky / přehledy k textu")
        ok = safe_add_picture(doc, pack.tables_png, width_cm=16.5)
        if not ok:
            add_note(doc, "⚠️ Tabulka není k dispozici (chybí PNG v assets/).")

    # Karetní hra: pyramida ve všech verzích
    if pack.include_pyramid:
        add_spacer(doc, 0.2)
        add_pyramid_column(doc)

    add_spacer(doc, 0.2)

    # 3) Otázky A/B/C
    add_h2(doc, "3) Otázky")
    doc.add_paragraph("A) Najdi v textu (pracuj s informací):")
    for q in pack.questions_A:
        doc.add_paragraph(f"• {q}\n  Odpověď: ______________________________________________")

    doc.add_spacer = add_spacer  # fallback kompatibilita

    add_spacer(doc, 0.15)
    doc.add_paragraph("B) Přemýšlej a vysvětli (porozumění):")
    for q in pack.questions_B:
        doc.add_paragraph(f"• {q}\n  Odpověď: ______________________________________________\n  ______________________________________________")

    add_spacer(doc, 0.15)
    doc.add_paragraph("C) Můj názor (kritické čtení):")
    for q in pack.questions_C:
        doc.add_paragraph(f"• {q}\n  Odpověď: ______________________________________________\n  ______________________________________________")

    # 4) Slovníček až na konci
    add_spacer(doc, 0.2)
    add_glossary_block(doc, pack.grade, pack.glossary_seed, text_variant)

    return doc


# =========================
# Methodology doc
# =========================
def build_method_doc(pack: Pack) -> Document:
    doc = Document()
    set_doc_defaults(doc)
    add_h1(doc, f"Metodický list pro učitele — {pack.title}")

    add_h2(doc, "Cíl hodiny")
    doc.add_paragraph(
        "Rozvoj čtenářské gramotnosti: vyhledávání informací, porozumění, interpretace a kritické čtení "
        "(rozlišení faktu a názoru, práce s tabulkou/přehledem, formulace vlastního stanoviska)."
    )

    add_h2(doc, "Doporučený postup (45 min)")
    doc.add_paragraph("1) Dramatizace (5–7 min)")
    doc.add_paragraph("   - krátká scénka podle pracovního listu, zapojení více žáků do rolí, cílem je motivace a „vhled“ do tématu.")

    doc.add_paragraph("2) Slovníček (5–8 min)")
    doc.add_paragraph(
        "   - i když je slovníček na konci pracovního listu, pracujte s ním hned po dramatizaci: "
        "vyberte slova, která mohou brzdit porozumění, krátce vysvětlete, žáci si doplní poznámky."
    )
    doc.add_paragraph("   - poté se vraťte na část „Text pro čtení“.")

    doc.add_paragraph("3) Čtení textu (10–12 min)")
    doc.add_paragraph("   - tiché čtení / čtení po odstavcích, kontrolní otázky, práce s tabulkami (pokud jsou součástí).")

    doc.add_paragraph("4) Otázky A/B/C (15–18 min)")
    doc.add_paragraph("   - A: dohledání informace v textu/tabulce")
    doc.add_paragraph("   - B: vysvětlení vlastními slovy, interpretace")
    doc.add_paragraph("   - C: vlastní názor + zdůvodnění")

    doc.add_paragraph("5) Reflexe (2–3 min)")
    doc.add_paragraph("   - krátce: co pomohlo porozumět (dramatizace, slovníček, tabulka).")

    add_h2(doc, "Rozdíly mezi verzemi (pro volbu u žáků)")
    doc.add_paragraph("Plná verze: plný text, plné formulace, běžná náročnost pro ročník.")
    doc.add_paragraph("Zjednodušená verze: stejné informace, kratší věty, jednodušší slovní zásoba.")
    doc.add_paragraph("LMP/SPU verze: velmi krátké věty, maximální srozumitelnost, odstranění složitých souvětí.")
    doc.add_paragraph("Ve všech verzích zůstávají tabulky/přehledy, pokud jsou nutné pro odpovědi.")

    add_h2(doc, "Poznámka k tabulkám")
    doc.add_paragraph(
        "Tabulky jsou vloženy jako obrázek (PNG) kvůli 100% shodě s originálem (bez chyb v procentech/známkách). "
        "Ujistěte se, že soubory PNG jsou ve složce assets/."
    )

    return doc


# =========================
# Streamlit UI + session state (tlačítka nemizí)
# =========================
def ensure_state():
    if "generated" not in st.session_state:
        st.session_state.generated = False
    if "files" not in st.session_state:
        st.session_state.files = {}  # key -> bytes
    if "names" not in st.session_state:
        st.session_state.names = {}  # key -> filename

def generate_all(pack: Pack, full_text: str, grade: int, title: str):
    # Variants from AI (or fallback)
    variants = ai_generate_variants(full_text, grade, title)
    text_full = full_text
    text_simpl = variants.get("simpl", full_text)
    text_lmp = variants.get("lmp", full_text)

    # update pack meta for custom
    pack2 = Pack(
        key=pack.key,
        title=title,
        grade=grade,
        full_text=full_text,
        tables_png=pack.tables_png,
        drama_intro=pack.drama_intro,
        drama_scene=pack.drama_scene,
        questions_A=pack.questions_A,
        questions_B=pack.questions_B,
        questions_C=pack.questions_C,
        glossary_seed=pack.glossary_seed,
        include_pyramid=pack.include_pyramid
    )

    # student docs
    doc_full = build_student_doc(pack2, "full", text_full)
    doc_simpl = build_student_doc(pack2, "simpl", text_simpl)
    doc_lmp = build_student_doc(pack2, "lmp", text_lmp)

    # method
    doc_method = build_method_doc(pack2)

    out = {
        "pl_full": doc_to_bytes(doc_full),
        "pl_simpl": doc_to_bytes(doc_simpl),
        "pl_lmp": doc_to_bytes(doc_lmp),
        "method": doc_to_bytes(doc_method),
    }

    # Karetní hra: kartičky extra
    if pack2.include_pyramid:
        cards_doc = build_animal_cards_doc()
        out["cards"] = doc_to_bytes(cards_doc)

    return out


def main():
    st.set_page_config(page_title="EdRead AI", layout="centered")
    ensure_state()

    st.title("EdRead AI — generátor pracovních listů (pro diplomku)")

    st.markdown(
        "Vyberte jeden z připravených textů (Karetní hra / Sladké mámení / Věnečky) nebo vložte vlastní text. "
        "Aplikace vygeneruje: **plnou verzi**, **zjednodušenou verzi**, **LMP/SPU verzi** a **metodiku**."
    )

    mode = st.radio("Režim:", ["Připravené texty (3 úlohy)", "Vlastní text"], horizontal=True)

    if mode == "Připravené texty (3 úlohy)":
        choice = st.selectbox("Vyber úlohu:", [
            ("Karetní hra (3. třída)", "karetni"),
            ("Sladké mámení (5. třída)", "sladke"),
            ("Věnečky (4. třída)", "venecky"),
        ])
        pack = PACKS[choice[1]]
        title = pack.title
        grade = pack.grade
        full_text = pack.full_text

        st.info("Pozn.: Ujisti se, že v app.py jsou vložené PLNÉ texty (ne jen zástupné).")

    else:
        title = st.text_input("Název úlohy:", value="Můj text")
        grade = st.selectbox("Ročník:", [3, 4, 5], index=0)
        full_text = st.text_area("Vlož plný text:", height=260)
        pack = PACKS["sladke"]  # použijeme univerzální strukturu (bez pyramidy)
        # pro vlastní text vypneme pyramidu i tabulky (pokud nechceš)
        pack = Pack(
            key="custom",
            title=title,
            grade=grade,
            full_text=full_text,
            tables_png=None,
            drama_intro="Než začneme číst, zahrajeme krátkou scénku k tématu textu. Pomůže nám to naladit se na čtení.",
            drama_scene=[
                ("Žák/yně 1", "„O čem asi ten text bude?“"),
                ("Žák/yně 2", "„Zkusme najít klíčová slova.“"),
                ("Žák/yně 3", "„A pak si to ověříme při čtení.“"),
            ],
            questions_A=[
                "Najdi v textu jednu důležitou informaci a napiš ji celou větou.",
                "Najdi v textu odpověď na otázku: Kdo? Co? Kdy? Kde? (vyber jednu).",
            ],
            questions_B=[
                "Vysvětli vlastními slovy, co je hlavní myšlenka textu.",
            ],
            questions_C=[
                "Souhlasíš s tím, co text říká? Proč ano / ne?",
            ],
            glossary_seed=["důležité", "informace", "význam", "myšlenka"],
            include_pyramid=False
        )

    st.divider()

    # Kontrola OpenAI klíče – jen upozornění, app funguje i bez (fallback)
    if not get_openai_key():
        st.warning("Chybí OPENAI_API_KEY → zjednodušená a LMP verze budou dočasně stejné jako plný text.")
    else:
        st.success(f"OPENAI_API_KEY nalezen. Model: {get_openai_model()}")

    btn = st.button("Vygenerovat dokumenty", type="primary")
    if btn:
        if mode == "Vlastní text" and not full_text.strip():
            st.error("Vlož prosím text.")
        else:
            try:
                with st.spinner("Generuji dokumenty…"):
                    out = generate_all(pack, full_text, int(grade), title)

                # ulož do session state
                st.session_state.files = out
                st.session_state.names = {
                    "pl_full": f"pracovni_list_{title}_plny.docx",
                    "pl_simpl": f"pracovni_list_{title}_zjednoduseny.docx",
                    "pl_lmp": f"pracovni_list_{title}_LMP_SPU.docx",
                    "method": f"metodika_{title}.docx",
                    "cards":
