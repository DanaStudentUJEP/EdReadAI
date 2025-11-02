import streamlit as st
import re
import textwrap

# -------------------------------------------------
# 1. Pomocné funkce
# -------------------------------------------------

def rozdel_na_vety(text):
    """
    Hrubé rozdělení textu na věty podle . ? !
    Používáme to k tvorbě otázek.
    """
    kandidati = re.split(r'(?<=[\.\?\!])\s+', text.strip())
    vety = [v.strip() for v in kandidati if len(v.strip()) > 0]
    return vety

def vyber_slovicka(text, max_slov=10):
    """
    Vybere možná 'těžší' slova do slovníčku.
    - Delší výrazy (8+ znaků),
    - jen písmena (žádná čísla),
    - bez duplicit.
    """
    slova = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    slova_cista = [s.strip().lower() for s in slova if len(s) >= 8]
    unik = []
    for s in slova_cista:
        if s not in unik:
            unik.append(s)
    return unik[:max_slov]

def jemne_vysvetleni_pro_ucitele(slovo):
    """
    Snaha nabídnout učiteli náznak významu u vybraných slov.
    Pokud slovo neznáme, necháme prázdné.
    Tohle je jen pomůcka pro učitele (v závorkách 'pro učitele'),
    dětem se nechá prázdná linka k doplnění.
    """
    slovnik_ucitel = {
        "margarín": "tuk podobný máslu",
        "pudink": "krém z mléka a škrobu / prášku",
        "receptura": "přesný postup a suroviny",
        "sražený": "špatně vyšlehaný, hrudkovitý",
        "chemickou": "umělou, ne přírodní",
        "korpus": "spodní těsto dortu nebo zákusku",
        "recept": "návod, jak co vyrobit",
        "hodnotitelka": "ta, co hodnotí / posuzuje kvalitu",
        "přepečená": "moc dlouho pečená",
        "zestárlá": "už není čerstvá",
        "průmyslově": "vyrobené ve velké továrně, ne doma",
        "pasáž": "průchod / ulička v domě s obchody",
        "porota": "skupina lidí, která hodnotí",
        "kvalitní": "dobré, poctivé"
    }
    if slovo in slovnik_ucitel:
        return slovnik_ucitel[slovo]
    else:
        return ""

def vytvor_slovnicek_blok(text):
    """
    Vrátí hotový blok slovníčku pro žáky.
    Formát:
    - slovo:
      Co to znamená: __________
    (a do závorky pro učitele dáme jemnou nápovědu, pokud ji známe)
    """
    slova = vyber_slovicka(text, max_slov=10)

    if not slova:
        return (
            "SLOVNÍČEK POJMŮ\n"
            "(V tomto textu nebyla nalezena delší / méně obvyklá slova.\n"
            "Učitel může dopsat ručně.)"
        )

    radky = ["SLOVNÍČEK POJMŮ"]
    for s in slova:
        hint = jemne_vysvetleni_pro_ucitele(s)
        if hint:
            radky.append(
                f"- {s}\n  Co to znamená (doplň vlastními slovy): ___________________\n"
                f"  (pro učitele: {hint})"
            )
        else:
            radky.append(
                f"- {s}\n  Co to znamená (doplň vlastními slovy): ___________________"
            )
    return "\n".join(radky)


def dramatizace_pro_rocnik(rocnik):
    """
    Krátká motivační dramatizace NA ZAČÁTEK hodiny.
    Přizpůsobeno věku.
    """
    if rocnik == "3. třída":
        return textwrap.dedent("""
        DRAMATIZACE (zahájení hodiny)
        Anička: „Hele, já mám pravidla té nové hry a vůbec jim nerozumím!“
        Marek: „Ukaž. Tady se píše, kdo přebíjí koho. To je jako kdo je silnější.“
        Učitelka: „Tak to zkusíme zahrát nanečisto. Každý bude jedno zvíře a uvidíme, kdo koho porazí.“
        → Cíl: děti si vyzkouší situaci z textu naživo, ještě než ho budou číst.
        """).strip()

    if rocnik == "4. třída":
        return textwrap.dedent("""
        DRAMATIZACE (zahájení hodiny)
        Učitelka: „Dneska jste porota jako v televizní soutěži cukrářů.“
        Eliška: „Já hodnotím, jak to vypadá.“
        Tomáš: „Já hodnotím chuť a vůni.“
        Natálie: „A já hlídám, jestli cukrář nešidí suroviny.“
        Učitelka: „Přesně takhle hodnotí i cukrářka v našem textu.“
        → Cíl: děti chápou, proč se v textu mluví o kvalitě věnečků.
        """).strip()

    if rocnik == "5. třída":
        return textwrap.dedent("""
        DRAMATIZACE (zahájení hodiny)
        Adam: „Mně chutná čokoláda, i kdyby měla milion kalorií.“
        Bára: „Já si radši vybírám sladkosti, co nejsou tak nezdravé.“
        Učitelka: „Tohle řeší i dospělí: chuť vs. zdraví. A o tom je dnešní text.“
        → Cíl: děti si uvědomí téma zdravé / nezdravé mlsání.
        """).strip()

    return "Vyber ročník, aby se zobrazila správná dramatizace."


def vygeneruj_otazky(vety):
    """
    Uděláme univerzální sadu otázek, které fungují pro jakýkoli vložený text.
    - A: porozumění
    - B: přemýšlení o textu
    - C: vlastní názor
    - sebehodnocení
    """

    if len(vety) == 0:
        return "OTÁZKY K TEXTU\n(Nebyl vložen žádný text.)"

    veta1 = vety[0] if len(vety) > 0 else ""
    veta2 = vety[1] if len(vety) > 1 else ""
    # veta3 = vety[2] if len(vety) > 2 else ""  # případně do budoucna

    blok = []

    blok.append("OTÁZKY K TEXTU")

    # Porozumění
    blok.append(
        "\n1) Porozumění textu\n"
        "Co z následujícího NEvyplývá z textu?\n"
        f"A) {veta1}\n"
        f"B) {veta2 if veta2 else 'Druhá důležitá myšlenka z textu.'}\n"
        "C) Tvrzení, které v textu vůbec nebylo.\n"
        "Odpověď: __________"
    )

    # Najdi v textu
    blok.append(
        "\n2) Najdi v textu\n"
        "Najdi část textu, kde se říká, kdo / co bylo nejlepší nebo nejhorší.\n"
        "Opíš tu větu:\n"
        "____________________________________________________________"
    )

    # Vysvětli
    blok.append(
        "\n3) Vysvětli vlastními slovy\n"
        "Proč si někdo v textu myslí, že jedna věc/byla lepší než ostatní?\n"
        "____________________________________________________________\n"
        "____________________________________________________________"
    )

    # Fakt vs. názor
    blok.append(
        "\n4) NÁZOR × FAKT\n"
        "Najdi v textu:\n"
        "• jednu větu, která je NÁZOR (co si někdo myslí),\n"
        "• jednu větu, která je FAKT (dá se ověřit).\n"
        "NÁZOR: _____________________________________________\n"
        "FAKT:  _____________________________________________"
    )

    # Můj názor
    blok.append(
        "\n5) Můj názor\n"
        "Souhlasíš s tím, jak někdo v textu hodnotil / popisoval situaci? Proč ano / proč ne?\n"
        "____________________________________________________________\n"
        "____________________________________________________________"
    )

    # Sebehodnocení
    blok.append(
        "\nSEBEHODNOCENÍ ŽÁKA\n"
        "Označ smajlíka:\n"
        "Rozuměl/a jsem textu.               😃 / 🙂 / 😐\n"
        "Našel/la jsem odpovědi.             😃 / 🙂 / 😐\n"
        "Umím to vysvětlit vlastními slovy.  😃 / 🙂 / 😐"
    )

    return "\n".join(blok)


def vytvor_metodiku(rocnik):
    """
    Metodický list pro učitele, odděleně od žákovského listu.
    Každý ročník má jiný důraz.
    """
    if rocnik == "3. třída":
        tema = "Práce s návodem / pravidly hry (např. Karetní hra)."
        rvp = (
            "• Žák rozumí jednoduchému návodu a dokáže se jím řídit.\n"
            "• Žák vyhledává konkrétní informaci v textu.\n"
            "• Žák odpovídá celou větou."
        )
    elif rocnik == "4. třída":
        tema = "Posuzování kvality a hodnocení výrobku / služby (např. Věnečky)."
        rvp = (
            "• Žák vyhledává informace v delším textu.\n"
            "• Žák rozlišuje názor a fakt.\n"
            "• Žák umí vysvětlit, proč je něco hodnoceno jako lepší / horší."
        )
    else:
        tema = "Zdravé vs. nezdravé / argumentace (např. Sladké mámení)."
        rvp = (
            "• Žák chápe hlavní myšlenku textu a umí ji říct vlastními slovy.\n"
            "• Žák rozumí základům argumentace (proč někdo něco doporučuje / nedoporučuje).\n"
            "• Žák přemýšlí o informacích z textu a formuluje svůj názor."
        )

    metodika = f"""
METODICKÝ LIST PRO UČITELE
(nevydávat žákům)

Téma hodiny:
{tema}

Cíl hodiny:
• rozvoj čtenářské gramotnosti (porozumění textu a práce s informacemi),
• umět najít odpověď v textu, ne ji „tipovat“,
• umět vlastními slovy vysvětlit, co jsem pochopil,
• umět rozlišit názor vs. fakt,
• sebehodnocení: žák reflektuje, jak se mu dařilo.

Očekávané výstupy (RVP – jazyk a jazyková komunikace):
{rvp}

Doporučený průběh hodiny (45 min):
1) MOTIVACE / DRAMATIZACE (5–7 min)
   - žáci sehrají krátkou scénku (viz blok DRAMATIZACE).
   - cílem je vtáhnout je do situace ještě před čtením textu.

2) ČTENÍ TEXTU (10–15 min)
   - žáci čtou vložený text (individuálně nebo společně).
   - podtrhávají důležité části.
   - vyjasní se „SLOVNÍČEK POJMŮ“ (učitel pomůže s významem).

3) PRACOVNÍ LIST – OTÁZKY (15 min)
   - otázky 1–4: práce s textem, vyhledání informace, pochopení,
   - otázka 5: vlastní názor / argumentace.

4) SEBEHODNOCENÍ (5 min)
   - žáci označí smajlíka 😃 🙂 😐,
   - řeknou jednu věc, která jim šla, a jednu, která byla těžká.

Digitální varianta EdRead AI:
• Učitel vloží libovolný text do EdRead AI.
• Vybere ročník (3., 4., 5. třída).
• Aplikace vygeneruje pracovní list pro žáky (včetně slovníčku, otázek a sebehodnocení)
  + samostatně metodický list pro učitele.
• List lze stáhnout / zkopírovat do Wordu a vytisknout.
""".strip()

    return metodika


def sestav_student_sheet(text_zadani, rocnik):
    """
    Sestaví JEDEN čistý blok pro žáky:
    - 1) MOTIVACE / DRAMATIZACE
    - 2) TEXT K PŘEČTENÍ
    - 3) SLOVNÍČEK (s prázdnou linkou k doplnění)
    - 4) OTÁZKY
    - 5) SEBEHODNOCENÍ
    """
    vety = rozdel_na_vety(text_zadani)
    scena = dramatizace_pro_rocnik(rocnik)
    slovnicek = vytvor_slovnicek_blok(text_zadani)
    otazky = vygeneruj_otazky(vety)

    blok = f"""
PRACOVNÍ LIST – EdRead AI
Ročník: {rocnik}

1) MOTIVACE / DRAMATIZACE
{scena}

2) TEXT K PŘEČTENÍ
{text_zadani.strip()}

3) SLOVNÍČEK
{slovnicek}

4) OTÁZKY
{otazky}

(5) SEBEHODNOCENÍ je součástí otázek nahoře.
"""
    return blok.strip()


# -------------------------------------------------
# 2. Streamlit rozhraní
# -------------------------------------------------

st.set_page_config(
    page_title="EdRead AI",
    page_icon="📖",
    layout="wide"
)

st.title("EdRead AI – prototyp pro rozvoj čtenářské gramotnosti")
st.write(
    "Postup: 1) Vlož text. 2) Vyber ročník. 3) Klikni na Vygenerovat. "
    "Dostaneš krásně oddělený Pracovní list pro žáky a Metodiku pro učitele."
)

col_vstup, col_info = st.columns([1, 1])

with col_vstup:
    st.subheader("Vlož text, se kterým chcete pracovat ve třídě")
    vstup_text = st.text_area(
        "Text pro žáky:",
        height=400,
        placeholder="Sem vlož text (např. Věnečky, Karetní hra, Sladké mámení...)."
    )

with col_info:
    st.subheader("Vyber ročník / obtížnost")
    rocnik = st.selectbox(
        "Ročník:",
        ["3. třída", "4. třída", "5. třída"]
    )
    st.markdown("Co dostaneš po vygenerování:")
    st.markdown("- **Pracovní list pro žáky** (motivace, text, slovníček, otázky, sebehodnocení).")
    st.markdown("- **Metodický list pro učitele** (cíle hodiny, RVP, postup hodiny, digitální varianta).")

generuj = st.button("Vygenerovat pracovní list a metodiku")

st.markdown("---")

if generuj:
    if len(vstup_text.strip()) == 0:
        st.error("Nejdřív vlož text 🙂")
    else:
        # vytvoříme oba bloky
        student_sheet = sestav_student_sheet(vstup_text, rocnik)
        teacher_sheet = vytvor_metodiku(rocnik)

        st.header("📄 Pracovní list pro žáky (zkopíruj do Wordu a vytiskni)")
        st.text(student_sheet)

        st.header("🧑‍🏫 Metodický list pro učitele (nezadávat žákům)")
        st.text(teacher_sheet)

        # volitelné: nabídnout stažení jako .txt (učitel si pak vloží do Wordu)
        st.download_button(
            label="Stáhnout pracovní list pro žáky (.txt)",
            data=student_sheet,
            file_name="pracovni_list_EdReadAI.txt",
            mime="text/plain",
        )

        st.download_button(
            label="Stáhnout metodiku pro učitele (.txt)",
            data=teacher_sheet,
            file_name="metodicky_list_EdReadAI.txt",
            mime="text/plain",
        )

else:
    st.info("Až vložíš text a vybereš ročník, klikni na 'Vygenerovat pracovní list a metodiku'.")
