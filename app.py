import re
import io
import textwrap
from datetime import date

import streamlit as st
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

from PIL import Image, ImageDraw, ImageFont


# =========================================================
# 1) DATA: TEXTY (PLNÉ + ZJEDNODUŠENÉ)
# =========================================================

TEXTS = {
    "karetni_hra": {
        "title": "Karetní hra",
        "grade": "3. třída",
        "source": "Bláznivá ZOO (uprav. zadání a text dle školní potřeby)",
        "full_text": (
            "NÁZEV ÚLOHY: KARETNÍ HRA\n\n"
            "1. Herní materiál\n"
            "60 karet živočichů: 4 komáři, 1 chameleon (žolík), 5 karet od každého z dalších 11 druhů živočichů.\n\n"
            "2. Popis hry\n"
            "Všechny karty se rozdají mezi jednotlivé hráče. Hráči se snaží vynášet karty v souladu s pravidly tak, "
            "aby se co nejdříve zbavili všech svých karet z ruky. Zahrát lze vždy pouze silnější kombinaci živočichů, "
            "než zahrál hráč před vámi.\n\n"
            "3. Pořadí karet\n"
            "Na každé kartě je zobrazen jeden živočich. V rámečku v horní části karty jsou namalováni živočichové, "
            "kteří danou kartu přebíjí.\n"
            "Symbol > označuje, že každý živočich může být přebit větším počtem karet stejného druhu.\n"
            "Příklad: Kosatku přebijí pouze dvě kosatky. Krokodýla přebijí dva krokodýli nebo jeden slon.\n\n"
            "Chameleon má ve hře obdobnou funkci jako žolík. Lze jej zahrát spolu s libovolnou jinou kartou "
            "a počítá se jako požadovaný druh živočicha. Nelze jej hrát samostatně.\n\n"
            "4. Průběh hry\n"
            "• Karty zamíchejte a rozdejte rovnoměrně mezi všechny hráče.\n"
            "• Hráč po levé ruce rozdávajícího hráče začíná.\n"
            "• Zahraje (vynese na stůl lícem nahoru) jednu kartu nebo více stejných karet.\n"
            "• Hráči se snaží přebít dříve zahrané karty.\n"
            "  - Buď zahrají stejný počet karet živočicha, který přebíjí předchozí druh,\n"
            "  - nebo zahrají stejný druh živočicha jako předchozí hráč, ale o jednu kartu více.\n"
            "• Kdo nechce nebo nemůže přebít, řekne „pass“.\n"
            "• Kdo se jako první zbaví všech karet z ruky, vítězí.\n"
        ),
        "simple_text": (
            "NÁZEV ÚLOHY: KARETNÍ HRA (zjednodušený text)\n\n"
            "Ve hře jsou karty se zvířaty.\n"
            "Každý hráč dostane karty do ruky a nechá si je pro sebe.\n\n"
            "Cíl hry:\n"
            "Vyhrává ten, kdo se jako první zbaví všech karet.\n\n"
            "Jak se hraje:\n"
            "• Hráč vyloží na stůl 1 kartu (nebo více stejných karet).\n"
            "• Další hráč musí položit silnější zvíře (stejný počet karet), nebo stejné zvíře, ale o 1 kartu víc.\n"
            "• Kdo nemůže, řekne „pass“.\n\n"
            "Pozor na žolíka:\n"
            "Chameleon je žolík. Pomáhá, ale nesmí být zahraný úplně sám.\n"
        ),
        # zvířata (pro kartičky a pyramidu) – pořadí od nejslabšího po nejsilnější
        "animals": [
            "komár",
            "myš",
            "sardinka",
            "okoun",
            "ježek",
            "liška",
            "tuleň",
            "lev",
            "lední medvěd",
            "krokodýl",
            "slon",
            "kosatka",
            "chameleon (žolík)",
        ],
    },

    "sladke_mameni": {
        "title": "Sladké mámení",
        "grade": "5. třída",
        "source": "Týden (uprav. kráceno pro výuku)",
        "full_text": (
            "NÁZEV ÚLOHY: SLADKÉ MÁMENÍ\n\n"
            "Euroamerickou civilizaci sužuje novodobá epidemie: obezita a s ní spojené choroby metabolismu, srdce a cév.\n"
            "Výrobci cukrovinek po celém světě pocítili sílící poptávku po nízkokalorických čokoládách, light mlsání "
            "a dietních bonbonech.\n\n"
            "V rozsáhlém výzkumu se však potvrdilo, že Češi netouží po nízkokalorickém mlsání. Nechtějí dokonce ani na obalu "
            "větším písmem uvedený energetický obsah.\n\n"
            "Novodobí „alchymisté“ v laboratořích stále hledají náhražku cukru, která by měla slušnou sladivost, neměla nepříjemnou "
            "chuť či pach a nezásobovala tělo zbytečnými kaloriemi.\n\n"
            "Analytici doporučují dávat pozor na typy cukrů: jednoduché cukry dodají rychlou energii, ale složité cukry "
            "(polysacharidy jako škrob, celulóza, vláknina) jsou pro tělo často vhodnější.\n"
        ),
        "simple_text": (
            "NÁZEV ÚLOHY: SLADKÉ MÁMENÍ (zjednodušený text)\n\n"
            "V Evropě a Americe má hodně lidí nadváhu. Proto lidé často chtějí sladkosti s méně kaloriemi.\n\n"
            "V článku se píše, že v Česku lidé moc nechtějí nízkokalorické sladkosti.\n"
            "Mnoha lidem ani nevadí, že sladkosti nejsou zdravé.\n\n"
            "Vědci hledají náhradu cukru. Chtějí, aby sladilo, ale mělo málo (nebo žádné) kalorie.\n"
            "Článek také vysvětluje rozdíl mezi jednoduchými a složitými cukry.\n"
        ),
    },

    "venecky": {
        "title": "Věnečky",
        "grade": "4. třída",
        "source": "Týden (uprav. kráceno pro výuku)",
        "full_text": (
            "NÁZEV ÚLOHY: VĚNEČKY\n\n"
            "Hodnotitelka ochutnává věnečky z různých podniků a porovnává jejich kvalitu.\n"
            "U některých kritizuje sražený krém, „chemickou“ pachuť nebo tvrdé těsto.\n"
            "Jeden věneček naopak chválí: má správnou náplň, dobré těsto a je vyrobený poctivě.\n"
            "V textu se také objeví tabulka s cenou a známkou „jako ve škole“.\n"
        ),
        "simple_text": (
            "NÁZEV ÚLOHY: VĚNEČKY (zjednodušený text)\n\n"
            "V článku někdo ochutnává věnečky z různých cukráren.\n"
            "Říká, co je dobré a co je špatné: náplň, těsto, chuť a suroviny.\n"
            "Nejlepší věneček dostane nejlepší známku.\n"
            "V tabulce vidíš cenu a známku.\n"
        ),
    },
}


# =========================================================
# 2) SLOVNÍČKY (předpřipravené vysvětlivky – aby bylo vysvětleno „většinou“)
#    + fallback pro neznámá slova = prázdná linka
# =========================================================

GLOSSARY_HINTS = {
    "karetni_hra": {
        "kombinace": "více karet dohromady",
        "pravidla": "to, co se musí dodržet",
        "přebít": "zahrát silnější kartu",
        "rovnoměrně": "stejně pro všechny",
        "vynést": "položit kartu na stůl",
        "samostatně": "úplně sám (bez další karty)",
        "obdobnou": "podobnou",
        "požadovaný": "takový, jaký je potřeba",
        "lícem": "obrázkem nahoru",
        "kombinaci": "více karet dohromady",
    },
    "sladke_mameni": {
        "epidemie": "když se něco hodně šíří mezi lidmi",
        "obezita": "velká nadváha",
        "metabolismus": "jak tělo zpracuje jídlo na energii",
        "nízkokalorických": "s málo kaloriemi",
        "energetický": "týkající se energie",
        "obsah": "kolik čeho tam je",
        "náhražku": "něco, co něco nahradí",
        "sladivost": "jak moc to sladí",
        "polysacharidy": "složitější cukry",
        "vláknina": "část jídla, která pomáhá trávení",
    },
    "venecky": {
        "sražený": "nepovedený, rozpadlý (o krému)",
        "chemická": "umělá, ne přírodní",
        "pachuť": "divná nepříjemná chuť",
        "korpus": "spodní část zákusku (těsto)",
        "odpalované": "druh těsta (na věnečky/větrníky)",
        "recepturu": "přesný postup a složení",
        "nadlehčený": "lehčí, vzdušnější",
        "vláčná": "měkká a příjemná na skus",
        "přepečená": "upečená moc",
        "zestárlá": "už stará, ne čerstvá",
        "upraveno": "trochu změněno",
        "napravit": "spravit to",
        "podnikům": "firmám/cukrárnám",
        "vyráběného": "udělaného (vyrobeného)",
        "jedinému": "jen jednomu",
        "dodrželi": "udělali správně podle pravidel",
        "nelistuje": "těsto se nerozpadá na vrstvy",
    },
}


# =========================================================
# 3) NÁSTROJE: výběr slov + vysvětlivky + formátování
# =========================================================

def pick_glossary_words(text: str, max_words: int = 10):
    """
    „Původní způsob“ výběru slov – delší slova, bez čísel, unikátní.
    """
    words = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    cleaned = []
    for w in words:
        w2 = w.strip().lower()
        if len(w2) >= 8 and w2 not in cleaned:
            cleaned.append(w2)
    return cleaned[:max_words]


def explain_word(task_key: str, word: str, grade_label: str):
    """
    Vrátí vysvětlení slova (pokud ho známe pro daný text). Jinak vrátí prázdný řetězec.
    """
    hints = GLOSSARY_HINTS.get(task_key, {})
    w = word.lower().strip()
    return hints.get(w, "")


def set_doc_default_style(doc: Document):
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)
    # pro diakritiku
    rFonts = style.element.rPr.rFonts
    rFonts.set(qn("w:eastAsia"), "Calibri")


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


def add_note(doc: Document, text: str):
    p = doc.add_paragraph(text)
    p.runs[0].italic = True


def add_lines(doc: Document, n: int = 3):
    for _ in range(n):
        doc.add_paragraph("_____________________________________________________________")


def wrap_paragraphs(doc: Document, text: str):
    for block in text.split("\n"):
        if block.strip() == "":
            doc.add_paragraph("")
        else:
            doc.add_paragraph(block.strip())


# =========================================================
# 4) OBRÁZKY: pyramid + kartičky (čb siluety bez internetu)
# =========================================================

def draw_silhouette(draw: ImageDraw.ImageDraw, animal: str, x0: int, y0: int, x1: int, y1: int):
    W = x1 - x0
    H = y1 - y0

    def cx(p): return x0 + int(W * p)
    def cy(p): return y0 + int(H * p)

    fill = "black"
    a = animal.lower().strip()

    if "komár" in a:
        draw.ellipse([cx(0.42), cy(0.35), cx(0.58), cy(0.65)], fill=fill)
        draw.ellipse([cx(0.55), cy(0.40), cx(0.70), cy(0.55)], fill=fill)
        draw.ellipse([cx(0.25), cy(0.25), cx(0.50), cy(0.50)], outline=fill, width=6)
        draw.ellipse([cx(0.25), cy(0.50), cx(0.50), cy(0.75)], outline=fill, width=6)
        draw.line([cx(0.70), cy(0.48), cx(0.88), cy(0.48)], fill=fill, width=6)

    elif "myš" in a:
        draw.ellipse([cx(0.30), cy(0.40), cx(0.70), cy(0.75)], fill=fill)
        draw.ellipse([cx(0.62), cy(0.45), cx(0.82), cy(0.62)], fill=fill)
        draw.ellipse([cx(0.62), cy(0.35), cx(0.70), cy(0.45)], fill=fill)
        draw.ellipse([cx(0.72), cy(0.35), cx(0.80), cy(0.45)], fill=fill)
        draw.line([cx(0.30), cy(0.65), cx(0.10), cy(0.55)], fill=fill, width=8)

    elif "sardinka" in a or "okoun" in a:
        draw.ellipse([cx(0.25), cy(0.40), cx(0.75), cy(0.70)], fill=fill)
        draw.polygon([(cx(0.75), cy(0.55)), (cx(0.92), cy(0.42)), (cx(0.92), cy(0.68))], fill=fill)
        draw.polygon([(cx(0.45), cy(0.40)), (cx(0.55), cy(0.25)), (cx(0.60), cy(0.40))], fill=fill)

    elif "ježek" in a:
        draw.ellipse([cx(0.22), cy(0.45), cx(0.78), cy(0.78)], fill=fill)
        draw.ellipse([cx(0.70), cy(0.55), cx(0.88), cy(0.70)], fill=fill)
        for i in range(6):
            sx = 0.25 + i * 0.10
            draw.polygon([(cx(sx), cy(0.50)), (cx(sx + 0.05), cy(0.25)), (cx(sx + 0.10), cy(0.50))], fill=fill)

    elif "liška" in a:
        draw.polygon([(cx(0.30), cy(0.75)), (cx(0.50), cy(0.30)), (cx(0.70), cy(0.75))], fill=fill)
        draw.polygon([(cx(0.35), cy(0.38)), (cx(0.30), cy(0.20)), (cx(0.45), cy(0.32))], fill=fill)
        draw.polygon([(cx(0.65), cy(0.38)), (cx(0.70), cy(0.20)), (cx(0.55), cy(0.32))], fill=fill)
        draw.polygon([(cx(0.70), cy(0.70)), (cx(0.92), cy(0.60)), (cx(0.80), cy(0.85))], fill=fill)

    elif "tuleň" in a:
        draw.ellipse([cx(0.20), cy(0.45), cx(0.85), cy(0.80)], fill=fill)
        draw.ellipse([cx(0.70), cy(0.40), cx(0.88), cy(0.58)], fill=fill)
        draw.polygon([(cx(0.35), cy(0.78)), (cx(0.20), cy(0.90)), (cx(0.45), cy(0.88))], fill=fill)

    elif "lev" in a:
        draw.ellipse([cx(0.30), cy(0.45), cx(0.78), cy(0.80)], fill=fill)
        draw.ellipse([cx(0.65), cy(0.35), cx(0.88), cy(0.60)], fill=fill)
        draw.ellipse([cx(0.60), cy(0.30), cx(0.93), cy(0.63)], outline=fill, width=10)
        draw.line([cx(0.30), cy(0.65), cx(0.12), cy(0.55)], fill=fill, width=8)
        draw.ellipse([cx(0.08), cy(0.50), cx(0.14), cy(0.58)], fill=fill)

    elif "lední medvěd" in a:
        draw.ellipse([cx(0.18), cy(0.48), cx(0.88), cy(0.82)], fill=fill)
        draw.ellipse([cx(0.75), cy(0.38), cx(0.90), cy(0.55)], fill=fill)

    elif "krokodýl" in a:
        draw.rectangle([cx(0.18), cy(0.55), cx(0.88), cy(0.72)], fill=fill)
        for i in range(6):
            x = 0.25 + i * 0.10
            draw.polygon([(cx(x), cy(0.55)), (cx(x + 0.05), cy(0.48)), (cx(x + 0.10), cy(0.55))], fill=fill)
        draw.polygon([(cx(0.88), cy(0.63)), (cx(0.98), cy(0.52)), (cx(0.98), cy(0.74))], fill=fill)

    elif "slon" in a:
        draw.ellipse([cx(0.20), cy(0.45), cx(0.80), cy(0.80)], fill=fill)
        draw.rectangle([cx(0.75), cy(0.55), cx(0.90), cy(0.78)], fill=fill)
        draw.ellipse([cx(0.32), cy(0.48), cx(0.50), cy(0.70)], fill=fill)

    elif "kosatka" in a:
        draw.ellipse([cx(0.18), cy(0.45), cx(0.88), cy(0.78)], fill=fill)
        draw.polygon([(cx(0.45), cy(0.45)), (cx(0.55), cy(0.18)), (cx(0.62), cy(0.45))], fill=fill)
        draw.polygon([(cx(0.88), cy(0.62)), (cx(0.98), cy(0.52)), (cx(0.98), cy(0.72))], fill=fill)

    elif "chameleon" in a:
        draw.ellipse([cx(0.22), cy(0.48), cx(0.80), cy(0.78)], fill=fill)
        draw.ellipse([cx(0.72), cy(0.42), cx(0.88), cy(0.58)], fill=fill)
        draw.arc([cx(0.10), cy(0.55), cx(0.32), cy(0.85)], start=0, end=330, fill=fill, width=10)

    else:
        draw.ellipse([cx(0.25), cy(0.40), cx(0.85), cy(0.80)], fill=fill)


def make_animal_card_png(title: str) -> bytes:
    w, h = 700, 450
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    draw.rectangle([20, 20, w - 20, h - 20], outline="black", width=6)

    try:
        font_big = ImageFont.truetype("DejaVuSans.ttf", 44)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 20)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    sil_x0, sil_y0 = 60, 70
    sil_x1, sil_y1 = w - 60, 260
    draw_silhouette(draw, title, sil_x0, sil_y0, sil_x1, sil_y1)

    bbox = draw.textbbox((0, 0), title, font=font_big)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) / 2, 290), title, fill="black", font=font_big)

    note = "vystřihni"
    nb = draw.textbbox((0, 0), note, font=font_small)
    nw = nb[2] - nb[0]
    nh = nb[3] - nb[1]
    draw.text((w - nw - 40, h - nh - 40), note, fill="black", font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_pyramid_template_png(levels: int = 7) -> bytes:
    """
    Jednoduchá tisková pyramida (šablona), kam žáci lepí kartičky.
    """
    w, h = 1000, 700
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    margin = 60
    top = 60
    bottom = h - 80
    left = margin
    right = w - margin

    # obrys pyramidy
    apex_x = w // 2
    apex_y = top
    draw.polygon([(apex_x, apex_y), (left, bottom), (right, bottom)], outline="black", width=6)

    # vodorovné linky (patra)
    for i in range(1, levels):
        y = apex_y + int((bottom - apex_y) * i / levels)
        # šířka v dané výšce (lineární)
        t = i / levels
        xL = int(apex_x + (left - apex_x) * t)
        xR = int(apex_x + (right - apex_x) * t)
        draw.line([xL, y, xR, y], fill="black", width=4)

    # popisky
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 28)
    except:
        font = ImageFont.load_default()
    draw.text((left, bottom + 10), "NEJSLABŠÍ", fill="black", font=font)
    draw.text((right - 180, top - 10), "NEJSILNĚJŠÍ", fill="black", font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# =========================================================
# 5) OTÁZKY A/B/C + DRAMATIZACE (pevně a bez chyb)
# =========================================================

def dramatization(task_key: str):
    if task_key == "karetni_hra":
        return [
            ("Učitelka", "Dneska budeme číst pravidla jedné hry. Ale nejdřív si zkusíme, co znamená „přebít“."),
            ("Žák 1", "Takže když položím myš…"),
            ("Žák 2", "…tak já ji přebiju silnějším zvířetem!"),
            ("Učitelka", "Přesně. A teď uvidíme, jak to pravidla říkají v textu.")
        ]
    if task_key == "sladke_mameni":
        return [
            ("Učitelka", "Představte si, že jste novináři a máte zjistit: proč lidé chtějí „light“ sladkosti."),
            ("Žák 1", "Protože chtějí méně kalorií?"),
            ("Žák 2", "A protože se mluví o obezitě."),
            ("Učitelka", "Výborně. Přečteme text a ověříme si to v článku.")
        ]
    if task_key == "venecky":
        return [
            ("Učitelka", "Dnes budete degustátoři. Jen očima! Budeme hodnotit věnečky podle toho, co čteme."),
            ("Žák 1", "Co budeme sledovat?"),
            ("Učitelka", "Náplň, těsto, chuť a suroviny. A z tabulky zjistíme i cenu a známku."),
        ]
    return []


def questions_abc(task_key: str):
    """
    Vrací otázky A/B/C tak, aby odpovídaly textu (bez rozbitých možností typu 'Věneček č.').
    """
    if task_key == "karetni_hra":
        return {
            "A": [
                ("Co je cílem hry?", ["Dosáhnout nejvyššího počtu přebití.", "Nemít v ruce žádné karty jako první.", "Nasbírat co nejvíce karet.", "Mít co nejvíce vyšších zvířat."], "B"),
                ("Co udělá hráč, když nechce nebo nemůže přebít?", ["Vezme si kartu ze stolu.", "Použije žolíka samostatně.", "Řekne „pass“.", "Vypadává ze hry."], "C"),
            ],
            "B": [
                ("Vysvětli vlastními slovy, co znamená „přebít“ kartu.", None, None),
                ("Proč chameleon (žolík) nesmí být zahraný úplně sám?", None, None),
            ],
            "C": [
                ("Líbila by se ti taková hra? Napiš proč ano/ne.", None, None),
            ]
        }

    if task_key == "sladke_mameni":
        return {
            "A": [
                ("Proč se ve světě zvyšuje poptávka po nízkokalorických sladkostech?", None, None),
                ("Co vědci hledají v laboratořích?", None, None),
            ],
            "B": [
                ("Vysvětli, co autor myslí větou „novodobí alchymisté hledají recept na zlato“.", None, None),
                ("Rozliš: je to FAKT nebo NÁZOR? „Češi netouží po nízkokalorickém mlsání.“ (Napiš a zdůvodni.)", None, None),
            ],
            "C": [
                ("Jaké sladkosti by sis vybral/a ty a proč? (Opři se o text.)", None, None),
            ]
        }

    if task_key == "venecky":
        return {
            "A": [
                ("Který věneček je podle textu hodnocen nejlépe? Napiš číslo věnečku.", None, None),
                ("Který věneček je podle textu „chemický pudink s vodou“?", None, None),
            ],
            "B": [
                ("Co hodnotitelka sleduje, když posuzuje věneček? Vyjmenuj alespoň 3 věci.", None, None),
                ("Najdi v textu jednu větu – NÁZOR. A jednu větu – FAKT.", None, None),
            ],
            "C": [
                ("Myslíš, že cena vždy odpovídá kvalitě? Napiš svůj názor a jeden důvod.", None, None),
            ]
        }

    return {"A": [], "B": [], "C": []}


# =========================================================
# 6) GENERÁTORY DOCX (FULL / SIMPLE / LMP + METODIKA)
# =========================================================

def build_glossary_block(doc: Document, task_key: str, grade_label: str, base_text: str, max_words: int = 10):
    add_h2(doc, "Slovníček")
    words = pick_glossary_words(base_text, max_words=max_words)

    for w in words:
        exp = explain_word(task_key, w, grade_label)
        p = doc.add_paragraph()
        p.add_run(f"• {w} = ").bold = True
        if exp.strip():
            p.add_run(exp)
        else:
            p.add_run("_______________________________")


def add_dramatization(doc: Document, task_key: str):
    add_h2(doc, "Dramatizace (úvodní motivace)")
    scene = dramatization(task_key)
    for who, line in scene:
        p = doc.add_paragraph()
        r1 = p.add_run(f"{who}: ")
        r1.bold = True
        p.add_run(f"„{line}“")
    add_note(doc, "Cíl: naladit třídu na téma a připravit žáky na čtení textu.")


def add_questions(doc: Document, task_key: str):
    q = questions_abc(task_key)

    add_h2(doc, "Otázky A: Vyhledej informace v textu")
    for i, item in enumerate(q["A"], 1):
        question, options, correct = item
        doc.add_paragraph(f"{i}) {question}")
        if options:
            for idx, opt in zip(["A", "B", "C", "D"], options):
                doc.add_paragraph(f"   {idx}) {opt}")
            doc.add_paragraph("Odpověď: ________")
        else:
            add_lines(doc, 2)

    add_h2(doc, "Otázky B: Přemýšlej a vysvětli")
    for i, item in enumerate(q["B"], 1):
        question, _, _ = item
        doc.add_paragraph(f"{i}) {question}")
        add_lines(doc, 2)

    add_h2(doc, "Otázky C: Můj názor")
    for i, item in enumerate(q["C"], 1):
        question, _, _ = item
        doc.add_paragraph(f"{i}) {question}")
        add_lines(doc, 2)

    add_h2(doc, "Sebeohodnocení")
    doc.add_paragraph("Zakroužkuj:")
    doc.add_paragraph("Rozuměl/a jsem textu:    😊  😐  😕")
    doc.add_paragraph("Našel/la jsem odpovědi:  😊  😐  😕")
    doc.add_paragraph("Umím to vysvětlit:       😊  😐  😕")


def add_karetni_pyramid_section(doc: Document, animals: list):
    add_h2(doc, "Zvířecí pyramida síly (pomůcka k pravidlům)")
    doc.add_paragraph("1) Vystřihni kartičky zvířat.")
    doc.add_paragraph("2) Nalep je do pyramidy podle toho, kdo je nejslabší a kdo nejsilnější.")
    doc.add_paragraph("   • Nejslabší zvíře patří dolů, nejsilnější nahoru.")
    doc.add_paragraph("")

    # pyramida jako obrázek
    pyramid_png = make_pyramid_template_png(levels=7)
    tmp = io.BytesIO(pyramid_png)
    doc.add_picture(tmp, width=Cm(16))
    doc.add_paragraph("")

    add_h2(doc, "Kartičky zvířat k vystřižení")
    doc.add_paragraph("Vystřihni kartičky a použij je do pyramidy.")

    # 3 sloupce
    table = doc.add_table(rows=0, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    cards = []
    for a in animals:
        cards.append((a, make_animal_card_png(a)))

    # po 3 do řádku
    for i in range(0, len(cards), 3):
        row = table.add_row().cells
        chunk = cards[i:i+3]
        for col in range(3):
            if col < len(chunk):
                name, png = chunk[col]
                run = row[col].paragraphs[0].add_run()
                run.add_picture(io.BytesIO(png), width=Cm(5.2))
            else:
                row[col].text = ""


def create_student_doc(task_key: str, variant: str):
    """
    variant: 'full' | 'simple' | 'lmp'
    """
    meta = TEXTS[task_key]
    doc = Document()
    set_doc_default_style(doc)

    title = f"EdRead AI – Pracovní list ({meta['title']})"
    if variant == "simple":
        title += " – ZJEDNODUŠENÁ VERZE"
    if variant == "lmp":
        title += " – LMP/SPU VERZE"

    add_title(doc, title)

    # hlavička
    p = doc.add_paragraph()
    p.add_run("JMÉNO: ").bold = True
    p.add_run("__________________________    ")
    p.add_run("TŘÍDA: ").bold = True
    p.add_run("__________")

    doc.add_paragraph("")

    # dramatizace vždy (úvodní)
    add_dramatization(doc, task_key)
    doc.add_paragraph("")

    # text (plný / zjednodušený)
    add_h2(doc, "Text pro žáky")
    if variant == "full":
        wrap_paragraphs(doc, meta["full_text"])
    else:
        wrap_paragraphs(doc, meta["simple_text"])

    doc.add_paragraph("")

    # slovníček (u LMP dáme víc slov)
    base_text = meta["full_text"] if variant == "full" else meta["simple_text"]
    max_words = 12 if variant == "lmp" else 10
    build_glossary_block(doc, task_key, meta["grade"], base_text, max_words=max_words)

    doc.add_paragraph("")

    # speciální pyramida pro Karetní hru
    if task_key == "karetni_hra":
        add_karetni_pyramid_section(doc, meta["animals"])
        doc.add_paragraph("")

    # otázky
    add_questions(doc, task_key)

    # drobná úprava pro LMP: větší řádky + méně textu na stránce už řeší simple_text + max_words
    return doc


def create_methodology_doc(task_key: str):
    meta = TEXTS[task_key]
    doc = Document()
    set_doc_default_style(doc)

    add_title(doc, f"EdRead AI – Metodický list pro učitele ({meta['title']})")

    add_h2(doc, "Základní informace")
    doc.add_paragraph(f"Ročník: {meta['grade']}")
    doc.add_paragraph(f"Text: {meta['title']}")
    doc.add_paragraph(f"Zdroj: {meta['source']}")
    doc.add_paragraph(f"Vygenerováno: {date.today().strftime('%d.%m.%Y')}")
    doc.add_paragraph("")

    add_h2(doc, "Cíl hodiny")
    doc.add_paragraph(
        "Rozvoj čtenářské gramotnosti: porozumění textu, vyhledávání informací, interpretace, a formulování vlastního názoru."
    )

    add_h2(doc, "Napojení na RVP ZV (Český jazyk a literatura – obecně)")
    doc.add_paragraph(
        "• Žák pracuje s textem: vyhledává informace, propojuje je a vyvozuje závěry.\n"
        "• Žák rozlišuje fakta a názory a své odpovědi zdůvodňuje.\n"
        "• Žák formuluje souvislou odpověď a opírá se o text."
    )

    add_h2(doc, "Doporučený průběh (45 minut)")
    doc.add_paragraph("1) Motivační dramatizace (5–7 min) – krátká scénka k tématu.")
    doc.add_paragraph("2) Tiché čtení / společné čtení (10–12 min) – práce s významy slov.")
    doc.add_paragraph("3) Otázky A (10 min) – vyhledání informací v textu.")
    doc.add_paragraph("4) Otázky B (10 min) – interpretace, fakt vs. názor.")
    doc.add_paragraph("5) Otázky C + sebehodnocení (6–8 min) – vlastní názor, reflexe.")

    if task_key == "karetni_hra":
        add_h2(doc, "Specifická pomůcka: zvířecí pyramida")
        doc.add_paragraph(
            "Pyramida je vizuální opora pro pochopení pravidel (kdo koho přebíjí). "
            "Žáci propojují text (pravidla) s obrázkem (hierarchie)."
        )

    if task_key in ("venecky", "sladke_mameni"):
        add_h2(doc, "Specifická pomůcka: slovníček + práce s informací")
        doc.add_paragraph(
            "Slovníček pomáhá zvýšit porozumění a snižuje bariéry při čtení náročnějšího textu. "
            "Otázky A/B/C cíleně rozvíjí porozumění, interpretaci a kritické čtení."
        )

    add_h2(doc, "Digitální varianta (EdRead AI)")
    doc.add_paragraph(
        "Aplikace generuje samostatné dokumenty: plná verze, zjednodušená verze, LMP/SPU verze a metodický list."
    )

    return doc


def doc_to_bytes(doc: Document) -> bytes:
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# =========================================================
# 7) STREAMLIT UI (tlačítka nezmizí díky session_state)
# =========================================================

st.set_page_config(page_title="EdRead AI – Generátor pracovních listů", layout="wide")
st.title("EdRead AI – Generátor pracovních listů (pro diplomovou práci)")

st.markdown(
    "Vyber text a vygeneruj **4 dokumenty**: "
    "**Plná verze**, **Zjednodušená verze**, **LMP/SPU verze**, **Metodický list**."
)

task = st.selectbox(
    "Vyber text:",
    options=[
        ("karetni_hra", "Karetní hra (3. třída)"),
        ("venecky", "Věnečky (4. třída)"),
        ("sladke_mameni", "Sladké mámení (5. třída)"),
    ],
    format_func=lambda x: x[1],
)
task_key = task[0]

col1, col2 = st.columns(2)

with col1:
    if st.button("Vygenerovat dokumenty", type="primary"):
        # vytvoř dokumenty
        doc_full = create_student_doc(task_key, "full")
        doc_simple = create_student_doc(task_key, "simple")
        doc_lmp = create_student_doc(task_key, "lmp")
        doc_m = create_methodology_doc(task_key)

        st.session_state["out_full"] = doc_to_bytes(doc_full)
        st.session_state["out_simple"] = doc_to_bytes(doc_simple)
        st.session_state["out_lmp"] = doc_to_bytes(doc_lmp)
        st.session_state["out_method"] = doc_to_bytes(doc_m)

        st.success("Hotovo. Níže můžeš stáhnout všechny dokumenty.")

with col2:
    st.info("Tip: u Karetní hry se automaticky vloží pyramida + kartičky (3 sloupce).")

st.divider()
st.subheader("Stažení")

def dl(name, key):
    if key in st.session_state and st.session_state[key]:
        st.download_button(
            label=f"Stáhnout: {name}",
            data=st.session_state[key],
            file_name=name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

base_name = TEXTS[task_key]["title"].replace(" ", "_")

dl(f"pracovni_list_{base_name}_PLNA.docx", "out_full")
dl(f"pracovni_list_{base_name}_ZJEDNODUSENA.docx", "out_simple")
dl(f"pracovni_list_{base_name}_LMP_SPU.docx", "out_lmp")
dl(f"metodicky_list_{base_name}.docx", "out_method")
