import streamlit as st
from docx import Document
from docx.shared import Pt
from io import BytesIO
import re
import datetime

# ============================================================
# 1) PŘEDNASTAVENÉ TEXTY PRO JEDNOTLIVÉ ROČNÍKY
# ============================================================

TEXTY = {
    "Karetní hra (3. třída)": {
        "trida": "3. třída",
        "text_puvodni": """NÁZEV ÚLOHY: KARETNÍ HRA

1. Herní materiál
60 karet živočichů: 4 komáři, 1 chameleon (žolík), 5 karet od každého z dalších 11 druhů živočichů

2. Popis hry
Všechny karty se rozdají mezi jednotlivé hráče. Hráči se snaží vynášet karty v souladu s pravidly tak, aby se co nejdříve zbavili všech svých karet z ruky. Zahrát lze vždy pouze silnější kombinaci živočichů, než zahrál hráč před vámi.

3. Pořadí karet
Na každé kartě je zobrazen jeden živočich. V rámečku v horní části karty jsou namalováni živočichové, kteří danou kartu přebíjí.

Příklad:
– Kosatku přebijí pouze dvě kosatky.
– Krokodýla přebijí dva krokodýli nebo jeden slon.
– Chameleon funguje jako žolík. Nelze ho hrát samostatně, ale může doplnit jinou kartu.

4. Průběh hry
• Karty zamíchejte a rozdejte rovnoměrně mezi všechny hráče. Každý hráč má karty v ruce a neukazuje je ostatním.
• Hráč po levé ruce rozdávajícího začíná. Položí na stůl jednu kartu nebo více stejných karet.
• Další hráči se snaží „přebít“ – buď položí stejný počet silnějších zvířat, nebo položí tentýž druh zvířete, ale o jednu kartu víc.
• Hráč, který nechce nebo nemůže přebít, řekne „pass“ a toto kolo přeskočí.
• Pokud nikdo nepřebije, hráč, který měl poslední platný tah, si vezme karty ze středu stolu na hromádku bokem (ty už se dál nepoužívají) a začne nové kolo.
• Vyhrává ten, kdo se první zbaví všech karet v ruce.
""",
        "text_zjednoduseny": """KARETNÍ HRA – zjednodušený text

V balíčku je 60 karet se zvířaty. Každý hráč dostane svoje karty.
Cíl hry: Být první, kdo nemá žádné karty v ruce.

Jak se hraje:
1. Jeden hráč vyloží kartu nebo více stejných karet (např. dvě myši).
2. Další hráč se snaží tyto karty „přebít“.
   - Přebít znamená dát silnější zvíře.
   - Nebo dát stejné zvíře, ale o jednu kartu víc (např. tři myši proti dvěma myším).
3. Kdo nemůže, řekne „pass“ a vynechá.
4. Když už nikdo nedokáže přebít, vezme si poslední hráč karty ze stolu bokem a začne nové kolo.
5. Kdo první nemá karty, vyhrál.

Pozor:
– Chameleon je speciální karta (žolík). Sám hrát nesmí. Pomáhá jiné kartě.
– Některá zvířata jsou „silnější“ než jiná. Silnější může přebít slabší.

Tohle je hra na přemýšlení a plánování 🙂.
""",
        "text_LMP": """KARETNÍ HRA – snadné vysvětlení

V balíčku jsou karty se zvířaty.
Každý hráč má svoje karty.

Cíl hry: Nemít žádné karty.

Jak hra probíhá:
1. První hráč dá kartu na stůl.
2. Další hráč musí dát silnější zvíře.
3. Když nemá silnější zvíře, řekne „pass“ (vynechám).
4. Vyhrává ten, kdo už nemá žádné karty.

Důležité:
– Některá zvířata jsou silná (např. lev).
– Některá zvířata jsou slabá (např. myš).
– Chameleon je speciální karta. Pomůže ti, ale nesmí být na stole úplně sám.
""",
        "dramatizace": """DRAMATIZACE (motivační scénka na začátek hodiny)

Tereza: „Hele, já mám pravidla té hry, ale moc tomu nerozumím.“
Daniel: „Já taky ne. Co znamená, že ‚lev přebije tuleně‘?“
Učitelka: „Dobře, pojďme si to zahrát naživo. Ty budeš lev. Ty budeš tuleň. Kdo vyhraje?“
(Děti se zasmějí, zkusí „souboj“ zvířat.)
Učitelka: „A přesně takhle to funguje v té karetní hře. Teď si přečteme pravidla a zjistíme proč.“""",
        "otazky_A": [
            "1) Jaký je cíl hry?",
            "2) Co znamená, když hráč řekne 'pass'?",
            "3) Kdy hra končí?"
        ],
        "otazky_B": [
            "4) Proč je chameleon speciální karta?",
            "5) Vysvětli, co znamená 'přebít kartu'."
        ],
        "otazky_C": [
            "6) Co by ti v téhle hře šlo nejvíc? Plánování? Paměť? Nebo rychlé rozhodnutí? Proč?"
        ],
        "slovnik_doplnkova_vysvetleni": {
            "přebít": "dát lepší / silnější kartu",
            "kombinace": "více karet, které dáváš najednou",
            "chameleon": "speciální karta, která může být jako jiné zvíře",
            "žolík": "karta, která nahrazuje jinou kartu",
            "pravidla": "to, jak se má správně hrát",
            "kolo": "část hry od začátku do chvíle, než nikdo další nepřehraje",
            "přeskočí": "vynechá svůj tah"
        },
        "rvp_vystupy": [
            "Žák rozumí krátkému návodu a dokáže podle něj jednat.",
            "Žák vyhledává konkrétní informaci v textu.",
            "Žák odpovídá celou větou a používá slova z textu."
        ]
    },

    "Věnečky (4. třída)": {
        "trida": "4. třída",
        "text_puvodni": """(původní text Věnečky ... z časopisu Týden atd.)""",
        "text_zjednoduseny": """(zkrácená verze pro 4. třídu – popis ochutnávání věnečků, co je dobré/špatné, kdo vyhrál, proč)""",
        "text_LMP": """(ještě jednodušší jazyk pro žáky s potřebou podpory – kratší věty, vysvětlena slova jako 'pudink', 'korpus', 'šlehačka')""",
        "dramatizace": """(scénka: 'Já chci nejlepší dort!' 'Jak poznáš, který je nejlepší?' -> 'Musíme ochutnat a porovnávat podle pravidel.')""",
        "otazky_A": [
            "1) Který věneček dopadl nejlépe?",
            "2) Proč byl jeden věneček kritizovaný?"
        ],
        "otazky_B": [
            "3) Jak cukrářka pozná, že krém je špatný?",
            "4) Co znamená, že těsto bylo 'ztvrdlé'?"
        ],
        "otazky_C": [
            "5) Co by pro tebe znamenalo 'dobrý zákusek'? Popiš."
        ],
        "slovnik_doplnkova_vysvetleni": {
            "pudink": "nasládlý krém (vaří se z mléka a prášku)",
            "korpus": "spodek / tělo zákusku z těsta",
            "margarín": "levnější tuk podobný máslu",
            "sražený": "špatně vyšlehaný, hrudkovatý",
            "receptura": "přesný postup a suroviny",
            "přepečená": "peklo se to moc dlouho, je to moc tvrdé",
            "štrúdl": "závin s náplní (třeba jablka)"
        },
        "rvp_vystupy": [
            "Žák porozumí popisnému / hodnotícímu textu.",
            "Žák vyhledává údaje v souvislém textu i v tabulce.",
            "Žák rozlišuje fakt (co se dá ověřit) a názor (osobní hodnocení)."
        ]
    },

    "Sladké mámení (5. třída)": {
        "trida": "5. třída",
        "text_puvodni": """(původní text o čokoládě, poptávce po nízkokalorických sladkostech, průzkumu Median atd.)""",
        "text_zjednoduseny": """(zjednodušený přehled pro 5. třídu – proč lidi řeší kalorie, co říkají čísla v tabulkách, jak často lidé jedí čokoládu)""",
        "text_LMP": """(verze pro LMP: kratší věty, vysvětlení 'nízkokalorický = málo kalorií', 'průzkum = ptali se lidí')""",
        "dramatizace": """DRAMATIZACE (úvod do hodiny)

Žák A: „Mám rád čokoládu. Ale máma říká, že je to samý cukr.“
Žák B: „A prodávají i takovou, co není tak sladká. Prý 'light'.”
Učitel: „Právě o tom budeme číst. Jak moc lidi jedí sladkosti a proč to řeší doktoři.”""",
        "otazky_A": [
            "1) Co je hlavní problém, o kterém text mluví?",
            "2) Co znamená 'nízkokalorická sladkost'?"
        ],
        "otazky_B": [
            "3) Proč některé firmy dělají 'light' sladkosti?",
            "4) Co dělali lidé v průzkumu? (Co dělala agentura Median?)"
        ],
        "otazky_C": [
            "5) Jaký máš ty vztah ke sladkému? Je to pro tebe odměna, energie, nebo zvyk?"
        ],
        "slovnik_doplnkova_vysvetleni": {
            "nízkokalorický": "málo kalorií = 'není tak výkrmné'",
            "průzkum": "ptali se hodně lidí a zapisovali odpovědi",
            "obezita": "když má tělo příliš mnoho tuku, ohrožuje to zdraví",
            "kalorie": "energie z jídla",
            "sladidlo": "něco, co dává sladkou chuť místo cukru",
            "spotřebitel": "člověk, který si něco kupuje a jí / používá",
            "energetická hodnota": "kolik energie z toho tělo dostane"
        },
        "rvp_vystupy": [
            "Žák umí číst publicistický text a vybrat hlavní sdělení.",
            "Žák umí použít údaje z grafu/tabulky do odpovědi.",
            "Žák formuluje svůj názor a odůvodní ho."
        ]
    }
}


# ============================================================
# 2) FUNKCE PRO AUTOMATICKÝ SLOVNÍČEK
#    - vybere kandidáty
#    - dá k nim jednoduché vysvětlení, pokud máme
#    - jinak nechá prázdnou linku
# ============================================================

def navrhni_slovicka(text, doplnkova_vysvetleni, max_slov=10):
    """
    1. vytáhne delší slova (8+ znaků) jako možná náročná
    2. odstraní duplicity
    3. vrátí do listu max_slov položek
    """
    slova = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    kandidati = []
    for s in slova:
        s_clean = s.strip().lower()
        if len(s_clean) >= 8 and s_clean not in kandidati:
            kandidati.append(s_clean)
    # doplníme i kratší důležitá slova z doplnkova_vysvetleni,
    # aby se určitě dostala dovnitř
    for k in doplnkova_vysvetleni.keys():
        if k not in kandidati:
            kandidati.append(k)

    return kandidati[:max_slov]


def vytvor_slovnicek(blist, doplnkova_vysvetleni):
    """
    Dostane list slov a slovník s vysvětleními.
    Vrátí list řádků typu:
    • slovo = vysvětlení
      (pokud vysvětlení není známé, nechá jen linku ________)
    """
    vystup = []
    for slovo in blist:
        if slovo in doplnkova_vysvetleni:
            radek = f"• {slovo} = {doplnkova_vysvetleni[slovo]}"
        else:
            radek = f"• {slovo} = _______________________________"
        vystup.append(radek)
    return vystup


# ============================================================
# 3) PYRAMIDA SÍLY PRO 3. TŘÍDU (KARETNÍ HRA)
# ============================================================

def vytvor_pyramidu_sily():
    """
    Vrací textovou 'pyramidu síly' zvířat z karetní hry.
    Je to vizuální opora pro žáky 3. třídy.
    (Příkladová hierarchie podle popisu pravidel:
     - silnější zvíře může přebít slabší,
     - myš je hodně slabá, kosatka hodně silná,
     - chameleon je speciální – může být jako jiné zvíře.)
    """
    pyramid_text = (
        "OBRÁZKOVÁ OPORA – PYRAMIDA SÍLY ZVÍŘAT\n"
        "(Kdo může přebít koho ve hře)\n\n"
        "   🦈 KOSATKA\n"
        "        ↓ přebije\n"
        "    🐘 SLON\n"
        "        ↓ přebije\n"
        "    🐊 KROKODÝL\n"
        "        ↓ přebije\n"
        "    🦁 LEV\n"
        "        ↓ přebije\n"
        "    🐻 LEDNÍ MEDVĚD / 🦭 TULEŇ\n"
        "        ↓ přebije\n"
        "    🐭 MYŠ\n\n"
        "CHAMELEON = ŽOLÍK\n"
        "• Chameleon se může tvářit jako jiné zvíře.\n"
        "• Sám hrát nesmí.\n\n"
        "Jak to čtu:\n"
        "Když chci přebít slabší zvíře, musím dát silnější zvíře.\n"
        "Nebo dám stejné zvíře, ale o jednu kartu navíc.\n"
    )
    return pyramid_text


# ============================================================
# 4) GENEROVÁNÍ DOKUMENTŮ WORD (pracovní list, metodika, LMP)
# ============================================================

def nastav_styl(document):
    """Základní čitelný font pro celý dokument."""
    style = document.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(12)


def pridej_nadpis(document, text, velikost=16, bold=True):
    p = document.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(velikost)
    return p


def pridej_text(document, text, velikost=12, bold=False):
    p = document.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(velikost)
    return p


def vytvor_docx_pracovni_list(data, slovnicek_radky, zahrnout_pyramidu=False):
    """
    Vytvoří DOCX pracovní list pro žáka (běžná třída).
    Obsah:
    1. Dramatizace
    2. Text pro žáky (zjednodušený)
    3. Obrázková opora (pyramida) – pouze 3. třída
    4. Slovníček
    5. Otázky A/B/C
    6. Sebehodnocení
    """
    document = Document()
    nastav_styl(document)

    # Hlavička
    pridej_nadpis(document, f"EdRead AI – pracovní list ({data['trida']})")
    pridej_text(document, f"Datum: {datetime.date.today().strftime('%d.%m.%Y')}")
    pridej_text(document, "Jméno žáka: ____________________________")
    pridej_text(document, "")

    # 1) Dramatizace
    pridej_nadpis(document, "1) Úvodní scénka (dramatizace)", 14)
    pridej_text(document, data["dramatizace"])
    pridej_text(document, "")

    # 2) Text pro žáky
    pridej_nadpis(document, "2) Text pro čtení", 14)
    pridej_text(document, data["text_zjednoduseny"])
    pridej_text(document, "")

    # 3) Obrázková opora (pyramida síly zvířat) – jen pokud chceme
    if zahrnout_pyramidu:
        pridej_nadpis(document, "3) Obrázková opora – pyramida zvířat", 14)
        pridej_text(document, vytvor_pyramidu_sily())
        pridej_text(document, "")

    # 4) Slovníček
    pridej_nadpis(document, "Slovníček", 14)
    for radek in slovnicek_radky:
        pridej_text(document, radek)
    pridej_text(document, "")

    # 5) Otázky A/B/C
    pridej_nadpis(document, "Otázky k textu", 14)

    pridej_text(document, "OTÁZKY A: Najdi v textu odpověď", bold=True)
    for ot in data["otazky_A"]:
        pridej_text(document, ot)

    pridej_text(document, "")
    pridej_text(document, "OTÁZKY B: Vysvětli vlastními slovy", bold=True)
    for ot in data["otazky_B"]:
        pridej_text(document, ot)

    pridej_text(document, "")
    pridej_text(document, "OTÁZKY C: Tvůj názor / přemýšlení", bold=True)
    for ot in data["otazky_C"]:
        pridej_text(document, ot)

    pridej_text(document, "")

    # 6) Sebehodnocení
    pridej_nadpis(document, "Sebehodnocení žáka", 14)
    pridej_text(document, "Rozuměl/a jsem textu:    😃   🙂   😐")
    pridej_text(document, "Našel/našla jsem odpovědi:    😃   🙂   😐")
    pridej_text(document, "Umím to vysvětlit vlastními slovy:    😃   🙂   😐")

    # hotovo -> vrátit bytes
    bytes_io = BytesIO()
    document.save(bytes_io)
    bytes_io.seek(0)
    return bytes_io


def vytvor_docx_LMP(data, slovnicek_radky, zahrnout_pyramidu=False):
    """
    Vytvoří DOCX list pro žáky s potřebou podpory (LMP/SPU).
    Je kratší, jasnější, větší rozsekání informací.
    """
    document = Document()
    nastav_styl(document)

    pridej_nadpis(document, f"EdRead AI – pracovní list (LMP/SPU) – {data['trida']}")
    pridej_text(document, f"Datum: {datetime.date.today().strftime('%d.%m.%Y')}")
    pridej_text(document, "Jméno žáka: ____________________________")
    pridej_text(document, "")

    # Dramatizace (zůstává, protože to je pochopitelné a vtahuje)
    pridej_nadpis(document, "1) Začátek hodiny – scénka", 14)
    pridej_text(document, data["dramatizace"])
    pridej_text(document, "")

    # Text LMP
    pridej_nadpis(document, "2) Text pro čtení – jednodušší verze", 14)
    pridej_text(document, data["text_LMP"])
    pridej_text(document, "")

    # Pyramida pro 3. třídu
    if zahrnout_pyramidu:
        pridej_nadpis(document, "3) Pomůcka k pochopení hry", 14)
        pridej_text(document, vytvor_pyramidu_sily())
        pridej_text(document, "")

    # Slovníček – u LMP je extra důležité
    pridej_nadpis(document, "Slovníček slov", 14)
    for radek in slovnicek_radky:
        pridej_text(document, radek)
    pridej_text(document, "")

    # Méně otázek, víc vedení
    pridej_nadpis(document, "Otázky", 14)
    pridej_text(document, "1) O čem text byl? (Napiš 1 větu.)")
    pridej_text(document, "______________________________________")
    pridej_text(document, "2) Řekni něco, co bylo DOBRÉ.")
    pridej_text(document, "______________________________________")
    pridej_text(document, "3) Řekni něco, co bylo ŠPATNÉ / PROBLÉM.")
    pridej_text(document, "______________________________________")

    pridej_text(document, "")
    pridej_nadpis(document, "Jak jsem to zvládl/a", 14)
    pridej_text(document, "Bylo to pro mě:   😊 snadné   😐 střední   😟 těžké")

    bytes_io = BytesIO()
    document.save(bytes_io)
    bytes_io.seek(0)
    return bytes_io


def vytvor_docx_metodika(data):
    """
    Vytvoří metodický list pro učitele:
    - cíl hodiny
    - vazba na RVP ZV (čtenářská gramotnost)
    - návrh struktury hodiny
    - co sledovat u žáků
    """
    document = Document()
    nastav_styl(document)

    pridej_nadpis(document, "METODICKÝ LIST PRO UČITELE", 16)

    pridej_text(document, f"Ročník: {data['trida']}", bold=True)
    pridej_text(document, f"Datum: {datetime.date.today().strftime('%d.%m.%Y')}")
    pridej_text(document, "")

    # Cíl hodiny
    pridej_nadpis(document, "1) Cíl hodiny", 14)
    pridej_text(document,
        "- Rozvoj čtenářské gramotnosti.\n"
        "- Porozumění textu (co se děje, kdo co říká, jaké jsou pravidla / hodnocení).\n"
        "- Vyhledávání informací v textu.\n"
        "- Rozdíl FAKT vs. NÁZOR.\n"
        "- Vlastní vyjádření (sebehodnocení)."
    )
    pridej_text(document, "")

    # Vazba na RVP
    pridej_nadpis(document, "2) Vazba na RVP ZV (Jazyk a jazyková komunikace)", 14)
    for v in data["rvp_vystupy"]:
        pridej_text(document, f"- {v}")
    pridej_text(document, "")

    # Struktura hodiny
    pridej_nadpis(document, "3) Doporučený průběh hodiny (45 minut)", 14)
    pridej_text(document,
        "a) MOTIVACE / DRAMATIZACE (5–7 min)\n"
        "   - krátká scénka = vstup do tématu\n"
        "   - cílem je aktivovat zkušenost žáků ještě před čtením\n\n"
        "b) ČTENÍ TEXTU (10–15 min)\n"
        "   - čteme upravený text pro daný ročník\n"
        "   - vyjasníme si těžká slova pomocí slovníčku\n"
        "   - u 3. třídy ukážeme pyramidu síly zvířat jako vizuální oporu\n\n"
        "c) PRÁCE S OTÁZKAMI (15 min)\n"
        "   - A = najdi v textu (porozumění)\n"
        "   - B = vysvětli vlastními slovy (vysvětlení významu)\n"
        "   - C = názor / hodnocení (kritické myšlení)\n\n"
        "d) SEBEHODNOCENÍ (5 min)\n"
        "   - žák označí, jak tomu rozuměl a co bylo těžké\n"
        "   - učitel získá okamžitou zpětnou vazbu"
    )
    pridej_text(document, "")

    # Pozorování učitele
    pridej_nadpis(document, "4) Na co se dívat (diagnostika učitele)", 14)
    pridej_text(document,
        "- Kdo dokáže najít odpověď přesně v textu?\n"
        "- Kdo umí převyprávět vlastními slovy?\n"
        "- Kdo zvládá rozlišit fakt vs. názor?\n"
        "- Kdo se ztrácí ve slovníčku nebo nerozumí pojmům?\n"
        "- U žáků s LMP/SPU sleduji spíš pochopení hlavní myšlenky, ne jazykovou přesnost."
    )

    bytes_io = BytesIO()
    document.save(bytes_io)
    bytes_io.seek(0)
    return bytes_io


# ============================================================
# 5) STREAMLIT UI
# ============================================================

st.set_page_config(page_title="EdRead AI – školní prototyp", layout="centered")

st.title("EdRead AI – Generátor pracovních listů")
st.write("Prototyp pro diplomovou práci: čtenářská gramotnost, RVP ZV, diferenciace, LMP/SPU.")

# výběr textu
vyber_text = st.selectbox(
    "Vyber text / ročník:",
    list(TEXTY.keys())
)

data = TEXTY[vyber_text]

st.subheader("Náhled základních parametrů")
st.write(f"Ročník: {data['trida']}")
st.write("Dramatizace (úvod hodiny):")
st.write(data["dramatizace"])

st.write("Zjednodušená verze textu pro žáky:")
st.write(data["text_zjednoduseny"])

st.write("Verze pro žáky s LMP/SPU:")
st.write(data["text_LMP"])

# slovníček – vygenerujeme
kandidati_slov = navrhni_slovicka(
    data["text_puvodni"],
    data["slovnik_doplnkova_vysvetleni"],
    max_slov=10
)
slovnicek_radky = vytvor_slovnicek(
    kandidati_slov,
    data["slovnik_doplnkova_vysvetleni"]
)

st.write("Náhled slovníčku (část):")
for r in slovnicek_radky:
    st.text(r)

# rozhodnutí, jestli má být přidána pyramida
zahrnout_pyramidu = (data["trida"] == "3. třída")

st.markdown("---")

st.subheader("Stáhnout materiály")

# pracovní list běžná verze
docx_bytes_pracovni = vytvor_docx_pracovni_list(
    data,
    slovnicek_radky,
    zahrnout_pyramidu=zahrnout_pyramidu
)
st.download_button(
    label="📄 Stáhnout pracovní list (běžná verze)",
    data=docx_bytes_pracovni,
    file_name=f"pracovni_list_{data['trida'].replace(' ', '')}_{datetime.date.today()}.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

# pracovní list LMP/SPU
docx_bytes_LMP = vytvor_docx_LMP(
    data,
    slovnicek_radky,
    zahrnout_pyramidu=zahrnout_pyramidu
)
st.download_button(
    label="📄 Stáhnout pracovní list – LMP / SPU",
    data=docx_bytes_LMP,
    file_name=f"pracovni_list_LMP_{data['trida'].replace(' ', '')}_{datetime.date.today()}.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

# metodika
docx_bytes_metodika = vytvor_docx_metodika(data)
st.download_button(
    label="📘 Stáhnout metodický list pro učitele",
    data=docx_bytes_metodika,
    file_name=f"metodika_{data['trida'].replace(' ', '')}_{datetime.date.today()}.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

st.markdown("---")
st.caption("EdRead AI – prototyp určený pro diplomovou práci. Všechny texty vycházejí z platného RVP ZV.")
