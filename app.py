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
    try:
        return int(volba_tridy)
    except:
        return 0


def priprav_dramatizaci(trida: int):
    if trida == 3:
        return [
            "Učitel: „Mám tu novou karetní hru. Kdo ví, jak se hraje?“",
            "Adam: „Já tomu vůbec nerozumím… tady píšou o přebíjení.“",
            "Ema: „Tak si to přečteme a zkusíme zahrát. Já budu liška!“",
            "→ Cíl: děti mají chuť pochopit pravidla hry."
        ]
    elif trida == 4:
        return [
            "Učitel: „Dneska jste porota v cukrárně.“",
            "Ema: „Můžu říct, že krém je špatný?“",
            "Učitel: „Ano, ale musíš říct proč. To je rozdíl mezi názorem a důvodem.“",
            "→ Cíl: žák chápe, že musí umět zdůvodnit hodnocení."
        ]
    else:  # 5. třída
        return [
            "Učitel: „Reklama chce, abys něco koupil. Článek chce, abys něco pochopil.“",
            "Tonda: „Takže ten náš text je článek?“",
            "Učitel: „Ano. Budeme zjišťovat, co říká o sladkostech a zdraví.“",
            "→ Cíl: žák rozumí, že text informuje, není to reklama."
        ]


def priprav_uvod_pro_zaka(trida: int) -> str:
    if trida == 3:
        return (
            "V tomhle textu se vysvětluje hra a její pravidla. "
            "Naučíš se, kdo je silnější a jak můžeš vyhrát. "
            "Budeš hledat informace přímo v textu."
        )
    elif trida == 4:
        return (
            "V tomhle textu někdo hodnotí zákusky (věnečky). Říká, co je dobré a co je špatné, "
            "a musí to umět vysvětlit. Ty poznáš fakt a názor."
        )
    else:
        return (
            "Text mluví o sladkostech, zdraví a o tom, co lidé opravdu jedí. "
            "Budeš hledat údaje, porovnávat tvrzení a říct, co si myslíš ty."
        )


# =========================
#  2. Slovníček
# =========================

# Základní vysvětlení častých „těžších“ slov / kořenů.
SLOVNIK_VYRAZU = {
    # karetní hra
    "přebí": "porazit jinou kartu (ukázat silnější kartu).",
    "kombinace": "více stejných karet zahraných najednou.",
    "žolík": "speciální karta, která se může tvářit jako jakákoli jiná karta.",
    "chameleon": "karta, která se počítá jako jiná karta (pomůže ti vyhrát).",
    "pravidl": "co se smí a nesmí dělat při hře.",
    "kolo": "část hry, kdy postupně hrají všichni hráči.",
    "pass": "hráč řekne „pass“ a ten tah nehraje (vynechá).",

    # věnečky
    "sražen": "krém se pokazil a má hrudky.",
    "margar": "tuk podobný máslu.",
    "odpalovan": "těsto na věneček nebo větrník, má být nadýchané a měkké.",
    "korpus": "spodní / tělová část zákusku (těsto).",
    "receptur": "správný postup a suroviny podle receptu.",
    "výuční": "papír (osvědčení), že je někdo vyučený řemeslu.",
    "chemick": "umělá chuť, není to přirozené.",
    "pachuť": "chuť, která zůstane v puse po jídle.",
    "zestárl": "už to není čerstvé, je to staré a tvrdé.",
    "připečen": "moc pečené, skoro spálené, tvrdé.",
    "nadlehčený": "udělaný lehčí, vzdušnější.",
    "recept": "návod, jak něco připravit (co tam dát a v jakém množství).",

    # sladké mámení / výživa
    "nízkokalor": "málo kalorií (jídlo, po kterém tolik nepřibírám).",
    "obezit": "nezdravě vysoká tělesná hmotnost.",
    "metabol": "jak tělo mění jídlo na energii.",
    "polysachar": "složitý cukr; energie se uvolňuje pomalu (např. vláknina).",
    "jednoduché": "rychlý cukr; energie hned (třeba hroznový cukr).",
    "energet": "kolik energie (kalorií) jídlo má.",
    "light": "verze jídla s méně cukru nebo méně tuku.",
    "kalori": "energie z jídla. Když jím moc kalorií a málo se hýbu, přibírám.",
    "analytik": "odborník, který vyhodnocuje informace a dělá závěry.",
}


DULEZITA_KRATKA_SLOVA = {
    # i kratší slova, ale důležitá pro porozumění textu 4. třídy (Věnečky)
    "rum": "alkohol, který dává zákusku typickou vůni.",
    "pudink": "krém z mléka a škrobu, hustý sladký krém.",
    "šlehačka": "našlehaná smetana, bílý nadýchaný krém.",
    "korpus": "spodní část zákusku, těsto.",
    "kvalita": "jak dobré něco je.",
    "cena": "kolik to stojí.",
    "hodnocení": "jak někdo říká, jestli je to dobré nebo špatné.",
    "porota": "lidé, kteří hodnotí a rozhodují, co je lepší."
}


def vyber_slovicka(text: str, max_slov: int = 14):
    """
    1. Najdeme slova 6+ znaků (dřív to bylo 8+).
    2. Přidáme i důležitá krátká odborná slova (rum, pudink...).
    3. Vrátíme unikáty v pořadí výskytu.
    """
    slova = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)

    kandidati = []
    for s in slova:
        ciste = s.strip(",.()!?;:„“\"").lower()
        if not ciste:
            continue
        # 6+ znaků -> bereme
        if len(ciste) >= 6:
            kandidati.append(ciste)
        # pokud je to ve slovníku krátkých důležitých slov, bereme taky
        elif ciste in DULEZITA_KRATKA_SLOVA:
            kandidati.append(ciste)

    unik = []
    for s in kandidati:
        if s not in unik:
            unik.append(s)

    return unik[:max_slov]


def fallback_vysvetleni(slovo_lower: str, trida: int) -> str:
    """
    Pokud slovo není v našich slovnících, vrátíme smysluplné,
    ale pořád jednoduché vysvětlení podle ročníku.
    Tohle řeší, že nechceme prázdné 'vysvětlíme si'.
    """
    if trida == 3:
        return "slovo z pravidel hry / vysvětlení dá učitel na příkladu."
    elif trida == 4:
        return "slovo z hodnocení jídla (chuť, kvalita, vzhled). Učitel ukáže na příkladu."
    else:  # 5. třída
        return "slovo z textu o zdraví / jídle / těle. Učitel vysvětlí s příkladem."


def vysvetli_slovo(slovo_lower: str, trida: int) -> str:
    """
    1. Zkus velký slovník (SLOVNIK_VYRAZU) - podle začátku slova.
    2. Zkus krátká důležitá slova (DULEZITA_KRATKA_SLOVA) - přesný match.
    3. Fallback.
    """
    # začátek slova podle hlavního slovníku
    for klic, vyznam in SLOVNIK_VYRAZU.items():
        if slovo_lower.startswith(klic):
            return vyznam

    # přesný match v krátkých důležitých slovech
    if slovo_lower in DULEZITA_KRATKA_SLOVA:
        return DULEZITA_KRATKA_SLOVA[slovo_lower]

    # fallback
    return fallback_vysvetleni(slovo_lower, trida)


def priprav_slovnicek(text: str, trida: int, max_slov: int = 14):
    slova = vyber_slovicka(text, max_slov=max_slov)
    vystup = []
    for slovo in slova:
        popis = vysvetli_slovo(slovo, trida)
        vystup.append((slovo, popis))
    return vystup


# =========================
#  3. Podpůrná verze textu (LMP/SPU)
# =========================

def zkrat_vetu(veta: str, limit_slov: int = 15):
    slova = veta.strip().split()
    if not slova:
        return ""
    omezena = slova[:limit_slov]
    kratsi = " ".join(omezena).strip(",;: ")
    return kratsi


def priprav_text_LMP(puvodni_text: str):
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

    if trida == 4:
        ot_A = [
            "1) Který věneček byl hodnocen jako nejlepší? (napiš číslo věnečku)",
            "2) Který věneček byl nejdražší a kolik stál?",
            "3) Které tvrzení NENÍ pravda podle textu?\n"
            "   A) V textu se porovnává kvalita různých zákusků.\n"
            "   B) Hodnotitelka vysvětluje, co je dobré a co je špatné.\n"
            "   C) Text dává úplný domácí recept krok za krokem."
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
            "Umím říct svůj názor a proč. 😃 / 🙂 / 😐"
        ]
        return ot_A, ot_B, ot_C, self_eval

    # 5. třída
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


def priprav_otazky_LMP(trida: int):
    """
    Jednodušší sada otázek pro LMP/SPU.
    Vezmeme jen lehčí otázky z části A a jednu názorovou.
    """
    if trida == 3:
        ot_easy = [
            "1) Jak vyhraješ hru? (zakroužkuj)\n"
            "   A) Nasbírám co nejvíc karet.\n"
            "   B) Zbavím se všech karet jako první.",
            "2) Co znamená 'pass'?"
        ]
        ot_nazor = [
            "3) Líbila by se ti ta hra? Ano / Ne. Proč?"
        ]
    elif trida == 4:
        ot_easy = [
            "1) Který věneček byl nejlepší? (napiš číslo)",
            "2) Proč byl nějaký krém špatný?"
        ]
        ot_nazor = [
            "3) Chtěl/a bys ten ‚nejlepší‘ věneček ochutnat?"
        ]
    else:
        ot_easy = [
            "1) O čem byl text? (označ)\n"
            "   A) O sladkostech a zdraví.\n"
            "   B) O historii zmrzliny.",
            "2) Co znamená ‚nízkokalorické‘?"
        ]
        ot_nazor = [
            "3) Myslíš, že je dobré hlídat, kolik sladkostí jím? Proč?"
        ]

    return ot_easy, ot_nazor


# =========================
#  5. Vytvoření Word dokumentů
# =========================

def nastav_docx_font(doc):
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
    doc = Document()
    nastav_docx_font(doc)

    p = doc.add_paragraph(f"{trida}. třída · Pracovní list (EdRead AI)")
    p.runs[0].bold = True
    doc.add_paragraph("Jméno: ______________________    Třída: ________    Datum: __________")
    doc.add_paragraph("")

    p = doc.add_paragraph("🎭 Úvodní scénka (zahájení hodiny)")
    p.runs[0].bold = True
    doc.add_paragraph("Zahrajte si krátkou scénku. Cíl: naladit se na text.")
    for replika in dramatizace:
        doc.add_paragraph("• " + replika)
    doc.add_paragraph("")

    p = doc.add_paragraph("📖 O čem je text")
    p.runs[0].bold = True
    doc.add_paragraph(uvod_txt)
    doc.add_paragraph("")

    p = doc.add_paragraph("📘 Text pro čtení (běžná verze)")
    p.runs[0].bold = True
    for odst in puvodni_text.split("\n"):
        if odst.strip():
            doc.add_paragraph(odst.strip())
    doc.add_paragraph("")

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

    if slovnicek:
        p = doc.add_paragraph("📚 Slovníček pojmů")
        p.runs[0].bold = True
        doc.add_paragraph(
            "Tato slova můžou být náročnější. Pomůže ti vysvětlení hned vedle."
        )
        for slovo, vyznam in slovnicek:
            doc.add_paragraph(f"• {slovo} = {vyznam}")
        doc.add_paragraph("")

    p = doc.add_paragraph("🧠 OTÁZKY A – Porozumění textu")
    p.runs[0].bold = True
    for q in otA:
        doc.add_paragraph(q)
        doc.add_paragraph("Odpověď: ______________________________________")
        doc.add_paragraph("")

    p = doc.add_paragraph("💭 OTÁZKY B – Vysvětluji a zdůvodňuji")
    p.runs[0].bold = True
    for q in otB:
        doc.add_paragraph(q)
        doc.add_paragraph("Odpověď: ______________________________________")
        doc.add_paragraph("")

    p = doc.add_paragraph("🌟 OTÁZKY C – Můj názor")
    p.runs[0].bold = True
    for q in otC:
        doc.add_paragraph(q)
        doc.add_paragraph("Odpověď: ______________________________________")
        doc.add_paragraph("")

    p = doc.add_paragraph("📝 Sebehodnocení žáka")
    p.runs[0].bold = True
    for r in self_eval:
        doc.add_paragraph(r)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


def docx_zaci_LMP(
    trida: int,
    lmp_odstavce,
    slovnicek,
    ot_easy,
    ot_nazor
):
    """
    Speciálně zjednodušená verze pro žáky s LMP / SPU.
    Kratší text, méně otázek, jasné zadání.
    """
    doc = Document()
    nastav_docx_font(doc)

    p = doc.add_paragraph(f"{trida}. třída · Podpůrný list (LMP / SPU) · EdRead AI")
    p.runs[0].bold = True
    doc.add_paragraph("Jméno: ____________________     Datum: __________")
    doc.add_paragraph("")

    p = doc.add_paragraph("🟦 Zjednodušený text")
    p.runs[0].bold = True
    doc.add_paragraph("Toto je kratší verze textu. Věty jsou jednodušší.")
    for odst in lmp_odstavce:
        if odst.strip():
            doc.add_paragraph(odst.strip())
    doc.add_paragraph("")

    if slovnicek:
        p = doc.add_paragraph("📚 Slovníček slov")
        p.runs[0].bold = True
        for slovo, vyznam in slovnicek:
            doc.add_paragraph(f"• {slovo} = {vyznam}")
        doc.add_paragraph("")

    p = doc.add_paragraph("🧠 OTÁZKY – Porozumění textu")
    p.runs[0].bold = True
    for q in ot_easy:
        doc.add_paragraph(q)
        doc.add_paragraph("Odpověď: _______________________________")
        doc.add_paragraph("")

    p = doc.add_paragraph("🌟 Můj názor")
    p.runs[0].bold = True
    for q in ot_nazor:
        doc.add_paragraph(q)
        doc.add_paragraph("Odpověď: _______________________________")
        doc.add_paragraph("")

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


def docx_ucitel(
    trida: int,
    dramatizace,
    uvod_txt: str,
    otA, otB, otC,
    self_eval
):
    doc = Document()
    nastav_docx_font(doc)

    p = doc.add_paragraph("📘 METODICKÝ LIST PRO UČITELE")
    p.runs[0].bold = True
    doc.add_paragraph(f"Ročník: {trida}. třída")
    doc.add_paragraph("")

    doc.add_paragraph("Téma hodiny:")
    if trida == 3:
        doc.add_paragraph(
            "Porozumění návodu / pravidlům hry. Pochopení kroků, kdo je silnější a jak vyhrát."
        )
    elif trida == 4:
        doc.add_paragraph(
            "Porozumění hodnoticímu textu o kvalitě zákusku. Rozlišování faktu a názoru."
        )
    else:
        doc.add_paragraph(
            "Porozumění publicistickému textu o sladkostech a zdraví. "
            "Práce s informací a argumentací."
        )
    doc.add_paragraph("")

    doc.add_paragraph("Cíle hodiny (pro žáka):")
    doc.add_paragraph("1. Žák rozumí hlavnímu sdělení textu.")
    doc.add_paragraph("2. Žák vyhledá konkrétní informaci v textu.")
    doc.add_paragraph("3. Žák rozlišuje FAKT vs. NÁZOR (4.–5. třída).")
    doc.add_paragraph("4. Žák formuluje svůj názor a zdůvodní ho v krátké větě.")
    doc.add_paragraph("5. Žák reflektuje své porozumění (sebehodnocení).")
    doc.add_paragraph("")

    p = doc.add_paragraph("Vazba na RVP ZV (Český jazyk a literatura – čtenářská gramotnost)")
    p.runs[0].bold = True
    doc.add_paragraph("• Žák čte s porozuměním text přiměřený věku.")
    doc.add_paragraph("• Žák vyhledává a třídí základní informace v textu.")
    doc.add_paragraph("• Žák rozlišuje mezi faktickým sdělením a názorem / hodnocením.")
    doc.add_paragraph("• Žák vyjadřuje jednoduché hodnocení textu nebo situace a svůj postoj zdůvodní.")
    doc.add_paragraph("• Žák reflektuje vlastní chápání textu (sebehodnocení).")
    doc.add_paragraph("")

    doc.add_paragraph("Doporučený průběh hodiny (45 min):")
    doc.add_paragraph("1) MOTIVACE / DRAMATIZACE (cca 5 min)")
    doc.add_paragraph("   - krátká scénka, žák se vtáhne do situace.")
    doc.add_paragraph("2) ČTENÍ TEXTU (cca 10–15 min)")
    doc.add_paragraph("   - společné nebo samostatné čtení původního textu.")
    doc.add_paragraph("   - žáci s LMP/SPU čtou zjednodušenou verzi (kratší věty).")
    doc.add_paragraph("   - vysvětlení slov podle slovníčku.")
    doc.add_paragraph("3) PRÁCE S OTÁZKAMI (cca 15 min)")
    doc.add_paragraph("   - A: porozumění textu.")
    doc.add_paragraph("   - B: vysvětlení pojmů / proč si to někdo myslí.")
    doc.add_paragraph("   - C: názor žáka + zdůvodnění.")
    doc.add_paragraph("4) SEBEHODNOCENÍ (cca 5 min)")
    doc.add_paragraph("   - výběr smajlíka 😃 🙂 😐 a krátké vysvětlení proč.")
    doc.add_paragraph("")

    doc.add_paragraph("Diferenciace (LMP / SPU):")
    doc.add_paragraph("• Žák dostane samostatný podpůrný list (zjednodušené věty).")
    doc.add_paragraph("• Pro něj použij jen lehčí otázky (A + jednoduchý názor).")
    doc.add_paragraph("• Menší objem psaní: kratší odpovědi, větší linka.")
    doc.add_paragraph("")

    doc.add_paragraph("Dramatizace (zahájení hodiny):")
    for r in dramatizace:
        doc.add_paragraph("• " + r)
    doc.add_paragraph("")

    doc.add_paragraph("Jak jednoduše vysvětlit dětem, o čem text je:")
    doc.add_paragraph(uvod_txt)
    doc.add_paragraph("")

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

    doc.add_paragraph(
        "Poznámka pro diplomovou práci: Nástroj EdRead AI pro daný text automaticky "
        "vytvořil diferenciované zadání (běžná verze + podpůrná LMP/SPU), "
        "slovníček náročných slov s dětským vysvětlením, otázky A/B/C podle úrovní čtenářské gramotnosti "
        "a přímou vazbu na RVP ZV."
    )

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


# =========================
#  6. Streamlit aplikace
# =========================

st.set_page_config(
    page_title="EdRead AI – generátor pracovních listů (verze 6)",
    layout="centered"
)

st.title("EdRead AI – generátor pracovních listů (verze 6)")
st.write("Výsledky:")
st.write("• Pracovní list pro žáky (.docx)")
st.write("• Podpůrný list LMP / SPU (.docx)")
st.write("• Metodický list pro učitele (.docx)")
st.write("Vše s vazbou na RVP ZV, se slovníčkem a s diferenciací.")

st.markdown("### 1) Vlož text pro žáky")
puvodni_text = st.text_area(
    "Sem vlož výchozí text (např. Karetní hra / Věnečky / Sladké mámení).",
    height=400
)

st.markdown("### 2) Vyber ročník")
trida_volba = st.selectbox("Ročník:", ["3", "4", "5"])


if "soubor_zaci" not in st.session_state:
    st.session_state["soubor_zaci"] = None
if "soubor_zaci_LMP" not in st.session_state:
    st.session_state["soubor_zaci_LMP"] = None
if "soubor_ucitel" not in st.session_state:
    st.session_state["soubor_ucitel"] = None
if "fname_students" not in st.session_state:
    st.session_state["fname_students"] = ""
if "fname_students_LMP" not in st.session_state:
    st.session_state["fname_students_LMP"] = ""
if "fname_teacher" not in st.session_state:
    st.session_state["fname_teacher"] = ""


if st.button("Vygenerovat Word dokumenty"):
    if not puvodni_text.strip():
        st.error("Musíš vložit text.")
    else:
        trida = detekuj_tridu(trida_volba)

        # obsah
        dramatizace = priprav_dramatizaci(trida)
        uvod_txt = priprav_uvod_pro_zaka(trida)
        lmp_verze = priprav_text_LMP(puvodni_text)
        slovnicek = priprav_slovnicek(puvodni_text, trida, max_slov=14)
        otA, otB, otC, self_eval = priprav_otazky(trida)
        ot_easy, ot_nazor = priprav_otazky_LMP(trida)

        # dokument pro běžné žáky
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

        # dokument pro LMP / SPU
        soubor_zaci_LMP = docx_zaci_LMP(
            trida,
            lmp_verze,
            slovnicek,
            ot_easy,
            ot_nazor
        )

        # metodický list
        soubor_ucitel = docx_ucitel(
            trida,
            dramatizace,
            uvod_txt,
            otA, otB, otC,
            self_eval
        )

        today = datetime.date.today().isoformat()

        st.session_state["soubor_zaci"] = soubor_zaci
        st.session_state["soubor_zaci_LMP"] = soubor_zaci_LMP
        st.session_state["soubor_ucitel"] = soubor_ucitel

        st.session_state["fname_students"] = f"EdReadAI_zaci_{trida}trida_{today}.docx"
        st.session_state["fname_students_LMP"] = f"EdReadAI_LMP_{trida}trida_{today}.docx"
        st.session_state["fname_teacher"] = f"EdReadAI_ucitel_{trida}trida_{today}.docx"

        st.success("Dokumenty jsou připravené níže. Teď můžeš stahovat každé tlačítko zvlášť, bez ztráty ostatních.")


# --- tlačítka ke stažení (fungují i po kliknutí na jedno z nich) ---
if st.session_state["soubor_zaci"]:
    st.download_button(
        label="📥 Stáhnout pracovní list pro žáky (.docx)",
        data=st.session_state["soubor_zaci"],
        file_name=st.session_state["fname_students"],
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if st.session_state["soubor_zaci_LMP"]:
    st.download_button(
        label="🟦 Stáhnout podpůrný list LMP / SPU (.docx)",
        data=st.session_state["soubor_zaci_LMP"],
        file_name=st.session_state["fname_students_LMP"],
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if st.session_state["soubor_ucitel"]:
    st.download_button(
        label="📘 Stáhnout metodický list pro učitele (.docx)",
        data=st.session_state["soubor_ucitel"],
        file_name=st.session_state["fname_teacher"],
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
