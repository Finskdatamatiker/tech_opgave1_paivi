
''' 
Beskeden splittes:
[0] besked (decodes også)  [1] afsenderAdreses (IP og socket).
Besked printes til console (fx msg-0=hej, com-0 accept osv.)
Denne besked splittes i to med den valgte separator (= eller mellemrum i protokollen)
[0] protokoldelen. Den skal vi igen dele i to (separator er -):
        [0] protokolteksten (fx msg) [1] taeller (fx 0)
[1] besked-delen
Funktionen returnerer en tuple med:
protokoltekst, protokolTal, beskeden
'''

def splitBeskeden(tupleTilSplitning, separator, cEllerS):

    besked = tupleTilSplitning[0].decode("UTF-8")
    afsenderAdresse = tupleTilSplitning[1]

    print(cEllerS + besked)

    beskedITuple = besked.split(separator)
    protokoldelen = beskedITuple[0]
    endnuMindre = protokoldelen.split("-")
    protokoltekst = endnuMindre[0]
    protokolTal = endnuMindre[1]
    beskeden = beskedITuple[1]

    infoTuple = (protokoltekst, protokolTal, beskeden)
    return infoTuple

