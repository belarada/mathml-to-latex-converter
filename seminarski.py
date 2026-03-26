import re, sys

# mapa koja preslikava tag u mathml-u u par u latexu - neophodno je da bude par, jer u latexu imamo otvarajuci i zatvarajuci deo
# kroz program cemo otvaranje i zatvaranje resiti koriscenjem steka
TAG_MAP = {
    "mfrac":      ("\\frac{", "}{"),
    "msup":       ("^{",      "}"),
    "msub":       ("_{",      "}"),
    "msubsup":    ("_{",      "}^{}"),
    "msqrt":      ("\\sqrt{", "}"),
    "mtable":     ("\\begin{bmatrix}", "\\end{bmatrix}"),
    "mtd":        ("",        " & "),
    "mtr":        ("",        " \\\\ "),
    # ovde je drugi element u paru "" jer nema zatvaranja u latexu
    "msin":       ("\\sin",   ""),
    "mcos":       ("\\cos",   ""),
    "munder":     ("\\underbrace{", "}"),
    "mover":      ("\\overrightarrow{", "}"),
    "munderover": ("_{",      "}^{}")
}

# mapa koja ce entitete slikati u odgovarajuci latex format
ENTITET_MAP = {
    "&sum;":           "\\sum",
    "&int;":           "\\int",
    "&pi;":            "\\pi",
    "&theta;":         "\\theta",
    "&rarr;":          "\\rightarrow",
    "&times;":         "\\times",
    "&sdot;":          "\\cdot",
    "&ApplyFunction;": "",
    "&infin;":         "\\infty",
    "&alpha;":         "\\alpha",
    "&beta;":          "\\beta",
}

# primetiti da sam ovde umesto mape koristila listu - razlog lezi u hijerarhiji koja u ovom slucaju postoji
# naime, vrlo je vazno da ENTITET prepoznamo pre IDENT
PRAVILA = [
    ("OTVARAJUCI_TAG", r"<[a-zA-Z]+[^>]*>"),
    ("ZATVARAJUCI_TAG", r"</[a-zA-Z]+>"),
    ("ENTITET",         r"&[a-zA-Z]+;"),
    ("BROJ",            r"\d+"),
    ("IDENT",           r"[a-zA-Z]+"),
    ("OPERATOR",        r"[+\-*/=!]"),
    ("PRAZNO",          r"\s+"),
    ("SIMBOL",          r"[(){}[\]]")
]

# ulazni tekst u mathml tokenizujemo
def tokenizuj(ulazni_tekst):
    # pravimo listu parova i kompajliranog regexa koje smo definisali iznad
    kompajlirana = [(tip, re.compile(pat)) for tip, pat in PRAVILA]
    pozicija = 0
    # lista prepoznatih tokena
    tokeni = []
    while pozicija < len(ulazni_tekst):
        pronadjen = False
        # za svaki od napravljenih paterna unutar liste kompajlirana proveravamo da li trenutni string zadovoljava taj patern
        for tip, pattern in kompajlirana:
            m = pattern.match(ulazni_tekst, pozicija)
            if m:
                pronadjen = True
                # beline cemo ignorisati, jer u latexu beline nisu vazne
                if tip != "PRAZNO":
                    tokeni.append((tip, m.group()))
                # nastavljamo od pozicije kraja pronadjenog paterna
                pozicija = m.end()
                break
        if not pronadjen:
            tokeni.append(("NEPOZNATO", ulazni_tekst[pozicija]))
            # nastavljamo od sledece pozicije jer nismo prepoznali nijedan patern za dati string
            pozicija += 1
    return tokeni

# pomocna funkcija, nije lose da nam program ispise i koje tokene smo sve prepoznali
def ispisi_tokene(tokeni):
    print(f"{'Br.':<5} {'Tip':<20} {'Vrednost'}")
    print("-" * 50)
    for i, (tip, vrednost) in enumerate(tokeni, 1):
        print(f"{i:<5} {tip:<20} {vrednost}")


def izvuci_ime_taga(tag_str):
    m = re.match(r"<([a-zA-Z]+)", tag_str)
    return m.group(1) if m else ""


def izvuci_atribut(tag_str, naziv):
    # f jer zelimo da se naziv menja sa konkretnim nazivom
    m = re.search(rf'{naziv}="([^"]*)"', tag_str)
    return m.group(1) if m else None


def konvertuj(tokeni):
    izlaz = ""
    # koristimo stek zbog pamcenja otvorenih tagova u latexu (kako bismo ih uspesno i tacno zatvarali)
    stek = []
    pozicija = 0
    while pozicija < len(tokeni):
        tip, vrednost = tokeni[pozicija]
        if tip == "OTVARAJUCI_TAG":
            tag_ime = izvuci_ime_taga(vrednost)
            # mfenced obavija izraz u zagrade, pa nam je potrebno i da znamo koje su zagrade u pitanju
            # podrazumevano se obavija obicnim zagradama ()
            if tag_ime == "mfenced":
                open_br  = izvuci_atribut(vrednost, "open")  or "("
                close_br = izvuci_atribut(vrednost, "close") or ")"
                izlaz += "\\left" + open_br + " "
                stek.append(("mfenced_close", close_br))
            elif re.match(r"m[a-z]+", tag_ime):
                izlaz += TAG_MAP.get(tag_ime, ("", ""))[0]
                stek.append(("tag", tag_ime))
        elif tip == "ZATVARAJUCI_TAG":
            if stek:
                vrsta, ime = stek.pop()
                if vrsta == "mfenced_close":
                    izlaz += " \\right" + ime
                else:
                    izlaz += TAG_MAP.get(ime, ("", ""))[1]
        elif tip == "ENTITET":
            izlaz += ENTITET_MAP.get(vrednost, vrednost)
        else:
            izlaz += vrednost
        pozicija += 1
    return izlaz


def konvertuj_fajl(ulazni_fajl, izlazni_fajl):
    with open(ulazni_fajl, "r", encoding="utf-8") as f:
        mathml_tekst = f.read()

    tokeni = tokenizuj(mathml_tekst)
    ispisi_tokene(tokeni)

    latex_tekst = konvertuj(tokeni)

    with open(izlazni_fajl, "w", encoding="utf-8") as f:
        f.write(latex_tekst)
    print("LaTeX izlaz:")
    print(latex_tekst)


if len(sys.argv) != 3:
    print("Greska: neispravno pozivanje programa")
    sys.exit(1)

ulazni_fajl  = sys.argv[1]
izlazni_fajl = sys.argv[2]

konvertuj_fajl(ulazni_fajl, izlazni_fajl)