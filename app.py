# app.py – EdRead AI (verze s opravou pyramidy a dramatizace)

import streamlit as st
from io import BytesIO
from docx import Document
from docx.shared import Pt

# -------------------------
# KONFIGURACE UI
# -------------------------

st.set_page_config(
    page_title="EdRead AI – prototyp",
    page_icon="📚",
    layout="centered"
)

st.title("📖 EdRead AI – prototyp pro diplomovou práci")
st.write(
    "Nástroj pro automatickou tvorbu pracovních listů a metodických listů "
    "k rozvoji čtenářské gramotnosti (3.–5. ročník ZŠ)."
)

# -------------------------
# PŘEDPŘIPRAVENÉ DRAMATIZACE
# -------------------------

def get_dramatizace(rocnik: int) -> str:
    """Vrátí krátkou úvodní dramatizaci podle ročníku."""
    if rocnik == 3:
        # Karetní hra – návodová situace
        return (
            "DRAMATIZACE (zahájení hodiny)\n"
            "Anička: „Mám tady pravidla nové karetní hry a vůbec jim nerozumím!“\n"
            "Marek: „Ukaž. Tady je napsané, kdo koho přebíjí. To je jako kdo je silnější.“\n"
            "Učitelka: „Zkusíme si to nejdřív zahrát jako divadlo. Každý bude jedno zvíře a uvidíme, "
            "kdo koho porazí. Pak si text přečteme ještě jednou.“\n"
        )
    elif rocnik == 4:
        # Věnečky – ochutnávka a hodnocení
        return (
            "DRAMATIZACE (zahájení hodiny)\n"
            "Žák A: „Já mám nejradši věnečky z cukrárny na rohu. Ty jsou nejlepší!“\n"
            "Žák B: „Mně naopak chutnají jinde, támhle v nové pekárně.“\n"
            "Učitel: „Každý z vás má nějakou zkušenost. Dnes se podíváme na text, kde profesionálka "
            "popisuje, jak posuzuje věnečky. Budeme číst, jak hodnotí vzhled, chuť i těsto.“\n"
        )
    elif rocnik == 5:
        # Sladké mámení – OPRAVENÁ dramatizace
        return (
            "DRAMATIZACE (zahájení hodiny)\n"
            "Žák A: „Já miluju čokoládu. Nejradši bych ji jedl každý den.“\n"
            "Žák B: „Máma mi říká, že je to samý cukr a že si mám dát radši něco zdravějšího.“\n"
            "Učitel: „Možná mají rodiče trochu pravdu. Dnes si přečteme článek o tom, jak moc "
            "lidé jedí sladkosti, proč se mluví o obezitě a co řeší výrobci čokolády. Budeme "
            "společně hledat v textu informace a přemýšlet, co si z toho odnést.“\n"
        )
    else:
        return ""


# -------------------------
# ZJEDNODUŠENÍ TEXTU (VELMI JEDNODUCHÉ)
# -------------------------

def zjednodus_text(text: str, rocnik: int) -> str:
    """
    Velmi jednoduché zjednodušení:
    - rozdělí na řádky / věty,
    - nechá odstavec po odstavci,
    - případně vloží prázdný řádek mezi dlouhé bloky.
    Nechceme chytračit, spíš text „provzdušnit“ pro děti.
    """
    if not text.strip():
        return ""

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    new_lines = []
    for ln in lines:
        # Pro mladší ročníky ještě víc „usekneme“ příliš dlouhé řádky
        if rocnik in (3, 4) and len(ln) > 150:
            # Rozdělit zhruba na dvě části
            stred = len(ln) // 2
            new_lines.append(ln[:stred].strip())
            new_lines.append(ln[stred:].strip())
            new_lines.append("")  # prázdný řádek
        else:
            new_lines.append(ln)
            new_lines.append("")

    return "\n".join(new_lines).strip()


# -------------------------
# SLOVNÍČEK – VÝBĚR SLOV A JEDNODUCHÉ VYSVĚTLENÍ
# -------------------------

# Malý ručně vytvořený mini-slovník pro typická „těžší“ slova, která
# se mohou v textech Karetní hra / Věnečky / Sladké mámení vyskytovat.
RUČNI_SLOVNIK = {
    "odpalované": "těsto, které se nejdříve vaří a pak peče (např. na věnečky)",
    "korpus": "spodní část dortu nebo zákusku, upečené těsto",
    "pudink": "sladký mléčný krém, který se vaří z mléka a prášku",
    "margarín": "rostlinný tuk podobný máslu",
    "krém": "hutná náplň do dortů nebo zákusků",
    "šlehačka": "našlehaná smetana, bílý nadýchaný krém",
    "chemický": "umělý, ne přírodní",
    "argumentace": "vysvětlování a zdůvodňování názoru",
    "obezita": "nadměrná tělesná hmotnost, člověk je výrazně tlustý",
    "metabolismus": "procesy v těle, které zpracovávají potravu",
    "cukrovinka": "sladkost, bonbon, tyčinka apod.",
    "návod": "popis, jak něco dělat krok za krokem",
    "strategie": "promyšlený postup, plán, jak ve hře zvítězit",
    "pravidla": "to, co se ve hře musí dodržovat",
}

import re

def vyber_slovicka(text: str, max_slov: int = 10):
    """
    Vybere kandidáty na 'těžší' slova:
    - delší výrazy (8+ znaků),
    - bez čísel,
    - unikátní.
    """
    slova = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    slova_cista = [s.strip().lower() for s in slova if len(s) >= 8]
    unik = []
    for s in slova_cista:
        if s not in unik:
            unik.append(s)
    return unik[:max_slov]


def generuj_slovnicek(text: str, rocnik: int):
    """
    Vrátí seznam (slovo, vysvětlení/None).
    - pokud máme ruční definici, použijeme ji,
    - jinak necháme prostor pro doplnění.
    """
    kandidati = vyber_slovicka(text, max_slov=10)
    vysledky = []
    for slovo in kandidati:
        vysvetleni = RUČNI_SLOVNIK.get(slovo)
        vysledky.append((slovo, vysvetleni))
    return vysledky


# -------------------------
# DOCX GENERÁTOR – PRACOVNÍ LIST
# -------------------------

def create_pracovni_list_docx(rocnik: int, text: str, nazev: str, lmp: bool = False) -> BytesIO:
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # Nadpis
    nadpis = f"EdRead AI – pracovní list ({rocnik}. ročník)"
    if lmp:
        nadpis += " – LMP/SPU verze"
    doc.add_heading(nadpis, level=1)

    doc.add_paragraph(f"Název textu: {nazev}")
    doc.add_paragraph("Jméno žáka: ____________________________")
    doc.add_paragraph("")

    # Dramatizace
    doc.add_heading("1. Úvodní dramatizace", level=2)
    doc.add_paragraph(get_dramatizace(rocnik))

    # Text pro žáky
    doc.add_heading("2. Text pro čtení", level=2)
    if lmp:
        doc.add_paragraph(
            "Tato verze je zkrácená a více členěná pro jednodušší čtení.\n"
        )
    zjed = zjednodus_text(text, rocnik)
    doc.add_paragraph(zjed if zjed else "(Text nebyl vložen.)")
    doc.add_page_break()

    # Slovníček
    doc.add_heading("3. Slovníček pojmů", level=2)
    slovicka = generuj_slovnicek(text, rocnik)
    if not slovicka:
        doc.add_paragraph("V tomto textu nebyla nalezena žádná delší složitější slova.")
    else:
        for slovo, vysvetleni in slovicka:
            if vysvetleni:
                doc.add_paragraph(f"• {slovo} = {vysvetleni}")
            else:
                doc.add_paragraph(f"• {slovo} = _______________________________")

    doc.add_page_break()

    # Otázky – jednoduchá, obecná sada podle ročníku
    doc.add_heading("4. Otázky k textu – A/B/C", level=2)

    # A – najdi v textu (porozumění)
    doc.add_paragraph("A) Najdi v textu (porozumění):")
    if rocnik == 3:
        doc.add_paragraph("1. Kdo v textu vyhrává hru? Jak se to pozná?", style=None)
        doc.add_paragraph("2. Které zvíře je podle textu nejslabší?", style=None)
    elif rocnik == 4:
        doc.add_paragraph("1. Který věneček byl v textu hodnocen nejlépe?", style=None)
        doc.add_paragraph("2. Který věneček byl nejdražší a proč cena neodpovídala kvalitě?", style=None)
    elif rocnik == 5:
        doc.add_paragraph("1. Proč se ve světě podle textu mluví o obezitě?", style=None)
        doc.add_paragraph("2. Jakou roli hrají sladkosti v jídelníčku lidí?", style=None)

    doc.add_paragraph("")

    # B – přemýšlení / vysvětlení
    doc.add_paragraph("B) Přemýšlej a vysvětli:")
    if rocnik == 3:
        doc.add_paragraph("3. Proč je důležité znát pravidla hry, než začneme hrát?", style=None)
    elif rocnik == 4:
        doc.add_paragraph("3. Jak poznáš podle textu, že je zákusek poctivě vyrobený?", style=None)
    elif rocnik == 5:
        doc.add_paragraph("3. Proč chtějí někteří lidé ‚light‘ sladkosti?", style=None)

    doc.add_paragraph("")

    # C – můj názor
    doc.add_paragraph("C) Můj názor:")
    doc.add_paragraph("4. Napiš, co si o tématu textu myslíš ty. Souhlasíš s tím, co se v textu říká? Proč ano / ne?")
    doc.add_paragraph("")

    # Sebehodnocení
    doc.add_heading("5. Sebehodnocení", level=2)
    doc.add_paragraph("Označ, jak se ti dnes pracovalo s textem (zakroužkuj nebo vybarvi):")
    doc.add_paragraph("🙂 Rozuměl/a jsem textu dobře.")
    doc.add_paragraph("😐 Něčemu jsem nerozuměl/a.")
    doc.add_paragraph("☹ Text byl pro mě hodně těžký.")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# -------------------------
# DOCX – METODICKÝ LIST
# -------------------------

def create_metodika_docx(rocnik: int, nazev: str) -> BytesIO:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    doc.add_heading("METODICKÝ LIST PRO UČITELE", level=1)
    doc.add_paragraph(f"Ročník: {rocnik}. třída")
    doc.add_paragraph(f"Název textu: {nazev}")
    doc.add_paragraph("")

    # Cíle hodiny
    doc.add_heading("1. Cíle hodiny", level=2)
    doc.add_paragraph("• rozvoj čtenářské gramotnosti (porozumění textu, práce s informací),")
    doc.add_paragraph("• práce se slovní zásobou (slovníček pojmů),")
    doc.add_paragraph("• rozlišení faktu a názoru,")
    doc.add_paragraph("• formulace vlastního názoru na základě textu.")
    doc.add_paragraph("")

    # RVP ZV – jazyk a jazyková komunikace
    doc.add_heading("2. Vazba na RVP ZV – Jazyk a jazyková komunikace", level=2)
    doc.add_paragraph(
        "Žák na úrovni 1. stupně ZŠ zejména:\n"
        "• čte s porozuměním jednoduché texty, plynule a s přiměřenou rychlostí,\n"
        "• vyhledává v textu klíčové informace,\n"
        "• rozlišuje podstatné a okrajové informace,\n"
        "• rozlišuje informaci a názor,\n"
        "• vyjadřuje vlastní názor na přečtený text a tento názor zdůvodní."
    )
    doc.add_paragraph("")

    # Doporučený průběh hodiny
    doc.add_heading("3. Doporučený průběh hodiny (45 min)", level=2)
    doc.add_paragraph("1) Úvodní dramatizace (5–7 min) – aktivace zkušeností žáků, naladění na téma.")
    doc.add_paragraph("2) Čtení textu (10–15 min) – individuální / společné, podtrhávání klíčových informací.")
    doc.add_paragraph("3) Práce s otázkami A/B/C (15–20 min) – vyhledání, vysvětlení, názor.")
    doc.add_paragraph("4) Sebehodnocení (5 min) – žák reflektuje, čemu rozuměl a co bylo těžké.")
    doc.add_paragraph("")

    # Specifika podle ročníku
    doc.add_heading("4. Specifika podle ročníku", level=2)
    if rocnik == 3:
        doc.add_paragraph(
            "3. třída (Karetní hra):\n"
            "• text má charakter návodu – důležité je porozumět pravidlům,\n"
            "• vizuální podpora: pyramida zvířat + zvířátka k vystřižení,\n"
            "• zaměřit se na čtení s porozuměním, kdo koho ‚přebíjí‘.\n"
        )
    elif rocnik == 4:
        doc.add_paragraph(
            "4. třída (Věnečky):\n"
            "• text kombinuje popis a hodnocení (argumentace),\n"
            "• žáci pracují i s tabulkou (nesouvislý text),\n"
            "• vhodné je porovnat vlastní zkušenost s cukrárnou s hodnocením v textu.\n"
        )
    elif rocnik == 5:
        doc.add_paragraph(
            "5. třída (Sladké mámení):\n"
            "• argumentační text o sladkostech, obezitě a složení potravin,\n"
            "• vhodné pro diskuzi o zdraví, míře sladkostí a reklame,\n"
            "• cílem není strašit, ale vést žáky k přemýšlení.\n"
        )

    # Poznámka k diferenciaci
    doc.add_heading("5. Diferenciace (LMP/SPU)", level=2)
    doc.add_paragraph(
        "K textu je k dispozici i zjednodušená verze pracovního listu pro žáky s LMP/SPU:\n"
        "• kratší věty,\n"
        "• menší počet otázek,\n"
        "• více prostoru pro zápis odpovědí,\n"
        "• stejná struktura činností – dramatizace, čtení, otázky, sebehodnocení."
    )

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# -------------------------
# DOCX – ZVÍŘÁTKA K PYRAMIDĚ (3. TŘÍDA)
# -------------------------

def create_zvirata_pyramida_docx() -> BytesIO:
    """
    Vytvoří jednoduchý list se zvířaty k vystřižení pro Karetní hru.
    Použijeme text + emoji jako jednoduchou obrázkovou oporu.
    """
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(14)

    doc.add_heading("Zvířátka k vystřižení – Karetní hra", level=1)
    doc.add_paragraph(
        "Vystřihni si zvířátka a nalep je do pyramidy podle toho, kdo je nejslabší a kdo nejsilnější."
    )
    doc.add_paragraph("Nejslabší zvíře bude dole, nejsilnější nahoře.")

    # tabulka se zvířaty
    zvirata = [
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
        ("🦟", "komár"),
        ("🦎", "chameleon (žolík)"),
    ]

    table = doc.add_table(rows=0, cols=2)
    for emoji, nazev in zvirata:
        row = table.add_row().cells
        row[0].text = emoji
        row[1].text = nazev

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# -------------------------
# HLAVNÍ UI – STREAMLIT
# -------------------------

st.subheader("1️⃣ Vyber ročník a vlož text")

rocnik = st.selectbox("Ročník", options=[3, 4, 5], format_func=lambda x: f"{x}. třída")
default_nazev = {
    3: "Karetní hra",
    4: "Věnečky",
    5: "Sladké mámení",
}.get(rocnik, "Text")

nazev_textu = st.text_input("Název textu", value=default_nazev)

vstupni_text = st.text_area(
    "Vlož původní text (např. Karetní hra / Věnečky / Sladké mámení):",
    height=300,
)

st.write("---")
st.subheader("2️⃣ Vygeneruj materiály")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 Pracovní list (běžná verze)"):
        if not vstupni_text.strip():
            st.error("Nejprve vlož text.")
        else:
            buf = create_pracovni_list_docx(rocnik, vstupni_text, nazev_textu, lmp=False)
            st.download_button(
                "⬇ Stáhnout pracovní list (DOCX)",
                data=buf.getvalue(),
                file_name=f"pracovni_list_{rocnik}trida.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

with col2:
    if st.button("📄 Pracovní list (LMP/SPU)"):
        if not vstupni_text.strip():
            st.error("Nejprve vlož text.")
        else:
            buf_lmp = create_pracovni_list_docx(rocnik, vstupni_text, nazev_textu, lmp=True)
            st.download_button(
                "⬇ Stáhnout LMP/SPU verzi (DOCX)",
                data=buf_lmp.getvalue(),
                file_name=f"pracovni_list_LMP_{rocnik}trida.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

with col3:
    if st.button("📘 Metodický list pro učitele"):
        buf_m = create_metodika_docx(rocnik, nazev_textu)
        st.download_button(
            "⬇ Stáhnout metodiku (DOCX)",
            data=buf_m.getvalue(),
            file_name=f"metodicky_list_{rocnik}trida.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

st.write("---")

# Extra sekce jen pro 3. třídu – Karetní hra
if rocnik == 3:
    st.subheader("3️⃣ Speciálně pro Karetní hru – obrázková opora")
    st.write(
        "Pro 3. třídu můžeš navíc stáhnout list se zvířátky k vystřižení "
        "pro pyramidu podle síly zvířat."
    )
    if st.button("🃏 Zvířátka k pyramidě (Karetní hra)"):
        buf_z = create_zvirata_pyramida_docx()
        st.download_button(
            "⬇ Stáhnout zvířátka k vystřižení (DOCX)",
            data=buf_z.getvalue(),
            file_name="zviratka_karetni_hra.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
