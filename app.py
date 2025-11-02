import streamlit as st
from io import BytesIO
from docx import Document
from datetime import datetime
import re
import textwrap

###########################################################
# 0. DATOVÉ PODKLADY: TEXTY, OTÁZKY, RVP, DRAMATIZACE
###########################################################

TEXTY = {
    "Karetní hra": {
        "trida": 3,
        "original": """NÁZEV ÚLOHY: KARETNÍ HRA

1. Herní materiál
60 karet živočichů: 4 komáři, 1 chameleon (žolík), 5 karet od každého z dalších 11 druhů živočichů

2. Popis hry
Všechny karty se rozdají mezi jednotlivé hráče. Hráči se snaží vynášet karty v souladu s pravidly tak, aby se co nejdříve zbavili všech svých karet z ruky. Zahrát lze vždy pouze silnější kombinaci živočichů, než zahrál hráč před vámi.

3. Pořadí karet
Na každé kartě je zobrazen jeden živočich. V rámečku v horní části karty jsou namalováni živočichové, kteří danou kartu přebíjí.
Symbol > označuje, že každý živočich může být přebit větším počtem karet se živočichem stejného druhu.
Příklad: Kosatku přebijí pouze dvě kosatky. Krokodýla přebijí dva krokodýli nebo jeden slon.
Chameleon má ve hře podobnou funkci jako žolík. Lze jej zahrát spolu s libovolnou jinou kartou a počítá se jako požadovaný druh živočicha. Nelze jej hrát samostatně.

4. Průběh hry
• Karty zamíchejte a rozdejte rovnoměrně mezi všechny hráče. Každý hráč si vezme své karty do ruky a neukazuje je ostatním.
• Hráč po levé ruce rozdávajícího hráče začíná. Zahraje (položí na stůl) jednu kartu nebo více stejných karet.
• Hráči hrají po směru hodinových ručiček a snaží se přebít dříve zahrané karty. Mohou to udělat dvěma způsoby:
  – buď položí stejný počet karet živočicha, který přebíjí dříve zahraný druh,
  – nebo použijí stejný druh živočicha jako předchozí hráč, ale položí o jednu kartu více.
• Hráč, který nechce nebo nemůže přebít, řekne „pass“. Tento tah vynechá, ale později může znovu hrát.
• Pokud se hráč dostane na řadu a nikdo nepřebil jeho poslední tah, vezme si všechny karty ze středu stolu stranou a začne nové kolo.
• Vyhrává ten, kdo se jako první zbaví všech svých karet z ruky.
""",
        "dramatizace": [
            "Anička: „Mám pravidla té nové hry a vůbec jim nerozumím!“",
            "Marek: „Ukaž. Tady se píše, kdo přebíjí koho. To je jako kdo je silnější.“",
            "Učitel/učitelka: „Zkusíme to nanečisto. Každý z vás bude jedno zvíře a budeme se ‚přebíjet‘.“",
            "→ Cíl: děti se dostanou do situace a mají motivaci číst pravidla."
        ],
        "otazky_A": [
            {
                "typ": "MC",
                "zadani": "Co je cílem hry?",
                "moznosti": [
                    "A) Mít jako první prázdnou ruku bez karet.",
                    "B) Nasbírat co nejvíce karet.",
                    "C) Křičet nejvíc 'pass'.",
                    "D) Mít co nejvíce stejných zvířat."
                ]
            },
            {
                "typ": "open",
                "zadani": "Kolik hráčů podle tebe může hrát tuto hru najednou? Jak to víš z textu?"
            }
        ],
        "otazky_B": [
            {
                "typ": "open",
                "zadani": "Vysvětli vlastními slovy, co dělá chameleon v této hře."
            },
            {
                "typ": "open",
                "zadani": "Proč je důležité říct 'pass' a nehrát dál, když nemůžu přebít?"
            }
        ],
        "otazky_C": [
            {
                "typ": "open",
                "zadani": "Chtěl/a bys tuhle hru hrát s kamarády? Proč ano / proč ne?"
            }
        ]
    },

    "Sladké mámení": {
        "trida": 5,
        "original": """Češi a čokoláda (zkráceno)

Euroamerickou civilizaci sužuje novodobá epidemie: obezita a s ní spojené choroby metabolismu, srdce a cév. Výrobci cukrovinek po celém světě cítí poptávku po nízkokalorických čokoládách, „light“ mlsání a dietních bonbonech. Až na Českou republiku.

„Češi netouží po nízkokalorickém mlsání, nechtějí mít na obalu velkým písmem napsané kalorie. Říkají: ‚Vím, že hřeším. Je to můj hřích. Nechte mi ho,‘“ říká pracovnice firmy, která sleduje chutě zákazníků.

V laboratořích se vědci snaží najít sladidla, která:
– mají dobrou sladkou chuť,
– nemají nepříjemný pach,
– nezásobují tělo zbytečnými kaloriemi.
Mluví se o náhražkách místo běžného cukru.

Výživoví odborníci upozorňují: není cukr jako cukr. „Jednoduché cukry“ (například hroznový cukr) dodají rychlou energii. „Složité cukry“ (vláknina, škrob) dodávají energii pomalu a nejsou tak škodlivé při běžném mlsání.

V textu je také průzkum toho, jaké čokolády a bonboniéry Češi kupují nejčastěji.
""",
        "dramatizace": [
            "Učitel/učitelka drží dvě tyčinky: „Tahle má hodně cukru a tahle je 'light'. Kterou byste si vybrali a proč?“",
            "Žák 1: „Já tu sladkou, protože je lepší.“",
            "Žák 2: „Já tu light, abych nepřibral.“",
            "→ Cíl: děti začnou přemýšlet o tom, že jídlo má nějaké vlastnosti, ne jen chuť."
        ],
        "otazky_A": [
            {
                "typ": "MC",
                "zadani": "Co je podle textu důvod, proč lidé chtějí nízkokalorické sladkosti?",
                "moznosti": [
                    "A) Protože jsou levnější.",
                    "B) Protože se bojí obezity a nemocí.",
                    "C) Protože lépe chutnají než normální sladkosti.",
                    "D) Protože to přikazuje zákon."
                ]
            },
            {
                "typ": "open",
                "zadani": "Jaký je rozdíl mezi 'jednoduchým cukrem' a 'složitým cukrem' podle textu?"
            }
        ],
        "otazky_B": [
            {
                "typ": "open",
                "zadani": "Co si o Češích myslí firma? Proč podle textu nechtějí 'light' sladkosti?"
            },
            {
                "typ": "open",
                "zadani": "Je podle tebe správné, že některé firmy zkoušejí vyrábět méně kalorické sladkosti?"
            }
        ],
        "otazky_C": [
            {
                "typ": "open",
                "zadani": "Jaké sladkosti by sis koupil/a ty osobně a proč?"
            }
        ]
    },

    "Věnečky": {
        "trida": 4,
        "original": """Ochutnávka zákusků (zkráceno, upraveno pro děti)

Věneček č. 2:
„Tohle je špatné,“ říká hodnotitelka. „Krém je sražený (rozpadlý). Spíš to chutná jako levný tuk místo opravdového krému. Je tam zvláštní chemická pachuť a chybí rum. Těsto je tvrdé a bez pěkného tvaru.“

Věneček č. 3:
„Tady je hodně cítit rum. To je dobře, ale asi to jen schovává to, že jinak skoro není žádná chuť. Krém je zvláštní a těsto je přepečené a dole tvrdé.“

Věneček č. 4:
„Tady konečně vypadá náplň jako opravdový pudink. Je žlutá, jemná a dobrá. Těsto je měkké, trochu křupavé a není spálené. Tohle dělal cukrář, který své řemeslo umí.“

Věneček č. 5:
„Vypadá hezky, ale uvnitř je jen práškový pudink rozmíchaný s vodou, bez chuti. Těsto je staré a tvrdé. Tenhle by u mě neprošel.“

Nakonec hodnotitelka říká, že nejlepší byl věneček číslo 4. Chutnal dobře a vypadal správně. Nejhorší byl věneček, který měl sice pěkný vzhled, ale staré těsto nebo špatnou náplň.
""",
        "dramatizace": [
            "Učitel/učitelka položí na stůl dva prázdné talířky.",
            "Učitel/učitelka: „Představte si, že jsme porota v televizní soutěži dortů. Vaším úkolem je říct, který zákusek je lepší a proč.“",
            "Žák A: „Ten vlevo, protože hezky vypadá!“",
            "Žák B: „Ne, ten vpravo, protože chutná líp!“",
            "→ Cíl: děti pochopí, že hodnocení není jen 'líbí/nelíbí', ale že musí umět říct proč."
        ],
        "otazky_A": [
            {
                "typ": "MC",
                "zadani": "Který věneček byl podle hodnotitelky nejlepší?",
                "moznosti": [
                    "A) Věneček č. 2",
                    "B) Věneček č. 3",
                    "C) Věneček č. 4",
                    "D) Věneček č. 5"
                ]
            },
            {
                "typ": "open",
                "zadani": "Proč nebyl věneček č. 5 podle hodnotitelky dobrý?"
            }
        ],
        "otazky_B": [
            {
                "typ": "open",
                "zadani": "Jaké chyby měla náplň (krém) u špatných věnečků?"
            },
            {
                "typ": "open",
                "zadani": "Co to podle textu znamená, že těsto bylo 'přepečené'?"
            }
        ],
        "otazky_C": [
            {
                "typ": "open",
                "zadani": "Co bys ty považoval/a za důležité při hodnocení zákusku? Vzhled? Chuť? Čerstvost? Proč?"
            }
        ]
    }
}

# RVP ZV cíle pro čtenářskou gramotnost – zjednodušené jádro, které budeme vkládat do metodiky
RVP_INFO = {
    3: [
        "Žák porozumí jednoduchému textu přiměřenému věku.",
        "Žák vyhledává základní informaci v textu.",
        "Žák dokáže vysvětlit důležité slovo jednoduše vlastními slovy."
    ],
    4: [
        "Žák rozliší fakt a názor v textu.",
        "Žák dokáže shrnout hlavní myšlenku textu.",
        "Žák umí vyhledat konkrétní údaj v textu nebo tabulce."
    ],
    5: [
        "Žák rozumí publicistickému/odbornějšímu textu přiměřenému věku.",
        "Žák propojuje informace z více odstavců a vyvozuje důvod.",
        "Žák dokáže vysvětlit význam pojmů souvisejících se zdravím, společností nebo vědou."
    ]
}


###########################################################
# 1. SLOVNÍČEK – TVOJE POŽADOVANÁ NOVÁ LOGIKA
###########################################################

# Slovníček vysvětlení:
# - klíče jsou KOŘENY slov (stačí, aby slovo začínalo tímto kusem)
# - hodnoty jsou dětsky, jednoduše formulovaná vysvětlení
SLOVNIK_VYRAZU = {
    # Karetní hra
    "přebí": "porazit jinou kartu – zahrát kartu, která je silnější.",
    "kombinace": "více stejných karet zahraných najednou.",
    "žolík": "speciální karta, která se může tvářit jako jakákoli jiná karta.",
    "chameleon": "karta, která může být jako jiné zvíře, aby ti pomohla vyhrát.",
    "pravidl": "to, co se při hře smí a nesmí.",
    "kolo": "část hry, kdy hrají všichni postupně.",
    "pass": "hráč řekne ‚pass‘ = tento tah vynechá.",
    "vítěz": "ten, kdo hru vyhraje.",
    "porazit": "být lepší než někdo jiný.",
    "tah": "když jsi na řadě a hraješ kartu.",
    "rozdávaj": "ten, kdo rozdává karty ostatním.",
    "zahrát": "položit kartu na stůl a tím hrát.",

    # Věnečky / cukrařina
    "sražen": "krém se pokazil a má hrudky.",
    "margar": "tuk podobný máslu, ale levnější a často horší chuti.",
    "chemick": "umělá chuť, nepůsobí přirozeně.",
    "pachuť": "chuť, která zůstane nepříjemně v puse.",
    "korpus": "spodní část zákusku – těsto.",
    "receptur": "přesný postup a suroviny podle receptu.",
    "odpalovan": "těsto na věneček/větrník, má být nadýchané a lehké.",
    "přepečen": "pečené moc dlouho → tvrdé / skoro spálené.",
    "nedopečen": "málo pečené → uvnitř ještě skoro syrové.",
    "tvrdé": "těžko se kouše, není měkké.",
    "křupav": "lehce praskne mezi zuby, dělá to křup.",
    "vláčn": "měkké, jemné, není to suché.",
    "zestárl": "už to není čerstvé, je to staré.",
    "náplň": "to, co je uvnitř zákusku (krém).",
    "nadlehčen": "udělaný jemnější a vzdušnější.",
    "katastrof": "něco opravdu hrozného, vůbec se to nepovedlo.",
    "hodnotitel": "člověk, který hodnotí, říká, co je dobré a co ne.",
    "řemesl": "práce, kterou se člověk vyučil (umí to dobře rukama).",
    "výuční": "papír, že člověk je vyučený řemeslu (umí to dělat jako profík).",
    "porota": "lidé, kteří společně rozhodují, co je lepší.",
    "čerstv": "právě udělané, ne staré.",
    "šlehačk": "našlehaná smetana, bílý nadýchaný krém.",
    "pudink": "sladký hustý krém z mléka a škrobu.",
    "rum": "vůně z alkoholu, která se dává do zákusků kvůli chuti.",

    # Sladké mámení
    "obezit": "nezdravě vysoká váha těla.",
    "metabol": "jak tělo mění jídlo na energii.",
    "srdce": "orgán, který pumpuje krev.",
    "cév": "trubičky v těle, kterými proudí krev.",
    "nízkokalor": "málo kalorií (jídlo, po kterém tolik nepřibírám).",
    "kalori": "energie z jídla.",
    "light": "verze s méně cukru nebo tuku.",
    "poptávk": "kolik toho lidé chtějí koupit.",
    "sladidl": "něco, co sladí místo obyčejného cukru.",
    "náhraž": "věc, která nahrazuje něco jiného.",
    "chuť": "jak to chutná v puse.",
    "pach": "jak to voní nebo smrdí.",
    "jednoduch": "rychlý cukr – energie hned.",
    "složité": "pomalý cukr – energie déle vydrží.",
    "vláknin": "část potravy, která pomáhá trávení a zasytí.",
    "škrob": "složitý cukr z potravin jako brambory nebo mouka.",
    "výživ": "to, co souvisí se zdravým jídlem.",
    "analytik": "odborník, který sleduje data a vysvětluje je."
}

# Krátká důležitá slova, která chceme určitě zahrnout i když jsou krátká
DULEZITA_KRATKA_SLOVA = {
    "rum": "vůně z alkoholu, která se dává do zákusků kvůli chuti.",
    "pudink": "sladký hustý krém z mléka a škrobu.",
    "krém": "měkká sladká náplň v dortu nebo zákusku.",
    "cena": "kolik to stojí.",
    "kvalita": "jak moc je to udělané dobře.",
    "těsto": "směs z mouky, vajec atd., ze které se něco peče.",
    "tabulka": "přehled informací v řádcích a sloupcích.",
    "výsledek": "to, jak to dopadlo.",
    "pravidla": "co se smí a nesmí při hře.",
    "hráč": "ten, kdo hraje hru.",
    "tah": "když jsi na řadě ve hře.",
    "pass": "řeknu 'pass' = tento tah vynechám."
}


def vyber_slovicka(text: str, max_slov: int = 14):
    """
    1. Najdeme slova (včetně s diakritikou).
    2. Bereme slova 6+ znaků PLUS všechna 'důležitá krátká slova'.
    3. Vracíme unikátní pořadí výskytu.
    """
    slova = re.findall(r"[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+", text)

    kandidati = []
    for s in slova:
        ciste = s.strip(",.()!?;:„“\"").lower()
        if not ciste:
            continue
        if len(ciste) >= 6:
            kandidati.append(ciste)
        elif ciste in DULEZITA_KRATKA_SLOVA:
            kandidati.append(ciste)

    unik = []
    for s in kandidati:
        if s not in unik:
            unik.append(s)

    return unik[:max_slov]


def najdi_vysvetleni(slovo_lower: str):
    """
    Zkus najít dětské vysvětlení.
    1. přesná shoda v DULEZITA_KRATKA_SLOVA
    2. začíná na některý kořen v SLOVNIK_VYRAZU
    3. jinak None
    """
    if slovo_lower in DULEZITA_KRATKA_SLOVA:
        return DULEZITA_KRATKA_SLOVA[slovo_lower]

    for klic, vyznam in SLOVNIK_VYRAZU.items():
        if slovo_lower.startswith(klic):
            return vyznam

    return None  # nemáme vysvětlení připravené


def priprav_slovnicek(text: str, trida: int, max_slov: int = 14):
    """
    Vrací list dvojic (slovo, vysvětlení nebo prázdná linka).
    Kde vysvětlení nemáme, dáme jen linku k dopsání.
    """
    slova = vyber_slovicka(text, max_slov=max_slov)
    vystup = []
    for slovo in slova:
        vysv = najdi_vysvetleni(slovo)
        if vysv is None:
            vystup.append((slovo, "_______________________________"))
        else:
            vystup.append((slovo, vysv))
    return vystup


###########################################################
# 2. GENEROVÁNÍ OBSAHU PRO ŽÁKA, ŽÁKA LMP A UČITELE
###########################################################

def priprav_text_pro_zaka_podle_tridy(puvodni_text: str, trida: int):
    """
    Zjednoduš variantu textu podle ročníku.
    Teď to děláme hrubě:
    - 3. třída: víc krátkých vět, méně vedlejších vět.
    - 4., 5. třída: necháváme skoro beze změny (už jsme texty ručně zkrátili).
    """
    if trida == 3:
        # velmi lehká úprava: rozdělit dlouhé věty za tečkami a dělat kratší odstavce
        bloky = puvodni_text.split("\n")
        nove_bloky = []
        for b in bloky:
            vety = re.split(r"(?<=[\.\?\!])\s+", b.strip())
            kratke = []
            for v in vety:
                if len(v) > 120:
                    kratke.append(textwrap.fill(v, width=80))
                else:
                    kratke.append(v)
            nove_bloky.append(" ".join(kratke))
        return "\n\n".join(nove_bloky).strip()

    # 4. a 5. třída: vracíme tak, jak jsme to už pro děti upravili ručně
    return puvodni_text.strip()


def priprav_text_LMP(puvodni_text: str, trida: int):
    """
    Verze pro žáky s LMP/SPU:
    - kratší věty,
    - říkáme hodně přímo,
    - vysvětlujeme hodnotící slova.
    """
    # Zjednoduš: rozbijeme věty a přidáme vysvětlující závorky u hodnotících slov
    text = puvodni_text

    # nahrazení typických náročných slov čitelnější verzí
    nahrazky = [
        ("sražený krém", "krém, který se pokazil a má v sobě hrudky"),
        ("chemická pachuť", "divná umělá chuť"),
        ("přepečené", "moc dlouho pečené, je to tvrdé"),
        ("nedopečené", "málo pečené, uvnitř to není hotové"),
        ("kvalita", "jak dobře je to udělané"),
        ("pravidla", "co se smí a nesmí"),
        ("přebyje", "porazí, je silnější"),
        ("obezita", "nezdravě vysoká váha těla"),
        ("nízkokalorické", "s menším množstvím kalorií (méně energie z cukru a tuku)")
    ]
    for hledat, nahradit in nahrazky:
        text = re.sub(hledat, nahradit, text, flags=re.IGNORECASE)

    # zkrátíme dlouhé řádky, aby se to dětem líp četlo
    bloky = text.split("\n")
    nove_bloky = []
    for b in bloky:
        vety = re.split(r"(?<=[\.\?\!])\s+", b.strip())
        kratke_vety = []
        for v in vety:
            if len(v) > 120:
                kratke_vety.append(textwrap.fill(v, width=70))
            else:
                kratke_vety.append(v)
        nove_bloky.append(" ".join(kratke_vety))
    return "\n\n".join(nove_bloky).strip()


def priprav_sebehodnoceni():
    return [
        "🙂 Sebehodnocení žáka:",
        "• Rozuměl/a jsem textu.  😃 / 🙂 / 😐",
        "• Našel/našla jsem odpovědi v textu.  😃 / 🙂 / 😐",
        "• Umím to vysvětlit vlastními slovy.  😃 / 🙂 / 😐",
        "Proč jsem si to tak vybral/a:"
    ]


def priprav_instrukci_k_otazkam():
    return (
        "OTÁZKY JSOU VE TŘECH ÚROVNÍCH:\n"
        "A = najdu odpověď přímo v textu.\n"
        "B = vysvětlím vlastními slovy.\n"
        "C = řeknu svůj názor."
    )


###########################################################
# 3. TVORBA WORD DOKUMENTŮ
###########################################################

def docx_zaci(
    nazev_textu: str,
    trida: int,
    text_pro_zaka: str,
    dramatizace: list,
    otazky_A: list,
    otazky_B: list,
    otazky_C: list,
    slovnicek: list
):
    doc = Document()

    doc.add_heading(f"EdRead AI – Pracovní list ({nazev_textu})", level=1)
    doc.add_paragraph(f"Ročník: {trida}. třída")
    doc.add_paragraph(f"Datum: {datetime.now().strftime('%d.%m.%Y')}")
    doc.add_paragraph("Jméno: __________________________")
    doc.add_paragraph("\n")

    # DRAMATIZACE
    p = doc.add_paragraph("🎭 Úvodní scénka (zahájení hodiny)")
    p.runs[0].bold = True
    for replika in dramatizace:
        doc.add_paragraph("• " + replika)

    doc.add_paragraph("\n")

    # TEXT
    p = doc.add_paragraph("📖 Text k práci s porozuměním")
    p.runs[0].bold = True
    for odst in text_pro_zaka.split("\n"):
        if odst.strip():
            doc.add_paragraph(odst.strip())

    doc.add_paragraph("\n")

    # SLOVNÍČEK
    if slovnicek:
        p = doc.add_paragraph("📚 Slovníček pojmů")
        p.runs[0].bold = True
        doc.add_paragraph(
            "Podívej se na slovo a přečti si vysvětlení. "
            "Když je tam jen prázdná čára, doplň si to vlastními slovy s paní učitelkou / panem učitelem."
        )
        for slovo, vyznam in slovnicek:
            doc.add_paragraph(f"• {slovo} = {vyznam}")
        doc.add_paragraph("")

    # OTÁZKY
    doc.add_paragraph("")
    p = doc.add_paragraph("❓ Otázky k textu")
    p.runs[0].bold = True
    doc.add_paragraph(priprav_instrukci_k_otazkam())

    doc.add_paragraph("\nA) Porozumění textu (vyhledej v textu)")
    for i, ot in enumerate(otazky_A, start=1):
        if ot["typ"] == "MC":
            doc.add_paragraph(f"{i}. {ot['zadani']}")
            for moz in ot["moznosti"]:
                doc.add_paragraph("   " + moz)
            doc.add_paragraph("   Odpověď: __________")
        else:
            doc.add_paragraph(f"{i}. {ot['zadani']}")
            doc.add_paragraph("   Odpověď: ______________________________")
            doc.add_paragraph("")

    doc.add_paragraph("\nB) Přemýšlení o textu (vysvětli vlastními slovy)")
    for j, ot in enumerate(otazky_B, start=1):
        doc.add_paragraph(f"{j}. {ot['zadani']}")
        doc.add_paragraph("   ______________________________")
        doc.add_paragraph("   ______________________________")
        doc.add_paragraph("")

    doc.add_paragraph("\nC) Tvůj názor")
    for k, ot in enumerate(otazky_C, start=1):
        doc.add_paragraph(f"{k}. {ot['zadani']}")
        doc.add_paragraph("   ______________________________")
        doc.add_paragraph("   ______________________________")
        doc.add_paragraph("")

    # SEBEHODNOCENÍ
    doc.add_paragraph("")
    p = doc.add_paragraph("📝 Sebehodnocení")
    p.runs[0].bold = True
    for radek in priprav_sebehodnoceni():
        doc.add_paragraph(radek)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


def docx_zaci_LMP(
    nazev_textu: str,
    trida: int,
    text_pro_LMP: str,
    dramatizace: list,
    otazky_A: list,
    otazky_B: list,
    otazky_C: list,
    slovnicek: list
):
    doc = Document()

    doc.add_heading(f"EdRead AI – Pracovní list (podpůrná varianta)", level=1)
    doc.add_paragraph(f"Ročník: {trida}. třída – úprava pro žáky s podporou (LMP/SPU)")
    doc.add_paragraph(f"Datum: {datetime.now().strftime('%d.%m.%Y')}")
    doc.add_paragraph("Jméno: __________________________")
    doc.add_paragraph("\n")

    # DRAMATIZACE
    p = doc.add_paragraph("🎭 Začátek hodiny (zahřátí)")
    p.runs[0].bold = True
    for replika in dramatizace:
        doc.add_paragraph("• " + replika)

    doc.add_paragraph("\n")

    # TEXT zjednodušený
    p = doc.add_paragraph("📖 Text (zjednodušená verze)")
    p.runs[0].bold = True
    for odst in text_pro_LMP.split("\n"):
        if odst.strip():
            doc.add_paragraph(odst.strip())

    doc.add_paragraph("\n")

    # SLOVNÍČEK
    if slovnicek:
        p = doc.add_paragraph("📚 Slovníček slov")
        p.runs[0].bold = True
        doc.add_paragraph(
            "Slova, která můžou být těžší. "
            "Když je tam jen prázdná čára, doplníme spolu."
        )
        for slovo, vyznam in slovnicek:
            doc.add_paragraph(f"• {slovo} = {vyznam}")
        doc.add_paragraph("")

    # OTÁZKY – jednodušší rozvržení (A+B dohromady)
    doc.add_paragraph("")
    p = doc.add_paragraph("❓ Otázky k textu")
    p.runs[0].bold = True

    # A otázky:
    doc.add_paragraph("A) Najdu to přímo v textu")
    for i, ot in enumerate(otazky_A, start=1):
        doc.add_paragraph(f"{i}. {ot['zadani']}")
        if ot["typ"] == "MC":
            for moz in ot["moznosti"]:
                doc.add_paragraph("   " + moz)
            doc.add_paragraph("   Odpověď: __________")
        else:
            doc.add_paragraph("   Odpověď: ______________________________")

    # B otázky:
    doc.add_paragraph("\nB) Řeknu to svými slovy")
    for j, ot in enumerate(otazky_B, start=1):
        doc.add_paragraph(f"{j}. {ot['zadani']}")
        doc.add_paragraph("   ______________________________")
        doc.add_paragraph("")

    # C otázky:
    doc.add_paragraph("\nC) Můj názor")
    for k, ot in enumerate(otazky_C, start=1):
        doc.add_paragraph(f"{k}. {ot['zadani']}")
        doc.add_paragraph("   ______________________________")
        doc.add_paragraph("")

    # Sebehodnocení
    doc.add_paragraph("")
    p = doc.add_paragraph("📝 Jak mi to šlo")
    p.runs[0].bold = True
    for radek in priprav_sebehodnoceni():
        doc.add_paragraph(radek)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


def docx_metodika(
    nazev_textu: str,
    trida: int,
    dramatizace: list,
    otazky_A: list,
    otazky_B: list,
    otazky_C: list
):
    doc = Document()

    doc.add_heading(f"METODICKÝ LIST PRO UČITELE – {nazev_textu}", level=1)
    doc.add_paragraph(f"Ročník: {trida}. třída")
    doc.add_paragraph(f"Datum přípravy: {datetime.now().strftime('%d.%m.%Y')}")
    doc.add_paragraph("\n")

    # CÍL HODINY
    p = doc.add_paragraph("1. Cíl hodiny")
    p.runs[0].bold = True
    doc.add_paragraph(
        "- rozvoj čtenářské gramotnosti (porozumění textu, vyhledávání informace v textu),\n"
        "- rozlišení faktu a názoru,\n"
        "- schopnost popsat význam slov vlastními slovy,\n"
        "- základní sebehodnocení žáka."
    )

    # RVP PROPOJENÍ
    p = doc.add_paragraph("2. Vazba na RVP ZV (jazyk a jazyková komunikace)")
    p.runs[0].bold = True
    if trida in RVP_INFO:
        for bod in RVP_INFO[trida]:
            doc.add_paragraph("• " + bod)
    else:
        doc.add_paragraph("• Žák rozvíjí porozumění textu přiměřenému věku a dokáže o něm mluvit.")

    # PRŮBĚH HODINY
    p = doc.add_paragraph("3. Doporučený průběh hodiny (45 min)")
    p.runs[0].bold = True
    doc.add_paragraph(
        "a) MOTIVACE / DRAMATIZACE (5–7 min)\n"
        "   - Pracujte s úvodní scénkou. Žáci si 'zahrají situaci', aby měli motivaci text číst.\n"
        "b) ČTENÍ TEXTU (10–15 min)\n"
        "   - Individuální tiché čtení nebo čtení po odstavcích nahlas.\n"
        "   - Vysvětlení slov ze Slovníčku.\n"
        "c) PRÁCE S OTÁZKAMI (15 min)\n"
        "   - A = najdi informaci (kontrola porozumění).\n"
        "   - B = popiš vlastními slovy (aktivní zpracování).\n"
        "   - C = názor / postoj (osobní zapojení).\n"
        "d) SEBEHODNOCENÍ (5 min)\n"
        "   - žák zhodnotí, jak rozuměl textu a co pro něj bylo těžké.\n"
        "   - rozvoj metakognice (žák si uvědomuje svoje učení)."
    )

    # DRAMATIZACE PRO UČITELE
    p = doc.add_paragraph("4. Úvodní dramatizace (zahájení hodiny)")
    p.runs[0].bold = True
    doc.add_paragraph(
        "Toto čteme/předvádíme ještě PŘED čtením textu. Cíl: vtáhnout žáky do tématu."
    )
    for replika in dramatizace:
        doc.add_paragraph("• " + replika)

    # OTÁZKY – přehled
    p = doc.add_paragraph("5. Otázky k textu (strukturace A / B / C)")
    p.runs[0].bold = True

    doc.add_paragraph("A) Najdi v textu (porozumění, faktická kontrola)")
    for ot in otazky_A:
        doc.add_paragraph("• " + ot["zadani"])

    doc.add_paragraph("\nB) Vysvětli vlastními slovy (zpracování informace)")
    for ot in otazky_B:
        doc.add_paragraph("• " + ot["zadani"])

    doc.add_paragraph("\nC) Můj názor (postoj, hodnocení)")
    for ot in otazky_C:
        doc.add_paragraph("• " + ot["zadani"])

    # POZNÁMKA K DIFERENCIACI
    p = doc.add_paragraph("6. Diferenciace a podpora (LMP / SPU)")
    p.runs[0].bold = True
    doc.add_paragraph(
        "- K dispozici je zjednodušená verze textu pro žáky s LMP/SPU.\n"
        "- V této verzi jsou:\n"
        "   • kratší věty,\n"
        "   • vysvětlená náročná slova přímo v textu,\n"
        "   • méně podnětů na stránce,\n"
        "   • otázky rozdělené jednodušeji.\n"
        "- Žák může odpovídat ústně nebo pomocí klíčových slov namísto celých vět."
    )

    # DIGITÁLNÍ POZNÁMKA (EdRead AI)
    p = doc.add_paragraph("7. Digitální varianta (EdRead AI)")
    p.runs[0].bold = True
    doc.add_paragraph(
        "Stejný text a otázky je možné zadat on-line. "
        "Aplikace EdRead AI vygeneruje pracovní list, slovníček a metodiku. "
        "Podporuje dvě úrovně: běžnou a upravenou (LMP/SPU). "
        "Výstupy jsou ve Wordu, aby je bylo možné okamžitě použít ve škole."
    )

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


###########################################################
# 4. STREAMLIT UI
###########################################################

st.set_page_config(
    page_title="EdRead AI – prototyp",
    page_icon="📖",
    layout="centered"
)

st.title("📖 EdRead AI – prototyp nástroje pro rozvoj čtenářské gramotnosti")
st.caption("Generuje pracovní list pro žáky, upravenou variantu pro LMP/SPU a metodický list pro učitele. V souladu s RVP ZV.")

# Volba textu
nazev_textu = st.selectbox(
    "Vyber text:",
    list(TEXTY.keys())
)

data = TEXTY[nazev_textu]
trida = data["trida"]

st.write(f"Zvolený text: **{nazev_textu}** (cílově {trida}. třída)")

# Původní text pro ten ročník
puvodni_text = data["original"]

# Připrav text pro běžnou skupinu a pro LMP/SPU
text_pro_zaka = priprav_text_pro_zaka_podle_tridy(puvodni_text, trida)
text_pro_LMP = priprav_text_LMP(puvodni_text, trida)

# Připrav slovníček z původního textu
slovnicek = priprav_slovnicek(puvodni_text, trida, max_slov=14)

# Zobraz náhled slovníčku přímo v aplikaci (jen info pro učitele)
with st.expander("Náhled slovníčku (takto půjde do pracovního listu)"):
    for slovo, vyznam in slovnicek:
        st.write(f"- {slovo} = {vyznam}")

# OTÁZKY
otazky_A = data["otazky_A"]
otazky_B = data["otazky_B"]
otazky_C = data["otazky_C"]
dramatizace = data["dramatizace"]

st.markdown("---")
st.subheader("⬇ Generování výstupů (Word .docx)")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 Stáhnout pracovní list (žáci)"):
        bio_student = docx_zaci(
            nazev_textu,
            trida,
            text_pro_zaka,
            dramatizace,
            otazky_A,
            otazky_B,
            otazky_C,
            slovnicek
        )
        st.download_button(
            label="💾 Uložit pracovní list (žáci)",
            data=bio_student,
            file_name=f"pracovni_list_{nazev_textu}_{trida}trida.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

with col2:
    if st.button("📘 Stáhnout pracovní list (LMP/SPU)"):
        bio_student_lmp = docx_zaci_LMP(
            nazev_textu,
            trida,
            text_pro_LMP,
            dramatizace,
            otazky_A,
            otazky_B,
            otazky_C,
            slovnicek
        )
        st.download_button(
            label="💾 Uložit pracovní list (LMP/SPU)",
            data=bio_student_lmp,
            file_name=f"pracovni_list_{nazev_textu}_{trida}trida_LMP.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

with col3:
    if st.button("🧑‍🏫 Stáhnout metodiku pro učitele"):
        bio_teacher = docx_metodika(
            nazev_textu,
            trida,
            dramatizace,
            otazky_A,
            otazky_B,
            otazky_C
        )
        st.download_button(
            label="💾 Uložit metodický list",
            data=bio_teacher,
            file_name=f"metodika_{nazev_textu}_{trida}trida.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

st.markdown("---")
st.markdown("Tento prototyp je určen k diplomové práci: rozvoj čtenářské gramotnosti na 1. stupni ZŠ pomocí AI podpory (EdRead AI).")
