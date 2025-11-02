import streamlit as st
from docx import Document
from docx.shared import Pt
from io import BytesIO
import datetime
import re


# =========================
#  1. Pomocné funkce
# =========================

def detekuj_tridu(volba_tridy: str) -> int:
    """Vrátí číslo ročníku jako int (3, 4, 5)."""
    try:
        return int(volba_tridy)
    except:
        return 0


def priprav_dramatizaci(trida: int):
    """Krátká motivační scénka na začátek hodiny podle ročníku."""
    if trida == 3:
        return [
            "Učitel: „Mám tu novou karetní hru. Kdo ví, jak se hraje?“",
            "Adam: „Já tomu vůbec nerozumím… tady píšou o přebíjení.“",
            "Ema: „Tak si to přečteme a zkusíme zahrát. Já budu liška!“",
            "→ Cíl: děti mají chuť pochopit návod ke hře."
        ]
    elif trida == 4:
        return [
            "Učitel: „Dneska jste porota cukrářské soutěže.“",
            "Ema: „Můžu říct, že krém je špatný?“",
            "Učitel: „Můžeš, ale musíš říct proč. To je rozdíl mezi názorem a důvodem.“",
            "→ Cíl: děti vidí, že text hodnotí kvalitu výrobků a musí to umět zdůvodnit."
        ]
    else:  # 5. třída
        return [
            "Učitel: „Představte si dva typy textů: reklama na čokoládu vs. článek o čokoládě.“",
            "Tonda: „Reklama chce, abych to koupil.“",
            "Lenka: „A článek řeší, co je zdravé?“",
            "Učitel: „Ano. My dnes čteme článek, ne reklamu.“",
            "→ Cíl: žáci chápou, že text informuje, neprodává."
        ]


def priprav_uvod_pro_zaka(trida: int) -> str:
    """Krátké vysvětlení pro děti: O čem je text / proč ho čteme."""
    if trida == 3:
        return (
            "V tomhle textu se vysvětluje hra a její pravidla. "
            "Naučíš se, kdo je silnější a jak můžeš vyhrát. "
            "Budeš hledat informace přímo v textu."
        )
    elif trida == 4:
        return (
            "V tomhle textu někdo hodnotí zákusky (věnečky). Říká, co je dobré a co je špatné. "
            "Ty se naučíš najít fakta v textu, poznat názor a říct svůj vlastní názor."
        )
    else:
        return (
            "Tento text mluví o sladkostech, zdraví a o tom, co lidé opravdu jedí. "
            "Budeš hledat údaje, porovnávat tvrzení a přemýšlet, co si o tom myslíš ty."
        )


# =========================
#  2. Slovníček
# =========================

# Malý „dětský slovník“ výrazů, které se často objevují v textech
# (karetní hra / věnečky / sladké mámení).
# Klíč = kořen slova (bez diakritiky tady řešit nemusíme, jen malá písmena),
# Hodnota = vysvětlení pro dítě.
SLOVNIK_VYRAZU = {
    # Karetní hra / pravidla hry
    "přebí": "porazit jinou kartu (ukázat silnější kartu).",
    "kombinace": "více stejných karet zahraných najednou.",
    "žolík": "speciální karta, která se může tvářit jako jakákoli jiná karta.",
    "chameleon": "karta, která se počítá jako jiná karta (pomůže ti vyhrát).",
    "pravidl": "co se smí a nesmí dělat při hře.",
    "kolo": "část hry, kdy postupně hrají všichni hráči.",
    "pass": "hráč řekne „pass“, a ten tah vynechá (teď nehraje).",

    # Věnečky / cukrařina
    "sražen": "krém se pokazil a jsou v něm hrudky.",
    "margar": "tuk podobný máslu.",
    "odpalovan": "těsto na věneček nebo větrník, má být nadýchané a měkké.",
    "korpus": "spodní nebo vnější část zákusku (těsto).",
    "receptur": "správný postup a suroviny podle receptu.",
    "výuční": "papír, kterým se dokazuje, že je někdo vyučený (má řemeslo).",
    "chemick": "umělá chuť, není to čerstvé a přirozené.",
    "pachuť": "chuť, která zůstane v puse po jídle.",
    "zestárl": "už to není čerstvé, je to tvrdé a staré.",
    "připečen": "moc pečené, skoro spálené, tvrdé.",

    # Sladké mámení / výživa
    "nízkokalor": "málo kalorií (jídlo, po kterém tolik nepřibírám).",
    "obezit": "nezdravě vysoká tělesná hmotnost (člověk má nadváhu).",
    "metabol": "to, jak tělo zpracovává jídlo na energii.",
    "polysachar": "složitý cukr, energie se uvolňuje pomalu (např. vláknina).",
    "jednoduché": "rychlý cukr, energie hned (třeba hroznový cukr).",
    "energet": "kolik energie (kalorií) jídlo má.",
    "light": "verze jídla s méně cukru nebo méně tuku."
}


def vyber_slovicka(text: str, max_slov: int = 10):
    """
    Automaticky vybere možná „těžší“ slova:
    - slova s délkou 8+ znaků,
    - bez čísel,
    - vezme unikáty v pořadí výskytu.
    Vrací seznam slov v lowercase.
    """
    slova = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    kandidati = [s.strip() for s in slova if len(s) >= 8]
    unik = []
    for s in kandidati:
        low = s.lower()
        if low not in unik:
            unik.append(low)
    return unik[:max_slov]


def vysvetli_slovo(slovo_lower: str, trida: int) -> str:
    """
    Najdi co nejpřesnější dětské vysvětlení.
    1. Zkusíme náš slovník (hledání podle začátku).
    2. Když nenajdeme, dáme jemné „slovo, které si vysvětlíme ve třídě“,
       formulované tak, aby to bylo přijatelné i do diplomky.
    """
    for klic, vyznam in SLOVNIK_VYRAZU.items():
        if slovo_lower.startswith(klic):
            return vyznam

    if trida == 3:
        return "důležité slovo z textu – vysvětlíme si ho spolu s učitelem."
    elif trida == 4:
        return "slovo z hodnocení jídla / kvality. Probereme spolu s učitelem."
    else:
        return "slovo z oblasti zdraví a jídla. Probereme spolu s učitelem."


def priprav_slovnicek(text: str, trida: int, max_slov: int = 10):
    """
    Vrátí list dvojic (slovo, vysvětlení).
    Tohle pak jde přímo do Wordu jako:
    • slovo = vysvětlení
    """
    vybrana_slova = vyber_slovicka(text, max_slov=max_slov)
    vystup = []
    for slovo in vybrana_slova:
        popis = vysvetli_slovo(slovo, trida)
        vystup.append((slovo, popis))
    return vystup


# =========================
#  3. Podpůrná verze textu LMP/SPU
# =========================

def zkrat_vetu(veta: str, limit_slov: int = 15):
    """
    Udělá z věty kratší větu max limit_slov slov.
    Čistě mechanicky, aby se to lépe četlo slabším čtenářům.
    """
    slova = veta.strip().split()
    if not slova:
        return ""
    omezena = slova[:limit_slov]
    kratsi = " ".join(omezena).strip(",;: ")
    return kratsi


def priprav_text_LMP(puvodni_text: str):
    """
    Vytvoří podpůrnou verzi textu:
    - rozdělí text na věty podle .?!,
    - každou větu zkrátí,
    - složí kratší odstavce po 2 větách.
    """
    vety = re.split(r'(?<=[\.\?\!])\s+', puvodni_text.strip())
    kratke_vety = []
    for v in vety:
        cista = v.replace("\n", " ").strip()
        if not cista:
            continue
        kratke_vety.append(zkrat_vetu(cista, limit_slov=15))

    odstavce = []
    blok = []
    for vv in kratke_vety:
        if vv:
            blok.append(vv)
        if len(blok) == 2:
            odstavce.append(" ".join(blok))
            blok = []
    if blok:
        odstavce.append(" ".join(blok))

    return odstavce


# =========================
#  4. Otázky pro žáky podle ročníku
# =========================

def priprav_otazky(trida: int):
    """
    Vrátí čtyři seznamy:
    - otazky_A (porozumění textu)
    - otazky_B (vysvětlení, důvody)
    - otazky_C (vlastní názor)
    - sebehodnoceni (smajlíky)
    Hotové texty bez chybného číslování.
    """

    # 3. třída: text typu "Karetní hra"
    if trida == 3:
        ot_A = [
            "1) Jaký je cíl hry? (zakroužkuj)\n"
            "   A) Mít co nejvíc karet na konci.\n"
            "   B) Zbavit se všech karet jako první.\n"
            "   C) Sbírat jen speciální kartu chameleona.",
            "2) Co znamená „přebít kartu“ v téhle hře?",
            "3) Co dělá chameleon (žolík) v té hře?"
        ]
        ot_B = [
            "4) Co znamená, když hráč řekne „pass“?",
            "5) Proč je důležité vědět, kdo koho přebíjí?"
        ]
        ot_C = [
            "6) Chtěl/a bys tu hru hrát? Proč ano / proč ne?"
        ]
        self_eval = [
            "Rozuměl/a jsem pravidlům hry. 😃 / 🙂 / 😐",
            "Vím, jak se dá vyhrát. 😃 / 🙂 / 😐",
            "Umím hru vysvětlit spolužákovi. 😃 / 🙂 / 😐"
        ]
        return ot_A, ot_B, ot_C, self_eval

    # 4. třída: text typu "Věnečky"
    if trida == 4:
        ot_A = [
            "1) Který věneček byl hodnocen jako nejlepší? (napiš číslo věnečku)",
            "2) Který věneček byl nejdražší a kolik stál?",
            "3) Které tvrzení NENÍ pravda podle textu?\n"
            "   A) V textu se porovnává kvalita různých zákusků.\n"
            "   B) Hodnotitelka říká, co je dobré a co je špatné, a proč.\n"
            "   C) Text dává podrobný domácí recept krok za krokem."
        ]
        ot_B = [
            "4) Co znamená, když je krém „sražený“?",
            "5) Proč někdo říká, že by ‚vrátil výuční list‘ cukráři? Co tím chce říct?",
            "6) Najdi v textu:\n"
            "   • jednu větu, která je FAKT (dá se ověřit),\n"
            "   • jednu větu, která je NÁZOR (pocit člověka)."
        ]
        ot_C = [
            "7) Souhlasíš s tím, který věneček byl nejlepší? Proč?",
            "8) Který zákusek bys chtěl/a ochutnat ty a proč?"
        ]
        self_eval = [
            "Rozuměl/a jsem textu. 😃 / 🙂 / 😐",
            "Našel/našla jsem informace v textu. 😃 / 🙂 / 😐",
            "Umím říct svůj názor a zdůvodnit ho. 😃 / 🙂 / 😐"
        ]
        return ot_A, ot_B, ot_C, self_eval

    # 5. třída: text typu "Sladké mámení"
    ot_A = [
        "1) Proč podle textu lidé hledají nízkokalorické sladkosti?",
        "2) Co znamená „nízkokalorické“? Vysvětli jednoduše.",
        "3) Jaký problém se v textu spojuje s obezitou?"
    ]
    ot_B = [
        "4) Najdi a napiš jeden údaj z průzkumu (např. procento) a co znamená.",
        "5) Jak autor popisuje, jaké sladkosti jsou ‚zdravější‘?",
        "6) Vysvětli vlastními slovy pojem „jednoduchý cukr“."
    ]
    ot_C = [
        "7) Myslíš si, že lidé vážně chtějí zdravější sladkosti? Proč ano / proč ne?",
        "8) Kdy podle tebe dává smysl dát si ‚rychlý cukr‘ (např. hroznový cukr)?"
    ]
    self_eval = [
        "Rozuměl/a jsem článku. 😃 / 🙂 / 😐",
        "Umím najít důležitou informaci. 😃 / 🙂 / 😐",
        "Vím, jak přemýšlet o zdravější volbě. 😃 / 🙂 / 😐"
    ]
    return ot_A, ot_B, ot_C, self_eval


# =========================
#  5. Vytvoření Word dokumentů
# =========================

def nastav_docx_font(doc):
    """Nastaví globální styl textu ve Wordu na Arial 11."""
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)


def docx_zaci(
    trida: int,
    puvodni_text: str,
    dramatizace,
    uvod_txt: str,
    lmp_odstavce,
    slovnicek,
    otA, otB, otC,
    self_eval
):
    """
    Vytvoří pracovní list pro žáky (.docx):
    - Hlavička
    - Dramatizace
    - O čem je text
    - Text (běžná verze)
    - Text zjednodušený (LMP/SPU)
    - Slovníček
    - Otázky A/B/C
    - Sebehodnocení
    """
    doc = Document()
    nastav_docx_font(doc)

    # Hlavička
    p = doc.add_paragraph(f"{trida}. třída · Pracovní list (EdRead AI)")
    p.runs[0].bold = True
    doc.add_paragraph("Jméno: ______________________    Třída: ________    Datum: __________")
    doc.add_paragraph("")

    # Dramatizace
    p = doc.add_paragraph("🎭 Úvodní scénka (zahájení hodiny)")
    p.runs[0].bold = True
    doc.add_paragraph("Zahrajte si krátkou scénku. Cíl: naladit se na text.")
    for replika in dramatizace:
        doc.add_paragraph("• " + replika)
    doc.add_paragraph("")

    # O čem je text
    p = doc.add_paragraph("📖 O čem je text")
    p.runs[0].bold = True
    doc.add_paragraph(uvod_txt)
    doc.add_paragraph("")

    # Text pro čtení (běžná verze)
    p = doc.add_paragraph("📘 Text pro čtení (běžná verze)")
    p.runs[0].bold = True
    for odst in puvodni_text.split("\n"):
        if odst.strip():
            doc.add_paragraph(odst.strip())
    doc.add_paragraph("")

    # Zjednodušená verze (LMP/SPU)
    p = doc.add_paragraph("🟦 Text pro čtení – zjednodušená podpora (LMP / SPU)")
    p.runs[0].bold = True
    doc.add_paragraph(
        "Tento text má kratší věty a jednodušší vyjádření. "
        "Použij ho, pokud se ti původní text čte hůř."
    )
    for odst in lmp_odstavce:
        if odst.strip():
            doc.add_paragraph(odst.strip())
    doc.add_paragraph("")

    # Slovníček pojmů
    if slovnicek:
        p = doc.add_paragraph("📚 Slovníček pojmů")
        p.runs[0].bold = True
        doc.add_paragraph(
            "Tato slova můžou být náročnější. Vysvětlení je napsané tak, "
            "aby ti pomohlo lépe rozumět textu."
        )
        for slovo, vyznam in slovnicek:
            doc.add_paragraph(f"• {slovo} = {vyznam}")
        doc.add_paragraph("")

    # OTÁZKY A
    p = doc.add_paragraph("🧠 OTÁZKY A – Porozumění textu")
    p.runs[0].bold = True
    for q in otA:
        doc.add_paragraph(q)
        doc.add_paragraph("Odpověď: ______________________________________")
        doc.add_paragraph("")

    # OTÁZKY B
    p = doc.add_paragraph("💭 OTÁZKY B – Vysvětluji a zdůvodňuji")
    p.runs[0].bold = True
    for q in otB:
        doc.add_paragraph(q)
        doc.add_paragraph("Odpověď: ______________________________________")
        doc.add_paragraph("")

    # OTÁZKY C
    p = doc.add_paragraph("🌟 OTÁZKY C – Můj názor")
    p.runs[0].bold = True
    for q in otC:
        doc.add_paragraph(q)
        doc.add_paragraph("Odpověď: ______________________________________")
        doc.add_paragraph("")

    # Sebehodnocení
    p = doc.add_paragraph("📝 Sebehodnocení žáka")
    p.runs[0].bold = True
    for r in self_eval:
        doc.add_paragraph(r)

    # hotovo
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


def docx_ucitel(
    trida: int,
    puvodni_text: str,
    dramatizace,
    uvod_txt: str,
    otA, otB, otC,
    self_eval
):
    """
    Metodický list pro učitele (.docx):
    - Téma, cíle, RVP ZV
    - Doporučený průběh hodiny
    - Diferenciace (LMP/SPU)
    - Přehled otázek
    - Poznámka pro DP
    """
    doc = Document()
    nastav_docx_font(doc)

    # Nadpis
    p = doc.add_paragraph("📘 METODICKÝ LIST PRO UČITELE")
    p.runs[0].bold = True
    doc.add_paragraph(f"Ročník: {trida}. třída")
    doc.add_paragraph("")

    # Téma hodiny
    doc.add_paragraph("Téma hodiny:")
    if trida == 3:
        doc.add_paragraph(
            "Porozumění návodu / pravidlům hry. Pochopení kroků, kdo je silnější a jak vyhrát."
        )
    elif trida == 4:
        doc.add_paragraph(
            "Porozumění hodnoticímu textu o kvalitě výrobku. Rozlišování faktu a názoru."
        )
    else:
        doc.add_paragraph(
            "Porozumění publicistickému textu o sladkostech a zdraví. "
            "Práce s informací a argumentací."
        )
    doc.add_paragraph("")

    # Cíle hodiny
    doc.add_paragraph("Cíle hodiny (pro žáka):")
    doc.add_paragraph("1. Žák rozumí hlavnímu sdělení textu.")
    doc.add_paragraph("2. Žák vyhledá konkrétní informaci v textu.")
    doc.add_paragraph("3. Žák rozlišuje FAKT vs. NÁZOR (4.–5. třída).")
    doc.add_paragraph("4. Žák formuluje svůj názor a zdůvodní ho v krátké větě.")
    doc.add_paragraph("5. Žák reflektuje své porozumění (sebehodnocení).")
    doc.add_paragraph("")

    # Vazba na RVP ZV
    p = doc.add_paragraph("Vazba na RVP ZV (Český jazyk a literatura – čtenářská gramotnost)")
    p.runs[0].bold = True
    doc.add_paragraph("• Žák čte s porozuměním text přiměřený věku.")
    doc.add_paragraph("• Žák vyhledává a třídí základní informace v textu.")
    doc.add_paragraph("• Žák rozlišuje mezi faktickým sdělením a názorem / hodnocením.")
    doc.add_paragraph("• Žák vyjadřuje jednoduché hodnocení textu nebo situace a svůj postoj zdůvodní.")
    doc.add_paragraph("• Žák se učí reflektovat vlastní porozumění textu (sebehodnocení → já rozumím / nerozumím).")
    doc.add_paragraph("")

    # Doporučený průběh hodiny
    doc.add_paragraph("Doporučený průběh hodiny (45 minut):")
    doc.add_paragraph("1) MOTIVACE / DRAMATIZACE (cca 5 min)")
    doc.add_paragraph("   - Krátká scénka (viz níže). Žáci se vtáhnou do situace.")
    doc.add_paragraph("2) ČTENÍ TEXTU (cca 10–15 min)")
    doc.add_paragraph("   - Společné nebo samostatné čtení původního textu.")
    doc.add_paragraph("   - Slabší čtenáři / žáci s LMP/SPU čtou zjednodušenou verzi (kratší věty).")
    doc.add_paragraph("   - Učitel vysvětlí obtížná slova pomocí slovníčku.")
    doc.add_paragraph("3) PRÁCE S OTÁZKAMI (cca 15 min)")
    doc.add_paragraph("   - A: porozumění textu – vyhledání informací.")
    doc.add_paragraph("   - B: vysvětlení pojmů / proč si to postava myslí.")
    doc.add_paragraph("   - C: názor žáka, krátká argumentace.")
    doc.add_paragraph("4) SEBEHODNOCENÍ (cca 5 min)")
    doc.add_paragraph("   - Žáci označí smajlíka 😃 🙂 😐 u tří vět.")
    doc.add_paragraph("")

    # Diferenciace / inkluze
    doc.add_paragraph("Diferenciace a podpora (inkluzivní přístup):")
    doc.add_paragraph("• Žáci s LMP/SPU pracují primárně se zjednodušenou verzí textu (kratší věty).")
    doc.add_paragraph("• U nich můžeme omezit počet otázek pouze na část A a jednu otázku z části C.")
    doc.add_paragraph("• Silnější žáci mohou dostat úkol ‚rozliš fakt vs. názor a vysvětli proč‘.")
    doc.add_paragraph("")

    # Dramatizace pro učitele
    doc.add_paragraph("Dramatizace (zahájení hodiny):")
    for r in dramatizace:
        doc.add_paragraph("• " + r)
    doc.add_paragraph("")

    # Stručný obsah textu (pro učitele, aby věděl, jak to shrnout dětem)
    doc.add_paragraph("Stručné vysvětlení textu pro žáky (jak jim to říct):")
    doc.add_paragraph(uvod_txt)
    doc.add_paragraph("")

    # Přehled otázek
    doc.add_paragraph("Přehled žákovských otázek:")
    doc.add_paragraph("OTÁZKY A – Porozumění textu")
    for q in otA:
        doc.add_paragraph("• " + q)
    doc.add_paragraph("")

    doc.add_paragraph("OTÁZKY B – Vysvětluji a zdůvodňuji")
    for q in otB:
        doc.add_paragraph("• " + q)
    doc.add_paragraph("")

    doc.add_paragraph("OTÁZKY C – Můj názor")
    for q in otC:
        doc.add_paragraph("• " + q)
    doc.add_paragraph("")

    doc.add_paragraph("Sebehodnocení žáka")
    for r in self_eval:
        doc.add_paragraph("• " + r)
    doc.add_paragraph("")

    # Poznámka pro DP
    doc.add_paragraph(
        "Poznámka pro diplomovou práci: Tento metodický list i žákovský list "
        "jsou vytvořené nástrojem EdRead AI. Nástroj automaticky generuje "
        "podpůrnou verzi textu (LMP/SPU), slovníček složitějších slov s dětským "
        "vysvětlením, otázky k porozumění/textové práci a vazbu na RVP ZV."
    )

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


# =========================
#  6. Streamlit aplikace
# =========================

st.set_page_config(
    page_title="EdRead AI – generátor pracovních listů (verze 5)",
    layout="centered"
)

st.title("EdRead AI – generátor pracovních listů (verze 5)")
st.write("Automaticky vytvoří:")
st.write("• pracovní list pro žáky (Word) – včetně LMP/SPU verze textu, slovníčku a otázek")
st.write("• metodický list pro učitele (Word) – včetně vazby na RVP ZV")

st.markdown("### 1) Vlož text pro žáky")
puvodni_text = st.text_area(
    "Sem vlož výchozí text (např. Karetní hra / Věnečky / Sladké mámení).",
    height=400
)

st.markdown("### 2) Vyber ročník")
trida_volba = st.selectbox("Ročník:", ["3", "4", "5"])


if st.button("Vygenerovat Word dokumenty"):
    if not puvodni_text.strip():
        st.error("Musíš vložit text.")
    else:
        trida = detekuj_tridu(trida_volba)

        # připravíme části obsahu
        dramatizace = priprav_dramatizaci(trida)
        uvod_txt = priprav_uvod_pro_zaka(trida)
        lmp_verze = priprav_text_LMP(puvodni_text)
        slovnicek = priprav_slovnicek(puvodni_text, trida, max_slov=10)
        otA, otB, otC, self_eval = priprav_otazky(trida)

        # vytvořit Word pro žáky
        soubor_zaci = docx_zaci(
            trida,
            puvodni_text,
            dramatizace,
            uvod_txt,
            lmp_verze,
            slovnicek,
            otA, otB, otC,
            self_eval
        )

        # vytvořit Word pro učitele
        soubor_ucitel = docx_ucitel(
            trida,
            puvodni_text,
            dramatizace,
            uvod_txt,
            otA, otB, otC,
            self_eval
        )

        today = datetime.date.today().isoformat()
        fname_students = f"EdReadAI_zaci_{trida}trida_{today}.docx"
        fname_teacher = f"EdReadAI_ucitel_{trida}trida_{today}.docx"

        st.success("Hotovo. Stáhni oba Word dokumenty níže:")

        st.download_button(
            label="📥 Stáhnout pracovní list pro žáky (.docx)",
            data=soubor_zaci,
            file_name=fname_students,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        st.download_button(
            label="📘 Stáhnout metodický list pro učitele (.docx)",
            data=soubor_ucitel,
            file_name=fname_teacher,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
