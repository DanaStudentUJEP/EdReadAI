import streamlit as st
from docx import Document
from docx.shared import Pt, Inches
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import textwrap
import re
import datetime

############################################
# 1) Pomocné funkce pro text
############################################

def ocisti_text(vstup):
    """Základní čištění: odstraní vícenásobné mezery, sjednotí nové řádky."""
    if not vstup:
        return ""
    t = vstup.replace("  ", " ").replace("\t", " ").strip()
    return re.sub(r"\n{3,}", "\n\n", t)

def zkrat_text_pro_rocnik(text, rocnik):
    """
    Lehké zjednodušení formulací pro mladší ročníky.
    Neprzníme obsah, jen drobně lámeme věty na kratší úseky
    u 3. a 4. třídy.
    """
    text = ocisti_text(text)

    if rocnik in ["3", "4", "3. třída", "4. třída"]:
        # vložíme tečky po delších souvětích, aby se to ve Wordu lépe četlo
        text = re.sub(r", ale", ". Ale", text)
        text = re.sub(r", protože", ". Protože", text)
        text = re.sub(r", že", ". Říká, že", text)
    return text

############################################
# 2) Dramatizace pro úvod hodiny
############################################

def dramatizace_template(rocnik):
    """
    Krátká scénka 'zahřívač' před čtením.
    Má vtáhnout žáky do tématu.
    Přizpůsobíme tón věku.
    """
    if rocnik in ["3", "3. třída"]:
        return (
            "DRAMATIZACE (začátek hodiny)\n"
            "Učitelka: „Dneska budeme hodnotit věnečky jako opravdoví porotci.“\n"
            "Tonda: „Můžu být ten, co ochutnává?“\n"
            "Bára: „A můžu říkat, co je dobré a co ne?“\n"
            "Učitelka: „Ano. Ale pozor – musíte to umět vysvětlit. Ne jen 'fuj' nebo 'mňam'.“\n"
            "→ Cíl: děti si zahrají roli porotců. Přepnou se do módu ‚hodnotím a zdůvodňuju‘.\n"
        )
    if rocnik in ["4", "4. třída"]:
        return (
            "DRAMATIZACE (začátek hodiny)\n"
            "Učitel: „Představte si, že jste v porotě televizní soutěže zákusků.“\n"
            "Ema: „Takže můžu říct, že krém je hrudkovitý a že bys měl vrátit výuční list?“\n"
            "Učitel: „Teoreticky ano… ale hlavně musíš říct PROČ si to myslíš.“\n"
            "→ Cíl: žáci chápou, že nestačí říct názor. Musí ho umět obhájit.\n"
        )
    else:
        return (
            "DRAMATIZACE (začátek hodiny)\n"
            "Učitel: „Budeme hodnotit kvalitu zákusků jako skuteční inspektoři.“\n"
            "Žák 1: „To fakt existuje? Že někdo ochutnává zákusky jako práce?“\n"
            "Učitel: „Ano. A musí to umět popsat odborně, ne jen říct 'dobrý' / 'nedobrý'.“\n"
            "→ Cíl: uvědomit si roli hodnotitele a jazyk hodnocení (slovní zásoba, argumenty).\n"
        )

############################################
# 3) Slovníček – výběr a jednoduché definice
############################################

# Předpřipravené dětské definice obtížných slov, které se často objevují
SLOVNIK_ZNAMA_SLOVA = {
    "výuční list": "papír (diplom), že člověk vystudoval obor, třeba cukrář",
    "sražený krém": "krém, který se nepovedl – má hrudky, není hladký",
    "margarín": "levnější tuk podobný máslu",
    "pachuť": "nepříjemná chuť v puse, která tam zůstane",
    "korpus": "spodek nebo tělo dortu / zákusku – to upečené těsto",
    "odpalované těsto": "těsto na větrníky nebo věnečky, má být duté a nadýchané",
    "receptura": "přesný postup + suroviny, jak se to má správně dělat",
    "pudink": "sladký krém z mléka a prášku, často žlutý",
    "rum": "vůně / příchuť, dává se někdy do krému pro chuť",
    "šlehačka": "našlehaná smetana, bílý nadýchaný krém",
    "průmyslově vyráběné": "dělá se to ve velké továrně, ne doma ručně",
    "porota": "lidi, kteří hodnotí a rozhodují, co je nejlepší",
    "známka": "hodnocení jako ve škole (1 je nejlepší)",
}

def najdi_kandidat_slov(text):
    """
    Najde možná složitější výrazy:
    - víceslovné odborné výrazy (např. 'sražený krém', 'odpalované těsto')
    - delší slova (8+ znaků)
    Pak to přefiltrujeme, aby to nebyly úplné nesmysly typu 'správným'.
    """
    kandidati = set()

    # ručně zkusíme vytáhnout dvouslovné spojení typu "xxx xxx"
    dvojice = re.findall(r"([A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+ [A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+)", text)
    for d in dvojice:
        low = d.lower()
        if any(kl in low for kl in ["krém", "těsto", "výuční", "pachuť"]):
            kandidati.add(low.strip())

    # delší jednotlivá slova
    slova = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)
    for s in slova:
        s_low = s.lower()
        if len(s_low) >= 8:
            kandidati.add(s_low)

    # Doplníme naše známé (aby tam byly jistě klíčové výrazy)
    for k in SLOVNIK_ZNAMA_SLOVA.keys():
        if k in text.lower():
            kandidati.add(k)

    # vyčistíme, aby tam nebyly běžné/lehké tvary
    pryc = {"správným", "maximálně", "dalšího", "ochutnejte"}
    konec = [w for w in kandidati if w not in pryc]

    # vezmeme max 10
    konec = konec[:10]
    return konec

def vysvetli_slovo(slovo):
    """
    Vrátí jednoduché vysvětlení pro děti.
    Pokud máme připravené, vezmeme ho. Jinak dáme čáru k doplnění.
    """
    if slovo in SLOVNIK_ZNAMA_SLOVA:
        return SLOVNIK_ZNAMA_SLOVA[slovo]
    # pokusíme se chytnout dvouslovné spojení jako 'sražený krém'
    for k in SLOVNIK_ZNAMA_SLOVA:
        if slovo.strip().lower() == k.lower():
            return SLOVNIK_ZNAMA_SLOVA[k]

    return "_______________________________"

def vytvor_slovnicek_pro_text(text):
    slova = najdi_kandidat_slov(text)
    polozky = []
    for s in slova:
        polozky.append((s, vysvetli_slovo(s)))
    return polozky

############################################
# 4) Otázky pro žáky
############################################

def otazky_pro_zaky(rocnik):
    """
    Vrací strukturované otázky (A / B / C),
    které se zapíšou do pracovního listu.
    Tyhle otázky jsou univerzální k hodnoticímu textu typu „Věnečky“,
    ale fungují i pro jiný hodnoticí/porovnávací text.
    """
    qA = [
        "1) Najdi v textu: Který výrobek (věneček / sladkost / výrobek) dopadl NEJLÉPE? Napiš číslo nebo název.",
        "2) Najdi v textu: Který výrobek dopadl NEJHŮŘE? Proč?",
        "3) Které tvrzení podle textu NENÍ pravda?\n   A) Hodnotitel(ka) vysvětluje, proč se jí něco nelíbí.\n   B) V textu se porovnává kvalita různých výrobků.\n   C) V textu je recept krok za krokem, jak věneček upéct doma.",
    ]

    qB = [
        "4) Vysvětli vlastními slovy: Co znamená, že krém je 'sražený'?",
        "5) Proč někdo v textu říká, že by 'vrátil výuční list'? Co tím chce říct?",
        "6) Najdi ve svém textu:\n   a) jednu větu, která je FAKT (dá se ověřit),\n   b) jednu větu, která je NÁZOR (pocit, hodnocení).",
    ]

    qC = [
        "7) Souhlasíš s hodnocením (kdo je nejlepší)? Proč ano / proč ne?",
        "8) Který z hodnocených výrobků bys TY chtěl/a ochutnat a proč?",
    ]

    sebehod = (
        "SEBEHODNOCENÍ ŽÁKA\n"
        "Označ, jak se cítíš po práci s textem:\n\n"
        "Rozuměl/a jsem textu.                😃 / 🙂 / 😐\n"
        "Našel/la jsem odpovědi v textu.       😃 / 🙂 / 😐\n"
        "Umím to říct vlastními slovy.         😃 / 🙂 / 😐\n"
    )

    return qA, qB, qC, sebehod

############################################
# 5) Metodický list pro učitele
############################################

def metodicky_list(rocnik):
    """
    Stručný metodický list (1 strana),
    který se uloží za pracovní list do stejného Wordu.
    Obsahuje:
    - cíle hodiny
    - vazbu na RVP ZV
    - doporučený průběh
    - co sledovat u žáků
    """
    return (
        "METODICKÝ LIST PRO UČITELE\n\n"
        "Téma hodiny:\n"
        "Porozumění hodnoticímu / publicistickému textu (ochutnávka, porota, srovnávání kvality výrobků).\n\n"
        "Ročník: " + rocnik + ". třída\n\n"
        "Vazba na RVP ZV (Jazyk a jazyková komunikace – Český jazyk a literatura):\n"
        "• Žák porozumí smyslu přečteného textu.\n"
        "• Žák vyhledává konkrétní informaci v textu.\n"
        "• Žák rozlišuje fakt a názor v jednoduchém publicistickém / hodnoticím textu.\n"
        "• Žák dokáže stručně formulovat vlastní názor a zdůvodnit ho.\n\n"
        "Cíle hodiny:\n"
        "1. Žák rozumí, co se v textu hodnotí a proč.\n"
        "2. Žák umí dohledat konkrétní údaj (nejlepší, nejhorší, cena…).\n"
        "3. Žák dokáže vysvětlit odborné/slabě odborné pojmy vlastními slovy ('sražený krém', 'výuční list').\n"
        "4. Žák rozezná rozdíl mezi FAKTEM a NÁZOREM.\n"
        "5. Žák sebereflektuje – jak tomu rozuměl, co pro něj bylo těžké.\n\n"
        "Doporučený průběh (45 min):\n"
        "1) MOTIVACE / DRAMATIZACE (cca 5 min)\n"
        "   - Učitel přečte dramatizaci nahlas s dětmi v rolích.\n"
        "   - Děti pochopí situaci: někdo hodnotí kvalitu výrobku.\n\n"
        "2) ČTENÍ TEXTU (cca 10–15 min)\n"
        "   - Společné čtení nebo čtení po dvojicích.\n"
        "   - Učitel vysvětluje těžší slova pomocí slovníčku.\n"
        "   - Obrázková opora: ukázka věnečku, medaile 1.–3. místo.\n\n"
        "3) PRÁCE S OTÁZKAMI (cca 15 min)\n"
        "   A – najdi informaci v textu,\n"
        "   B – vysvětli/zdůvodni,\n"
        "   C – tvůj názor.\n"
        "   Učitel sleduje, jestli žák cituje text, nebo si vymýšlí mimo text.\n\n"
        "4) SEBEHODNOCENÍ (cca 5 min)\n"
        "   - Žáci vyberou smajlík a řeknou 1 větou proč.\n\n"
        "Diferenciace / podpora:\n"
        "• Slabší čtenář může text dostat se zvýrazněnými (tučně) klíčovými větami.\n"
        "• Silnější čtenář může doplnit vlastní mini-recenzi: 'Jak bych hodnotil já'.\n\n"
        "Poznámka k evaluaci:\n"
        "Tyto výstupy (otázky A/B/C + sebehodnocení) slouží jako doklad rozvoje čtenářské gramotnosti pro praxi a pro diplomovou práci.\n"
    )

############################################
# 6) Obrázková opora – generování obrázků
############################################

def nakresli_venecek_obr():
    """
    Vytvoří jednoduchý obrázek 'věnečku':
    žlutý střed + béžový kroužek. Je to simbolická opora, ne výtvarné dílo :-)
    Vrací Pillow Image.
    """
    img = Image.new("RGB", (300, 200), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # kroužek (těsto)
    draw.ellipse((60, 40, 240, 180), fill=(230, 200, 150), outline=(130, 90, 40), width=4)

    # střed (krém)
    draw.ellipse((110, 90, 190, 160), fill=(255, 235, 120), outline=(180, 150, 60), width=3)

    # popisek
    draw.text((70, 10), "Věneček (pohled shora)", fill=(0, 0, 0))
    return img

def nakresli_medaile_obr():
    """
    Jednoduchá medaile '1. místo' – vizuální podpora žebříčku kvality.
    """
    img = Image.new("RGB", (300, 200), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.ellipse((80, 30, 220, 170), fill=(255, 215, 0), outline=(150, 120, 0), width=4)
    draw.text((130, 85), "1.", fill=(0, 0, 0))
    draw.text((110, 150), "místo", fill=(0, 0, 0))

    return img

############################################
# 7) Generování Word dokumentu
############################################

def vytvor_word_dokument(
    text_zaky,
    rocnik,
    dramatizace,
    slovnicek,
    qA, qB, qC, sebehodnoceni,
    metodika_text
):
    """
    Sestaví finální .docx do paměti (BytesIO) a vrátí ho.
    """
    doc = Document()

    # Styl základního textu (písmo, velikost)
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(12)

    # HLAVIČKA
    nadpis = doc.add_heading(f"{rocnik}. třída · Pracovní list (EdRead AI)", level=1)
    nadpis.alignment = 0
    info_radek = doc.add_paragraph(
        "Jméno: ______________________      Třída: __________      Datum: __________"
    )
    info_radek.space_after = Pt(12)

    # DRAMATIZACE
    doc.add_heading("🎭 Úvodní scénka (začátek hodiny)", level=2)
    for line in dramatizace.split("\n"):
        doc.add_paragraph(line)

    # O ČEM JE TEXT
    doc.add_heading("📖 O čem je text", level=2)
    doc.add_paragraph(
        "V textu někdo hodnotí výrobky (třeba zákusky) a vysvětluje, co je dobré a co je špatné. "
        "Tvým úkolem je pochopit hodnocení a umět ho říct vlastními slovy."
    )

    # TEXT K PŘEČTENÍ
    doc.add_heading("📖 Text k přečtení", level=2)
    text_clean = zkrat_text_pro_rocnik(text_zaky, rocnik)
    for odst in text_clean.split("\n"):
        if odst.strip():
            p = doc.add_paragraph(odst.strip())
            p.space_after = Pt(6)

    # SLOVNÍČEK
    doc.add_heading("📚 Slovníček pojmů (pomoc při čtení)", level=2)
    doc.add_paragraph("Tahle slova mohou být těžší. Vysvětlení je dětsky a jednoduše:")
    for slovo, vysv in slovnicek:
        para = doc.add_paragraph(style="List Bullet")
        para.add_run(f"{slovo} = {vysv}")

    # OBRÁZKOVÁ OPORA
    doc.add_heading("🖼 Obrázková opora k textu", level=2)
    doc.add_paragraph("Pomůcka: Jak vypadá věneček a co znamená '1. místo' v hodnocení:")

    venecek_img = nakresli_venecek_obr()
    medaile_img = nakresli_medaile_obr()

    # Uložíme provizorně do paměti a vložíme
    venecek_bytes = BytesIO()
    venecek_img.save(venecek_bytes, format="PNG")
    venecek_bytes.seek(0)
    doc.add_picture(venecek_bytes, width=Inches(2.0))

    medaile_bytes = BytesIO()
    medaile_img.save(medaile_bytes, format="PNG")
    medaile_bytes.seek(0)
    doc.add_picture(medaile_bytes, width=Inches(2.0))

    # OTÁZKY – A / B / C
    doc.add_heading("🧠 OTÁZKY A – Rozumím textu", level=2)
    for q in qA:
        doc.add_paragraph(q, style="List Number")

    doc.add_heading("💭 OTÁZKY B – Př Nacházím a vysvětluji", level=2)
    for q in qB:
        doc.add_paragraph(q, style="List Number")

    doc.add_heading("🌟 OTÁZKY C – Můj názor", level=2)
    for q in qC:
        doc.add_paragraph(q, style="List Number")

    # SEBEHODNOCENÍ
    doc.add_heading("📝 Sebehodnocení žáka", level=2)
    for line in sebehodnoceni.split("\n"):
        doc.add_paragraph(line)

    # ODDĚLENÍ STRAN
    doc.add_page_break()

    # METODICKÝ LIST PRO UČITELE
    doc.add_heading("📘 METODICKÝ LIST PRO UČITELE", level=1)
    for odst in metodika_text.split("\n"):
        if odst.strip():
            p = doc.add_paragraph(odst.strip())
            p.space_after = Pt(6)
        else:
            doc.add_paragraph("")

    # ULOŽENÍ DO PAMĚTI
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


############################################
# 8) STREAMLIT UI
############################################

st.set_page_config(page_title="EdRead AI – pracovní list", layout="wide")

st.title("EdRead AI – generátor pracovních listů")
st.write("Prototyp pro diplomovou práci: rozvoj čtenářské gramotnosti podle RVP ZV.")

st.markdown("**Krok 1.** Vlož text (např. Věnečky).")
vstup_text = st.text_area("Vstupní text pro žáky", height=350, placeholder="Sem vlož celý text, se kterým chcete pracovat...")

st.markdown("**Krok 2.** Vyber ročník (kvůli slovní zásobě a typu otázek).")
rocnik = st.selectbox("Ročník", ["3", "4", "5"])

if st.button("Vytvořit pracovní list (.docx)"):
    if not vstup_text.strip():
        st.error("Nejdřív vlož text 🙂")
    else:
        # připravíme části
        draz = dramatizace_template(rocnik)
        slovnik = vytvor_slovnicek_pro_text(vstup_text)
        qA, qB, qC, sebehod = otazky_pro_zaky(rocnik)
        metodika = metodicky_list(rocnik)

        # vytvořit word
        word_bytes = vytvor_word_dokument(
            text_zaky=vstup_text,
            rocnik=rocnik,
            dramatizace=draz,
            slovnicek=slovnik,
            qA=qA, qB=qB, qC=qC,
            sebehodnoceni=sebehod,
            metodika_text=metodika
        )

        # pojmenujeme soubor
        dnes = datetime.date.today().isoformat()
        filename = f"pracovni_list_EdReadAI_{rocnik}trida_{dnes}.docx"

        st.success("Hotovo. Stáhni si pracovní list a můžeš tisknout 👍")
        st.download_button(
            label="⬇️ Stáhnout .docx",
            data=word_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        st.info("Soubor obsahuje: dramatizaci, text k práci, slovníček, otázky A/B/C, sebehodnocení a metodický list pro učitele (RVP ZV). Obrázková opora je vložena automaticky.")
