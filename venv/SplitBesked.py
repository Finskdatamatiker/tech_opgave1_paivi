
'''
   Denne funktion opdeler klientens besked i forskellige elementer
   og returnerer dem i en tuple.

   Beskeden fra klienten (som funktionen får som parameter) er også gemt
   i en tuple, hvor den ene del(0) er selve beskeden og den anden del(1)
   er adressen til klientens socket (det er faktisk også en tuple).

   Først skal besked-delen (0) decodes til tekststring (den var jo encodet).
   cEllers står for, hvem er er afsenderen. Det er rart at se på consolen.

   De forskellige elementer, som er adskilt af separator (i handshake kaldes
   funktionen med et mellemrum og ellers med = som separator):

   splitter = beskedens forskellige elementer gemt i en tuple (de var adskilt af -)
   beskedDel1 = den første del af beskeden, dvs. com-0
   protokolDel = beskedDel1 er delt i to, dvs. her har vi com
   protokolTal ) beskedDel1 er delt i to, dvs. her har vi 0
   beskeden = selve beskeden, som kan være server-IP eller accept

   samlet, som returneres i en tuple:
   infoTuple = (protokolDel, protokolTal, beskeden, afsenderAdresse)
'''

def splitBeskeden(tupleTilSplitning, separator, cEllerS):

    besked = tupleTilSplitning[0].decode("UTF-8")
    afsenderAdresse = tupleTilSplitning[1]

    print(cEllerS + besked)

    splitter = besked.split(separator)
    beskedDel1 = splitter[0]
    endnuMindre = beskedDel1.split("-")
    protokolDel = endnuMindre[0]
    protokolTal = endnuMindre[1]
    beskeden = splitter[1]

    infoTuple = (protokolDel, protokolTal, beskeden, afsenderAdresse)
    return infoTuple

