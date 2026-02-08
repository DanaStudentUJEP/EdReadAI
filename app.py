import re
import io
from datetime import date

import streamlit as st
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

from PIL import Image, ImageDraw, ImageFont


# =========================================================
# 0) KONFIG
# =========================================================

APP_TITLE = "EdRead AI – generátor pracovních listů (pro diplomovou práci)"
DOC_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


# =========================================================
# 1) TEXTY (výchozí – učitel je může v aplikaci upravit)
# =========================================================

DEFAULT_TEXTS = {
    "karetni_hra": {
        "title": "Karetní hra",
        "grade": "3. třída",
        "source": "Školní didaktická úprava (pravidla hry – zjednodušeno pro výuku)",
        "full_text": (
            "NÁZEV ÚLOHY: KARETNÍ HRA\n\n"
            "1) Herní materiál\n"
            "Karty se zvířaty. Každé zvíře má ve hře svou sílu (některá jsou slabší, jiná silnější).\n\n"
            "2) Cíl hry\n"
            "Vyhrává hráč, který se jako první zbaví všech karet.\n\n"
            "3) Jak se hraje\n"
            "• Všichni dostanou karty do ruky.\n"
            "• První hráč vyloží jednu kartu nebo více stejných karet.\n"
            "• Další hráč musí přebít předchozí tah:\n"
            "  – buď zahraje silnější zvíře (stejný počet karet),\n"
            "  – nebo zahraje stejné zvíře, ale o jednu kartu více.\n"
            "• Kdo nemůže nebo nechce přebít, řekne „pass“.\n\n"
            "4) Žolík\n"
            "Chameleon je žolík. Pomáhá vytvořit potřebnou dvojici, ale nesmí být zahraný úplně sám.\n"
        ),
        "simple_text": (
            "NÁZEV ÚLOHY: KARETNÍ HRA (zjednodušený text)\n\n"
            "Ve hře jsou karty se zvířaty.\n"
            "Vyhrává ten, kdo se jako první zbaví všech karet.\n\n"
            "Jak se hraje:\n"
            "• Položíš na stůl kartu (nebo více stejných).\n"
            "• Další hráč musí dát silnější zvíře (stejný počet karet), nebo stejné zvíře, ale o 1 kartu více.\n"
            "• Když to nejde, řekne „pass“.\n\n"
            "Chameleon je žolík. Pomůže ti, ale nesmí být sám.\n"
        ),
        # Pořadí síly (od nejslabšího po nejsilnější) – logika pyramidy
        "animals_ranked": [
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

    "venecky": {
        "title": "Věnečky",
        "grade": "4. třída",
        "source": "Týden (uprav. kráceno pro výuku)",
        "full_text": (
            "NÁZEV ÚLOHY: VĚNEČKY\n\n"
            "Hodnotitelka ochutnává věnečky z různých podniků a porovnává jejich kvalitu.\n"
            "U některých kritizuje sražený krém, „chemickou“ pachuť nebo tvrdé těsto.\n"
            "Jeden věneček naopak chválí: má správnou náplň, dobré těsto a je vyrobený poctivě.\n"
            "V textu se také objevuje tabulka s cenou a známkou „jako ve škole“.\n"
        ),
        "simple_text": (
            "NÁZEV ÚLOHY: VĚNEČKY (zjednodušený text)\n\n"
            "Někdo ochutnává věnečky z různých cukráren.\n"
            "Říká, co je dobré a co je špatné: náplň, těsto, chuť a suroviny.\n"
            "Nejlepší věneček dostane nejlepší známku.\n"
        ),
    },

    "sladke_mameni": {
        "title": "Sladké mámení",
        "grade": "5. třída",
        "source": "Týden (uprav. kráceno pro výuku)",
        "full_text": (
            "NÁZEV ÚLOHY: SLADKÉ MÁMENÍ\n\n"
            "V Evropě a Americe je rozšířená obezita a s ní spojené zdravotní potíže.\n"
            "Proto roste poptávka po nízkokalorických sladkostech.\n\n"
            "V textu se píše, že v Česku lidé většinou nechtějí „light“ sladkosti.\n"
            "Někteří spotřebitelé nechtějí ani vidět energetický obsah na obalu.\n\n"
            "Vědci hledají náhražku cukru: má sladit, nemá mít nepříjemnou chuť či pach\n"
            "a nemá tělo zbytečně zásobovat kaloriemi.\n\n"
            "Text také připomíná rozdíl mezi jednoduchými cukry (rychlá energie)\n"
            "a složitými cukry (např. škrob, vláknina).\n"
        ),
        "simple_text": (
            "NÁZEV ÚLOHY: SLADKÉ MÁMENÍ (zjednodušený text)\n\n"
            "V mnoha zemích má hodně lidí nadváhu.\n"
            "Proto lidé chtějí sladkosti s méně kaloriemi.\n\n"
            "Článek říká, že u nás lidé často nechtějí „light“ sladkosti.\n"
            "Vědci hledají náhradu cukru, která bude sladká, ale nebude mít mnoho kalorií.\n"
        ),
    },
}


# =========================================================
# 2) SLOVNÍČKY – kvalitní vysvětlení + poznámky žáka
#    (učitel může kdykoli doplnit; pro neznámá slova dáme řádek)
# =========================================================

GLOSSARY_HINTS = {
    "karetni_hra": {
        "materiál": "věci, které ke hře potřebujeme",
        "cíl": "to, čeho chceme dosáhnout",
        "přebít": "zahrát silnější kartu než ta předchozí",
        "kombinace": "více karet dohromady",
        "rovnoměrně": "stejně pro všechny",
        "vynést": "položit kartu na stůl",
        "samostatně": "úplně sám, bez další karty",
        "obdobnou": "podobnou",
        "požadovaný": "takový, jaký je potřeba",
    },
    "venecky": {
        "sražený": "nepovedený (krém je rozpadlý nebo hrudkovitý)",
        "chemická": "umělá, nepřirozená",
        "pachuť": "nepříjemná chuť, která zůstane v puse",
        "korpus": "spodní část zákusku (těsto)",
        "odpalované": "druh těsta používaný na věnečky/větrníky",
        "receptura": "přesný postup a složení",
        "nadlehčený": "lehčí a vzdušnější",
        "vláčná": "měkká a příjemná na skus",
        "přepečená": "upečená moc, až příliš",
        "zestárlá": "už není čerstvá",
        "upraveno": "trochu změněno",
        "napravit": "spravit, zlepšit",
        "podnik": "firma nebo cukrárna",
        "dodrželi": "udělali správně podle pravidel",
    },
    "sladke_mameni": {
        "epidemie": "když se něco hodně rozšíří mezi lidmi",
        "obezita": "velká nadváha",
        "metabolismus": "jak tělo zpracuje jídlo na energii",
        "nízkokalorických": "s málo kaloriemi",
        "energetický": "týkající se energie",
        "obsah": "kolik čeho tam je",
        "náhražka": "něco, co nahradí něco jiného",
        "sladivost": "jak moc to sladí",
        "kalorie": "jednotka energie z jídla",
        "vláknina": "část jídla, která pomáhá trávení",
        "jednoduché": "rychlé cukry (dodají energii rychle)",
        "složité": "cukry, které se tráví déle",
    },
}


# =========================================================
# 3) VÝBĚR SLOV – logicky, přiměřeně věku
#    - prioritně slova, která máme ve slovníčku (aby byl skutečně vysvětlený)
#    - doplní další delší slova (a ta dostanou prázdnou linku + poznámky)
# =========================================================

def normalize_word(w: str) -> str:
    return w.strip().lower()

def extract_words(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)

def pick_glossary_words(task_key: str, text: str, max_words: int = 10) -> list[str]:
    words = [normalize_word(w) for w in extract_words(text)]
    uniq = []
    for w in words:
        if w and w not in uniq:
            uniq.append(w)

    hints = GLOSSARY_HINTS.get(task_key, {})
    # 1) nejdřív slova, která umíme vysvětlit a opravdu se v textu objevují
    prioritized = [w for w in uniq if w in hints]

    # 2) doplnění delších slov (8+) jako dříve
    longer = [w for w in uniq if len(w) >= 8 and w not in prioritized]

    out = (prioritized + longer)[:max_words]
    return out


# =========================================================
# 4) DOCX – základní styl
# =========================================================

def set_doc_default_style(doc: Document):
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)
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
    if p.runs:
        p.runs[0].italic = True

def add_lines(doc: Document, n: int = 2):
    for _ in range(n):
        doc.add_paragraph("_____________________________________________________________")

def wrap_paragraphs(doc: Document, text: str):
    for block in text.split("\n"):
        if block.strip() == "":
            doc.add_paragraph("")
        else:
            doc.add_paragraph(block.strip())


# =========================================================
# 5) DRAMATIZACE – realizovatelná bez pomůcek
# =========================================================

def dramatization(task_key: str) -> list[tuple[str, str]]:
    if task_key == "karetni_hra":
        return [
            ("Učitel/ka", "Dnes budeme číst pravidla hry. Nejdřív si vyzkoušíme slovo „přebít“."),
            ("Žák A", "Když dám na stůl myš, co může být silnější?"),
            ("Žák B", "Něco, co myš porazí – třeba liška!"),
            ("Učitel/ka", "Výborně. Teď zjistíme, jak to přesně říkají pravidla v textu."),
        ]
    if task_key == "venecky":
        return [
            ("Učitel/ka", "Zahrajeme si na hodnotitele. Já řeknu: „věneček je dobrý“ a vy řeknete: PROČ?"),
            ("Žák A", "Protože má dobrou náplň."),
            ("Žák B", "A protože těsto není tvrdé."),
            ("Učitel/ka", "Skvěle. V textu budeme hledat, podle čeho se věneček posuzuje."),
        ]
    if task_key == "sladke_mameni":
        return [
            ("Učitel/ka", "Zkuste hádat: proč lidé chtějí sladkosti s méně kaloriemi?"),
            ("Žák A", "Protože chtějí být zdravější."),
            ("Žák B", "Protože mají strach z nadváhy."),
            ("Učitel/ka", "Přečteme text a zjistíme, co přesně článek říká – a co je jen názor."),
        ]
    return []


# =========================================================
# 6) OTÁZKY A/B/C – bez „rozbitých“ možností, přiměřené ročníku
# =========================================================

def questions_abc(task_key: str):
    if task_key == "karetni_hra":
        return {
            "A": [
                ("Co je cílem hry?", ["Získat nejvíc karet.", "Zbavit se všech karet jako první.", "Mít nejsilnější zvíře.", "Vyhrát každé kolo."], "B"),
                ("Co řekne hráč, když nemůže nebo nechce přebít?", ["„stop“", "„pass“", "„konec“", "„znovu“"], "B"),
            ],
            "B": [
                ("Vysvětli vlastními slovy, co znamená „přebít“.", None, None),
                ("Proč chameleon (žolík) nesmí být zahraný úplně sám?", None, None),
            ],
            "C": [
                ("Myslíš, že je férové, když někdo řekne „pass“? Proč ano/ne?", None, None),
            ],
        }

    if task_key == "venecky":
        return {
            "A": [
                ("Co hodnotitelka porovnává u věnečků? Napiš aspoň 3 věci.", None, None),
                ("Co je hlavním tématem textu?", ["Recept na věnečky.", "Porovnání kvality věnečků.", "Historie cukráren.", "Návod na pečení."], "B"),
            ],
            "B": [
                ("Najdi v textu jednu větu, která je NÁZOR. A jednu větu, která je FAKT.", None, None),
                ("Proč je dobré porovnávat víc znaků (náplň, těsto, chuť…), ne jen vzhled?", None, None),
            ],
            "C": [
                ("Stalo se ti někdy, že něco vypadalo hezky, ale nechutnalo? Napiš krátce.", None, None),
            ],
        }

    if task_key == "sladke_mameni":
        return {
            "A": [
                ("Proč ve světě roste poptávka po nízkokalorických sladkostech?", None, None),
                ("Co vědci hledají jako náhradu cukru?", None, None),
            ],
            "B": [
                ("Vysvětli vlastními slovy, co znamená „náhražka cukru“.", None, None),
                ("Rozhodni: je to FAKT nebo NÁZOR? „V Česku lidé většinou nechtějí light sladkosti.“ Napiš a zdůvodni.", None, None),
            ],
            "C": [
                ("Myslíš, že je důležité číst složení a energii na obalu? Proč?", None, None),
            ],
        }

    return {"A": [], "B": [], "C": []}


# =========================================================
# 7) OBRÁZKY – čb siluety + pyramida 13 úrovní (logika hry)
# =========================================================

def load_font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

def draw_silhouette(draw: ImageDraw.ImageDraw, animal: str, x0: int, y0: int, x1: int, y1: int):
    # Jednoduché černobílé siluety (bez internetu, bezpečné pro tisk)
    W = x1 - x0
    H = y1 - y0
    fill = "black"

    def cx(p): return x0 + int(W * p)
    def cy(p): return y0 + int(H * p)

    a = animal.lower()

    if "komár" in a:
        draw.ellipse([cx(0.42), cy(0.35), cx(0.58), cy(0.65)], fill=fill)
        draw.ellipse([cx(0.55), cy(0.40), cx(0.70), cy(0.55)], fill=fill)
        draw.ellipse([cx(0.25), cy(0.25), cx(0.50), cy(0.50)], outline=fill, width=6)
        draw.ellipse([cx(0.25), cy(0.50), cx(0.50), cy(0.75)], outline=fill, width=6)
        draw.line([cx(0.70), cy(0.50), cx(0.88), cy(0.50)], fill=fill, width=6)

    elif "myš" in a:
        draw.ellipse([cx(0.30), cy(0.45), cx(0.70), cy(0.78)], fill=fill)
        draw.ellipse([cx(0.60), cy(0.48), cx(0.82), cy(0.65)], fill=fill)
        draw.ellipse([cx(0.62), cy(0.37), cx(0.70), cy(0.45)], fill=fill)
        draw.ellipse([cx(0.72), cy(0.37), cx(0.80), cy(0.45)], fill=fill)
        draw.line([cx(0.30), cy(0.70), cx(0.12), cy(0.60)], fill=fill, width=8)

    elif "sardinka" in a or "okoun" in a:
        draw.ellipse([cx(0.25), cy(0.45), cx(0.75), cy(0.72)], fill=fill)
        draw.polygon([(cx(0.75), cy(0.58)), (cx(0.92), cy(0.46)), (cx(0.92), cy(0.70))], fill=fill)
        draw.polygon([(cx(0.45), cy(0.45)), (cx(0.55), cy(0.28)), (cx(0.60), cy(0.45))], fill=fill)

    elif "ježek" in a:
        draw.ellipse([cx(0.22), cy(0.48), cx(0.78), cy(0.80)], fill=fill)
        draw.ellipse([cx(0.70), cy(0.58), cx(0.88), cy(0.72)], fill=fill)
        for i in range(6):
            sx = 0.25 + i * 0.10
            draw.polygon([(cx(sx), cy(0.52)), (cx(sx + 0.05), cy(0.28)), (cx(sx + 0.10), cy(0.52))], fill=fill)

    elif "liška" in a:
        draw.polygon([(cx(0.30), cy(0.80)), (cx(0.50), cy(0.32)), (cx(0.70), cy(0.80))], fill=fill)
        draw.polygon([(cx(0.35), cy(0.40)), (cx(0.30), cy(0.22)), (cx(0.45), cy(0.34))], fill=fill)
        draw.polygon([(cx(0.65), cy(0.40)), (cx(0.70), cy(0.22)), (cx(0.55), cy(0.34))], fill=fill)
        draw.polygon([(cx(0.70), cy(0.75)), (cx(0.92), cy(0.62)), (cx(0.80), cy(0.90))], fill=fill)

    elif "tuleň" in a:
        draw.ellipse([cx(0.20), cy(0.50), cx(0.85), cy(0.82)], fill=fill)
        draw.ellipse([cx(0.70), cy(0.42), cx(0.88), cy(0.60)], fill=fill)
        draw.polygon([(cx(0.35), cy(0.80)), (cx(0.20), cy(0.92)), (cx(0.45), cy(0.90))], fill=fill)

    elif "lev" in a:
        draw.ellipse([cx(0.30), cy(0.50), cx(0.78), cy(0.82)], fill=fill)
        draw.ellipse([cx(0.65), cy(0.38), cx(0.88), cy(0.62)], fill=fill)
        draw.ellipse([cx(0.60), cy(0.33), cx(0.93), cy(0.67)], outline=fill, width=10)
        draw.line([cx(0.30), cy(0.70), cx(0.12), cy(0.60)], fill=fill, width=8)
        draw.ellipse([cx(0.08), cy(0.56), cx(0.14), cy(0.64)], fill=fill)

    elif "lední medvěd" in a:
        draw.ellipse([cx(0.18), cy(0.52), cx(0.88), cy(0.84)], fill=fill)
        draw.ellipse([cx(0.75), cy(0.40), cx(0.90), cy(0.58)], fill=fill)

    elif "krokodýl" in a:
        draw.rectangle([cx(0.18), cy(0.58), cx(0.88), cy(0.74)], fill=fill)
        for i in range(6):
            x = 0.25 + i * 0.10
            draw.polygon([(cx(x), cy(0.58)), (cx(x + 0.05), cy(0.48)), (cx(x + 0.10), cy(0.58))], fill=fill)
        draw.polygon([(cx(0.88), cy(0.66)), (cx(0.98), cy(0.54)), (cx(0.98), cy(0.78))], fill=fill)

    elif "slon" in a:
        draw.ellipse([cx(0.20), cy(0.50), cx(0.80), cy(0.84)], fill=fill)
        draw.rectangle([cx(0.75), cy(0.62), cx(0.90), cy(0.84)], fill=fill)
        draw.ellipse([cx(0.32), cy(0.52), cx(0.50), cy(0.74)], fill=fill)

    elif "kosatka" in a:
        draw.ellipse([cx(0.18), cy(0.50), cx(0.88), cy(0.80)], fill=fill)
        draw.polygon([(cx(0.45), cy(0.50)), (cx(0.55), cy(0.18)), (cx(0.62), cy(0.50))], fill=fill)
        draw.polygon([(cx(0.88), cy(0.66)), (cx(0.98), cy(0.56)), (cx(0.98), cy(0.76))], fill=fill)

    elif "chameleon" in a:
        draw.ellipse([cx(0.22), cy(0.52), cx(0.80), cy(0.80)], fill=fill)
        draw.ellipse([cx(0.72), cy(0.44), cx(0.88), cy(0.60)], fill=fill)
        draw.arc([cx(0.10), cy(0.58), cx(0.32), cy(0.88)], start=0, end=330, fill=fill, width=10)

    else:
        draw.ellipse([cx(0.25), cy(0.50), cx(0.85), cy(0.84)], fill=fill)


def make_animal_card_png(title: str) -> bytes:
    w, h = 700, 460
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    draw.rectangle([20, 20, w - 20, h - 20], outline="black", width=6)

    font_big = load_font(44)
    font_small = load_font(20)

    sil_x0, sil_y0 = 60, 70
    sil_x1, sil_y1 = w - 60, 265
    draw_silhouette(draw, title, sil_x0, sil_y0, sil_x1, sil_y1)

    bbox = draw.textbbox((0, 0), title, font=font_big)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) / 2, 295), title, fill="black", font=font_big)

    note = "vystřihni"
    nb = draw.textbbox((0, 0), note, font=font_small)
    nw = nb[2] - nb[0]
    nh = nb[3] - nb[1]
    draw.text((w - nw - 40, h - nh - 40), note, fill="black", font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_ranked_pyramid_template_png(animals_ranked: list[str]) -> bytes:
    """
    Pyramida podle logiky hry: 13 úrovní = 13 zvířat v pořadí síly.
    Dole = nejslabší, nahoře = nejsilnější.
    """
    levels = len(animals_ranked)
    w, h = 1200, 820
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    font = load_font(26)
    font_small = load_font(22)

    margin_x = 70
    top = 70
    bottom = h - 90
    apex_x = w // 2

    # obrys
    left_base = margin_x
    right_base = w - margin_x
    draw.polygon([(apex_x, top), (left_base, bottom), (right_base, bottom)], outline="black", width=6)

    # úrovně (vodorovné linky + číslo)
    for i in range(levels):
        t_top = i / levels
        t_bottom = (i + 1) / levels

        y1 = top + int((bottom - top) * t_top)
        y2 = top + int((bottom - top) * t_bottom)

        x1L = int(apex_x + (left_base - apex_x) * t_top)
        x1R = int(apex_x + (right_base - apex_x) * t_top)
        x2L = int(apex_x + (left_base - apex_x) * t_bottom)
        x2R = int(apex_x + (right_base - apex_x) * t_bottom)

        # linka spodku patra
        draw.line([x2L, y2, x2R, y2], fill="black", width=3)

        # číslo patra (1 dole -> levels nahoře), aby odpovídalo práci s pořadím
        rank_from_bottom = levels - i  # nahoře nejvyšší
        # lepší čitelnost: čísluj odspodu 1..levels
        rank_label = str(i + 1)  # 1 nahoře? Ne – chceme 1 dole.
        # opravíme: 1 = nejslabší = dole
        rank_label = str(levels - i)

        # vložíme číslo doprostřed pásu
        mid_y = (y1 + y2) // 2
        mid_x = apex_x
        bbox = draw.textbbox((0, 0), rank_label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((mid_x - tw/2, mid_y - th/2), rank_label, fill="black", font=font)

    # popisky
    draw.text((left_base, bottom + 10), "NEJSLABŠÍ (dole)", fill="black", font=font_small)
    draw.text((right_base - 260, top - 40), "NEJSILNĚJŠÍ (nahoře)", fill="black", font=font_small)
    draw.text((left_base, top - 40), "Pyramida síly zvířat", fill="black", font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# =========================================================
# 8) GENEROVÁNÍ BLOKŮ: slovníček + otázky + pyramida
# =========================================================

def build_glossary_block(doc: Document, task_key: str, grade_label: str, base_text: str, max_words: int):
    add_h2(doc, "Slovníček (srozumitelně + prostor na poznámky)")
    words = pick_glossary_words(task_key, base_text, max_words=max_words)
    hints = GLOSSARY_HINTS.get(task_key, {})

    for w in words:
        exp = hints.get(w, "")
        p = doc.add_paragraph()
        r = p.add_run(f"• {w} = ")
        r.bold = True
        if exp:
            p.add_run(exp)
        else:
            p.add_run("_______________________________")
        # poznámky žáka (vždy)
        doc.add_paragraph("Poznámky žáka: _________________________________")


def add_dramatization(doc: Document, task_key: str):
    add_h2(doc, "Dramatizace (úvodní motivace – bez pomůcek)")
    scene = dramatization(task_key)
    for who, line in scene:
        p = doc.add_paragraph()
        r1 = p.add_run(f"{who}: ")
        r1.bold = True
        p.add_run(f"„{line}“")
    add_note(doc, "Cíl: naladit třídu na téma a připravit žáky na porozumění textu.")


def add_questions(doc: Document, task_key: str, is_lmp: bool):
    q = questions_abc(task_key)

    add_h2(doc, "Otázky A: Najdi v textu")
    for i, item in enumerate(q["A"], 1):
        question, options, correct = item
        doc.add_paragraph(f"{i}) {question}")
        if options:
            for idx, opt in zip(["A", "B", "C", "D"], options):
                doc.add_paragraph(f"   {idx}) {opt}")
            doc.add_paragraph("Odpověď: ________")
        else:
            add_lines(doc, 2)

    add_h2(doc, "Otázky B: Vysvětli a přemýšlej")
    for i, item in enumerate(q["B"], 1):
        question, _, _ = item
        doc.add_paragraph(f"{i}) {question}")
        add_lines(doc, 2 if not is_lmp else 3)

    add_h2(doc, "Otázky C: Můj názor")
    for i, item in enumerate(q["C"], 1):
        question, _, _ = item
        doc.add_paragraph(f"{i}) {question}")
        add_lines(doc, 2 if not is_lmp else 3)

    add_h2(doc, "Sebeohodnocení")
    doc.add_paragraph("Zakroužkuj:")
    doc.add_paragraph("Rozuměl/a jsem textu:    😊  😐  😕")
    doc.add_paragraph("Našel/la jsem odpovědi:  😊  😐  😕")
    doc.add_paragraph("Umím to vysvětlit:       😊  😐  😕")


def add_karetni_pyramid_section(doc: Document, animals_ranked: list[str]):
    add_h2(doc, "Zvířecí pyramida síly (pomůcka k pravidlům)")
    doc.add_paragraph("1) Vystřihni kartičky zvířat.")
    doc.add_paragraph("2) Nalep je do pyramidy podle síly zvířat.")
    doc.add_paragraph("   • Nejslabší patří dolů, nejsilnější nahoru.")
    doc.add_paragraph("3) Pak se vrať k textu a ověř si, že to odpovídá pravidlům „přebíjení“.")
    doc.add_paragraph("")

    # pyramida jako obrázek (13 úrovní = 13 zvířat)
    pyramid_png = make_ranked_pyramid_template_png(animals_ranked)
    doc.add_picture(io.BytesIO(pyramid_png), width=Cm(17))
    doc.add_paragraph("")

    # přehled pořadí síly (kontrola logiky)
    add_note(
        doc,
        "Kontrola pořadí (od nejslabšího po nejsilnější): "
        + " → ".join(animals_ranked)
    )
    doc.add_paragraph("")

    add_h2(doc, "Kartičky zvířat k vystřižení (3 sloupce)")
    table = doc.add_table(rows=0, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    cards = [(a, make_animal_card_png(a)) for a in animals_ranked]
    for i in range(0, len(cards), 3):
        row = table.add_row().cells
        chunk = cards[i:i+3]
        for col in range(3):
            if col < len(chunk):
                _, png = chunk[col]
                run = row[col].paragraphs[0].add_run()
                run.add_picture(io.BytesIO(png), width=Cm(5.4))
            else:
                row[col].text = ""


# =========================================================
# 9) VÝROBA DOKUMENTŮ (plná / zjednodušená / LMP-SPU / metodika)
# =========================================================

def create_student_doc(task_key: str, variant: str, full_text: str, simple_text: str):
    """
    variant: 'full' | 'simple' | 'lmp'
    LMP/SPU verze = zjednodušený text + více prostoru + více slovníčku
    """
    meta = DEFAULT_TEXTS[task_key]
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

    # dramatizace
    add_dramatization(doc, task_key)
    doc.add_paragraph("")

    # text
    add_h2(doc, "Text pro žáky")
    if variant == "full":
        wrap_paragraphs(doc, full_text)
    else:
        wrap_paragraphs(doc, simple_text)

    doc.add_paragraph("")

    # slovníček
    base = full_text if variant == "full" else simple_text
    max_words = 10 if variant in ("full", "simple") else 12
    build_glossary_block(doc, task_key, meta["grade"], base, max_words=max_words)
    doc.add_paragraph("")

    # pyramida pro Karetní hru
    if task_key == "karetni_hra":
        add_karetni_pyramid_section(doc, meta["animals_ranked"])
        doc.add_paragraph("")

    # otázky
    add_questions(doc, task_key, is_lmp=(variant == "lmp"))

    return doc


def create_methodology_doc(task_key: str):
    meta = DEFAULT_TEXTS[task_key]
    doc = Document()
    set_doc_default_style(doc)

    add_title(doc, f"EdRead AI – Metodický list pro učitele ({meta['title']})")

    add_h2(doc, "Základní informace")
    doc.add_paragraph(f"Ročník: {meta['grade']}")
    doc.add_paragraph(f"Text: {meta['title']}")
    doc.add_paragraph(f"Zdroj: {meta['source']}")
    doc.add_paragraph(f"Vygenerováno: {date.today().strftime('%d.%m.%Y')}")
    doc.add_paragraph("")

    add_h2(doc, "Didaktický záměr")
    doc.add_paragraph(
        "Materiál podporuje čtenářskou gramotnost na 1. stupni: porozumění textu, vyhledávání informací, "
        "interpretaci a formulaci vlastního názoru. Nástroj pracuje s vizuální a strukturovanou oporou "
        "(slovníček, otázky A/B/C, u Karetní hry také pyramida)."
    )

    add_h2(doc, "Napojení na RVP ZV (Český jazyk a literatura – 1. stupeň)")
    doc.add_paragraph(
        "Materiál je v souladu s cíli a očekávanými činnostmi v oblasti práce s textem:\n"
        "• Žák čte s porozuměním přiměřeně náročné texty a vyhledává v nich informace.\n"
        "• Žák propojuje informace z textu a vysvětluje je vlastními slovy.\n"
        "• Žák rozlišuje (v přiměřené míře) fakta a názory a zdůvodňuje své odpovědi.\n"
        "• Žák komunikuje srozumitelně, odpovídá celou větou a opírá se o text.\n"
        "Pozn.: V metodice jsou využity obecné formulace RVP ZV tak, aby byly použitelné napříč ŠVP."
    )

    add_h2(doc, "Doporučený průběh hodiny (45 minut)")
    doc.add_paragraph("1) Dramatizace (5–7 min) – krátká scénka k tématu, bez pomůcek.")
    doc.add_paragraph("2) Čtení textu (10–12 min) – tiché čtení / čtení po odstavcích, krátké zastávky k porozumění.")
    doc.add_paragraph("3) Slovníček (5 min) – vysvětlit klíčová slova, žáci doplní poznámky.")
    doc.add_paragraph("4) Otázky A (10 min) – vyhledání informací (opora v textu).")
    doc.add_paragraph("5) Otázky B (8 min) – interpretace, vysvětlení, fakt vs. názor.")
    doc.add_paragraph("6) Otázky C + sebehodnocení (3–5 min) – vlastní názor, krátká reflexe.")
    doc.add_paragraph("")

    if task_key == "karetni_hra":
        add_h2(doc, "Specifická podpora: pyramida síly (Karetní hra)")
        doc.add_paragraph(
            "Pyramida je vizuální opora pro porozumění pravidlům „přebíjení“. "
            "Žáci propojují text (pravidla) s vizuálním pořadím (hierarchie síly). "
            "Doporučení: nejprve kartičky nalepit, poté se vrátit do textu a ověřit logiku."
        )

    if task_key in ("venecky", "sladke_mameni"):
        add_h2(doc, "Specifická podpora: slovníček + otázky A/B/C")
        doc.add_paragraph(
            "Slovníček snižuje jazykové bariéry a zvyšuje porozumění. "
            "Otázky A vedou k vyhledávání informací, otázky B k interpretaci a otázky C k argumentaci."
        )

    add_h2(doc, "Diferenciace (doporučení)")
    doc.add_paragraph(
        "• Zjednodušená verze: vhodná pro slabší čtenáře nebo při kratším čase.\n"
        "• LMP/SPU verze: více prostoru na odpovědi, více podpory ve slovníčku, delší čas.\n"
        "• Podpora učitele: společné čtení, práce ve dvojicích, zvýraznění klíčových vět."
    )

    add_h2(doc, "Hodnocení / záznam pro učitele (rychlá kontrola)")
    doc.add_paragraph(
        "Sledujte zejména:\n"
        "• zda žák odpovídá s oporou v textu (ne „podle pocitu“),\n"
        "• zda umí vlastními slovy vysvětlit pojem (slovníček),\n"
        "• zda rozlišuje fakt a názor (u starších ročníků),\n"
        "• jak žák reflektuje vlastní práci (sebehodnocení)."
    )

    return doc


def doc_to_bytes(doc: Document) -> bytes:
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# =========================================================
# 10) STREAMLIT UI – stabilní stažení (nezmizí tlačítka)
# =========================================================

st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)

st.markdown(
    "Vyber text a vygeneruj **4 samostatné dokumenty DOCX**:\n"
    "1) **Plná verze** (včetně textu)\n"
    "2) **Zjednodušená verze**\n"
    "3) **LMP/SPU verze** (více podpory, více prostoru)\n"
    "4) **Metodický list pro učitele**\n"
)

task_key = st.selectbox(
    "Vyber text:",
    options=["karetni_hra", "venecky", "sladke_mameni"],
    format_func=lambda k: f"{DEFAULT_TEXTS[k]['title']} ({DEFAULT_TEXTS[k]['grade']})",
)

meta = DEFAULT_TEXTS[task_key]

st.subheader("Texty (můžeš upravit před generováním)")
colA, colB = st.columns(2)

with colA:
    full_text = st.text_area("Plný text", value=meta["full_text"], height=260)
with colB:
    simple_text = st.text_area("Zjednodušený text", value=meta["simple_text"], height=260)

st.divider()

if "generated" not in st.session_state:
    st.session_state["generated"] = False

if st.button("Vygenerovat dokumenty", type="primary"):
    doc_full = create_student_doc(task_key, "full", full_text, simple_text)
    doc_simple = create_student_doc(task_key, "simple", full_text, simple_text)
    doc_lmp = create_student_doc(task_key, "lmp", full_text, simple_text)
    doc_m = create_methodology_doc(task_key)

    st.session_state["out_full"] = doc_to_bytes(doc_full)
    st.session_state["out_simple"] = doc_to_bytes(doc_simple)
    st.session_state["out_lmp"] = doc_to_bytes(doc_lmp)
    st.session_state["out_method"] = doc_to_bytes(doc_m)
    st.session_state["generated"] = True

    st.success("Hotovo. Níže můžeš stáhnout všechny dokumenty (tlačítka zůstanou dostupná).")

st.subheader("Stažení")

def dl(label: str, key: str, filename: str):
    if st.session_state.get("generated") and st.session_state.get(key):
        st.download_button(
            label=label,
            data=st.session_state[key],
            file_name=filename,
            mime=DOC_MIME,
            use_container_width=True,
        )

base_name = meta["title"].replace(" ", "_")

c1, c2 = st.columns(2)
with c1:
    dl("Stáhnout: Pracovní list – PLNÁ verze", "out_full", f"pracovni_list_{base_name}_PLNA.docx")
    dl("Stáhnout: Pracovní list – ZJEDNODUŠENÁ verze", "out_simple", f"pracovni_list_{base_name}_ZJEDNODUSENA.docx")
with c2:
    dl("Stáhnout: Pracovní list – LMP/SPU verze", "out_lmp", f"pracovni_list_{base_name}_LMP_SPU.docx")
    dl("Stáhnout: Metodický list pro učitele", "out_method", f"metodicky_list_{base_name}.docx")
