import re, sys

TAG_MAP = {
    "mfrac":      ("\\frac{", "}{"),
    "msqrt":      ("\\sqrt{", "}"),
    "mtable":     ("\\begin{bmatrix}", "\\end{bmatrix}"),
    "mtd":        ("", " & "),
    "mtr":        ("", " \\\\ "),
    "msin":       ("\\sin", ""),
    "mcos":       ("\\cos", "")
}

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

def tokenizuj(ulazni_tekst):
    kompajlirana = [(tip, re.compile(pat)) for tip, pat in PRAVILA]
    pozicija = 0
    tokeni = []
    while pozicija < len(ulazni_tekst):
        pronadjen = False
        for tip, pattern in kompajlirana:
            m = pattern.match(ulazni_tekst, pozicija)
            if m:
                pronadjen = True
                if tip != "PRAZNO":
                    tokeni.append((tip, m.group()))
                pozicija = m.end()
                break
        if not pronadjen:
            tokeni.append(("NEPOZNATO", ulazni_tekst[pozicija]))
            pozicija += 1
    return tokeni

def ispisi_tokene(tokeni):
    print(f"{'Br.':<5} {'Tip':<20} {'Vrednost'}")
    print("-" * 50)
    for i, (tip, vrednost) in enumerate(tokeni, 1):
        print(f"{i:<5} {tip:<20} {vrednost}")


def izvuci_ime_taga(tag_str):
    m = re.match(r"<([a-zA-Z]+)", tag_str)
    return m.group(1) if m else ""


def izvuci_atribut(tag_str, naziv):
    m = re.search(rf'{naziv}="([^"]*)"', tag_str)
    return m.group(1) if m else None


def konvertuj(tokeni):
    izlaz = ""
    stek = []
    pozicija = 0
    while pozicija < len(tokeni):
        tip, vrednost = tokeni[pozicija]
        if tip == "OTVARAJUCI_TAG":
            tag_ime = izvuci_ime_taga(vrednost)
            if tag_ime == "mfenced":
                open_br = izvuci_atribut(vrednost, "open")  or "("
                close_br = izvuci_atribut(vrednost, "close") or ")"
                izlaz += "\\left" + open_br + " "
                stek.append(("mfenced_close", close_br))
            # poseban slucaj jer su ovo viseargumentni tagovi
            elif tag_ime in ("msub", "msup", "msubsup", "munder", "mover", "munderover"):
                stek.append((tag_ime, 0))

            elif re.match(r"m[a-z]+", tag_ime):
                izlaz += TAG_MAP.get(tag_ime, ("", ""))[0]
                stek.append(("tag", tag_ime))
        elif tip == "ZATVARAJUCI_TAG":
            if stek:
                vrsta, ime = stek.pop()
                if vrsta == "mfenced_close":
                    izlaz += " \\right" + ime
                elif vrsta in ("msub", "msup", "msubsup", "munder", "mover", "munderover"):
                    # ovu vrstu cemo posebno obradjivati zbog vise argumenata
                    pass
                else:
                    izlaz += TAG_MAP.get(ime, ("", ""))[1]
        elif tip == "ENTITET":
            izlaz += ENTITET_MAP.get(vrednost, vrednost)
        else:
            izlaz += vrednost

        if stek and stek[-1][0] in ("msub", "msup", "msubsup", "munder", "mover", "munderover"):
            vrsta, brojac = stek.pop()

            if vrsta == "msub" or vrsta == "munder":
                if brojac == 0:
                    izlaz += "_{"
                elif brojac == 1:
                    izlaz += "}"

            elif vrsta == "msup" or vrsta == "mover":
                if brojac == 0:
                    izlaz += "^{"
                elif brojac == 1:
                    izlaz += "}"

            elif vrsta == "msubsup" or vrsta == "munderover":
                if brojac == 0:
                    izlaz += "_{"
                elif brojac == 1:
                    izlaz += "}^{"
                elif brojac == 2:
                    izlaz += "}"

            brojac += 1

            if (vrsta in ("msub", "msup", "munder", "mover") and brojac < 2) or (vrsta in ("msubsup", "munderover") and brojac < 3):
                stek.append((vrsta, brojac))
        pozicija += 1
    return izlaz

def napravi_latex_doc(formula):
    return ("\\documentclass{article}\n"
            "\\usepackage{amsmath}\n"
            "\\begin{document}\n"
            "\\[\n"
            + formula +
            "\n\\]\n"
            "\\end{document}")


def konvertuj_fajl(ulazni_fajl, izlazni_fajl):
    with open(ulazni_fajl, "r", encoding="utf-8") as f:
        mathml_tekst = f.read()

    tokeni = tokenizuj(mathml_tekst)
    ispisi_tokene(tokeni)

    latex_tekst = konvertuj(tokeni)
    latex_doc = napravi_latex_doc(latex_tekst)

    with open(izlazni_fajl, "w", encoding="utf-8") as f:
        f.write(latex_doc)

    print("LaTeX formula:")
    print(latex_tekst)


if len(sys.argv) != 3:
    print("Greska: neispravno pozivanje programa")
    sys.exit(1)

ulazni_fajl  = sys.argv[1]
izlazni_fajl = sys.argv[2]

konvertuj_fajl(ulazni_fajl, izlazni_fajl)
