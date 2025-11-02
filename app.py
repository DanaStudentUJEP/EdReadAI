import streamlit as st
from docx import Document
from docx.shared import Pt
from io import BytesIO
import datetime
import re


# =========================
# Pomocné funkce
# =========================

def detekuj_tridu(volba_tridy):
    """Vrátí číslo třídy jako int (3,4,5...)."""
    try:
        return int(volba_tridy)
    except:
        return None


def priprav_dramatizaci(trida):
    """Krátká úvodní scénka jako motivace (zahájení hodiny)."""
    if trida <= 3:
        return [
            'Učitel: „Mám tu novou hru. Kdo ji umí vysvětlit?”',
            'Adam: „Já ne, ty pravidla jsou nějak složitá…”',
            'Ema: „Možná stačí pochopit, kdo přebíjí koho.”',
            'Učitel: „Tak si to spolu zkusíme zahrát a k tomu budeme číst text.”',
            '→ Cíl: děti mají chuť číst návod a pochopit pravidla.'
        ]
    elif trida == 4:
        return [
            'Učitel: „Představte si, že jste porota v soutěži zákusků.”',
            'Ema: „Takže já můžu říct, že krém je hrozný?”',
            'Učitel: „Můžeš, ale musíš také vysvětlit proč.”',
            '→ Cíl: děti chápou rozdíl mezi názorem a odůvodněním.'
        ]
    else:  # 5. třída
        return [
            'Učitel: „Představte si reklamu na čokoládu a článek o čokoládě.”',
            'Tonda: „Reklama chce, abych to koupil.”',
            'Lenka: „A článek říká, co je zdravé a co ne.”',
            'Učitel: „Přesně. Dneska čteme ten článek.”',
            '→ Cíl: žáci uvidí rozdíl mezi informací a přesvědčováním.'
        ]


def priprav_uvod_pro_zaka(trida):
    """Krátké vysvětlení 'o čem je text', pro děti dané třídy."""
    if trida <= 3:
        return (
            "V tomhle textu najdeš popis hry. Naučíš se pravidla, "
            "kdo je silnější a jak vyhrát. Budeš odpovídat na otázky přímo z textu."
        )
    elif trida == 4:
        return (
            "V tomhle textu někdo hodnotí zákusky (věnečky). Říká, co je dobré "
            "a co je špatné. Ty se naučíš najít fakta v textu, poznat názor "
            "a říct svůj vlastní názor."
        )
    else:
        return (
            "Tento text mluví o sladkostech, zdraví a o tom, co lidé opravdu jedí. "
            "Budeš hledat informace, porovnávat, co je pravda, a přemýšlet, co si myslíš ty."
        )


# -------------------------
#  SLOVNÍČEK
# -------------------------

# Slovník častých výrazů z našich typů textů (karetní hra, věnečky, sladké mámení).
# Klíč = kořen/slovo v malých písmenech. Hodnota = dětské vysvětlení.
SLOVNIK_VYRAZU = {
    # Karetní hra / pravidla
    "přebí": "být silnější než karta před tebou (porazit ji).",
    "kombinace": "víc stejných karet zahraných najednou.",
    "žolík": "speciální karta, může dělat jako jiná karta.",
    "chameleon": "speciální karta, která se počítá jako jiné zvíře.",
    "pravidl": "co se smí a nesmí dělat během hry.",
    "kolo": "část hry, kdy všichni hrají postupně po sobě.",
    "pass": "řeknu ‚pass‘ = teď nehraju, vynechávám tah.",
    # Věnečky / cukrář
    "sražen": "pokazilo se to, jsou v tom hrudky.",
    "margar": "tuk podobný máslu.",
    "odpalovan": "těsto na věnečky/větrníky, má být nadýchané.",
    "korpus": "spodní část zákusku, těsto.",
    "receptur": "přesný postup a suroviny podle receptu.",
    "výuční": "papír, že je někdo vyučený cukrář / řemeslník.",
    "chemick": "umělá, nepřirozená chuť.",
    "pachuť": "chuť po jídle, která zůstane v puse.",
    "zestárl": "už to není čerstvé, je to tvrdé / suché.",
    # Sladké mámení / výživa
    "nízkokalor": "málo kalorií = méně energie z jídla.",
    "obezit": "když má člověk moc tělesného tuku, je to už nezdravé.",
    "metabol": "jak tělo mění jídlo na energii pro nás.",
    "polysachar": "složité cukry – energie se uvolňuje pomalu (třeba vláknina).",
    "jednoduché cukr": "rychlý cukr, energia hned (třeba hroznový cukr).",
    "energetick": "kolik energie (kalorií) v jídle je.",
    "light": "verze jídla s méně cukru nebo méně tuku.",
}

def najdi_jednoduche_vysvetleni(slovo_lower, trida):
    """
    Zkusíme najít vysvětlení pro slovo podle našeho minislovníku.
    Hledáme podle začátku slova (kořen).
    Pokud nenajdeme, vrátíme obecnou větu, ale už NE 'vysvětli sám'.
    """
    for klic, vyznam in SLOVNIK_VYRAZU.items():
        if slovo_lower.startswith(klic):
            return vyznam
    # fallback – učitel může s žákem dovysvětlit, ale není to chyba typu
    # "vysvětli vlastními slovy".
    if trida <= 3:
        return "slovo, které si vysvětlíme spolu ve třídě (důležité pro hru)."
    elif trida == 4:
        return "slovo, které si vysvětlíme společně (týká se hodnocení / jídla)."
    else:
        return "slovo, které si vysvětlíme společně (týká se zdraví a výživy)."


def vyber_slovicka(text, max_slov=10):
    """
    Automatický výběr slov jako dřív:
    - vezmeme delší výrazy (8+ znaků),
    - odstraníme čísla,
    - uděláme unikáty.
    Vrací seznam slov (lowercase).
    """
    slova = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    kandidati = [s.strip() for s in slova if len(s) >= 8]
    unik = []
    for s in kandidati:
        low = s.lower()
        if low not in unik:
            unik.append(low)
    return unik[:max_slov]


def priprav_slovnicek(text, trida, max_slov=10):
    """
    Vrátí list dvojic (slovo, vysvětlení pro dítě).
    Použije automatický výběr a k nim přidá dětské vysvětlení.
    """
    vybrana_slova = vyber_slovicka(text, max_slov=max_slov)
    slovnik = []
    for slovo in vybrana_slova:
        vysv = najdi_jednoduche_vysvetleni(slovo, trida)
        slovnik.append((slovo, vysv))
    return slovnik


# -------------------------
#  LMP / SPU PODPORA
# -------------------------

def zjednodus_vetu(veta, max_slov=15):
    """
    Hodně jednoduchá 'hrubá' úprava:
    - vezmeme větu
    - rozdělíme na slova
    - uřízneme po max_slov
    - odstraníme extra čárky na konci
    Cíl: kratší věty pro LMP/SPU. Není to krásná literární úprava,
    ale je to použitelný podpůrný text.
    """
    slova = veta.strip().split()
    if not slova:
        return ""
    omezena = slova[:max_slov]
    kratsi = " ".join(omezena)
    kratsi = kratsi.strip(",;: ")
    return kratsi


def priprav_LMP_text(puvodni_text):
    """
    Uděláme podpůrnou verzi textu:
    - rozdělíme text na věty podle .?!,
    - každou větu zkrátíme,
    - složíme zpět do kratších odstavců.
    """
    # hrubé rozdělení na věty
    vety = re.split(r'(?<=[\.\?\!])\s+', puvodni_text.strip())
    jednodussi_vety = []
    for v in vety:
        v_clean = v.replace("\n", " ").strip()
        if not v_clean:
            continue
        jednodussi_vety.append(zjednodus_vetu(v_clean, max_slov=15))

    # spojíme po ~2 větách do krátkých odstavců
    odstavce = []
    blok = []
    for i, vv in enumerate(jednodussi_vety):
        blok.append(vv)
        if len(blok) == 2:
            odstavce.append(" ".join(blok))
            blok = []
    if blok:
        odstavce.append(" ".join(blok))

    return odstavce


# -------------------------
# OTÁZKY A / B / C podle ročníku
# -------------------------

def priprav_otazky(trida, text):
    """
    Vrátí (otazky_A, otazky_B, otazky_C, sebehodnoceni)
    – stabilní sada pro diplomku.
    """
    txt_lower = text.lower()

    # 3. třída - Karetní hra / návod
    if trida == 3:
        otazky_A = [
            "1) Jaký je cíl hry? (zakroužkuj)\n"
            "   A) Mít co nejvíc karet na konci.\n"
            "   B) Zbavit se všech karet jako první.\n"
            "   C) Nasbírat co nejvíc žolíků.",
            "2) Co znamená v této hře 'přebít kartu'?",
            "3) Kdo nebo co je chameleon v téhle hře?"
        ]
        otazky_B = [
            "4) Vysvětli: Co znamená říct 'pass'?",
            "5) Proč je důležité vědět, kdo přebíjí koho?"
        ]
        otazky_C = [
            "6) Chtěl/a bys tu hru hrát? Proč ano / proč ne?"
        ]
        sebehodnoceni = [
            "Rozuměl/a jsem pravidlům hry. 😃 / 🙂 / 😐",
            "Vím, jak vyhrát hru. 😃 / 🙂 / 😐",
            "Umím hru vysvětlit spolužákovi. 😃 / 🙂 / 😐",
        ]
        return otazky_A, otazky_B, otazky_C, sebehodnoceni

    # 4. třída - Věnečky / hodnocení kvality
    if trida == 4:
        otazky_A = [
            "1) Který věneček dopadl nejlépe? (napiš číslo věnečku)",
            "2) Který věneček byl nejdražší? Kolik stál?",
            "3) Které tvrzení NENÍ pravda podle textu?\n"
            "   A) Hodnotitelka říká, proč se jí něco líbí nebo nelíbí.\n"
            "   B) V textu se porovnává kvalita různých zákusků.\n"
            "   C) Text dává přesný domácí recept krok za krokem."
        ]
        otazky_B = [
            "4) Co znamená, že krém je 'sražený'?",
            "5) Proč někdo říká, že by ‚vrátil výuční list‘ cukráři? Co tím chce říct?",
            "6) Najdi v textu:\n"
            "   • jednu větu, která je FAKT (dá se ověřit),\n"
            "   • jednu větu, která je NÁZOR (pocit člověka)."
        ]
        otazky_C = [
            "7) Souhlasíš s tím, kdo byl označen jako nejlepší? Proč?",
            "8) Který zákusek bys chtěl/a ochutnat ty a proč?"
        ]
        sebehodnoceni = [
            "Rozuměl/a jsem textu. 😃 / 🙂 / 😐",
            "Našel/la jsem odpovědi v textu. 😃 / 🙂 / 😐",
            "Umím vysvětlit vlastními slovy. 😃 / 🙂 / 😐",
        ]
        return otazky_A, otazky_B, otazky_C, sebehodnoceni

    # 5. třída - Sladké mámení / článek o zdraví a cukru
    otazky_A = [
        "1) Proč podle textu lidé hledají nízkokalorické sladkosti?",
        "2) Co znamená slovo ‚nízkokalorické‘? Vysvětli jednoduše.",
        "3) Které tvrzení je v rozporu s textem (není pravda)?"
    ]
    otazky_B = [
        "4) Najdi v textu nějaký údaj z průzkumu (např. procenta) a opiš ho.",
        "5) Jak autor popisuje, které sladkosti jsou ‚zdravější‘?",
        "6) Vysvětli vlastními slovy pojem ‚jednoduché cukry‘."
    ]
    otazky_C = [
        "7) Myslíš si, že lidé opravdu chtějí ‚zdravé sladkosti‘? Proč ano / proč ne?",
        "8) Kdy podle tebe dává smysl dát si ‚rychlý cukr‘?"
    ]
    sebehodnoceni = [
        "Rozuměl/a jsem článku. 😃 / 🙂 / 😐",
        "Umím z textu vytáhnout informaci. 😃 / 🙂 / 😐",
        "Vím, co je zdravější volba. 😃 / 🙂 / 😐",
    ]
    return otazky_A, otazky_B, otazky_C, sebehodnoceni


# -------------------------
# Vytvoření dokumentu pro žáky
# -------------------------

def vytvor_docx_zaci(
    trida,
    puvodni_text,
    dramatizace,
    uvod,
    lmp_odstavce,
    slovnicek,
    otazky_A, otazky_B, otazky_C,
    sebehodnoceni
):
    """
    Vytvoří žákovský pracovní list do .docx (Word).
    Obsahuje:
    - jméno, třída
    - dramatizace
    - text (běžná verze)
    - text (zjednodušená podpora LMP/SPU)
    - slovníček
    - otázky A / B / C
    - sebehodnocení
    """

    doc = Document()

    # Globální font
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)

    doc.add_paragraph(f"{trida}. třída · Pracovní list (EdRead AI)")
    doc.add_paragraph("Jméno: ______________________    Třída: ________    Datum: __________")
    doc.add_paragraph("")

    # Dramatizace
    nadp = doc.add_paragraph("🎭 Úvodní scénka (zahájení hodiny)")
    nadp.runs[0].bold = True
    doc.add_paragraph("Zahrajte si krátkou scénku. Cíl: naladit se na text.")
    for replika in dramatizace:
        doc.add_paragraph("• " + replika)
    doc.add_paragraph("")

    # O čem je text
    nadp = doc.add_paragraph("📖 O čem je text")
    nadp.runs[0].bold = True
    doc.add_paragraph(uvod)
    doc.add_paragraph("")

    # Text pro čtení (běžná verze)
    nadp = doc.add_paragraph("📘 Text pro čtení (běžná verze)")
    nadp.runs[0].bold = True
    for odst in puvodni_text.split("\n"):
        if odst.strip():
            doc.add_paragraph(odst.strip())
    doc.add_paragraph("")

    # Text pro čtení – LMP/SPU
    nadp = doc.add_paragraph("🟦 Text pro čtení – zjednodušená podpora (LMP / SPU)")
    nadp.runs[0].bold = True
    doc.add_paragraph(
        "Tento text má kratší věty a jednodušší vyznění. "
        "Použij ho, pokud se ti původní text čte hůř."
    )
    for odst in lmp_odstavce:
        if odst.strip():
            doc.add_paragraph(odst.strip())
    doc.add_paragraph("")

    # Slovníček pojmů
    if slovnicek:
        nadp = doc.add_paragraph("📚 Slovníček pojmů")
        nadp.runs[0].bold = True
        doc.add_paragraph(
            "Tato slova můžou být náročnější. Vysvětlení je jednoduché, aby ti pomohlo textu lépe rozumět."
        )
        for slovo, vysvetleni in slovnicek:
            doc.add_paragraph(f"• {slovo} = {vysvetleni}")
        doc.add_paragraph("")

    # Otázky A
    nadp = doc.add_paragraph("🧠 OTÁZKY A – Porozumění textu")
    nadp.runs[0].bold = True
    for q in otazky_A:
        doc.add_paragraph(q)
        doc.add_paragraph("Odpověď: ________________________________")
        doc.add_paragraph("")

    # Otázky B
    nadp = doc.add_paragraph("💭 OTÁZKY B – Vysvětluji / zdůvodňuji")
    nadp.runs[0].bold = True
    for q in otazky_B:
        doc.add_paragraph(q)
        doc.add_paragraph("Odpověď: ________________________________")
        doc.add_paragraph("")

    # Otázky C
    nadp = doc.add_paragraph("🌟 OTÁZKY C – Můj názor")
    nadp.runs[0].bold = True
    for q in otazky_C:
        doc.add_paragraph(q)
        doc.add_paragraph("Odpověď: ________________________________")
        doc.add_paragraph("")

    # Sebehodnocení
    nadp = doc.add_paragraph("📝 Sebehodnocení žáka")
    nadp.runs[0].bold = True
    for r in sebehodnoceni:
        doc.add_paragraph(r)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


# -------------------------
# Vytvoření METODICKÉHO LISTU
# -------------------------

def vytvor_docx_ucitel(
    trida,
    puvodni_text,
    dramatizace,
    uvod,
    otazky_A, otazky_B, otazky_C,
    sebehodnoceni
):
    """
    Metodický list je SAMOSTATNÝ dokument.
    Obsahuje:
    - Cíl hodiny
    - Vazbu na RVP ZV (čtenářská gramotnost)
    - Doporučený průběh
    - Diferenciaci (včetně LMP / SPU)
    - Přehled otázek A / B / C
    """

    doc = Document()

    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)

    nadp = doc.add_paragraph("📘 METODICKÝ LIST PRO UČITELE")
    nadp.runs[0].bold = True
    doc.add_paragraph(f"Ročník: {trida}. třída")
    doc.add_paragraph("")

    doc.add_paragraph("Téma hodiny:")
    if trida == 3:
        doc.add_paragraph("Porozumění návodu / pravidlům hry, práce s informací krok za krokem.")
    elif trida == 4:
        doc.add_paragraph("Porozumění hodnoticímu textu (zákusek = produkt), rozdíl názor/fakt.")
    else:
        doc.add_paragraph("Porozumění publicistickému textu o sladkostech a zdraví, práce s daty a tvrzeními.")

    doc.add_paragraph("")

    doc.add_paragraph("Cíle hodiny (pro žáka):")
    doc.add_paragraph("1. Žák rozumí hlavnímu sdělení textu.")
    doc.add_paragraph("2. Žák vyhledá konkrétní informaci v textu.")
    doc.add_paragraph("3. Žák rozliší FAKT a NÁZOR (4.–5. třída).")
    doc.add_paragraph("4. Žák formuluje vlastní názor a krátce ho zdůvodní.")
    doc.add_paragraph("5. Žák reflektuje, jak se mu četlo (sebehodnocení).")
    doc.add_paragraph("")

    # Vazba na RVP ZV: český jazyk a jazyková komunikace – čtenářská gramotnost
    # (formulace z RVP ZV typu: porozumění textu; vyhledávání informací; rozlišování faktu a názoru;
    # vyjadřování vlastního postoje k textu)
    nadp = doc.add_paragraph("Vazba na RVP ZV (obor Český jazyk a literatura, čtenářská gramotnost)")
    nadp.runs[0].bold = True
    doc.add_paragraph("• Žák čte s porozuměním a rozumí smyslu textu.")
    doc.add_paragraph("• Žák vyhledává a třídí základní informace v různých typech textů.")
    doc.add_paragraph("• Žák rozlišuje mezi faktickým sdělením a názorem / hodnocením (4.–5. ročník).")
    doc.add_paragraph("• Žák formuluje jednoduché vlastní hodnocení textu a zdůvodní ho s pomocí učitele.")
    doc.add_paragraph("• Žák reflektuje vlastní porozumění textu (sebehodnocení).")
    doc.add_paragraph("")

    doc.add_paragraph("Doporučený průběh (45 min):")
    doc.add_paragraph("1) MOTIVACE / DRAMATIZACE (cca 5 min)")
    doc.add_paragraph("   - Krátká scénka podle dramatizace. Vtáhne žáky do situace a smyslu textu.")
    doc.add_paragraph("2) PRÁCE S TEXTEM (cca 10–15 min)")
    doc.add_paragraph("   - Žáci čtou běžnou verzi textu.")
    doc.add_paragraph("   - Slabší čtenáři nebo žáci s LMP/SPU čtou zjednodušenou verzi (kratší věty).")
    doc.add_paragraph("   - Učitel vysvětlí složitější slova pomocí slovníčku.")
    doc.add_paragraph("3) OTÁZKY A / B / C (cca 15 min)")
    doc.add_paragraph("   - A: vyhledání informací v textu.")
    doc.add_paragraph("   - B: vysvětlení a odůvodnění, práce s pojmy.")
    doc.add_paragraph("   - C: vyjádření vlastního názoru k textu / produktu / situaci.")
    doc.add_paragraph("4) SEBEHODNOCENÍ (cca 5 min)")
    doc.add_paragraph("   - Žáci označí, jak se jim dařilo rozumět textu.")
    doc.add_paragraph("")

    doc.add_paragraph("Diferenciace a podpora (inkluzivní přístup):")
    doc.add_paragraph("• Žáci s LMP/SPU mohou pracovat hlavně se zjednodušenou verzí textu (kratší věty).")
    doc.add_paragraph("• U nich můžeme zmenšit počet otázek, např. pouze z OTÁZEK A a jednu otázku z části C.")
    doc.add_paragraph("• U silnějších čtenářů lze naopak rozšířit část C: chtít delší zdůvodnění.")
    doc.add_paragraph("")

    doc.add_paragraph("Dramatizace (zahájení hodiny):")
    for r in dramatizace:
        doc.add_paragraph("• " + r)
    doc.add_paragraph("")

    doc.add_paragraph("Stručný obsah textu pro učitele:")
    doc.add_paragraph(uvod)
    doc.add_paragraph("")

    doc.add_paragraph("Přehled otázek pro žáky:")
    doc.add_paragraph("OTÁZKY A – Porozumění textu:")
    for q in otazky_A:
        doc.add_paragraph("• " + q)
    doc.add_paragraph("")

    doc.add_paragraph("OTÁZKY B – Vysvětluji / zdůvodňuji:")
    for q in otazky_B:
        doc.add_paragraph("• " + q)
    doc.add_paragraph("")

    doc.add_paragraph("OTÁZKY C – Můj názor:")
    for q in otazky_C:
        doc.add_paragraph("• " + q)
    doc.add_paragraph("")

    doc.add_paragraph("Sebehodnocení žáka:")
    for r in sebehodnoceni:
        doc.add_paragraph("• " + r)

    doc.add_paragraph("")
    doc.add_paragraph(
        "Poznámka pro diplomovou práci: Tento list a metodika "
        "jsou generovány prototypem EdRead AI. Nástroj "
        "vytváří (1) text pro čtení, (2) jednodušší podporu pro žáky s LMP/SPU, "
        "(3) slovníček složitějších slov s jednoduchým vysvětlením, "
        "(4) otázky A/B/C podle RVP ZV zaměřené na čtenářskou gramotnost."
    )

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


# =========================
# STREAMLIT APLIKACE
# =========================

st.set_page_config(page_title="EdRead AI – školní prototyp", layout="centered")

st.title("EdRead AI – generátor pracovních listů")
st.write("Verze 4 (LMP/SPU podpora, slovníček s vysvětlením, metodika zvlášť).")

st.write("1) Vlož text pro žáky (přesně tak, jak ho použiješ ve výuce).")
puvodni_text = st.text_area("Výchozí text (kopie z testu / článku / zadání úlohy)", height=400)

st.write("2) Vyber ročník, pro který list tvoříš.")
trida_volba = st.selectbox("Ročník:", ["3", "4", "5"])

if st.button("Vytvořit dokumenty (.docx)"):
    if not puvodni_text.strip():
        st.error("Nejdřív vlož text.")
    else:
        trida = detekuj_tridu(trida_volba)

        # připravíme části
        dramatizace = priprav_dramatizaci(trida)
        uvod = priprav_uvod_pro_zaka(trida)

        lmp_odstavce = priprav_LMP_text(puvodni_text)

        slovnicek = priprav_slovnicek(puvodni_text, trida, max_slov=10)

        otA, otB, otC, sebehod = priprav_otazky(trida, puvodni_text)

        # vytvořit dokument pro žáky
        docx_zaci = vytvor_docx_zaci(
            trida,
            puvodni_text,
            dramatizace,
            uvod,
            lmp_odstavce,
            slovnicek,
            otA, otB, otC,
            sebehod
        )

        # vytvořit metodiku pro učitele
        docx_ucitel = vytvor_docx_ucitel(
            trida,
            puvodni_text,
            dramatizace,
            uvod,
            otA, otB, otC,
            sebehod
        )

        today_str = datetime.date.today().isoformat()
        fname_student = f"pracovni_list_EdReadAI_{trida}trida_{today_str}.docx"
        fname_teacher = f"metodicky_list_EdReadAI_{trida}trida_{today_str}.docx"

        st.success("Dokumenty připraveny. Stáhni Word soubory níže:")

        st.download_button(
            label="📥 Stáhnout pracovní list pro žáky (.docx)",
            data=docx_zaci,
            file_name=fname_student,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        st.download_button(
            label="📘 Stáhnout metodický list pro učitele (.docx)",
            data=docx_ucitel,
            file_name=fname_teacher,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
