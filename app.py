# app.py
# EdRead AI – prototyp pro diplomovou práci (3 texty: Karetní hra / Věnečky / Sladké mámení)
# Generuje 4 samostatné DOCX:
# 1) Pracovní list – PLNÁ verze (plný text)
# 2) Pracovní list – ZJEDNODUŠENÁ verze
# 3) Pracovní list – LMP/SPU verze (ještě jednodušší + větší opora)
# 4) Metodický list pro učitele + manuál testování

import re
import io
import datetime
from dataclasses import dataclass
from typing import List, Dict, Tuple

import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn

from PIL import Image, ImageDraw, ImageFont


# =========================
# 0) Streamlit základ
# =========================
st.set_page_config(page_title="EdRead AI (prototyp)", page_icon="📘", layout="centered")

st.title("📘 EdRead AI – prototyp (pro diplomovou práci)")
st.write("Vygeneruj pracovní listy a metodiku pro 3 ověřované texty. Výstupy se stáhnou jako samostatné DOCX soubory.")


# =========================
# 1) Pomocné funkce – vzhled DOCX
# =========================
def set_doc_margins(doc: Document, top_cm=2.0, bottom_cm=2.0, left_cm=2.0, right_cm=2.0):
    section = doc.sections[0]
    section.top_margin = Cm(top_cm)
    section.bottom_margin = Cm(bottom_cm)
    section.left_margin = Cm(left_cm)
    section.right_margin = Cm(right_cm)

def add_hr(doc: Document):
    p = doc.add_paragraph()
    p_format = p.paragraph_format
    p_format.space_before = Pt(6)
    p_format.space_after = Pt(6)
    run = p.add_run("―" * 40)
    run.font.size = Pt(10)

def add_heading_center(doc: Document, text: str, size=16):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(size)

def add_small(doc: Document, text: str):
    p = doc.add_paragraph(text)
    for r in p.runs:
        r.font.size = Pt(10)

def add_label_value_line(doc: Document, label: str, line_len=40):
    p = doc.add_paragraph()
    r1 = p.add_run(label + " ")
    r1.bold = True
    r2 = p.add_run("_" * line_len)
    r1.font.size = Pt(11)
    r2.font.size = Pt(11)

def add_box_lines(doc: Document, lines=3):
    for _ in range(lines):
        doc.add_paragraph("____________________________________________________________")

def docx_bytes(doc: Document) -> bytes:
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def normalize_spaces(s: str) -> str:
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def pick_vocab_words(text: str, max_words=10) -> List[str]:
    # podobně jako dřív – vybírá „těžší“ slova (delší, bez čísel), unikáty
    words = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    cand = []
    for w in words:
        w2 = w.strip().lower()
        if len(w2) >= 8 and w2.isalpha():
            cand.append(w2)
    uniq = []
    for w in cand:
        if w not in uniq:
            uniq.append(w)
    return uniq[:max_words]


# =========================
# 2) Texty – plné a zjednodušené
# =========================
@dataclass
class TextPack:
    title: str
    grade: int
    full_text: str
    simple_text: str
    lmp_text: str

# --- Karetní hra (3. třída) ---
KARETNI_FULL = normalize_spaces("""
NÁZEV ÚLOHY: KARETNÍ HRA    JMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

1. Herní materiál
60 karet živočichů: 4 komáři, 1 chameleon (žolík), 5 karet od každého z dalších 11 druhů živočichů

2. Popis hry
Všechny karty se rozdají mezi jednotlivé hráče. Hráči se snaží vynášet karty v souladu s pravidly tak, aby se co nejdříve zbavili všech svých karet z ruky. Zahrát lze vždy pouze silnější kombinaci živočichů, než zahrál hráč před vámi.

3. Pořadí karet
Na každé kartě je zobrazen jeden živočich. V rámečku v horní části karty jsou namalováni živočichové, kteří danou kartu přebíjí.
Symbol > označuje, že každý živočich může být přebit větším počtem karet se živočichem stejného druhu.
Příklad: Kosatku přebijí pouze dvě kosatky. Krokodýla přebijí dva krokodýli nebo jeden slon.
Chameleon má ve hře obdobnou funkci jako žolík. Lze jej zahrát spolu s libovolnou jinou kartou a počítá se jako požadovaný druh živočicha. Nelze jej hrát samostatně.

4. Průběh hry
Karty zamíchejte a rozdejte rovnoměrně mezi všechny hráče. Každý hráč si vezme své karty do ruky a neukazuje je ostatním.
Hráč po levé ruce rozdávajícího hráče začíná. Zahraje jednu kartu nebo více stejných karet.
Hráči se snaží přebít dříve zahrané karty: buď stejným počtem karet „vyššího“ živočicha, nebo stejným druhem, ale o jednu kartu více.
Kdo nechce nebo nemůže přebít, řekne pass.
Hráč, který se zbaví všech karet z ruky jako první, vítězí.
""")

KARETNI_SIMPLE = normalize_spaces("""
KARETNÍ HRA (zjednodušeně)

Ve hře jsou karty se zvířaty. Karty si hráči rozdají.
Cíl hry: zbavit se všech karet v ruce jako první.

Jak se přebíjí?
- Můžeš zahrát „silnější“ zvíře.
- Nebo stejné zvíře, ale o jednu kartu víc.

Chameleon je žolík:
- hraje se spolu s jinou kartou,
- může se tvářit jako jiné zvíře.
""")

KARETNI_LMP = normalize_spaces("""
KARETNÍ HRA (pro snadnější čtení)

Hra má karty se zvířaty.
Cíl: mít jako první prázdnou ruku (žádné karty).

Když někdo něco zahraje, ty můžeš:
- přebít silnějším zvířetem,
- nebo dát stejné zvíře, ale o jednu kartu více.

Chameleon je žolík (pomocná karta). Nehraje se sám.
""")

# --- Věnečky (4. třída) ---
VENECKY_FULL = normalize_spaces("""
NÁZEV ÚLOHY: VĚNEČKY    JMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Text popisuje hodnocení několika věnečků z různých cukráren. Hodnotitelka porovnává krém, korpus, vůni (např. rum), suroviny a celkový dojem.
Součástí je také tabulka s cenou a známkami (jako ve škole) pro jednotlivé věnečky a podniky.

Závěr: Nejlépe dopadl věneček z cukrárny Mámení. Některé jiné věnečky byly podle hodnotitelky „na vrácení výučního listu“.
""")

VENECKY_SIMPLE = normalize_spaces("""
VĚNEČKY (zjednodušeně)

V textu se hodnotí věnečky z pěti podniků.
Hodnotitelka sleduje:
- krém (jestli je poctivý),
- těsto/korpus (jestli je správně upečený),
- chuť a vůni (například rum),
- suroviny a celkový dojem.

V tabulce je cena a známka (jako ve škole).
Nejlépe dopadl věneček z cukrárny Mámení.
""")

VENECKY_LMP = normalize_spaces("""
VĚNEČKY (pro snadnější čtení)

Někdo zkouší věnečky z pěti podniků.
Dívá se, jak chutnají a jak jsou udělané.
V tabulce je:
- cena,
- známka (jako ve škole).

Nejlepší byl věneček z cukrárny Mámení.
""")

# --- Sladké mámení (5. třída) ---
SLADKE_FULL = normalize_spaces("""
NÁZEV ÚLOHY: SLADKÉ MÁMENÍ    JMÉNO:

Správným řešením celé úlohy lze získat maximálně 12 bodů.

Text informuje o sladkostech, obezitě a snaze vyrábět nízkokalorické čokolády.
Zmiňuje, že ve světě roste poptávka po „light“ sladkostech, ale u nás to lidé tolik nechtějí.
Uvádí se také, jak vědci hledají náhražku cukru, která by sladila, ale neměla energii (kalorie).
Součástí je tabulka s údaji z průzkumu (procenta).
""")

SLADKE_SIMPLE = normalize_spaces("""
SLADKÉ MÁMENÍ (zjednodušeně)

Text je o sladkostech a zdraví.
Ve světě lidé chtějí sladkosti s méně kaloriemi.
U nás to lidé tolik neřeší.

Vědci hledají sladidlo, které:
- sladí,
- nebude mít divnou chuť,
- nebude mít moc kalorií.

V tabulce jsou výsledky průzkumu (procenta).
""")

SLADKE_LMP = normalize_spaces("""
SLADKÉ MÁMENÍ (pro snadnější čtení)

Text je o sladkostech.
Ve světě lidé chtějí „lehčí“ sladkosti (méně kalorií).
Vědci hledají náhražku cukru.

V tabulce jsou čísla z průzkumu (procenta).
""")

TEXTS: Dict[str, TextPack] = {
    "Karetní hra (3. třída)": TextPack("Karetní hra", 3, KARETNI_FULL, KARETNI_SIMPLE, KARETNI_LMP),
    "Věnečky (4. třída)": TextPack("Věnečky", 4, VENECKY_FULL, VENECKY_SIMPLE, VENECKY_LMP),
    "Sladké mámení (5. třída)": TextPack("Sladké mámení", 5, SLADKE_FULL, SLADKE_SIMPLE, SLADKE_LMP),
}


# =========================
# 3) Dramatizace – konkrétní a bez pomůcek
# =========================
def dramatizace(title: str, grade: int) -> str:
    if title == "Karetní hra":
        return normalize_spaces("""
Krátká scénka na začátek (2–3 min)

Učitelka: „Mám pro vás pravidla nové hry. Ale někdo tvrdí, že jsou zamotaná.“
Žák A: „Já vůbec nevím, kdo koho přebíjí. Jak to poznám?“
Žák B: „Já si myslím, že velké zvíře je vždycky silnější.“
Žák C: „A co když to tady platí jinak?“

Učitelka: „Dnes zjistíme, jak to je doopravdy. Nejprve si text přečteme a budeme hledat důkazy v pravidlech.“
""")
    if title == "Věnečky":
        return normalize_spaces("""
Krátká scénka na začátek (2–3 min)

Učitelka: „Představte si, že jste porota. Máte vybrat nejlepší věneček.“
Žák A: „Já rozhodnu podle ceny – dražší je určitě lepší!“
Žák B: „Já podle chuti – ale tu teď nemáme…“
Žák C: „Tak budeme rozhodovat podle toho, co je napsané v textu a v tabulce.“

Učitelka: „Přesně tak. Budeme číst pozorně a porovnávat informace z textu i tabulky.“
""")
    # Sladké mámení
    return normalize_spaces("""
Krátká scénka na začátek (2–3 min)

Učitelka: „Dnes budeme číst text o sladkostech a zdraví.“
Žák A: „Když je to light, tak toho můžu sníst kolik chci, ne?“
Žák B: „Já chci vědět, co je to náhražka cukru.“
Žák C: „A jak poznám, jestli text mluví o faktech, nebo jen o názoru?“

Učitelka: „To jsou výborné otázky. Budeme hledat informace v textu a vysvětlíme si důležité pojmy.“
""")


# =========================
# 4) Slovníček – vysvětlit co nejvíc, jinak prázdná linka
# =========================
# „jádrové“ jednoduché definice – přiměřené věku (doplňujeme podle potřeby)
BASE_DEFS = {
    # obecně
    "maximálně": "nejvíc, nejvyšší možný počet",
    "výuční": "týká se učení na řemeslo (např. cukrář)",
    "upraveno": "trochu změněno (zkráceno, opraveno)",
    "zdůvodni": "vysvětli proč",
    "porovnej": "najdi rozdíly a podobnosti",
    "tabulka": "přehled v řádcích a sloupcích",

    # karetní hra
    "kombinaci": "víc karet dohromady",
    "pravidly": "tím, co je ve hře dovoleno",
    "přebít": "zahrát něco silnějšího",
    "žolík": "speciální karta, která se může změnit",
    "rovnoměrně": "stejně pro všechny",
    "postupně": "jedno po druhém",
    "samostatně": "bez jiné pomoci / sám",

    # věnečky
    "odpalované": "druh těsta, které se peče do věnečků",
    "korpus": "upečený základ zákusku (těsto)",
    "pudink": "sladký krém (často z mléka)",
    "margarín": "tuk podobný máslu",
    "chemická": "umělá, ne přírodní",
    "zestárlá": "už není čerstvá",
    "napravit": "zkusit to zlepšit",
    "podnikům": "firmám / cukrárnám",
    "nelistuje": "těsto se nerozpadá na vrstvy",

    # sladké mámení
    "epidemie": "když je něco hodně rozšířené",
    "metabolismu": "jak tělo zpracovává energii z jídla",
    "nízkokalorické": "s málo kaloriemi",
    "energetický": "týká se energie (kalorií)",
    "náhražka": "něco, co může nahradit původní věc",
    "sladivost": "jak moc něco sladí",
    "polysacharidy": "složitější cukry (např. škrob)",
    "glukóza": "jednoduchý cukr (hroznový cukr)",
    "fruktóza": "jednoduchý cukr (ovocný cukr)",
}

def explain_word(word: str, grade: int) -> str:
    w = word.lower().strip()
    # přizpůsobení „jednoduchosti“ podle ročníku – ve 3. tř. kratší
    base = BASE_DEFS.get(w, "")
    if not base:
        return ""
    if grade == 3:
        # zkrátíme
        base = base.replace("speciální", "zvláštní").replace("která", "co").replace("firmám /", "")
    return base

def add_vocab_section(doc: Document, title: str, grade: int, source_text: str, max_words=10):
    doc.add_paragraph()
    r = doc.add_paragraph("3) SLOVNÍČEK").runs[0]
    r.bold = True

    words = pick_vocab_words(source_text, max_words=max_words)
    if not words:
        doc.add_paragraph("Slovníček se nepodařilo vytvořit – text je příliš krátký.")
        return

    for w in words:
        exp = explain_word(w, grade)
        p = doc.add_paragraph()
        r1 = p.add_run(f"• {w} = ")
        r1.bold = True
        if exp:
            p.add_run(exp)
            # prostor pro poznámku žáka
            doc.add_paragraph("Moje poznámka: ______________________________________________")
        else:
            # žádná „divná věta“ – jen linka
            doc.add_paragraph("______________________________________________")


# =========================
# 5) Generování obrázků – pyramidy + kartičky (černobílé, bez internetu)
# =========================
def _font(size=28):
    # bezpečný fallback – když není Arial
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()

def make_pyramid_template_png(animals_order: List[str]) -> bytes:
    """
    Vytvoří šablonu pyramidy jako obrázek (A4-ish na šířku),
    s 12 okénky pro lepení + popisky.
    """
    W, H = 1400, 900
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    title_f = _font(40)
    small_f = _font(24)

    d.text((40, 25), "Pyramida síly (Karetní hra)", fill="black", font=title_f)
    d.text((40, 90), "Dole = nejslabší, nahoře = nejsilnější. Nalep zvířata do správných okének.", fill="black", font=small_f)

    # 12 boxů ve tvaru pyramidy (6 řad: 4 + 3 + 2 + 1 + 1 + 1 by bylo málo)
    # Uděláme 6 řad: 6,5,4,3,2,1 = 21 -> použijeme jen 12 boxů: 4,3,2,2,1 (12)
    rows = [4, 3, 2, 2, 1]  # 12 boxů
    top_y = 160
    box_w = 260
    box_h = 90
    gap_x = 30
    gap_y = 22

    idx = 0
    for r, n in enumerate(rows):
        row_w = n * box_w + (n - 1) * gap_x
        start_x = (W - row_w) // 2
        y = top_y + r * (box_h + gap_y)

        for c in range(n):
            x = start_x + c * (box_w + gap_x)
            d.rectangle([x, y, x + box_w, y + box_h], outline="black", width=3)
            idx += 1
            # číslo okénka
            d.text((x + 10, y + 8), f"{idx}", fill="black", font=small_f)

    d.text((40, H - 80), "TIP: Žolík (chameleon) do pyramidy nelep – je mimo pořadí.", fill="black", font=small_f)

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()

def make_simple_silhouette_icon(animal: str, size=240) -> Image.Image:
    """
    Vytvoří jednoduchou černobílou „siluetu“ (piktogram) – bez internetu.
    Je to záměrně jednoduché, ale tiskově čisté.
    """
    img = Image.new("RGB", (size, size), "white")
    d = ImageDraw.Draw(img)

    # mapování na jednoduché tvary
    a = animal.lower()
    if "myš" in a:
        # tělo + uši + ocásek
        d.ellipse([60, 90, 170, 170], fill="black")
        d.ellipse([55, 80, 85, 110], fill="black")
        d.ellipse([145, 80, 175, 110], fill="black")
        d.line([170, 150, 220, 170], fill="black", width=6)
    elif "sardinka" in a or "okoun" in a:
        d.ellipse([50, 95, 190, 160], fill="black")
        d.polygon([(190, 127), (230, 95), (230, 160)], fill="black")
    elif "ježek" in a:
        d.ellipse([60, 110, 190, 175], fill="black")
        # ostny
        for x in range(70, 190, 12):
            d.polygon([(x, 110), (x+6, 80), (x+12, 110)], fill="black")
    elif "liška" in a:
        d.polygon([(70, 180), (120, 90), (170, 180)], fill="black")
        d.polygon([(110, 120), (95, 90), (120, 105)], fill="black")
        d.polygon([(130, 120), (120, 105), (145, 90)], fill="black")
        d.rectangle([175, 140, 220, 170], fill="black")  # ocásek
    elif "tuleň" in a:
        d.ellipse([55, 110, 210, 180], fill="black")
        d.ellipse([40, 135, 95, 180], fill="black")
    elif "lev" in a:
        d.ellipse([70, 80, 190, 200], fill="black")
        d.ellipse([95, 105, 165, 175], fill="white")  # „obličej“ dojem hřívy
    elif "lední medvěd" in a:
        d.rounded_rectangle([50, 110, 220, 190], radius=35, fill="black")
        d.ellipse([60, 90, 120, 140], fill="black")
    elif "krokodýl" in a:
        d.rounded_rectangle([40, 130, 230, 175], radius=20, fill="black")
        for x in range(60, 220, 18):
            d.polygon([(x, 130), (x+9, 110), (x+18, 130)], fill="black")
    elif "slon" in a:
        d.rounded_rectangle([55, 95, 220, 190], radius=35, fill="black")
        d.rectangle([200, 120, 235, 170], fill="black")  # chobot
    elif "kosatka" in a:
        d.ellipse([50, 95, 220, 165], fill="black")
        d.polygon([(120, 95), (145, 60), (160, 95)], fill="black")  # hřbetní ploutev
    elif "komár" in a:
        d.line([120, 60, 120, 200], fill="black", width=8)
        d.ellipse([70, 90, 120, 140], outline="black", width=6)
        d.ellipse([120, 90, 170, 140], outline="black", width=6)
    elif "chameleon" in a:
        d.ellipse([70, 110, 190, 190], fill="black")
        d.arc([160, 150, 235, 225], start=0, end=300, fill="black", width=8)
    else:
        # fallback
        d.ellipse([70, 70, 190, 190], fill="black")

    return img

def make_animal_card_png(animal_name: str) -> bytes:
    """
    Kartička: název + piktogram (černobílý), vhodné pro tisk.
    """
    W, H = 480, 320
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, W-10, H-10], outline="black", width=3)

    f_title = _font(28)
    f_small = _font(18)

    # Název nahoře
    name = animal_name.upper()
    d.text((20, 18), name, fill="black", font=f_title)

    # Ikona
    icon = make_simple_silhouette_icon(animal_name, size=200)
    img.paste(icon, (140, 80))

    # malé místo pro poznámku
    d.text((20, H-45), "Poznámka:", fill="black", font=f_small)
    d.line([120, H-32, W-25, H-32], fill="black", width=2)

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


# =========================
# 6) Otázky A/B/C – bez chyb a „neuseknutých“ možností
# =========================
def questions_ABC(title: str, grade: int) -> List[Tuple[str, str]]:
    """
    Vrací seznam sekcí (nadpis, obsah).
    Otázky jsou pevně připravené pro ověřované texty – bez „halucinací“.
    """
    if title == "Karetní hra":
        return [
            ("4) OTÁZKY A – Najdi v textu",
             normalize_spaces("""
1. Co je cílem hry?
   a) Nasbírat co nejvíc karet.
   b) Zbavit se všech karet z ruky jako první.
   c) Mít nejvíc kosatek.
   Odpověď: _______

2. Co znamená „pass“?
   Odpověď: _______________________________________

3. Proč se chameleon nedá hrát samostatně?
   Odpověď: _______________________________________
""")),
            ("5) OTÁZKY B – Přemýšlej",
             normalize_spaces("""
4. Proč může být výhodné mít více stejných zvířat?
   Odpověď: _______________________________________

5. Kdy může být lepší „passovat“?
   Odpověď: _______________________________________
""")),
            ("6) OTÁZKY C – Můj názor",
             normalize_spaces("""
6. Chtěl/a bys tu hru hrát? Proč ano / ne?
   Odpověď: _______________________________________
""")),
        ]

    if title == "Věnečky":
        return [
            ("4) OTÁZKY A – Najdi v textu a v tabulce",
             normalize_spaces("""
1. Který podnik dopadl nejlépe?
   Odpověď: _______________________________________

2. Který věneček byl nejdražší?
   Odpověď: _______________________________________

3. Jaká dvě kritéria se v hodnocení sledují nejčastěji? (např. krém, korpus…)
   Odpověď: _______________________________________
""")),
            ("5) OTÁZKY B – Přemýšlej",
             normalize_spaces("""
4. Znamená vyšší cena vždy vyšší kvalitu? Vysvětli.
   Odpověď: _______________________________________

5. Najdi jednu větu, která je NÁZOR, a jednu, která je FAKT.
   NÁZOR: ________________________________________
   FAKT:  ________________________________________
""")),
            ("6) OTÁZKY C – Můj názor",
             normalize_spaces("""
6. Podle čeho bys ty hodnotil/a zákusek, kdybys byl/a porotce?
   Odpověď: _______________________________________
""")),
        ]

    # Sladké mámení
    return [
        ("4) OTÁZKY A – Najdi v textu",
         normalize_spaces("""
1. Proč se ve světě zvyšuje poptávka po nízkokalorických sladkostech?
   Odpověď: _______________________________________

2. Co mají mít „ideální“ sladidla podle textu?
   Odpověď: _______________________________________

3. Co znamená v textu přirovnání „novodobí alchymisté“?
   Odpověď: _______________________________________
""")),
        ("5) OTÁZKY B – Přemýšlej",
         normalize_spaces("""
4. Najdi v textu jednu informaci, kterou autor uvádí jako fakt (dá se ověřit),
   a jednu část, která zní jako názor.
   FAKT:  _________________________________________
   NÁZOR: _________________________________________

5. K čemu je v textu tabulka s procenty? Jak pomáhá čtenáři?
   Odpověď: _______________________________________
""")),
        ("6) OTÁZKY C – Můj názor",
         normalize_spaces("""
6. Myslíš, že je důležité sledovat složení sladkostí? Proč?
   Odpověď: _______________________________________
""")),
    ]


# =========================
# 7) Karetní hra – karta zvířat + pyramidní šablona + kartičky (3 sloupce)
# =========================
KARETNI_ORDER_PYRAMID = [
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
    "myš",
    "kosatka",
]
KARETNI_JOKER = "chameleon (žolík)"

def add_karetni_pyramid_and_cards(doc: Document):
    # instrukce
    doc.add_paragraph()
    r = doc.add_paragraph("2) PYRAMIDA SÍLY (pomůcka)").runs[0]
    r.bold = True
    doc.add_paragraph("Vystřihni kartičky zvířat a nalep je do pyramidy podle toho, kdo je nejslabší a kdo nejsilnější.")
    doc.add_paragraph("Dole = nejslabší, nahoře = nejsilnější. Chameleon je žolík – nelepí se do pyramidy.")

    # pyramid template (PNG)
    pyr_png = make_pyramid_template_png(KARETNI_ORDER_PYRAMID)
    pyr_path = io.BytesIO(pyr_png)
    doc.add_paragraph()
    doc.add_picture(pyr_path, width=Cm(16.5))

    doc.add_paragraph()
    doc.add_paragraph("Žolík (mimo pyramidu): " + KARETNI_JOKER)

    add_hr(doc)

    # kartičky (3 sloupce)
    r = doc.add_paragraph("3) KARTIČKY ZVÍŘAT (vystřihni)").runs[0]
    r.bold = True
    doc.add_paragraph("Kartičky vystřihni a použij je pro lepení do pyramidy.")

    animals_all = KARETNI_ORDER_PYRAMID + [KARETNI_JOKER]
    cols = 3
    rows = (len(animals_all) + cols - 1) // cols
    table = doc.add_table(rows=rows, cols=cols)
    table.autofit = True

    i = 0
    for r_i in range(rows):
        for c_i in range(cols):
            cell = table.cell(r_i, c_i)
            cell.paragraphs[0].clear()
            if i < len(animals_all):
                card_png = make_animal_card_png(animals_all[i])
                bio = io.BytesIO(card_png)
                p = cell.paragraphs[0]
                run = p.add_run()
                run.add_picture(bio, width=Cm(5.2))
            i += 1


# =========================
# 8) Generátor pracovních listů (full/simple/LMP) + metodika
# =========================
def build_student_doc(pack: TextPack, variant: str) -> Document:
    """
    variant: "full" | "simple" | "lmp"
    """
    doc = Document()
    set_doc_margins(doc)

    # hlavička
    add_heading_center(doc, f"PRACOVNÍ LIST – {pack.title.upper()}")
    add_label_value_line(doc, "Jméno:")
    add_label_value_line(doc, "Třída:")
    doc.add_paragraph()

    # dramatizace
    r = doc.add_paragraph("1) DRAMATIZACE (začátek hodiny)").runs[0]
    r.bold = True
    doc.add_paragraph(dramatizace(pack.title, pack.grade))

    add_hr(doc)

    # text
    r = doc.add_paragraph("2) TEXT PRO ŽÁKY").runs[0]
    r.bold = True

    if variant == "full":
        doc.add_paragraph(pack.full_text)
    elif variant == "simple":
        doc.add_paragraph(pack.simple_text)
    else:
        doc.add_paragraph(pack.lmp_text)

    add_hr(doc)

    # speciální část pro Karetní hru (3. třída)
    if pack.title == "Karetní hra":
        add_karetni_pyramid_and_cards(doc)
        add_hr(doc)

    # slovníček – vychází z textu, který je v dané variantě použit
    if variant == "full":
        src = pack.full_text
    elif variant == "simple":
        src = pack.simple_text
    else:
        src = pack.lmp_text

    add_vocab_section(doc, pack.title, pack.grade, src, max_words=10)

    add_hr(doc)

    # otázky
    for head, body in questions_ABC(pack.title, pack.grade):
        r = doc.add_paragraph(head).runs[0]
        r.bold = True
        doc.add_paragraph(body)

    add_hr(doc)

    # sebehodnocení (lehké)
    r = doc.add_paragraph("7) SEBEHODNOCENÍ").runs[0]
    r.bold = True
    doc.add_paragraph("Označ, jak se ti pracovalo:")
    doc.add_paragraph("Rozuměl/a jsem textu:   😀 / 🙂 / 😐")
    doc.add_paragraph("Našel/la jsem odpovědi: 😀 / 🙂 / 😐")
    doc.add_paragraph("Umím to vysvětlit:      😀 / 🙂 / 😐")

    return doc


def build_teacher_doc(pack: TextPack) -> Document:
    doc = Document()
    set_doc_margins(doc)

    add_heading_center(doc, f"METODICKÝ LIST + MANUÁL TESTOVÁNÍ – {pack.title.upper()}", size=15)
    add_small(doc, f"Třída: {pack.grade}. ročník | Varianta: plný list / zjednodušený / LMP-SPU | Vygenerováno: {datetime.date.today().isoformat()}")

    add_hr(doc)

    # Záměr a RVP vazba
    r = doc.add_paragraph("1) Didaktický záměr a vazba na RVP ZV").runs[0]
    r.bold = True

    doc.add_paragraph(
        "Materiály rozvíjejí čtení s porozuměním, vyhledávání informací v textu, interpretaci a práci s informacemi "
        "(včetně porovnávání souvislého textu s tabulkou / pomůckou). U starších žáků dále rozvíjejí rozlišování faktu a názoru "
        "a formulaci vlastního stanoviska."
    )

    doc.add_paragraph(
        "RVP ZV (Český jazyk a literatura – 1. stupeň) klade důraz na čtení s porozuměním a porozumění pokynům, práci s informacemi "
        "a porozumění různým typům textů; v kurikulu je také zdůrazněna schopnost odlišovat fakta, názory a autorský záměr."
    )

    # krátké „citování“ ve smyslu parafráze + opora na zdroje (učitel/DP)
    doc.add_paragraph(
        "Opora v kurikulu: očekávané výstupy ČJL pro 1. stupeň zahrnují plynulé čtení s porozuměním a porozumění pokynům; "
        "současně se zdůrazňuje porozumění různým textům, vyhledávání a zpracování informací a rozlišování faktů a názorů."
    )

    add_hr(doc)

    # Konkrétní metodika
    r = doc.add_paragraph("2) Doporučený průběh (45 minut)").runs[0]
    r.bold = True

    doc.add_paragraph("A) Úvod – dramatizace (2–3 min)\n- Přehrajte krátkou scénku z pracovního listu.\n- Cíl: aktivovat téma a motivovat ke čtení.")
    doc.add_paragraph("B) Práce s textem (10–15 min)\n- Tiché čtení / střídavé čtení.\n- U slabších čtenářů čtení po odstavcích + kontrolní otázka.")
    doc.add_paragraph("C) Slovníček (5–7 min)\n- Projděte slova (učitel může doplnit vlastní příklady).\n- Žáci doplní poznámku, pokud potřebují.")
    doc.add_paragraph("D) Úkoly a otázky A/B/C (15–18 min)\n- A: vyhledání informace\n- B: interpretace / propojení\n- C: vlastní názor (podložený textem)")
    doc.add_paragraph("E) Sebehodnocení (2–3 min)\n- žáci zvolí smajlík + krátce řeknou proč.")

    add_hr(doc)

    # Specifika textu
    r = doc.add_paragraph("3) Specifika ověřovaného textu").runs[0]
    r.bold = True

    if pack.title == "Karetní hra":
        doc.add_paragraph(
            "Karetní hra (3. ročník): klíčovou podporou je vizuální opora – pyramida síly + kartičky zvířat. "
            "Žáci propojují informaci z textu (pravidla přebíjení) s pomůckou a ověřují porozumění. "
            "Chameleon je žolík a je veden mimo pyramidu."
        )
    elif pack.title == "Věnečky":
        doc.add_paragraph(
            "Věnečky (4. ročník): text kombinuje hodnotící jazyk a tabulku. Žáci porovnávají údaje (cena/známka) "
            "s výpověďmi v textu a rozlišují fakt vs. hodnotící soud."
        )
    else:
        doc.add_paragraph(
            "Sladké mámení (5. ročník): argumentační text + data. Žáci vyhledávají hlavní myšlenky, vysvětlují pojmy "
            "a rozlišují fakta a názory."
        )

    add_hr(doc)

    # Manuál testování (stručně, ale jasně)
    r = doc.add_paragraph("4) Manuál pro testujícího učitele (kvaziexperiment – praxe)").runs[0]
    r.bold = True

    doc.add_paragraph(
        "• Před testem: připravte vytištěnou verzi (plná / zjednodušená / LMP podle potřeby).\n"
        "• V průběhu: neprozrazujte odpovědi, pouze ujasňujte zadání.\n"
        "• U slovníčku: můžete vysvětlit 1–2 slova jako příklad, ostatní nechajte na žácích.\n"
        "• Čas: doporučeno 35–45 minut (podle třídy).\n"
        "• Záznam: zapisujte bodování dle připraveného klíče (pokud ho používáte) nebo dle vlastního schématu."
    )

    return doc


# =========================
# 9) UI – výběr a generování
# =========================
choice = st.selectbox("Vyber text:", list(TEXTS.keys()))
pack = TEXTS[choice]

st.info(f"Vybráno: **{pack.title}** | Doporučený ročník: **{pack.grade}. třída**")

col1, col2 = st.columns(2)
with col1:
    gen = st.button("✅ Vygenerovat materiály", type="primary")
with col2:
    st.write("")

def store_outputs(pack: TextPack):
    # student docs
    doc_full = build_student_doc(pack, "full")
    doc_simple = build_student_doc(pack, "simple")
    doc_lmp = build_student_doc(pack, "lmp")
    doc_teacher = build_teacher_doc(pack)

    st.session_state["out_full"] = docx_bytes(doc_full)
    st.session_state["out_simple"] = docx_bytes(doc_simple)
    st.session_state["out_lmp"] = docx_bytes(doc_lmp)
    st.session_state["out_teacher"] = docx_bytes(doc_teacher)

if gen:
    store_outputs(pack)
    st.success("Hotovo. Níže si stáhni jednotlivé soubory (nezmizí po stažení).")

# Download blok – stabilní, nezmizí
if "out_full" in st.session_state:
    st.subheader("⬇️ Stažení výstupů (DOCX)")
    c1, c2 = st.columns(2)

    with c1:
        st.download_button(
            "📄 Pracovní list – PLNÝ (s plným textem)",
            data=st.session_state["out_full"],
            file_name=f"pracovni_list_{pack.title}_plny.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="dl_full",
        )
        st.download_button(
            "📄 Pracovní list – LMP/SPU verze",
            data=st.session_state["out_lmp"],
            file_name=f"pracovni_list_{pack.title}_LMP.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="dl_lmp",
        )

    with c2:
        st.download_button(
            "📄 Pracovní list – ZJEDNODUŠENÝ",
            data=st.session_state["out_simple"],
            file_name=f"pracovni_list_{pack.title}_zjednoduseny.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="dl_simple",
        )
        st.download_button(
            "📘 Metodický list + manuál testování",
            data=st.session_state["out_teacher"],
            file_name=f"metodicky_list_{pack.title}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="dl_teacher",
        )

st.caption("Pozn.: Kartičky a pyramidní šablona jsou generované jako černobílé obrázky (bez internetu) a jsou vhodné pro školní tisk.")
