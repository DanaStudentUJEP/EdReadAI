import os
import io
import json
import re
import requests
import streamlit as st
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


# =========================
# OpenAI (stabilní)
# =========================
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

def get_openai_key() -> str:
    # Streamlit secrets
    if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
        return str(st.secrets["OPENAI_API_KEY"]).strip()
    # Env
    return (os.getenv("OPENAI_API_KEY") or "").strip()

def get_openai_model() -> str:
    if hasattr(st, "secrets") and "OPENAI_MODEL" in st.secrets:
        return str(st.secrets["OPENAI_MODEL"]).strip()
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
    r = requests.post(OPENAI_CHAT_URL, headers=headers, json=payload, timeout=90)

    if r.status_code != 200:
        # nic netry/except — ať je chyba jasná
        raise RuntimeError(f"OpenAI API chyba ({r.status_code}): {r.text}")

    data = r.json()
    return data["choices"][0]["message"]["content"]


# =========================
# DOCX helpers
# =========================
def set_doc_defaults(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

def add_h1(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(16)

def add_h2(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(13)

def add_spacer(doc: Document, cm: float = 0.2) -> None:
    p = doc.add_paragraph("")
    p.paragraph_format.space_after = Pt(int(cm * 28.35))

def doc_to_bytes(doc: Document) -> bytes:
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def safe_add_picture(doc: Document, path: str, width_cm: float) -> bool:
    if not path or not os.path.exists(path):
        return False
    # python-docx může vyhodit chybu, ale nechceme try bez except → použijeme jednoduchý „guard“
    try:
        doc.add_picture(path, width=Cm(width_cm))
        return True
    except Exception:
        return False


# =========================
# Assets (tabulky PNG)
# =========================
ASSET_DIR = "assets"
ASSET_KARETNI_TABLE = os.path.join(ASSET_DIR, "karetni_tabulka.png")
ASSET_SLADKE_TABLES = os.path.join(ASSET_DIR, "sladke_tabulky.png")
ASSET_VENECKY_TABLE = os.path.join(ASSET_DIR, "venecky_tabulka.png")


# =========================
# Datová struktura
# =========================
@dataclass
class Pack:
    key: str
    title: str
    grade: int
    full_text: str
    tables_png: Optional[str]
    drama_intro: str
    drama_scene: List[Tuple[str, str]]
    questions_A: List[str]
    questions_B: List[str]
    questions_C: List[str]
    glossary_seed: List[str]
    include_pyramid: bool = False


# =========================
# TEXTY (SEM VLOŽ PLNÉ)
# =========================
KARETNI_FULL = """(SEM VLOŽ PLNÝ TEXT „Karetní hra“ včetně části, kde je tabulka v PDF.)"""
SLADKE_FULL = """(SEM VLOŽ PLNÝ TEXT „Sladké mámení“.)"""
VENECKY_FULL = """(SEM VLOŽ PLNÝ TEXT „Věnečky“.)"""


# =========================
# Karetní hra: zvířata
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
    add_h2(doc, "Pyramida síly (nalepování)")
    doc.add_paragraph("Vystřihni kartičky zvířat a nalep je do sloupce: nahoře nejsilnější, dole nejslabší.")
    doc.add_paragraph("Každé zvíře má vlastní úroveň.")

    rows = len(ANIMALS_ORDER_STRONG_TO_WEAK)
    t = doc.add_table(rows=rows, cols=1)
    t.autofit = False

    for i in range(rows):
        cell = t.cell(i, 0)
        cell.width = Cm(12.5)
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(f"{i+1}. (sem nalep kartičku)")
        r.font.size = Pt(10)
        # prostor pro lepení
        cell.add_paragraph("")
        cell.add_paragraph("")
        cell.add_paragraph("")


def build_animal_cards_doc() -> Document:
    doc = Document()
    set_doc_defaults(doc)
    add_h1(doc, "Kartičky zvířat – Karetní hra (k vystřižení)")
    doc.add_paragraph("Vystřihni kartičky. Slouží k nalepení do sloupce (pyramidy síly).")

    cols = 3
    items = ANIMALS_ORDER_STRONG_TO_WEAK[:]
    rows = (len(items) + cols - 1) // cols

    table = doc.add_table(rows=rows, cols=cols)
    table.autofit = False

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.width = Cm(6.0)
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

    return doc


# =========================
# AI varianty + slovníček
# =========================
def ai_generate_variants(full_text: str, grade: int, title: str) -> Dict[str, str]:
    # Bez klíče vrátíme stejné texty (ať to funguje)
    if not get_openai_key():
        return {"simpl": full_text, "lmp": full_text}

    system = (
        "Jsi odborník na český jazyk a didaktiku čtenářské gramotnosti 1. stupně. "
        "Piš česky, bez chyb. Nevymýšlej fakta. Zachovej význam."
    )
    user = f"""
Uprav text pro žáky {grade}. ročníku ZŠ. Název: {title}

Vrať přesně JSON:
{{
  "simpl": "...",
  "lmp": "..."
}}

Požadavky:
- simpl: kratší věty, jednodušší slovní zásoba, zachovej klíčové informace.
- lmp/spu: ještě jednodušší, velmi krátké věty, jasné formulace.
- Nepřidávej nové informace.

TEXT:
\"\"\"{full_text}\"\"\"
"""
    out = call_openai_chat(system, user, temperature=0.15, max_tokens=2600)
    # parse
    data = json.loads(out)
    simpl = str(data.get("simpl", full_text)).strip() or full_text
    lmp = str(data.get("lmp", full_text)).strip() or full_text
    return {"simpl": simpl, "lmp": lmp}


def ai_explain_glossary(words: List[str], grade: int) -> Dict[str, str]:
    if not get_openai_key():
        return {}

    system = (
        "Jsi učitel/ka 1. stupně. Vysvětluješ slova krátce a srozumitelně pro daný ročník. "
        "Bez chyb. Vysvětlení max 12 slov."
    )
    user = f"""
Vysvětli pro žáka {grade}. ročníku tato slova.
Vrať jen JSON slovník: {{ "slovo": "vysvětlení", ... }}.
Slova: {", ".join(words)}
"""
    out = call_openai_chat(system, user, temperature=0.1, max_tokens=1200)
    data = json.loads(out)
    cleaned = {}
    for k, v in data.items():
        kk = str(k).strip()
        vv = str(v).strip()
        if kk and vv:
            cleaned[kk] = vv
    return cleaned


def add_glossary_at_end(doc: Document, grade: int, seed_words: List[str], text_for_pick: str) -> None:
    add_h2(doc, "Slovníček pojmů (pracujeme s ním po dramatizaci)")
    doc.add_paragraph("Pokud nějakému vysvětlení nerozumíš, napiš si poznámku.")

    words: List[str] = []
    for w in seed_words:
        if w not in words:
            words.append(w)

    # přidáme pár vhodných slov z textu
    found = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text_for_pick.lower())
    for w in found:
        if len(w) >= 6 and w not in words and len(words) < 14:
            words.append(w)

    explanations = ai_explain_glossary(words, grade)

    for w in words:
        p = doc.add_paragraph()
        rw = p.add_run(f"• {w} — ")
        rw.bold = True
        expl = explanations.get(w, "").strip()
        if expl:
            p.add_run(expl)
            p.add_run(" | Poznámka: ________________________________")
        else:
            # U nevysvětlených slov žádná věta navíc — jen linka
            p.add_run("_______________________________ | Poznámka: ________________________________")


# =========================
# Packs (3 úlohy)
# =========================
PACKS: Dict[str, Pack] = {
    "karetni": Pack(
        key="karetni",
        title="Karetní hra",
        grade=3,
        full_text=KARETNI_FULL,
        tables_png=ASSET_KARETNI_TABLE,
        drama_intro="Na začátku si zahrajeme krátké kolo karetní hry. Pomůže nám to pochopit pravidla dřív, než je budeme číst.",
        drama_scene=[
            ("Žák A", "„Hraju kartu. Myslím, že teď vyhraju!“"),
            ("Žák B", "„Stop — podívej do tabulky: kdo koho přebije?“"),
            ("Žák C (rozhodčí)", "„Řekněte pravidlo nahlas a teprve pak zahrajte.“"),
            ("Všichni", "„Nejdřív pravidlo, potom tah!“"),
        ],
        questions_A=[
            "Najdi v pravidlech, kdy hráč vyhrává kolo. Odpověz celou větou.",
            "Jak se pozná, že je nějaké zvíře „žolík“? Najdi to v textu.",
            "Kde je napsáno, co se děje po odehrání karty?",
        ],
        questions_B=[
            "Proč je užitečná tabulka „Kdo přebije koho?“ Vysvětli vlastními slovy.",
            "Co by se stalo, kdyby tabulka neexistovala?",
        ],
        questions_C=[
            "Líbí se ti, že hra má žolíka? Proč ano / ne?",
            "Napiš jedno pravidlo, které bys do hry přidal/a.",
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
        drama_intro="Než začneme číst, zahrajeme rozhovor „novinář × odborník“. Pomůže nám to odhadnout téma textu.",
        drama_scene=[
            ("Novinář/ka", "„Proč lidé řeší, kolik má sladkost energie?“"),
            ("Odborník/ice", "„Protože přibývá obezita a s ní další problémy.“"),
            ("Novinář/ka", "„A co chtějí zákazníci?“"),
            ("Odborník/ice", "„Často chtějí sladké — bez připomínání rizik.“"),
        ],
        questions_A=[
            "Najdi v textu jednu větu, která vysvětluje hlavní problém.",
            "Podle textu: jaké vlastnosti by nemělo mít ideální sladidlo?",
        ],
        questions_B=[
            "Proč roste zájem o nízkokalorické sladkosti? Napiš vlastními slovy.",
            "Vysvětli přirovnání „novodobí alchymisté“ (co to znamená?).",
        ],
        questions_C=[
            "Myslíš, že je dobré mít energii napsanou na přední straně obalu? Proč?",
            "Jaké sladkosti bys doporučil/a na delší cestu a proč?",
        ],
        glossary_seed=["obezita", "poptávka", "energetická hodnota", "sladidlo", "náhražka", "kalorie"],
        include_pyramid=False
    ),

    "venecky": Pack(
        key="venecky",
        title="Věnečky",
        grade=4,
        full_text=VENECKY_FULL,
        tables_png=ASSET_VENECKY_TABLE,
        drama_intro="Zahrajeme krátkou „degustaci“. Uvidíme, že hodnotitelka posuzuje více věcí najednou (vzhled, chuť, suroviny, těsto).",
        drama_scene=[
            ("Hodnotitel/ka", "„Nejdřív vzhled. Potom vůně…“"),
            ("Pomocník/ice", "„A suroviny? Je to poctivé, nebo chemické?“"),
            ("Hodnotitel/ka", "„A korpus: je měkký, nebo tvrdý?“"),
            ("Pomocník/ice", "„Takže nestačí, že to vypadá hezky!“"),
        ],
        questions_A=[
            "Který věneček neobsahuje pudink uvařený z mléka?",
            "Ve kterém věnečku je rum použitý hlavně proto, aby zakryl jiné nedostatky?",
            "Který podnik dopadl v testu nejlépe?",
        ],
        questions_B=[
            "Co všechno podle textu potřebuje cukrář k poctivému věnečku? Vypiš.",
            "Proč nestačí hodnotit jen „vzhled“?",
        ],
        questions_C=[
            "Souhlasíš, že nejdražší věneček nemusí být nejlepší? Proč?",
            "Podle čeho bys hodnotil/a zákusek? Napiš 3 kritéria.",
        ],
        glossary_seed=["degustace", "korpus", "pudink", "suroviny", "receptura", "poměr", "chemický", "verdikt"],
        include_pyramid=False
    ),
}


# =========================
# Dokumenty: student + metodika
# =========================
def build_student_doc(pack: Pack, variant_label: str, text_variant: str) -> Document:
    doc = Document()
    set_doc_defaults(doc)

    add_h1(doc, f"NÁZEV ÚLOHY: {pack.title} — {variant_label}")
    doc.add_paragraph("JMÉNO: ________________________________    DATUM: _______________")
    add_spacer(doc, 0.2)

    # 1) dramatizace
    add_h2(doc, "1) Krátká dramatizace (začátek hodiny)")
    doc.add_paragraph(pack.drama_intro)
    for role, line in pack.drama_scene:
        doc.add_paragraph(f"{role}: {line}")
    add_spacer(doc, 0.2)

    # 2) text
    add_h2(doc, "2) Text pro čtení")
    doc.add_paragraph(text_variant)

    # tabulky: ve všech verzích
    if pack.tables_png:
        add_spacer(doc, 0.15)
        add_h2(doc, "Tabulky / přehledy k textu")
        ok = safe_add_picture(doc, pack.tables_png, width_cm=16.5)
        if not ok:
            doc.add_paragraph("⚠️ Tabulka není k dispozici (chybí PNG v assets/).")

    # karetní hra: pyramida ve všech verzích
    if pack.include_pyramid:
        add_spacer(doc, 0.2)
        add_pyramid_column(doc)

    add_spacer(doc, 0.2)

    # 3) otázky
    add_h2(doc, "3) Otázky")
    doc.add_paragraph("A) Najdi v textu (pracuj s informací):")
    for q in pack.questions_A:
        doc.add_paragraph(f"• {q}\n  Odpověď: ______________________________________________")

    add_spacer(doc, 0.15)
    doc.add_paragraph("B) Přemýšlej a vysvětli (porozumění):")
    for q in pack.questions_B:
        doc.add_paragraph(f"• {q}\n  Odpověď: ______________________________________________\n  ______________________________________________")

    add_spacer(doc, 0.15)
    doc.add_paragraph("C) Můj názor (kritické čtení):")
    for q in pack.questions_C:
        doc.add_paragraph(f"• {q}\n  Odpověď: ______________________________________________\n  ______________________________________________")

    # slovníček až na konci
    add_spacer(doc, 0.25)
    add_glossary_at_end(doc, pack.grade, pack.glossary_seed, text_variant)

    return doc


def build_method_doc(pack: Pack) -> Document:
    doc = Document()
    set_doc_defaults(doc)

    add_h1(doc, f"Metodický list pro učitele — {pack.title}")

    add_h2(doc, "Doporučený postup práce")
    doc.add_paragraph("1) Dramatizace (5–7 min) – krátká scénka z pracovního listu, cílem je motivace.")
    doc.add_paragraph("2) Slovníček (5–8 min) – i když je na konci listu, projděte ho hned po dramatizaci.")
    doc.add_paragraph("   Učitel/ka vede: „Nejdřív scénka, pak slovníček, potom čtení textu a otázky.“")
    doc.add_paragraph("3) Čtení textu (10–12 min) – práce s textem i tabulkami.")
    doc.add_paragraph("4) Otázky A/B/C (15–18 min) – A: dohledání info, B: porozumění, C: názor.")
    doc.add_paragraph("5) Krátká reflexe (2–3 min).")

    add_h2(doc, "Rozdíly verzí (pro volbu u žáků)")
    doc.add_paragraph("Plná verze: plný text a běžná náročnost.")
    doc.add_paragraph("Zjednodušená: stejné informace, kratší věty, jednodušší slovní zásoba.")
    doc.add_paragraph("LMP/SPU: velmi krátké věty, maximální srozumitelnost.")
    doc.add_paragraph("Tabulky/přehledy zůstávají ve všech verzích (jsou nutné pro odpovědi).")

    add_h2(doc, "Tabulky jako PNG")
    doc.add_paragraph("Tabulky jsou vloženy jako PNG kvůli 100% shodě s originálem z PDF.")
    doc.add_paragraph("Zkontrolujte složku assets/ v repozitáři (musí obsahovat PNG soubory).")

    return doc


# =========================
# Generování všech variant
# =========================
def generate_all(pack: Pack) -> Dict[str, bytes]:
    variants = ai_generate_variants(pack.full_text, pack.grade, pack.title)
    text_full = pack.full_text
    text_simpl = variants["simpl"]
    text_lmp = variants["lmp"]

    doc_full = build_student_doc(pack, "PLNÝ", text_full)
    doc_simpl = build_student_doc(pack, "ZJEDNODUŠENÝ", text_simpl)
    doc_lmp = build_student_doc(pack, "LMP/SPU", text_lmp)
    doc_method = build_method_doc(pack)

    out = {
        "pl_full": doc_to_bytes(doc_full),
        "pl_simpl": doc_to_bytes(doc_simpl),
        "pl_lmp": doc_to_bytes(doc_lmp),
        "method": doc_to_bytes(doc_method),
    }

    if pack.include_pyramid:
        cards_doc = build_animal_cards_doc()
        out["cards"] = doc_to_bytes(cards_doc)

    return out


# =========================
# Streamlit state (tlačítka nemizí)
# =========================
def ensure_state():
    if "files" not in st.session_state:
        st.session_state["files"] = {}
    if "names" not in st.session_state:
        st.session_state["names"] = {}
    if "generated" not in st.session_state:
        st.session_state["generated"] = False


def show_downloads():
    files: Dict[str, bytes] = st.session_state.get("files", {})
    names: Dict[str, str] = st.session_state.get("names", {})
    if not files:
        return

    st.subheader("Stažení dokumentů")

    order = ["pl_full", "pl_simpl", "pl_lmp", "method", "cards"]
    labels = {
        "pl_full": "⬇️ Stáhnout pracovní list (plný)",
        "pl_simpl": "⬇️ Stáhnout pracovní list (zjednodušený)",
        "pl_lmp": "⬇️ Stáhnout pracovní list (LMP/SPU)",
        "method": "⬇️ Stáhnout metodiku pro učitele",
        "cards": "⬇️ Stáhnout kartičky zvířat",
    }

    for k in order:
        if k in files:
            st.download_button(
                label=labels.get(k, f"Stáhnout {k}"),
                data=files[k],
                file_name=names.get(k, f"{k}.docx"),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"dl_{k}"  # stabilní key => tlačítka nemizí
            )

    if st.button("🧹 Vymazat vygenerované soubory (nové generování)", key="clear_generated"):
        st.session_state["files"] = {}
        st.session_state["names"] = {}
        st.session_state["generated"] = False


# =========================
# UI
# =========================
def main():
    st.set_page_config(page_title="EdRead AI", layout="centered")
    ensure_state()

    st.title("EdRead AI — pracovní listy + metodika")

    if get_openai_key():
        st.success(f"OPENAI_API_KEY nalezen. Model: {get_openai_model()}")
    else:
        st.warning("Chybí OPENAI_API_KEY → zjednodušená a LMP verze budou stejné jako plný text.")

    st.info("Tabulky se vkládají jako PNG ze složky assets/ (kvůli 100% shodě s PDF).")

    # výběr úlohy
    options = [
        ("Karetní hra (3. třída)", "karetni"),
        ("Sladké mámení (5. třída)", "sladke"),
        ("Věnečky (4. třída)", "venecky"),
    ]
    label_to_key = {lbl: key for (lbl, key) in options}
    chosen_label = st.selectbox("Vyber úlohu:", [o[0] for o in options])
    chosen_key = label_to_key[chosen_label]
    pack = PACKS[chosen_key]

    st.divider()
    st.write("⚠️ Pokud máš v app.py u textů jen zástupné věty, vlož sem prosím plné texty do proměnných KARETNI_FULL / SLADKE_FULL / VENECKY_FULL.")

    if st.button("Vygenerovat dokumenty", type="primary", key="btn_generate"):
        if not pack.full_text.strip() or pack.full_text.strip().startswith("(SEM VLOŽ"):
            st.error("Nejdřív vlož plné texty do proměnných v app.py.")
        else:
            out = generate_all(pack)
            st.session_state["files"] = out
            st.session_state["names"] = {
                "pl_full": f"pracovni_list_{pack.title}_plny.docx",
                "pl_simpl": f"pracovni_list_{pack.title}_zjednoduseny.docx",
                "pl_lmp": f"pracovni_list_{pack.title}_LMP_SPU.docx",
                "method": f"metodika_{pack.title}.docx",
                "cards": f"karticky_{pack.title}.docx",
            }
            st.session_state["generated"] = True
            st.success("Hotovo. Dokumenty jsou připravené ke stažení.")

    show_downloads()


if __name__ == "__main__":
    main()
