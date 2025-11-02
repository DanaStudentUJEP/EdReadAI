import streamlit as st
import re
import textwrap
from io import BytesIO
from docx import Document
from docx.shared import Pt

# ======================================================
# Pomocné: formátování textu
# ======================================================

def normalizuj(text):
    """Zarovná vícenásobné mezery a prázdné řádky."""
    t = textwrap.dedent(text).strip("\n ")
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t

# ======================================================
# DRAMATIZACE podle ročníku
# ======================================================

def dramatizace_pro_rocnik(rocnik):
    if rocnik == "3. třída":
        return normalizuj("""
        🎭 ÚVODNÍ SCÉNKA (začátek hodiny)
        Anička: „Hele, já mám pravidla té nové hry a vůbec jim nerozumím!“
        Marek: „Ukaž. Tady je napsané, kdo přebíjí koho. To je jako kdo je silnější.“
        Učitelka: „Tak si to zkusíme zahrát nanečisto. Každý z vás bude jedno zvíře.
        A uvidíme, kdo koho může přebít.“
        
        ➜ Cíl: děti si nejdřív prožijí situaci z textu, teprve potom text čtou.
        """)

    if rocnik == "4. třída":
        return normalizuj("""
        🎭 ÚVODNÍ SCÉNKA (začátek hodiny)
        Učitelka: „Dnes budete jako porota v cukrářské soutěži.“
        Eliška: „Já hodnotím, jak zákusek vypadá.“
        Tomáš: „Já hodnotím chuť a vůni.“
        Natálie: „Já hlídám, jestli cukrář nešidí suroviny.“
        Učitelka: „Přesně takhle mluví i paní v našem textu. Budeme spolu zjišťovat,
        co je dobré, co je slabé a proč.“
        
        ➜ Cíl: žáci hned pochopí, že text je o hodnocení kvality.
        """)

    if rocnik == "5. třída":
        return normalizuj("""
        🎭 ÚVODNÍ SCÉNKA (začátek hodiny)
        Eliška: „Víš, že lidi chtějí sladkosti s méně kaloriemi?“
        Tomáš: „Mně je jedno, kolik to má kalorií. Hlavně když je to dobré.“
        Natálka: „No právě o tom je náš text – sladkosti, zdraví a čísla z průzkumu.“
        
        ➜ Cíl: žáci hned vědí, že text řeší zdraví, cukr a to, co lidi kupují.
        """)

    return "Zvol třídu, aby se ukázala dramatizace."


# ======================================================
# Úvodní vysvětlení textu dětem
# ======================================================

def uvodni_popis_textu(rocnik):
    if rocnik == "3. třída":
        return normalizuj("""
        📖 O ČEM JE TEXT
        Text vysvětluje pravidla (kdo smí co udělat, kdo je silnější, jak se správně hraje).
        Tvým úkolem je porozumět tomu, jak hra funguje, a umět říct to vlastními slovy.
        """)

    if rocnik == "4. třída":
        return normalizuj("""
        📖 O ČEM JE TEXT
        Text mluví o tom, jak někdo hodnotí zákusky a kvalitu jejich výroby.
        Někdy jsou to FAKTA (dá se ověřit), někdy NÁZORY (osobní hodnocení).
        Ty máš ukázat, že ten rozdíl poznáš.
        """)

    if rocnik == "5. třída":
        return normalizuj("""
        📖 O ČEM JE TEXT
        Text řeší sladkosti, zdraví, kalorie a co lidé kupují.
        Je tam i tabulka s čísly. Budeš číst informace, porovnávat je
        a vysvětlovat, co z toho plyne.
        """)

    return "📖 Tento text budeme číst a rozumět mu."


# ======================================================
# Slovníček pojmů
# ======================================================

POJMY_S_VYSVETLENIM = {
    # 3. třída / hry
    "přebít": "položit silnější kartu než měl hráč před tebou",
    "žolík": "speciální karta, která se může tvářit jako jakákoli jiná karta",
    "receptura": "přesný předpis, jak se to má udělat a z čeho",
    "kombinace karet": "víc karet, které se mají hrát spolu",

    # 4. třída / věnečky
    "výuční list": "doklad o tom, že někdo vystudoval obor (třeba cukrář)",
    "sražený krém": "nepovedený krém, má hrudky",
    "margarín": "tuk podobný máslu, levnější náhrada másla",
    "korpus": "spodní část dortu nebo zákusku – samotné těsto",
    "odpalované těsto": "těsto na větrníky / věnečky, má být duté a nadýchané",
    "chemická pachuť": "divná umělá chuť",
    "průmyslově vyráběné listové těsto": "kupované listové těsto z továrny",
    "plundrové těsto": "těsto podobné listovému, máslové, vrstvené",

    # 5. třída / sladkosti
    "nízkokalorický": "s menším množstvím kalorií (energie z jídla)",
    "obezita": "když má tělo nadměrně moc tuku",
    "metabolismus": "jak tělo zpracovává jídlo a mění ho na energii",
    "polysacharid": "složitý cukr, tělo ho tráví pomalu",
    "transmastné kyseliny": "druhy tuků, které nejsou moc zdravé",
    "energetická hodnota": "kolik energie ti jídlo dá (v kaloriích)",
}

STOP_SLOVA = {
    "správným", "správně", "maximálně", "navíc", "škoda",
    "chutná", "dobrý", "dobře", "hezky", "hezčí", "cítit",
    "soustech", "sousto", "tvrdé", "měkká", "křupavá",
    "zlatavá", "vláčná", "chemickou", "chemický", "chemická",
    "přepečená", "zestárlá"
}

VIC_SLOV_KANDIDATI = [
    "výuční list",
    "sražený krém",
    "odpalované těsto",
    "chemická pachuť",
    "průmyslově vyráběné listové těsto",
    "plundrové těsto",
    "transmastné kyseliny",
    "energetická hodnota",
]

def vyber_pojmy_z_textu(text, max_pojmu=8):
    """
    1) zkusíme víceslovné pojmy
    2) doplníme delší podezřelá slova (7+ znaků), bez těch co nechceme
    """
    nalezene = []
    lt = text.lower()

    # víceslovné
    for fraze in VIC_SLOV_KANDIDATI:
        if fraze in lt and fraze not in nalezene:
            nalezene.append(fraze)

    # delší jednotlivá slova
    slova = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    for s in slova:
        s_low = s.lower()
        if len(s_low) >= 7 and s_low not in STOP_SLOVA:
            if s_low not in nalezene:
                nalezene.append(s_low)

    return nalezene[:max_pojmu]

def vytvor_slovnicek_blok(text):
    pojmy = vyber_pojmy_z_textu(text, max_pojmu=8)

    if not pojmy:
        return normalizuj("""
        📚 SLOVNÍČEK POJMŮ
        (V tomto textu nejsou výrazně složitá slova. Učitel může dopsat vlastní.)
        """)

    radky = ["📚 SLOVNÍČEK POJMŮ"]
    for p in pojmy:
        klic = p.lower()
        vysv = POJMY_S_VYSVETLENIM.get(klic, "")
        if vysv:
            radky.append(f"- {p} = {vysv}")
        else:
            radky.append(f"- {p} = ____________________________________________")
    return "\n".join(radky)


# ======================================================
# OTÁZKY podle ročníku
# ======================================================

def otazky_3tr():
    # U 3. třídy držíme jazyk velmi jednoduchý a stabilní
    return normalizuj("""
    🧠 OTÁZKY A – ROZUMÍM TEXTU
    1) O čem ten text je?
       ☐ O pravidlech hry
       ☐ O včelách v přírodě
       ☐ O tom, jak péct dort

    2) Kdo je v textu důležitý?
       (doplň jméno osoby / zvířete / věci z textu)
       ______________________________________

    3) Co se má podle textu dělat SPRÁVNĚ?
       (např. jak se hraje, co je povolené)
       ______________________________________
       ______________________________________

    4) Zaškrtni možnost, která v textu NENÍ.
       ☐ Někdo něco vysvětluje nebo hodnotí.
       ☐ Mluví se o tom, co je správně a co špatně.
       ☐ Děti jedou na výlet do vesmíru.

    💭 OTÁZKY B – PŘEMÝŠLÍM O TOM
    5) Proč někdo něco v textu chválí nebo kritizuje?
       „Líbí se mu / nelíbí se mu, protože…“
       ______________________________________
       ______________________________________

    6) Najdi ve svém textu:
       a) 1 větu, která je FAKT (dá se ověřit)
          ___________________________________
       b) 1 větu, která je NÁZOR (pocit / hodnocení)
          ___________________________________

    🌟 SEBEHODNOCENÍ
    Rozuměl/a jsem textu.                🙂 / 😐 / 😕
    Našel/la jsem správné odpovědi.      🙂 / 😐 / 😕
    Umím říct vlastními slovy proč.      🙂 / 😐 / 😕
    """)

def otazky_4tr():
    return normalizuj("""
    🧠 OTÁZKY A – HLEDÁM V TEXTU
    1) Který výrobek / věc byla hodnocena jako NEJLEPŠÍ? Proč?
       ______________________________________
       ______________________________________

    2) Co bylo podle textu nejhorší? Co mu vadilo?
       ______________________________________
       ______________________________________

    3) Co má mít dobrý výrobek, aby byl poctivý a kvalitní?
       • _______________________________
       • _______________________________
       • _______________________________

    🔍 OTÁZKY B – FAKT vs. NÁZOR
    4) Najdi ve svém textu:
       FAKT (dá se ověřit, změřit):
       ______________________________________

       NÁZOR (jak to někomu chutná / líbí se mu to):
       ______________________________________

    💬 OTÁZKY C – TVŮJ NÁZOR
    5) Souhlasíš s hodnocením kvality v textu? Proč ano / proč ne?
       ______________________________________
       ______________________________________

    🌟 SEBEHODNOCENÍ
    Vím, co je FAKT a co je NÁZOR.        🙂 / 😐 / 😕
    Umím vysvětlit, proč je něco dobré.  🙂 / 😐 / 😕
    Rozuměl/a jsem textu.                🙂 / 😐 / 😕
    """)

def otazky_5tr():
    return normalizuj("""
    🧠 OTÁZKY A – HLAVNÍ MYŠLENKA
    1) O čem text hlavně je?
       ☐ O sladkostech, zdraví a kaloriích
       ☐ O tom, jak opravit kolo
       ☐ O stavbě hradu z písku

    2) Proč lidé dnes řeší, kolik má jídlo cukru a tuku?
       ______________________________________
       ______________________________________

    🔍 OTÁZKY B – PRÁCE S INFORMACÍ
    3) V textu (nebo tabulce) jsou čísla v procentech.
       Co znamená, když u něčeho bylo třeba „20 % lidí“?
       ☐ Asi pětina lidí to jí / kupuje
       ☐ Znamená to zákaz
       ☐ Znamená to, že to nikomu nechutná

    4) Označ Ano / Ne:
       a) Některé výrobky se kupují častěji než jiné.      Ano / Ne
       b) Víme přesně úplně vše o všech značkách.          Ano / Ne
       c) Řeší se i zdraví a rizika (tuky, obezita).       Ano / Ne

    💭 OTÁZKY C – PŘEMÝŠLÍM
    5) V textu se říká, že vědci „hledají recept na zlato“.
       Co to podle tebe znamená?
       ______________________________________
       ______________________________________

    6) Co by sis vybral/a ty: rychlou sladkost (= rychlá energie),
       nebo spíš zdravější možnost? Proč?
       ______________________________________
       ______________________________________

    🌟 SEBEHODNOCENÍ
    Umím vysvětlit, co je hlavní myšlenka textu.        🙂 / 😐 / 😕
    Umím použít údaje z textu / tabulky.                🙂 / 😐 / 😕
    Umím napsat vlastní názor a zdůvodnit ho.           🙂 / 😐 / 😕
    """)

def vygeneruj_otazky(rocnik):
    if rocnik == "3. třída":
        return otazky_3tr()
    if rocnik == "4. třída":
        return otazky_4tr()
    if rocnik == "5. třída":
        return otazky_5tr()
    return "OTÁZKY K TEXTU"


# ======================================================
# Obrázková opora
# ======================================================

def obrazkova_opora(rocnik):
    if rocnik == "3. třída":
        return normalizuj("""
        🖼 OBRÁZKOVÁ OPORA
        • Nakresli šipky mezi zvířaty: kdo koho přebíjí (kdo je silnější).
        • Nakresli kartičku „žolík“ a napiš, proč je zvláštní.
        """)
    if rocnik == "4. třída":
        return normalizuj("""
        🖼 OBRÁZKOVÁ OPORA
        • Nakresli malou cedulku „Porota“ a vedle tři hvězdičky ⭐⭐⭐.
        • Nakresli koláček / věneček a šipky k nápisům:
          „vzhled“, „chuť“, „poctivé suroviny“.
        """)
    if rocnik == "5. třída":
        return normalizuj("""
        🖼 OBRÁZKOVÁ OPORA
        • Nakresli tabulku s procenty a nad ni lupu 🔍.
        • Nakresli srdce ❤️ a vedle něj nápis „zdraví“.
        """)
    return ""


# ======================================================
# Metodický list pro učitele (RVP ZV)
# ======================================================

def metodicky_list(rocnik, puvodni_text):
    if rocnik == "3. třída":
        nazev = "EdRead AI – Práce s jednoduchým návodem / pravidly hry (3. ročník ZŠ)"
        cile = [
            "Žák rozumí kratšímu textu s pravidly / postupem.",
            "Žák vyhledá v textu konkrétní informaci (kdo, co, jak).",
            "Žák začíná rozlišovat FAKT vs. NÁZOR.",
            "Žák dokáže převyprávět pravidla vlastními slovy."
        ]
        rvp = (
            "RVP ZV – Jazyk a jazyková komunikace:\n"
            "• žák čte s porozuměním jednoduché texty (návod, pravidla hry),\n"
            "• vyhledává v textu podstatnou informaci,\n"
            "• reprodukuje text vlastními slovy."
        )

    elif rocnik == "4. třída":
        nazev = "EdRead AI – Hodnocení kvality a rozlišení FAKT / NÁZOR (4. ročník ZŠ)"
        cile = [
            "Žák rozpozná rozdíl mezi FAKTEM (ověřitelným údajem) a NÁZOREM (hodnocení).",
            "Žák rozumí tomu, podle jakých kritérií je něco hodnoceno (vzhled, chuť, poctivost).",
            "Žák dokáže formulovat vlastní souhlas/nesouhlas a zdůvodnit ho.",
        ]
        rvp = (
            "RVP ZV – Jazyk a jazyková komunikace:\n"
            "• žák porovnává informace z různých částí textu,\n"
            "• rozlišuje subjektivní hodnocení a objektivní sdělení,\n"
            "• vyjadřuje svůj názor celou větou a zdůvodňuje ho."
        )

    else:
        nazev = "EdRead AI – Práce s publicistickým textem a údaji v procentech (5. ročník ZŠ)"
        cile = [
            "Žák chápe hlavní sdělení publicistického / populárně naučného textu.",
            "Žák pracuje s čísly a procenty v textu nebo tabulce.",
            "Žák propojuje text se svým životem (zdraví, strava, volba).",
            "Žák formuluje vlastní postoj a umí ho vysvětlit."
        ]
        rvp = (
            "RVP ZV – Jazyk a jazyková komunikace:\n"
            "• žák vyhledává a porovnává informace v souvislém i nesouvislém textu (tabulka, průzkum),\n"
            "• interpretuje význam údajů (procenta, četnost),\n"
            "• vyjadřuje a zdůvodňuje svůj názor k textu."
        )

    body_cile = "\n".join([f"- {c}" for c in cile])

    postup = normalizuj("""
    1) MOTIVACE / DRAMATIZACE (5–7 min)
       Žáci sehrají krátkou scénku (viz DRAMATIZACE). Cíl: aby věděli, o čem text bude,
       ještě před čtením.

    2) ČTENÍ TEXTU (10–15 min)
       Žáci čtou text (individuálně nebo hlasitě po odstavcích).
       Podtrhají slova, kterým nerozumí.
       Společně projdete slovníček pojmů.

    3) PRÁCE S OTÁZKAMI (15–20 min)
       Blok A = rozumím textu (vyhledám informaci).
       Blok B = přemýšlím o textu (proč je něco dobře/špatně).
       Blok C = můj názor (vysvětlím, proč si to myslím já).
       Sleduj, jestli dítě odpovídá s oporou v textu, nebo „tipuje“.

    4) SEBEHODNOCENÍ (5 min)
       Žáci vyplní vlastní reflexi (🙂 / 😐 / 😕).
       Učitel si může dělat poznámky k dalšímu rozvoji čtenářské gramotnosti.
    """)

    obrazky = obrazkova_opora(rocnik)

    digital = normalizuj("""
    DIGITÁLNÍ VARIANTA (EdRead AI)
    • Učitel vloží libovolný text do EdRead AI.
    • Vybere ročník (3., 4. nebo 5. třída).
    • Nástroj automaticky vytvoří:
      – pracovní list pro žáka (text + slovníček + otázky + sebehodnocení),
      – metodický list pro učitele (cíle, RVP, průběh hodiny, reflexe).
    • List lze stáhnout jako .docx a archivovat jako důkaz podpory čtenářské gramotnosti
      a individualizace výuky v souladu s RVP ZV.
    """)

    vystup = normalizuj(f"""
    METODICKÝ LIST PRO UČITELE
    {nazev}

    VAZBA NA RVP ZV
    {rvp}

    CÍLE HODINY
    {body_cile}

    ČASOVÁ DOTACE
    1 vyučovací hodina (45 minut)

    POTŘEBNÉ POMŮCKY
    • Pracovní list pro žáka
    • Text k úloze (tištěný / na tabuli)
    • Tužka, zvýrazňovač
    • (Volitelně) počítač / tablet – digitální vyplnění

    POPIS HODINY KROK ZA KROKEM
    {postup}

    OBRÁZKOVÁ OPORA / PIKTOGRAMY
    {obrazky}

    POZNÁMKY UČITELE PRO ZÁZNAM (REFLEXE HODINY)
    • Co šlo dětem snadno?
    • Kde tápaly?
    • Kdo měl potíž pochopit zadání otázky?
    • Jak děti mluvily o faktu a názoru?
    • Jak hodnotily samy sebe (🙂 / 😐 / 😕)?

    {digital}

    (Vytvořeno pomocí EdRead AI – nástroj na podporu čtenářské gramotnosti.)
    """)
    return vystup


# ======================================================
# Sestavení pracovního listu pro žáky (text + všechno kolem)
# ======================================================

def vytvor_pracovni_list(text, rocnik):
    hlavicka = normalizuj(f"""
    {rocnik} · Pracovní list (EdRead AI)

    Jméno: ______________________      Třída: __________      Datum: __________
    """)

    scenka = dramatizace_pro_rocnik(rocnik)
    uvod = uvodni_popis_textu(rocnik)
    slovnicek = vytvor_slovnicek_blok(text)
    otazky = vygeneruj_otazky(rocnik)
    obrazky = obrazkova_opora(rocnik)

    cele = normalizuj(f"""
    {hlavicka}

    {scenka}

    {uvod}

    📖 TEXT K PŘEČTENÍ
    {text.strip()}

    {slovnicek}

    {otazky}

    {obrazky}

    ────────────────────────────
    Vytvořeno pomocí EdRead AI · Rozvoj čtenářské gramotnosti · Strana 1
    """)

    return cele


# ======================================================
# Pomocné: vytvoření .docx souboru z textu
# ======================================================

def vytvor_docx(zneni_textu, nazev_dokumentu):
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    for blok in zneni_textu.split("\n\n"):
        p = doc.add_paragraph(blok)
        p_format = p.paragraph_format
        p_format.space_after = Pt(6)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer, nazev_dokumentu


# ======================================================
# STREAMLIT UI
# ======================================================

st.set_page_config(
    page_title="EdRead AI",
    page_icon="📖",
    layout="wide"
)

st.title("EdRead AI – prototyp nástroje pro rozvoj čtenářské gramotnosti")
st.write(
    "Tento nástroj je připraven pro diplomovou práci.\n\n"
    "1) Vlož původní text (např. Věnečky, Sladké mámení, Karetní hra).\n"
    "2) Vyber ročník.\n"
    "3) Klikni na Vygenerovat.\n\n"
    "Výstup:\n"
    "• Pracovní list pro žáky (dramatizace na úvod hodiny, text, slovníček, otázky, obrázková opora, sebehodnocení).\n"
    "• Metodický list pro učitele (cíle hodiny, vazba na RVP ZV, postup hodiny, reflexe).\n"
    "Oba dokumenty si stáhneš rovnou jako .docx."
)

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("1. Vlož text pro žáky")
    vstup_text = st.text_area(
        "Sem vlož celý text (např. Věnečky, Sladké mámení, Karetní hra…) – přesně tak, jak ho chceš dát dětem ke čtení.",
        height=400,
        placeholder="Zkopíruj sem původní text..."
    )

with col_right:
    st.subheader("2. Vyber ročník / obtížnost")
    rocnik = st.selectbox(
        "Pro jakou třídu je list určen?",
        ["3. třída", "4. třída", "5. třída"]
    )

    generuj = st.button("📄 Vygenerovat pracovní list pro žáky + metodiku pro učitele")

st.markdown("---")

if generuj:
    if len(vstup_text.strip()) == 0:
        st.error("Nejdřív vlož text 🙃")
    else:
        # vygeneruj textové bloky
        student_sheet = vytvor_pracovni_list(vstup_text, rocnik)
        teacher_sheet = metodicky_list(rocnik, vstup_text)

        st.header("📄 Pracovní list pro žáky (náhled)")
        st.text(student_sheet)

        st.header("📘 Metodický list pro učitele (náhled)")
        st.text(teacher_sheet)

        # udělat .docx soubory
        stud_buf, stud_name = vytvor_docx(student_sheet, "pracovni_list_EdReadAI.docx")
        teach_buf, teach_name = vytvor_docx(teacher_sheet, "metodicky_list_EdReadAI.docx")

        st.download_button(
            label="⬇ Stáhnout pracovní list (.docx)",
            data=stud_buf,
            file_name=stud_name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        st.download_button(
            label="⬇ Stáhnout metodický list (.docx)",
            data=teach_buf,
            file_name=teach_name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

else:
    st.info("Až vložíš text a vybereš ročník, klikni nahoře na tlačítko 📄.")
