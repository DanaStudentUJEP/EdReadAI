import streamlit as st
import re
import textwrap

# ======================================================
# 1. Pomocné funkce – jazyk, slovníček, dramatizace
# ======================================================

def normalizuj(text):
    """Odstraní extra mezery a zarovná odstavce."""
    # strip konců řádků + nahradí vícenásobné prázdné řádky max dvěma
    t = textwrap.dedent(text).strip("\n ")
    return re.sub(r"\n{3,}", "\n\n", t)

# ---------- DRAMATIZACE PODLE ROČNÍKU ----------

def dramatizace_pro_rocnik(rocnik):
    if rocnik == "3. třída":
        return normalizuj("""
        🎭 ÚVODNÍ SCÉNKA (zahájení hodiny)
        Anička: „Hele, já mám pravidla té nové hry a vůbec jim nerozumím!“
        Marek: „Ukaž. Tady je napsané, kdo přebíjí koho. To je jako kdo je silnější.“
        Učitelka: „Tak si to zkusíme zahrát naživo. Každý bude jedno zvíře.
        A uvidíme, kdo vyhrává nad kým.“
        ➜ Cíl: děti si nejdřív zahrají situaci z textu, a teprve potom text čtou.
        """)

    if rocnik == "4. třída":
        return normalizuj("""
        🎭 ÚVODNÍ SCÉNKA (zahájení hodiny)
        Učitelka: „Dneska budete porota jako v televizní soutěži cukrářů.“
        Eliška: „Já hodnotím, jak ten věneček vypadá.“
        Tomáš: „Já hodnotím chuť a vůni.“
        Natálie: „A já hlídám, jestli cukrář nešidí suroviny.“
        Učitelka: „Přesně takhle mluví i hodnotitelka v našem textu.“
        ➜ Cíl: žáci pochopí, proč se v textu řeší kvalita jídla.
        """)

    if rocnik == "5. třída":
        return normalizuj("""
        🎭 ÚVODNÍ SCÉNKA (zahájení hodiny)
        Eliška: „Víš, že lidi ve světě chtějí čokoládu s méně cukrem,
        ale u nás to lidi skoro neřeší?“
        Tomáš: „Mně je jedno, kolik to má kalorií. Buď je to dobrý, nebo ne.“
        Natálka: „No právě o tom je náš text. Sladkosti, zdraví, tuky, cukry…“
        ➜ Cíl: děti si uvědomí, že text řeší reálný problém (chuť × zdraví).
        """)

    # fallback
    return "Zvol ročník, aby se zobrazila scénka."


# ---------- STRUČNÉ UVEDENÍ TEXTU PRO ŽÁKY ----------

def uvodni_popis_textu(rocnik):
    if rocnik == "3. třída":
        return ("📖 O čem je text?\n"
                "Text vysvětluje pravidla nebo popisuje situaci (hru / činnost). "
                "Tvým úkolem je pochopit kdo co smí a proč. Budeme hledat, kdo je silnější, "
                "jak se „přebíjí“, a jak se má správně hrát nebo postupovat.")

    if rocnik == "4. třída":
        return ("📖 O čem je text?\n"
                "Text popisuje, jak někdo hodnotí jídlo (třeba zákusek) a posuzuje kvalitu. "
                "Říká, co je dobře udělané a co je šizené. Někdy je to názor, někdy fakt. "
                "Ty máš zkusit poznat rozdíl.")

    if rocnik == "5. třída":
        return ("📖 O čem je text?\n"
                "Text mluví o tom, jak často lidé jedí sladkosti, kolik cukru je v jídle, "
                "o zdraví a obezitě, a o tom, jak výrobci zkouší dělat ‚lehčí‘ sladkosti. "
                "Je tam i tabulka s čísly a procenty.")

    return "📖 O čem je text?\nTento text budeme společně číst a rozumět mu."


# ---------- VÝBĚR DŮLEŽITÝCH POJMŮ ----------

# Pojmy, které jsou pro děti užitečné (pro karetní hru, cukrářství, zdravé jídlo...)
POJMY_S_VYSVETLENIM = {
    # 3. třída / Karetní hra styl
    "přebít": "ve hře položit silnější kartu než ten před tebou.",
    "žolík": "speciální karta, která může nahradit jinou kartu.",
    "recept": "návod krok za krokem, jak něco udělat.",
    "receptura": "přesný postup a suroviny podle kterých se má péct.",
    "kombinace karet": "karty, které položíš najednou, protože k sobě patří.",
    # 4. třída / Věnečky styl
    "výuční list": "doklad, že člověk vystudoval obor (třeba cukrář) a umí tu práci.",
    "sražený krém": "krém, který se nepovedl a má hrudky.",
    "margarín": "tuk podobný máslu, levnější náhrada másla.",
    "korpus": "spodní část dortu nebo zákusku – samotné těsto.",
    "odpalované těsto": "těsto na věnečky nebo větrníky, má být nadýchané a duté.",
    "chemická pachuť": "divná umělá chuť, která nepůsobí jako opravdové jídlo.",
    "průmyslově vyráběné listové těsto": "kupované těsto z továrny, ne domácí.",
    "plundrové těsto": "těsto podobné listovému, vrstvené a máslové.",
    # 5. třída / Sladké mámení styl
    "nízkokalorický": "s menším množstvím kalorií (energie z jídla).",
    "obezita": "stav, kdy má člověk nadměrné množství tuku v těle.",
    "metabolismus": "jak tělo zpracovává jídlo a mění ho na energii.",
    "polysacharid": "složitý cukr – tělo ho tráví pomaleji.",
    "transmastné kyseliny": "druhy tuků, které nejsou pro tělo moc zdravé.",
    "energetická hodnota": "kolik energie ti jídlo dá (v kaloriích).",
    "cukrovinka": "sladkost, něco na mlsání (tyčinka, bonbón, čokoláda).",
}

# Slova, která NECHCEME ve slovníčku, i když jsou dlouhá
STOP_SLOVA = {
    "správným", "správně", "maximálně", "ochutnejte", "navíc",
    "škoda", "chutná", "dobrý", "dobře", "hezky", "hezčí",
    "vzdáleně", "nepřipomíná", "cítit", "soustech", "sousto",
    "přepečená", "zestárlá", "tvrdé", "měkká", "křupavá",
    "zlatavá", "vláčná", "chemickou", "chemický", "chemická",
    "průmyslově", "rostlinná", "jemně", "jemný"
}

# Delší pojmy (víceslovné), které chceme umět chytit jako celek
VÍC SLOV_KANDIDÁTI = [
    "výuční list",
    "sražený krém",
    "odpalované těsto",
    "chemická pachuť",
    "průmyslově vyráběné listové těsto",
    "plundrové těsto",
    "transmastné kyseliny",
    "energetická hodnota",
]


def vyber_pojmy_z_textu(text, max_pojmu=10):
    """
    1) Podíváme se, jestli text obsahuje některé naše předpřipravené odbornější pojmy.
    2) Doplníme delší podivnější slova (7+ znaků), která nejsou zakázaná.
    3) Odstraníme duplicity.
    """
    nalezene = []

    lt = text.lower()

    # krok 1: víceslovné pojmy
    for fraze in VÍC SLOV_KANDIDÁTI:
        if fraze in lt and fraze not in nalezene:
            nalezene.append(fraze)

    # krok 2: slova 7+ znaků
    slova = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    for s in slova:
        s_low = s.lower().strip(",. ")
        if len(s_low) >= 7 and s_low not in STOP_SLOVA:
            if s_low not in nalezene:
                nalezene.append(s_low)

    # krok 3: omezíme počet
    return nalezene[:max_pojmu]


def vytvor_slovnicek_blok(text):
    """
    Vrátí pěkný slovníček pro žáky:
    - pojem = jednoduché vysvětlení
    - když vysvětlení neznáme, necháme prázdnou linku k doplnění ve třídě
    """
    pojmy = vyber_pojmy_z_textu(text, max_pojmu=10)

    if not pojmy:
        return normalizuj("""
        📚 SLOVNÍČEK POJMŮ
        (V tomto textu nejsou složitější pojmy. Učitel může dopsat své pojmy ručně.)
        """)

    radky = ["📚 SLOVNÍČEK POJMŮ"]
    for p in pojmy:
        vysv = POJMY_S_VYSVETLENIM.get(p.strip(",. ").lower(), "")
        if vysv:
            radky.append(f"- {p} = {vysv}")
        else:
            radky.append(f"- {p} = ____________________________________________")

    return "\n".join(radky)


# ======================================================
# 2. Otázky podle ročníku
# ======================================================

def otazky_3tr(vety):
    """
    Otázky pro 3. třídu – jednodušší, zaměřené na přímé porozumění textu,
    kdo-co-proč a rozlišení názor / fakt na úplně základní úrovni.
    """
    v1 = vety[0] if len(vety) > 0 else ""
    v2 = vety[1] if len(vety) > 1 else ""

    return normalizuj(f"""
    🧠 OTÁZKY A – Porozumím textu
    1) Kdo / co je v textu nejdůležitější? (zakroužkuj nebo napiš)
       ____________________________________________

    2) Co má být podle textu „správně“? (např. jak se má hrát, co je povolené)
       ____________________________________________
       ____________________________________________

    3) Které tvrzení podle textu NENÍ pravda?
       A) {v1 if v1 else "První věta textu."}
       B) {v2 if v2 else "Další důležitá věta z textu."}
       C) Tvrzení, které v textu vůbec nebylo.
       Odpověď: __________

    💭 OTÁZKY B – Přemýšlím
    4) Napiš vlastními slovy, proč někdo v textu něco chválí nebo kritizuje.
       „Líbí se mu / nelíbí se mu, protože…“
       ____________________________________________
       ____________________________________________

    5) Najdi jednu větu z textu, která je FAKT (dá se ověřit).
       ____________________________________________

       Najdi jednu větu z textu, která je NÁZOR (něčí pocit / hodnocení).
       ____________________________________________

    🌟 SEBEHODNOCENÍ
    Dokázal/a jsem pochopit, o čem ten text je.   ✅ ano   🤔 trochu   ❌ ještě ne
    Umím najít důležitou informaci v textu.       ✅ ano   🤔 trochu   ❌ ještě ne
    Umím říct svůj názor.                         ✅ ano   🤔 trochu   ❌ ještě ne
    """)

def otazky_4tr(vety):
    """
    Otázky pro 4. třídu – kvalita / hodnocení (Věnečky styl),
    rozlišení faktu a názoru, posouzení kvality, argumentace.
    """
    return normalizuj(f"""
    🧠 OTÁZKY A – Najdu to v textu
    1) Která věc / výrobek / varianta byla označená jako nejlepší?
       ____________________________________________

    2) Která byla podle textu nejhorší? Proč?
       ____________________________________________

    3) Co všechno má mít dobrý výrobek podle hodnotitelky / autora textu?
       (napiš aspoň tři věci – např. chuť, vzhled, čerstvost…)
       • ______________________________________
       • ______________________________________
       • ______________________________________

    🔍 OTÁZKY B – Fakt × Názor
    4) Najdi v textu příklad FAKTU
       (je to něco, co se dá změřit / ověřit):
       ____________________________________________

       Najdi v textu příklad NÁZORU
       (něčí hodnocení, pocit, dojem):
       ____________________________________________

    💬 OTÁZKY C – Tvoje hodnocení
    5) Souhlasíš s tím, jak autor hodnotil kvalitu?
       Proč ano / proč ne?
       ____________________________________________
       ____________________________________________

    🌟 SEBEHODNOCENÍ
    Vím, co je fakt a co je názor.                ✅ ano   🤔 trochu   ❌ ještě ne
    Umím napsat, proč je něco dobré / špatné.     ✅ ano   🤔 trochu   ❌ ještě ne
    Rozuměl/a jsem textu.                         ✅ ano   🤔 trochu   ❌ ještě ne
    """)

def otazky_5tr(vety):
    """
    Otázky pro 5. třídu – to je styl 'Sladké mámení':
    práce s informací, tabulkou/procenty (obecně formulováno),
    interpretace a názor.
    """
    v1 = vety[0] if len(vety) > 0 else "První hlavní tvrzení z textu."
    v2 = vety[1] if len(vety) > 1 else "Druhé důležité tvrzení z textu."

    return normalizuj(f"""
    🧠 OTÁZKY A – Porozumění obsahu
    1) Které tvrzení podle textu NEplatí?
       A) {v1}
       B) {v2}
       C) Autor říká, že existuje dokonalá náhrada cukru, která je zdravá a chutná úplně stejně.
       Odpověď: __________

    2) Vysvětli vlastními slovy:
       Proč dnes lidi řeší složení sladkostí (cukr, tuky, kalorie)?
       ____________________________________________
       ____________________________________________

    🔍 OTÁZKY B – Čísla a informace
    3) V textu / tabulce se mluví o tom, jak často lidé něco jedí nebo kupují.
       Co znamená, když je u něčeho třeba 20 %?
       A) Že to jí nebo kupuje asi pětina lidí.
       B) Že to je zakázané.
       C) Že to nikomu nechutná.
       Odpověď: __________

    4) Označ Ano / Ne:
       a) Více než polovina lidí dělá X.      Ano / Ne
       b) Některé značky se kupují častěji než jiné.   Ano / Ne
       c) Víme úplně přesně všechno o všech značkách.  Ano / Ne

    💭 OTÁZKY C – Přemýšlím a hodnotím
    5) V textu se říká, že vědci „hledají recept na zlato“.
       Co to podle tebe znamená?
       ____________________________________________
       ____________________________________________

    6) Jaký typ sladkosti by sis vybral/a ty
       (rychlá energie × zdravější volba)? Proč?
       ____________________________________________
       ____________________________________________

    🌟 SEBEHODNOCENÍ
    Umím vysvětlit hlavní myšlenku textu.         ✅ ano   🤔 trochu   ❌ ještě ne
    Umím použít informaci z tabulky / čísel.      ✅ ano   🤔 trochu   ❌ ještě ne
    Umím napsat svůj názor a zdůvodnit ho.        ✅ ano   🤔 trochu   ❌ ještě ne
    """)

def vygeneruj_otazky(rocnik, text):
    """
    Vybere správný set otázek pro ročník.
    'text' použijeme jen k tomu, abychom vytáhli první věty
    pro volby A/B u některých otázek (= působí to osobněji).
    """
    # rozseknout text na věty pro personalizaci A/B u některých otázek
    kandidati = re.split(r'(?<=[\.\?\!])\s+', text.strip())
    vety = [v.strip() for v in kandidati if len(v.strip()) > 0]

    if rocnik == "3. třída":
        return otazky_3tr(vety)
    if rocnik == "4. třída":
        return otazky_4tr(vety)
    if rocnik == "5. třída":
        return otazky_5tr(vety)
    return "OTÁZKY K TEXTU (nezvolen ročník)"


# ======================================================
# 3. Metodika pro učitele
# ======================================================

def metodicky_list(rocnik, text):
    """
    Stylově vychází z METODICKÝ LIST PRO UČITELE, který používáš do DP.
    Je univerzální: popisuje cíle, RVP, postup hodiny, sebehodnocení.
    (Neobsahuje konkrétní řešení na body – protože ten text se může měnit.)
    """

    if rocnik == "3. třída":
        nazev = "Porozumění návodu / pravidlům hry (EdRead AI, 3. ročník)"
        cile = [
            "Žák rozumí jednoduchému návodu / popisu postupu.",
            "Žák umí najít v textu odpověď na otázku typu kdo-co-jak.",
            "Žák vysvětlí vlastními slovy, co je správně a co ne.",
            "Žák začíná rozlišovat fakt a názor."
        ]
        vystupy = (
            "• Žák vyhledává informaci v krátkém textu.\n"
            "• Žák se dokáže řídit jednoduchými pravidly.\n"
            "• Žák odpovídá celou větou.\n"
            "• Žák ví, že názor = co si někdo myslí, fakt = co můžu ověřit."
        )
    elif rocnik == "4. třída":
        nazev = "Hodnocení kvality / práce s názorem a faktem (EdRead AI, 4. ročník)"
        cile = [
            "Žák rozliší fakt (ověřitelnou informaci) a názor (hodnocení).",
            "Žák umí najít v textu argument: proč je něco dobré / špatné.",
            "Žák chápe, že kvalita se dá popsat pomocí kritérií (chuť, vzhled, čerstvost...).",
            "Žák formuluje svůj vlastní názor celou větou."
        ]
        vystupy = (
            "• Žák vyhledává informaci v delším textu.\n"
            "• Žák pojmenuje kritéria hodnocení.\n"
            "• Žák vysvětlí, proč autor něco chválí nebo kritizuje.\n"
            "• Žák pracuje se slovníkem pojmů (např. korpus, odpalované těsto...)."
        )
    else:
        nazev = "Práce s informacemi, čísly a názorem (EdRead AI, 5. ročník)"
        cile = [
            "Žák chápe hlavní myšlenku delšího publicistického textu.",
            "Žák pracuje s údaji (procenta, nejčastější volby, srovnání).",
            "Žák dokáže vyjádřit vlastní postoj a zdůvodnit ho.",
            "Žák ví, že autor textu může mít záměr (poučit, varovat, informovat...)."
        ]
        vystupy = (
            "• Žák vyhledává informaci v souvislém i nesouvislém textu (tabulka, graf...).\n"
            "• Žák rozlišuje fakt a názor autora.\n"
            "• Žák rozumí pojmům jako nízkokalorický, obezita, složené cukry.\n"
            "• Žák reflektuje vlastní návyk („co jím a proč“)."
        )

    body_cile = "\n".join([f"- {c}" for c in cile])

    postup = normalizuj("""
    1️⃣ Motivační část (5–7 minut)
    • Žáci sehrají úvodní scénku (dramatizaci) ve dvojicích nebo malých skupinách.
    • Cíl: vtáhnout je do tématu ještě před čtením textu.
    • Učitel klade otázky typu:
      – „Co si o tom myslíš ty?“
      – „Setkal/a ses s něčím podobným?“

    2️⃣ Čtení textu (10–15 minut)
    • Žáci čtou text (samostatně nebo po částech nahlas).
    • Při čtení si podtrhávají slova, která nechápou.
    • Následně společně projdete 📚 SLOVNÍČEK POJMŮ.
      → Lze využít kartičky pojmů, promítat na tabuli nebo psát na flipchart.

    3️⃣ Práce s otázkami A / B / C (15–20 minut)
    • A = najdu v textu (porozumění).
    • B = přemýšlím / používám informaci.
    • C = můj názor, vlastní formulace.
    • Učitel sleduje, jestli dítě umí odpovědět s oporou v textu
      (ne tipovat bez čtení).

    4️⃣ Sebehodnocení (5 minut)
    • Žáci vyplní část „🌟 SEBEHODNOCENÍ“ (✅ ano / 🤔 trochu / ❌ ještě ne).
    • Krátká reflexe: „Co pro mě bylo nejtěžší?“, „Co mě překvapilo?“
    • Tohle je důležité pro RVP – žák sleduje vlastní učení.
    """)

    digital = normalizuj("""
    💻 Digitální varianta (EdRead AI)
    • Učitel vloží do EdRead AI libovolný text (článek, ukázku z učebnice,
      novinový článek, pravidla hry…).
    • Zvolí ročník (3., 4. nebo 5. třída).
    • Nástroj automaticky vytvoří:
      – pracovní list pro žáky (se scénkou, čtením, slovníčkem, otázkami, sebehodnocením),
      – metodický list pro učitele (toto, co právě čtete).
    • Tohle pak lze:
      – zkopírovat do Wordu a vytisknout,
      – uložit jako přílohu diplomové práce,
      – použít jako důkaz individualizace podle RVP.
    """)

    vystup_text = normalizuj(f"""
    📘 METODICKÝ LIST PRO UČITELE
    {nazev}

    🎯 Cíl hodiny
    {body_cile}

    🧩 Očekávané výstupy (RVP ZV)
    {vystupy}

    ⏰ Časová dotace
    1 vyučovací hodina (45 minut)

    🪄 Pomůcky
    • Pracovní list (1× na žáka)
    • Text k úloze (tištěný nebo na interaktivní tabuli)
    • Tužka, zvýrazňovač
    • (Volitelně) přístup k EdRead AI a kartičky slovníčku

    💬 Postup hodiny
    {postup}

    🧠 Poznámky pro učitele / záznam do výzkumu
    • Co žáci dělali snadno? (např. našli informaci v textu)
    • Co dělalo problém? (např. vysvětlit pojem vlastními slovy)
    • Kdo potřeboval pomoc s čtením zadání otázky?
    • Jak děti zvládly sebehodnocení (✅ / 🤔 / ❌)?

    Tyto body si můžeš uložit jako reflexi do praktické části diplomové práce.

    {digital}

    (Vytvořeno pomocí EdRead AI – nástroj pro rozvoj čtenářské gramotnosti a dokumentaci práce učitele.)
    """)

    return vystup_text


# ======================================================
# 4. Sestavení pracovního listu pro žáky
# ======================================================

def vytvor_pracovni_list(text, rocnik):
    """
    Finální list pro žáky:
    - hlavička (jméno, třída, datum)
    - dramatizace
    - 'o čem je text'
    - původní text (tak jak ho učitel vložil)
    - slovníček pojmů
    - otázky (A/B/C/sebehodnocení)
    """

    hlavicka = normalizuj(f"""
    {rocnik} · Pracovní list (EdRead AI)

    Jméno: ______________________      Třída: __________      Datum: __________
    """)

    scenka = dramatizace_pro_rocnik(rocnik)
    uvod = uvodni_popis_textu(rocnik)

    slovnicek = vytvor_slovnicek_blok(text)
    otazky = vygeneruj_otazky(rocnik, text)

    cele = normalizuj(f"""
    {hlavicka}

    {scenka}

    {uvod}

    📖 TEXT K PŘEČTENÍ
    {text.strip()}

    {slovnicek}

    {otazky}

    ────────────────────────────
    Vytvořeno pomocí EdRead AI · Rozvoj čtenářské gramotnosti · Strana 1
    """)

    return cele


# ======================================================
# 5. Streamlit UI
# ======================================================

st.set_page_config(
    page_title="EdRead AI",
    page_icon="📖",
    layout="wide"
)

st.title("EdRead AI – prototyp nástroje pro rozvoj čtenářské gramotnosti")
st.write(
    "→ Toto je verze pro diplomovou práci.\n"
    "1) Vlož text, se kterým chceš pracovat.\n"
    "2) Vyber ročník.\n"
    "3) Klikni na Vygenerovat.\n\n"
    "Dostaneš:\n"
    "• krásně formátovaný pracovní list pro žáky (scénka, text, slovníček, otázky, sebehodnocení),\n"
    "• samostatně metodický list pro učitele (cíle hodiny, RVP, postup hodiny...)."
)

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("1. Vlož text pro žáky")
    vstup_text = st.text_area(
        "Sem vlož celý text (např. Karetní hra, Věnečky, Sladké mámení…)",
        height=400,
        placeholder="Zkopíruj sem původní text, se kterým chceš pracovat..."
    )

with col_right:
    st.subheader("2. Vyber ročník / obtížnost")
    rocnik = st.selectbox(
        "Pro jakou třídu je tenhle list?",
        ["3. třída", "4. třída", "5. třída"]
    )

    st.markdown("3. Klikni na tlačítko níže 👍")

generuj = st.button("Vygenerovat pracovní list pro žáky + metodický list pro učitele")

st.markdown("---")

if generuj:
    if len(vstup_text.strip()) == 0:
        st.error("Nejdřív vlož text 🙃")
    else:
        # vytvoříme obsah
        student_sheet = vytvor_pracovni_list(vstup_text, rocnik)
        teacher_sheet = metodicky_list(rocnik, vstup_text)

        st.header("📄 Pracovní list pro žáky (zkopíruj do Wordu a vytiskni)")
        st.text(student_sheet)

        st.header("📘 Metodický list pro učitele (nezadávat žákům)")
        st.text(teacher_sheet)

        # Umožníme stažení jako .txt soubory (ty si pak vložíš do Wordu / přiložíš do DP)
        st.download_button(
            label="⬇ Stáhnout pracovní list pro žáky (.txt)",
            data=student_sheet,
            file_name="pracovni_list_EdReadAI.txt",
            mime="text/plain",
        )

        st.download_button(
            label="⬇ Stáhnout metodický list pro učitele (.txt)",
            data=teacher_sheet,
            file_name="metodicky_list_EdReadAI.txt",
            mime="text/plain",
        )

else:
    st.info("Až vložíš text a vybereš ročník, klikni na „Vygenerovat pracovní list…“ 🙂")
