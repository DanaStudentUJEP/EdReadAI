import streamlit as st
import re
import textwrap

# -------------------------------------------------
# Pomocné funkce pro zpracování textu
# -------------------------------------------------

def rozdel_na_vety(text):
    """
    Hrubé rozdělení textu na věty podle . ? !
    (Není dokonalé, ale stačí pro generování otázek.)
    """
    kandidati = re.split(r'(?<=[\.\?\!])\s+', text.strip())
    vety = [v.strip() for v in kandidati if len(v.strip()) > 0]
    return vety

def vyber_slovicka(text, max_slov=10):
    """
    Vybere možná 'těžší' slova pro slovníček.
    Bereme delší výrazy (8+ znaků), bez čísel.
    Výsledkem je návrh – učitel to může ručně upravit.
    """
    slova = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    slova_cista = [s.strip().lower() for s in slova if len(s) >= 8]
    unik = []
    for s in slova_cista:
        if s not in unik:
            unik.append(s)
    return unik[:max_slov]

def navrh_vysvetleni(slovo):
    """
    Jednoduché obecné vysvětlení.
    Učitelka může přepsat na konkrétní jednoduchou definici pro děti.
    """
    return f"{slovo} = složitější slovo z textu. Vysvětli ho dětem jednoduše vlastními slovy."

def dramatizace_pro_rocnik(rocnik):
    """
    Krátká zahajovací scénka - dramatizace.
    Ta jde na začátek hodiny jako motivace.
    Připraveno pro 3., 4. a 5. třídu.
    """
    if rocnik == "3. třída":
        return textwrap.dedent("""
        DRAMATIZACE (zahájení hodiny)
        Anička: „Hele, já mám pravidla té nové hry a vůbec jim nerozumím!“
        Marek: „Ukaž. Tady se píše, kdo přebíjí koho. To je jako kdo je silnější.“
        Učitelka: „Tak to zkusíme zahrát nanečisto. Každý je jedno zvíře a uvidíme, kdo koho porazí.“
        → Cíl: děti si vyzkouší situaci z textu naživo, ještě než ho budou číst.
        """).strip()

    if rocnik == "4. třída":
        return textwrap.dedent("""
        DRAMATIZACE (zahájení hodiny)
        Učitelka: „Dneska budete porota jako v soutěži cukrářů.“
        Eliška: „Já hodnotím, jak to vypadá.“
        Tomáš: „Já hodnotím chuť a vůni.“
        Natálie: „A já hlídám, jestli cukrář nešidil suroviny.“
        Učitelka: „A přesně takhle postupovala i skutečná cukrářka v našem textu.“
        → Cíl: děti chápou, proč se v textu mluví o kvalitě zákusků.
        """).strip()

    if rocnik == "5. třída":
        return textwrap.dedent("""
        DRAMATIZACE (zahájení hodiny)
        Adam: „Já mám rád čokoládu a je mi jedno, kolik má cukru.“
        Bára: „Já si radši hlídám kalorie, prý je to zdravější.“
        Učitelka: „Tohle řeší i dospělí – jak mít něco dobrého a přitom ne úplně nezdravého.“
        → Cíl: děti si uvědomí téma: chuť vs. zdraví.
        """).strip()

    return "Vyber ročník nahoře, aby se zobrazila správná dramatizace."

def vygeneruj_slovnicek(text):
    """
    Vytvoří návrh slovníčku pojmů.
    """
    slova = vyber_slovicka(text, max_slov=10)
    if not slova:
        return "SLOVNÍČEK POJMŮ:\n(nebyla nalezena složitější slova – učitel může doplnit ručně)"
    radky = [f"- {navrh_vysvetleni(s)}" for s in slova]
    return "SLOVNÍČEK POJMŮ:\n" + "\n".join(radky)

def vygeneruj_otazky(vety):
    """
    Vytvoří univerzální otázky:
    - porozumění (A/B/C),
    - vyhledávání informací z textu,
    - vlastní názor,
    - sebehodnocení.
    Tohle funguje na libovolný text.
    """
    if len(vety) == 0:
        return "Nebyl vložen žádný text."

    # Použijeme první 2-3 věty jako základ pro otázky.
    veta1 = vety[0] if len(vety) > 0 else ""
    veta2 = vety[1] if len(vety) > 1 else ""
    veta3 = vety[2] if len(vety) > 2 else ""

    cast_a = []
    cast_a.append(
        "OTÁZKA 1 (Porozumění textu)\n"
        "Co z následujícího NEvyplývá z textu?\n"
        f"A) {veta1}\n"
        f"B) {veta2 if veta2 else 'Druhá důležitá informace z textu.'}\n"
        "C) Tvrzení, které v textu vůbec nebylo.\n"
        "Odpověď: __________"
    )

    cast_a.append(
        "OTÁZKA 2 (Najdi v textu)\n"
        "Napiš, která část textu říká, kdo / co bylo nejlepší nebo nejhorší.\n"
        "Odpověď: ___________________________________"
    )

    cast_b = []
    cast_b.append(
        "OTÁZKA 3 (Vysvětli vlastními slovy)\n"
        "Proč si někdo v textu myslí, že jedna věc/byla lepší než ostatní?\n"
        "__________________________________________\n"
        "__________________________________________"
    )

    cast_b.append(
        "OTÁZKA 4 (NÁZOR vs. FAKT)\n"
        "Najdi v textu:\n"
        "• jednu větu, která je NÁZOR (co si někdo myslí),\n"
        "• a jednu větu, která je FAKT (dá se ověřit).\n"
        "NÁZOR:\n_____________________________\n"
        "FAKT:\n_____________________________"
    )

    cast_c = []
    cast_c.append(
        "OTÁZKA 5 (Můj názor)\n"
        "Souhlasíš s hodnocením v textu? Proč ano / ne?\n"
        "__________________________________________\n"
        "__________________________________________"
    )

    sebehodnoceni = textwrap.dedent("""
    SEBEHODNOCENÍ ŽÁKA
    Označ, jak se cítíš po práci s textem:

    Rozuměl/a jsem textu.               😃 / 🙂 / 😐
    Našel/la jsem odpovědi.             😃 / 🙂 / 😐
    Umím to vysvětlit vlastními slovy.  😃 / 🙂 / 😐
    """)

    vystup = []
    vystup.append("=== OTÁZKY A: Porozumění textu ===")
    vystup.extend(cast_a)
    vystup.append("\n=== OTÁZKY B: Přemýšlení o textu ===")
    vystup.extend(cast_b)
    vystup.append("\n=== OTÁZKY C: Můj názor ===")
    vystup.extend(cast_c)
    vystup.append("\n=== SEBEHODNOCENÍ ===")
    vystup.append(sebehodnoceni)

    return "\n\n".join(vystup)

def vytvor_metodiku(rocnik):
    """
    Krátký metodický list k danému ročníku:
    - cíl hodiny,
    - návaznost na RVP,
    - průběh hodiny,
    - digitální varianta EdRead AI.
    """
    if rocnik == "3. třída":
        rvp = (
            "Žák rozumí jednoduchému návodu a dokáže se jím řídit.\n"
            "Žák vyhledává konkrétní informaci v textu.\n"
            "Žák odpovídá celou větou."
        )
        tema = "Práce s návodem/pravidly hry (Karetní hra)."
    elif rocnik == "4. třída":
        rvp = (
            "Žák vyhledává informace v delším textu.\n"
            "Žák rozlišuje názor a fakt.\n"
            "Žák umí popsat, proč něco bylo hodnoceno jako lepší/horší."
        )
        tema = "Hodnocení kvality (Věnečky)."
    else:
        rvp = (
            "Žák pracuje s publicistickým / populárně naučným textem.\n"
            "Žák chápe hlavní myšlenku textu a umí ji vysvětlit vlastními slovy.\n"
            "Žák umí popsat hlavní argumenty."
        )
        tema = "Zdravé mlsání, cukry a reklama (Sladké mámení)."

    metodika = f"""
METODICKÝ LIST PRO UČITELE

Téma hodiny:
{tema}

Cíl hodiny:
- rozvoj čtenářské gramotnosti (porozumění textu a práce s informací),
- schopnost vysvětlit vlastními slovy, co jsem pochopil,
- schopnost rozlišit fakt vs. názor.

Očekávané výstupy (RVP – jazyk a jazyková komunikace):
{rvp}

Doporučený průběh hodiny (45 min):
1) MOTIVACE / DRAMATIZACE (5–7 min)
   - žáci hrají scénku podle dramatizace.
   - cílem je vtáhnout je do situace ještě před čtením.

2) ČTENÍ TEXTU (10–15 min)
   - žáci čtou dodaný text (samostatně nebo nahlas po odstavcích),
   - podtrhují důležité informace,
   - objasníme slovníček pojmů.

3) PRÁCE S OTÁZKAMI (15 min)
   - A: najdi informaci v textu,
   - B: vysvětli vlastními slovy,
   - C: vyjádři svůj názor.
   -> Učitel sleduje, kdo umí odpovědět s oporou v textu.

4) SEBEHODNOCENÍ (5 min)
   - žáci vyberou smajlíka 😃 🙂 😐 a krátce řeknou proč.
   - rozvoj sebereflexe („Rozuměl/a jsem? Co bylo těžké?“).

Digitální varianta EdRead AI:
- Stejný text lze vložit do webového rozhraní EdRead AI.
- Aplikace vygeneruje pracovní list a otázky automaticky.
- Odpovědi žáků lze zadat přímo do počítače/tabletu.
- Učitel pak vidí, kdo zvládl vyhledat informaci v textu a kdo ne.
"""
    return metodika.strip()


# -------------------------------------------------
# Streamlit UI
# -------------------------------------------------

st.set_page_config(page_title="EdRead AI", page_icon="📖", layout="wide")

st.title("EdRead AI – prototyp pro rozvoj čtenářské gramotnosti")
st.write("1. Vlož text. 2. Vyber ročník. 3. Klikni na Vygenerovat. Pak výstup zkopíruj do Wordu a můžeš tisknout.")

# levý sloupec (vstup)
col1, col2 = st.columns([1,1])

with col1:
    st.subheader("Vlož výukový text (např. Věnečky, Karetní hra...)")
    vstup_text = st.text_area(
        "Text pro žáky:",
        height=300,
        placeholder="Sem vlož text, se kterým budete pracovat ve třídě."
    )

with col2:
    st.subheader("Vyber ročník / obtížnost")
    rocnik = st.selectbox(
        "Ročník:",
        ["3. třída", "4. třída", "5. třída"]
    )

    st.markdown("Po vygenerování dostaneš:")
    st.markdown("- dramatizaci (zahájení hodiny),")
    st.markdown("- slovníček pojmů,")
    st.markdown("- otázky pro žáky,")
    st.markdown("- metodický list pro učitele (RVP, průběh hodiny, digitální varianta).")

    tlacitko = st.button("Vygenerovat pracovní list")

# výstup
if tlacitko:
    if len(vstup_text.strip()) == 0:
        st.error("Nejdřív vlož text 🙂")
    else:
        vety = rozdel_na_vety(vstup_text)
        scena = dramatizace_pro_rocnik(rocnik)
        slovnicek = vygeneruj_slovnicek(vstup_text)
        otazky = vygeneruj_otazky(vety)
        metodika = vytvor_metodiku(rocnik)

        st.markdown("---")
        st.header("📄 Výstup pro kopírování do Wordu")

        st.subheader("1) Dramatizace (začátek hodiny)")
        st.text(scena)

        st.subheader("2) Text pro žáky (tvůj vstup)")
        st.text(vstup_text.strip())

        st.subheader("3) Slovníček pojmů")
        st.text(slovnicek)

        st.subheader("4) Otázky pro žáky")
        st.text(otazky)

        st.subheader("5) Metodický list pro učitele")
        st.text(metodika)

        st.markdown("---")
        st.caption("EdRead AI – prototyp pro rozvoj čtenářské gramotnosti na 1. stupni ZŠ.")
else:
    st.info("Až vložíš text a vybereš ročník, klikni na tlačítko Vygenerovat pracovní list.")
