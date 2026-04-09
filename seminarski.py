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
    "&phi;":           "\\phi"
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

# argument atributi dodat je zbog prevodjenja taga mfenced - nisam zelela da izbacujem nijedan tag koji sam prvobitno ukljucila
# uostalom, ovo pojednostavljuje dodavanje novih tagova
def prevedi_tag(tag, deca, atributi):
    if tag == "mfrac":
        # mfrac -> \frac{brojilac}{imenilac}
        if len(deca) >= 2:
            return f"\\frac{{{deca[0]}}}{{{deca[1]}}}"
        return deca[0] if deca else ""
    elif tag == "msqrt":
        return f"\\sqrt{{{deca[0]}}}" if deca else ""
    elif tag == "mtable":
        return f"\\begin{{matrix}}{' \\\\ '.join(deca)}\\end{{matrix}}"
    elif tag == "mtr":
        return " & ".join(deca)
    elif tag == "mtd":
        return "".join(deca)
    elif tag == "mi":
        # npr <mi>sin</mi> -> deca = [sin] -> trazimo sin u FUNC_MAP i dobijamo \sin
        # ako nije u mapi (npr x, F, n , ...) -> vracamo nepromenjeno
        sadrzaj = "".join(deca).strip()
        return FUNC_MAP.get(sadrzaj, sadrzaj)
    elif tag in ("msin", "mcos"):
        return TAG_MAP[tag][0]
    elif tag in ("msub", "msup", "munder", "mover"):
        if len(deca) >= 2:
            if tag == "msub":
                return f"{deca[0]}_{{{deca[1]}}}"
            elif tag == "msup":
                return f"{deca[0]}^{{{deca[1]}}}"
            elif tag == "munder":
                return f"\\underset{{{deca[1]}}}{{{deca[0]}}}"
            elif tag == "mover":
                return f"\\overset{{{deca[1]}}}{{{deca[0]}}}"
        return deca[0] if deca else ""
    # ovi tagovi imaju troje dece npr:  \int_{0}^{\pi}
    elif tag in ("msubsup", "munderover"):
        if len(deca) >= 3:
            return f"{deca[0]}_{{{deca[1]}}}^{{{deca[2]}}}"
        elif len(deca) == 2:
            return f"{deca[0]}_{{{deca[1]}}}"
        return deca[0] if deca else ""
    elif tag == "mfenced":
        otvorena = atributi.get("open", "(")
        zatvorena = atributi.get("close", ")")
        sadrzaj = "".join(deca)
        return f"\\left{otvorena} {sadrzaj} \\right{zatvorena}"
    else:
        return "".join(deca)
    
def konvertuj_rekurzivno(tokeni, pozicija):
    # za svaki otvarajuci_tag rekurzivno obradjujemo svu decu dok ne naidjemo na zatvarajuci_tag
    deca = []
    while pozicija < len(tokeni):
        tip, vrednost = tokeni[pozicija]
        if tip == 'ZATVARAJUCI_TAG':
            # naisli smo na kraj ovog taga - vracamo se 
            return deca, pozicija + 1
        elif tip == 'OTVARAJUCI_TAG':
            tag_ime = izvuci_ime_taga(vrednost)
            atributi = {}
            # atribute (za trenutno podrzane tagove) imamo samo za mfenced
            if tag_ime == "mfenced":
                otvorena = izvuci_atribut(vrednost, "open")
                zatvorena = izvuci_atribut(vrednost, "close")
                if otvorena: atributi["open"] = otvorena
                if zatvorena: atributi["close"] = zatvorena
            # obradjujemo decu ovog taga
            deca_trenutno, pozicija = konvertuj_rekurzivno(tokeni, pozicija+1)

            latex = prevedi_tag(tag_ime, deca_trenutno, atributi)
            deca.append(latex)
        elif tip == 'ENTITET':
            deca.append(ENTITET_MAP.get(vrednost, vrednost))
            pozicija+=1
        else:
            deca.append(vrednost)
            pozicija += 1
    return deca,pozicija

def konvertuj(tokeni):
    deca, _ = konvertuj_rekurzivno(tokeni, 0)
    return "".join(deca)


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
