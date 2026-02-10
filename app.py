import os
import io
import json
import re
import requests
import streamlit as st
from dataclasses import dataclass
from typing import Dict, List, Tuple

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


# =========================
# OpenAI
# =========================
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


def get_openai_key() -> str:
    if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
        return str(st.secrets["OPENAI_API_KEY"]).strip()
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


# =========================
# AI – struktura z vlastního textu
# =========================
@dataclass
class GeneratedStructure:
    simpl: str
    lmp: str
    drama_intro: str
    drama_scene: List[Tuple[str, str]]
    glossary: Dict[str, str]
    questions_A: List[str]
    questions_B: List[str]
    questions_C: List[str]


def ai_generate_structure(full_text: str, grade: int, title: str) -> GeneratedStructure:
    """
    Z jednoho vstupního textu vygeneruje:
    - zjednodušenou verzi
    - LMP/SPU verzi
    - dramatizaci (intro + 3–6 replik)
    - slovníček pojmů
    - otázky A/B/C (ČŠI / RVP ZV styl)
    Vše v jednom JSONu.
    """
    if not get_openai_key():
        # fallback bez AI – všechno stejné, bez dramatizace a slovníčku
        return GeneratedStructure(
            simpl=full_text,
            lmp=full_text,
            drama_intro="(Dramatizace není k dispozici – chybí OPENAI_API_KEY.)",
            drama_scene=[],
            glossary={},
            questions_A=["(Otázky A nejsou k dispozici – chybí OPENAI_API_KEY.)"],
            questions_B=["(Otázky B nejsou k dispozici – chybí OPENAI_API_KEY.)"],
            questions_C=["(Otázky C nejsou k dispozici – chybí OPENAI_API_KEY.)"],
        )

    system = (
        "Jsi odborník na český jazyk, čtenářskou gramotnost a RVP ZV. "
        "Umíš tvořit pracovní listy ve stylu ČŠI (čtení s porozuměním). "
        "Výstup musí být validní JSON, žádný komentář navíc."
    )

    user = f"""
Máš vytvořit pracovní list pro žáky {grade}. ročníku ZŠ.
Název úlohy: {title}

Vstupní text (plná verze):
\"\"\"{full_text}\"\"\"

ÚKOL:
1) Vytvoř ZJEDNODUŠENOU verzi textu (pro běžné žáky).
2) Vytvoř LMP/SPU verzi (velmi krátké věty, maximální srozumitelnost).
3) Vytvoř krátkou DRAMATIZACI:
   - 1–2 věty „drama_intro“ (co se bude hrát, proč).
   - 3–6 replik ve formátu: [ ["Role", "replika"], ... ]
   - Dramatizace má žákům pomoci pochopit, o čem text bude (varianta C – vymysli ji podle textu).
4) Vytvoř SLOVNÍČEK pojmů:
   - vyber 6–14 slov z textu, která mohou být pro žáky obtížná,
   - ke každému napiš krátké vysvětlení (max 12 slov),
   - vrať jako slovník {{"slovo": "vysvětlení", ...}}.
5) Vytvoř OTÁZKY A/B/C:
   - A: 3–4 otázky na vyhledávání informací v textu (konkrétní odpovědi).
   - B: 2–3 otázky na porozumění a interpretaci (vysvětlení vlastními slovy).
   - C: 2–3 otázky na názor / kritické čtení (žák argumentuje).
   - Stylově podobné úlohám ČŠI (čtení s porozuměním), v souladu s RVP ZV.

VRAŤ POUZE JSON VE FORMÁTU:

{{
  "simpl": "...",
  "lmp": "...",
  "drama_intro": "...",
  "drama_scene": [
    ["Role 1", "replika 1"],
    ["Role 2", "replika 2"]
  ],
  "glossary": {{
    "slovo1": "vysvětlení1",
    "slovo2": "vysvětlení2"
  }},
  "questions_A": ["otázka A1", "otázka A2"],
  "questions_B": ["otázka B1", "otázka B2"],
  "questions_C": ["otázka C1", "otázka C2"]
}}
"""

    out = call_openai_chat(system, user, temperature=0.2, max_tokens=2600)
    data = json.loads(out)

    simpl = str(data.get("simpl", full_text)).strip() or full_text
    lmp = str(data.get("lmp", full_text)).strip() or full_text
    drama_intro = str(data.get("drama_intro", "")).strip()
    drama_scene_raw = data.get("drama_scene", [])
    drama_scene: List[Tuple[str, str]] = []
    for item in drama_scene_raw:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            role = str(item[0]).strip()
            line = str(item[1]).strip()
            if role and line:
                drama_scene.append((role, line))

    glossary_raw = data.get("glossary", {})
    glossary: Dict[str, str] = {}
    if isinstance(glossary_raw, dict):
        for k, v in glossary_raw.items():
            kk = str(k).strip()
            vv = str(v).strip()
            if kk and vv:
                glossary[kk] = vv

    def _clean_list(key: str) -> List[str]:
        arr = data.get(key, [])
        out_list: List[str] = []
        if isinstance(arr, list):
            for q in arr:
                qq = str(q).strip()
                if qq:
                    out_list.append(qq)
        return out_list or [f"(Žádné otázky v sekci {key} – zkus generovat znovu.)"]

    questions_A = _clean_list("questions_A")
    questions_B = _clean_list("questions_B")
    questions_C = _clean_list("questions_C")

    return GeneratedStructure(
        simpl=simpl,
        lmp=lmp,
        drama_intro=drama_intro or "Na začátku si krátce zahrajeme scénku, která ti pomůže pochopit, o čem text bude.",
        drama_scene=drama_scene,
        glossary=glossary,
        questions_A=questions_A,
        questions_B=questions_B,
        questions_C=questions_C,
    )


# =========================
# DOCX – stavba pracovního listu
# =========================
def add_glossary_block(doc: Document, glossary: Dict[str, str]) -> None:
    add_h2(doc, "Slovníček pojmů")
    if not glossary:
        doc.add_paragraph("Slovníček není k dispozici.")
        return

    doc.add_paragraph("Nejdřív si slovíčka projděte společně s učitelem/kou. Pak se vraťte k textu.")
    for w, expl in glossary.items():
        p = doc.add_paragraph()
        r = p.add_run(f"• {w} — ")
        r.bold = True
        p.add_run(expl)
        p.add_run("  | Poznámka: ________________________________")


def build_student_doc(
    title: str,
    grade: int,
    variant_label: str,
    text_variant: str,
    drama_intro: str,
    drama_scene: List[Tuple[str, str]],
    glossary: Dict[str, str],
    questions_A: List[str],
    questions_B: List[str],
    questions_C: List[str],
) -> Document:
    doc = Document()
    set_doc_defaults(doc)

    add_h1(doc, f"NÁZEV ÚLOHY: {title} — {variant_label}")
    doc.add_paragraph(f"Ročník: {grade}. třída")
    doc.add_paragraph("JMÉNO: ________________________________    DATUM: _______________")
    add_spacer(doc, 0.2)

    # 1) dramatizace
    add_h2(doc, "1) Krátká dramatizace (začátek hodiny)")
    doc.add_paragraph(drama_intro)
    for role, line in drama_scene:
        doc.add_paragraph(f"{role}: {line}")
    add_spacer(doc, 0.2)

    # 2) text
    add_h2(doc, "2) Text pro čtení")
    doc.add_paragraph(text_variant)
    add_spacer(doc, 0.2)

    # 3) otázky
    add_h2(doc, "3) Otázky k textu")

    doc.add_paragraph("A) Najdi v textu (vyhledávání informací):")
    for q in questions_A:
        doc.add_paragraph(f"• {q}\n  Odpověď: ______________________________________________")

    add_spacer(doc, 0.15)
    doc.add_paragraph("B) Přemýšlej a vysvětli (porozumění / interpretace):")
    for q in questions_B:
        doc.add_paragraph(
            f"• {q}\n  Odpověď: ______________________________________________\n  ______________________________________________"
        )

    add_spacer(doc, 0.15)
    doc.add_paragraph("C) Můj názor (kritické čtení / argumentace):")
    for q in questions_C:
        doc.add_paragraph(
            f"• {q}\n  Odpověď: ______________________________________________\n  ______________________________________________"
        )

    add_spacer(doc, 0.25)
    add_glossary_block(doc, glossary)

    return doc


def build_method_doc(
    title: str,
    grade: int,
    full_text: str,
    structure: GeneratedStructure,
) -> Document:
    doc = Document()
    set_doc_defaults(doc)

    add_h1(doc, f"Metodický list pro učitele — {title}")
    doc.add_paragraph(f"Ročník: {grade}. třída")

    add_h2(doc, "Cíl hodiny")
    doc.add_paragraph(
        "Rozvoj čtenářské gramotnosti v souladu s RVP ZV: vyhledávání informací, porozumění textu, interpretace, "
        "kritické čtení a formulace vlastního názoru."
    )

    add_h2(doc, "Doporučený postup (45 min)")
    doc.add_paragraph("1) Dramatizace (5–7 min) – krátká scénka podle pracovního listu, motivace a vhled do tématu.")
    doc.add_paragraph(
        "2) Slovníček (5–8 min) – i když je na konci listu, pracujte s ním hned po dramatizaci. "
        "Vyberte slova, která mohou brzdit porozumění, krátce vysvětlete, žáci si doplní poznámky."
    )
    doc.add_paragraph("3) Čtení textu (10–12 min) – tiché čtení / čtení po odstavcích, kontrolní otázky.")
    doc.add_paragraph(
        "4) Otázky A/B/C (15–18 min) – A: dohledání informace v textu, B: vysvětlení vlastními slovy, "
        "C: vlastní názor a zdůvodnění."
    )
    doc.add_paragraph("5) Reflexe (2–3 min) – co žákům pomohlo porozumět (dramatizace, slovníček, otázky).")

    add_h2(doc, "Poznámka k verzím textu")
    doc.add_paragraph("Plná verze: původní text (vstup učitele).")
    doc.add_paragraph("Zjednodušená verze: kratší věty, jednodušší slovní zásoba, zachování klíčových informací.")
    doc.add_paragraph("LMP/SPU verze: velmi krátké věty, maximální srozumitelnost, odstranění složitých souvětí.")

    add_h2(doc, "Vstupní text (plná verze)")
    doc.add_paragraph(full_text)

    add_h2(doc, "Zjednodušená verze (náhled)")
    doc.add_paragraph(structure.simpl)

    add_h2(doc, "LMP/SPU verze (náhled)")
    doc.add_paragraph(structure.lmp)

    return doc


# =========================
# Generování všech dokumentů z vlastního textu
# =========================
def generate_all_from_text(title: str, grade: int, full_text: str) -> Dict[str, bytes]:
    structure = ai_generate_structure(full_text, grade, title)

    doc_full = build_student_doc(
        title=title,
        grade=grade,
        variant_label="PLNÝ",
        text_variant=full_text,
        drama_intro=structure.drama_intro,
        drama_scene=structure.drama_scene,
        glossary=structure.glossary,
        questions_A=structure.questions_A,
        questions_B=structure.questions_B,
        questions_C=structure.questions_C,
    )

    doc_simpl = build_student_doc(
        title=title,
        grade=grade,
        variant_label="ZJEDNODUŠENÝ",
        text_variant=structure.simpl,
        drama_intro=structure.drama_intro,
        drama_scene=structure.drama_scene,
        glossary=structure.glossary,
        questions_A=structure.questions_A,
        questions_B=structure.questions_B,
        questions_C=structure.questions_C,
    )

    doc_lmp = build_student_doc(
        title=title,
        grade=grade,
        variant_label="LMP/SPU",
        text_variant=structure.lmp,
        drama_intro=structure.drama_intro,
        drama_scene=structure.drama_scene,
        glossary=structure.glossary,
        questions_A=structure.questions_A,
        questions_B=structure.questions_B,
        questions_C=structure.questions_C,
    )

    doc_method = build_method_doc(
        title=title,
        grade=grade,
        full_text=full_text,
        structure=structure,
    )

    out: Dict[str, bytes] = {
        "pl_full": doc_to_bytes(doc_full),
        "pl_simpl": doc_to_bytes(doc_simpl),
        "pl_lmp": doc_to_bytes(doc_lmp),
        "method": doc_to_bytes(doc_method),
    }
    return out


# =========================
# Streamlit state + UI
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

    labels = {
        "pl_full": "⬇️ Pracovní list – plná verze",
        "pl_simpl": "⬇️ Pracovní list – zjednodušená verze",
        "pl_lmp": "⬇️ Pracovní list – LMP/SPU verze",
        "method": "⬇️ Metodický list pro učitele",
    }

    order = ["pl_full", "pl_simpl", "pl_lmp", "method"]
    for k in order:
        if k in files:
            st.download_button(
                label=labels.get(k, f"Stáhnout {k}"),
                data=files[k],
                file_name=names.get(k, f"{k}.docx"),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"dl_{k}",
            )

    if st.button("🧹 Vymazat vygenerované soubory", key="clear_btn"):
        st.session_state["files"] = {}
        st.session_state["names"] = {}
        st.session_state["generated"] = False
        st.success("Vygenerované soubory byly vymazány.")


def main():
    st.set_page_config(page_title="EdRead AI – vlastní text", layout="centered")
    ensure_state()

    st.title("EdRead AI — pracovní list z vlastního textu")

    if get_openai_key():
        st.success(f"OPENAI_API_KEY nalezen. Model: {get_openai_model()}")
    else:
        st.warning("Chybí OPENAI_API_KEY → vše poběží v nouzovém režimu (bez AI úprav).")

    st.info(
        "Vlož vlastní text. EdRead AI z něj vytvoří plný, zjednodušený a LMP/SPU pracovní list "
        "s dramatizací, slovníčkem a otázkami A/B/C ve stylu ČŠI / RVP ZV."
    )

    title = st.text_input("Název úlohy:", value="Moje čtení s porozuměním")
    grade = st.number_input("Ročník (1–9):", min_value=1, max_value=9, value=5, step=1)
    full_text = st.text_area("Vlož text pro čtení:", height=300, placeholder="Sem vlož celý text, se kterým chceš pracovat...")

    if st.button("Vygenerovat pracovní listy", type="primary", key="btn_generate"):
        if not full_text.strip():
            st.error("Nejdřív vlož text.")
        else:
            try:
                with st.spinner("Generuji pracovní listy…"):
                    out = generate_all_from_text(title, int(grade), full_text.strip())
                st.session_state["files"] = out
                st.session_state["names"] = {
                    "pl_full": f"pracovni_list_{title}_plny.docx",
                    "pl_simpl": f"pracovni_list_{title}_zjednoduseny.docx",
                    "pl_lmp": f"pracovni_list_{title}_LMP_SPU.docx",
                    "method": f"metodika_{title}.docx",
                }
                st.session_state["generated"] = True
                st.success("Hotovo. Dokumenty jsou připravené ke stažení.")
            except Exception as e:
                st.error(f"Došlo k chybě při generování: {e}")

    show_downloads()


if __name__ == "__main__":
    main()
