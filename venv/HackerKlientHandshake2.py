import socket, struct, sys
import SplitBesked
from threading import Thread
import time

''' UDP-socket (SOCK_DGRAM er datagram-baseret) for klienten. 
    AF_INET indikerer typer af adresser, som socket er i stand til at kommunikere med.
    bufferSøttelse er max 8192, localhost'''

klientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
serverIP = "127.0.0.1"
serverPort = 3030
serverAdressen = (serverIP, serverPort)
bufferSize = 4096

taeller = 0
sidsteSendt = time.time()
forskelHEARTBEAT = 0.0
forskellenTOLERANCE = 0.0

'''
   Modtager serverens beskeder.
   recvfrom() returnerer en tuple med to elementer: 
   [0] beskeden, som gemmes i en mindre tuple  
   [1] afsenderens sockets adresse (IP + port) 
   Hvis serveren sender FEJL, lukkes forbindelsen.    
   TOLERANCE: Hvis serveren sender con-res 0xFE, sendes 
   con-res 0xFF til serveren og forbindelsen lukkes.
   '''


def modtag():
    try:
        svarFraServer = klientSocket.recvfrom(bufferSize)
        fejl = svarFraServer[0].decode()

        if (fejl.__eq__("FEJL")):
            print(fejl + ":serveren lukker forbindelsen.")
            klientSocket.close()
            sys.exit(1)
            return

        elif (fejl.__eq__("con-res 0xFE")):
            print("C: con-res 0xFF. Serveren lukker forbindelsen")
            sendSvarTilServer = str.encode("con-res 0xFF")
            klientSocket.sendto(sendSvarTilServer, serverAdressen)
            klientSocket.close()
            sys.exit(1)
            return

    except OSError as e:
        print("Programmet er afsluttet.")
        klientSocket.close()
        sys.exit(1)

    return svarFraServer


def handshake():
    while (True):

        global forskelHEARTBEAT
        global sidsteSendt

        '''Klienten sender først request om handshake '''
        beskedFraKlient = "com-" + str(taeller) + " " + serverIP
        print("C: " + beskedFraKlient)
        encodedBesked = str.encode(beskedFraKlient)
        klientSocket.sendto(encodedBesked, serverAdressen)

        '''SidstSendt blev sat til time.timer(), da main-tråden begyndte at køre. 
        Nu opdateres forskellen for at udregne behover for heartbeat og tiden, 
        som både heartbeat og consoletjek bruger.'''
        forskelHEARTBEAT = time.time() - sidsteSendt
        sidsteSendt = time.time()

        svarFraServer = modtag()
        if (svarFraServer):

            '''beskeden splittes: [0] protokoldelen [1] taeller [2] besked'''
            infoTuple = SplitBesked.splitBeskeden(svarFraServer, " ", "S: ");
            '''besked-delen opdeles yderligere i accept og IP'''
            acceptDelen = infoTuple[2].split()
            accept = acceptDelen[0];

            '''hvis protokollen overholdes, sender klienten com-0 accept til serveren'''
            if (infoTuple[0].__eq__("com") & infoTuple[1].__eq__(str(taeller))
                    & accept.__eq__("accept")
                    & svarFraServer[1][0].__eq__(serverIP)):

                '''
                FEJL I HANDSHAKE COM
                '''
                ack = "daniel-" + str(taeller) + " accept"
                print("C: " + ack)
                sendSvarTilServer = str.encode(ack)
                klientSocket.sendto(sendSvarTilServer, serverAdressen)
                return True
                break

            else:
                return False


''' Klienten sender besked enten via console eller autobesked. 
    Hvis autobeskeder er valgt (automatiseringValgt læses fra opt.conf), bliver de kørt først.
    Hvis der er over 25 beskeder per sekund, giver serveren en fejlbesked,
    og forbindelsen lukkes. Er der under, kan klienten begynde at chatte. '''


def sendBesked(automatiseringValgt):
    try:
        if (automatiseringValgt == False):
            global sidsteSendt

            print("Skriv en ny besked.")
            indtast = input()
            msg = "msg-" + str(taeller) + "=" + indtast
            sendBesked = str.encode(msg)
            klientSocket.sendto(sendBesked, serverAdressen)
            '''tidspunktet for sendt besked opdateres for heartbeat og consoletjek'''
            sidsteSendt = time.time()

        else:
            indtast = "autobesked"
            msg = "msg-" + str(taeller) + "=" + indtast
            sendBesked = str.encode(msg)
            klientSocket.sendto(sendBesked, serverAdressen)

    except OSError as e:
        print("Programmet afslutter")
        klientSocket.close()
        sys.exit(1)


''' automatiseringValgt er True (autoBeskederAntal større end 0 i filen) 
    eller False (autoBeskederAntal 0 (eller under 0 eller et andet tegn end et tal) i filen) 
    Hvis automatisering valgt, starter vi ikke med at bede om 
    input fra console, men der sendes autobesked i stedet først.  
    Funktionen skal også have antallet af autobeskeder.'''


def behandlBesked(automatiseringValgt, autoBeskederAntal):
    autoBeskedTaeller = 1
    '''Holder styr på omgangene af autobeskeder (serveren svarer til dem alle)
      Når vi er færdige, skal vi over til almindelig chat
      (hvis serveren ikke har lukket pga TOLERANCE.)'''

    while (True):

        svarFraServer = modtag()

        if (svarFraServer):
            global taeller

            if (svarFraServer[0].decode().__eq__("okhb")):
                '''serveren anerkender heartbeat, men der er ikke behov handling fra klientens side'''

            else:
                '''beskeden splittes: [0] protokoldelen [1] taeller [2] besked'''
                infoTuple = SplitBesked.splitBeskeden(svarFraServer, "=", "S: ")

                if (infoTuple[0].__eq__("res") & infoTuple[1].__eq__(str(taeller + 1))):
                    '''taeller gøres klar til næste omgang'''
                    taeller = taeller + 2
                    sendBesked(automatiseringValgt)

                    '''
                       Hvis autobeskeder valgt, tæller vi dem. Når vi rammer antallet angivet i opt.conf,
                       skal almindelig chat begynde (hvis under 25 autobeskeder per sec, dvs. inden for tolerance). 
                       Så taeller tilføjes 2, automatisering false og antallet af autobeskeder til 0. 
                    '''
                    if (autoBeskederAntal > 0):
                        autoBeskedTaeller += 1
                        '''Når vi er færdig med autoantal, skal vi igang med chat, hvis der var under 25 per sekund'''
                        if (autoBeskedTaeller == autoBeskederAntal):
                            taeller += 2
                            automatiseringValgt = False
                            autoBeskedTaeller = 0;

                else:
                    print("protokolkontrol")
                    sendBesked(False)


'''Læser opt.conf og returnerer en tuple med linjerne'''


def laesConfFil():
    f = open("Scripts\opt.conf", "r")
    if f.mode == 'r':
        linjer = f.readlines()
        return linjer


'''Læser den første linje med antallet af autobeskeder.
   Er antallet over 0, skal der sendes autobeskeder.
   Hvis ikke int eller et negativt tal, læses det som 0'''


def laesAutoBeskederAntal():
    try:
        tekst = laesConfFil()
        autoDelen = tekst[0].split(":")
        autoBeskederAntal = int(autoDelen[1])
        if (autoBeskederAntal < 0):
            return 0
    except ValueError:
        autoBeskederAntal = 0
    return autoBeskederAntal


'''Læser den anden linje med heartbeat eller ej'''


def laesKeepAlive():
    tekst = laesConfFil()
    keepAliveDelen = tekst[1].split(":")
    keepAlive = keepAliveDelen[1][1:]
    return keepAlive


''' HEARTBEAT: 
    Tjekker, hvor lang tid der er gået fra sidste besked. 
    Er der gået mere end 2 sekunder, returnerer true.
    Heartbeat skal sendes hvert 3. sekund, men det er ikke nok tid til 
    at sende og at serveren kan nå at udregne forskellen mellem beskeder 
    i tolerance, så jeg tjekker hvert 2. sekund. Så dør tråden ikke, selv
    om klienten ikke foretager sig noget som helst.'''


def udfoerCheck():
    global forskelHEARTBEAT
    global sidsteSendt

    forskelHEARTBEAT = time.time() - sidsteSendt
    if (forskelHEARTBEAT > 2):
        return True
    return False


''' heartbeat kører i sin egen tråd: tjekker først behovet for heartbeat med udfoerCheck()
    og sender heartbeat, hvis der er behov for det. 
    Hvis chat-tråden lukker, kommer der OSError med heartbeat, 
    som lukkes efterfølgende. Jeg giver besked om fejlen med except'''


def udfoerHeartbeat():
    global sidsteSendt
    global forskelHEARTBEAT
    try:
        while (True):
            sendHeartBeatOk = udfoerCheck()
            if (sendHeartBeatOk):
                sendHeartbeat()
                '''Tiden på den sidstsendt besked, dvs. her er det heartbeat, opdateres. 
                   Forskellen opdateres også.'''
                forskelHEARTBEAT = time.time() - sidsteSendt
                sidsteSendt = time.time()

    except OSError as e:
        print("Programmet afsluttes")


'''Sender heartbeat til serveren, hvis heartbeat-tråden beder om det.'''


def sendHeartbeat():
    hb = "con-h 0x00"
    sendBesked = str.encode(hb)
    klientSocket.sendto(sendBesked, serverAdressen)
    print("sender con-h")


'''TOLERANCE -tjek. 
  Hvis kunden ikke sender beskeder, bruges denne tråd til at tjekke 
  hvert 4. sekund, om serveren har sendt tolerance-fejlen. Kører i sin egen tråd, fordi 
  main-tråden er optaget i console for at vente på klientens beskeder. 
  Returnerer True, hvis forskellen er blevet mere end 4 sekunder. 
  Ellers opdateres forskellen til sidste tjek og returneres false. 

  '''


def udfoerCheckToleranceStatus():
    global forskellenTOLERANCE
    global sidsteSendt

    if (forskellenTOLERANCE > 4.0):
        return True
    else:
        forskellenTOLERANCE = time.time() - sidsteSendt

    return False


'''Tråden beder den forrige funktion om at tjekke, hvorvidt der er gået 4 sekunder
   uden nogen beskeder. Hvis ja, skal denne tråd tjekker, om serveren har sendt
   tolerance-fejl. Hvis ja, sender klienten sin bekræftelse og lukker. 
   Ellers sover tråden 4 sekunder og tjekker igen.'''


def checkConsole():
    try:
        while (True):
            skalConsoleReleases = udfoerCheckToleranceStatus()
            if (skalConsoleReleases):
                svarFraServer = klientSocket.recvfrom(bufferSize)
                if (svarFraServer[0].decode().__eq__("con-res 0xFE")):
                    print("S: " + svarFraServer[0].decode())
                    print("C: con-res 0xFF - chatten er lukket.")
                    sendSvarTilServer = str.encode("con-res 0xFF")
                    klientSocket.sendto(sendSvarTilServer, serverAdressen)
                    klientSocket.close()
                    sys.exit(1)
                    return

            else:
                time.sleep(4)

    except OSError as e:
        print("Programmet afsluttes")


''' Funktionen, som kører i hoved-tråden. Hvis handshake gået ok, 
    læses antallet af autobeskeder. Er det sat til 0, 
    er der ikke nogen og almindelig chat kører. 
    Er der autobeskeder, køres de først. '''


def udfoerChat():
    if (handshake()):
        autoBeskederAntal = laesAutoBeskederAntal()

        if (autoBeskederAntal == 0):
            sendBesked(False)
            behandlBesked(False, autoBeskederAntal)
        else:
            sendBesked(True)
            behandlBesked(True, autoBeskederAntal)


'''Trådene startes: hovedtråden, som kører chatten og tråden, som 
   tjekker hvert 4. sekund, om der er kommet tolerance-fejl. 
   Filen opt.conf læses, og hvis heartbeat er True, kører den tråd også. '''

if __name__ == '__main__':

    keepAlive = laesKeepAlive()
    if (keepAlive.__eq__("True")):
        heart = Thread(target=udfoerHeartbeat).start()

    chat = Thread(target=udfoerChat).start()
    consoleCheck = Thread(target=checkConsole).start()

