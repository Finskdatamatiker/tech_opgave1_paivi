import socket, sys
import SplitBesked
import threading
import time
from threading import Thread


''' UDP-socket (SOCK_DGRAM er datagram-baseret) for serveren. 
    AF_INET indikerer typer af adresser, som socket er i stand til at kommunikere med.
    localhost, bufferSøttelse er max 8192'''

serverSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
serverIP = "127.0.0.1"
serverPort = 3030
adressen = (serverIP, serverPort)
serverSocket.bind(adressen)
bufferStoerrelse = 4096

taeller = 0
klientadressen = ()
sidsteBeskedTid = time.time()
forskelITidTOLERANCE = 0.0

''' Modtager beskeder fra klienten. Klientadressen gemmes.
   recvfrom() returnerer en tuple med to elementer: 
   [0] beskeden, som gemmes i en mindre tuple  
   [1] afsenderens sockets adresse (IP + port) '''

def modtag():
    beskedFraKlienten = serverSocket.recvfrom(bufferStoerrelse)
    global klientadressen
    klientadressen = (beskedFraKlienten[1])
    return beskedFraKlienten




def handshake():
    while (True):

        global sidsteBeskedTid
        global forskelITidTOLERANCE

        beskedFraKlienten = modtag()
        if(beskedFraKlienten):

            '''beskeden splittes: [0] protokoldelen [1] taeller [2] besked'''
            infoTuble = SplitBesked.splitBeskeden(beskedFraKlienten, " ", "C: ");

            if(infoTuble[0].__eq__("com") & infoTuble[1].__eq__(str(taeller))):

                '''hvis com-0 IP korrekt, sendes accept til klienten'''
                if(infoTuble[2].__eq__(serverIP)):
                    svarFraServeren = "com-" + str(taeller) + " accept " + serverIP
                    print("S: " + svarFraServeren)
                    beskedTilKlient = str.encode(svarFraServeren)
                    serverSocket.sendto(beskedTilKlient, klientadressen)

                '''hvis com-0 accept, etableres forbindelsen'''
                if (infoTuble[2].__eq__("accept")):
                    print("Klienten har accepteret og forbindelsen er etableret")

                    '''Handshake logges, a = append'''
                    f = open("Scripts\log", "a")
                    nu = time.ctime(time.time())
                    f.write("handshake " + str(nu) + "\n")
                    f.close()


                    '''tiden for TOlERANCE opdateres'''
                    forskelITidTOLERANCE = time.time() - sidsteBeskedTid
                    sidsteBeskedTid = time.time()

                    return True
                    break
            else:
                print("S: Fejl i handshake")
                svarTilMsg = "FEJL"
                sendTilKlient = str.encode(svarTilMsg)
                serverSocket.sendto(sendTilKlient, klientadressen)

                '''Når klienten har lukket, lukkes serveren også'''
                if (ConnectionError):
                    serverSocket.close()
                    sys.exit(0)

'''Klientens besked behandles.'''
def behandlBeskeder():
        starttid = time.time()
        maxTaeller = 0;
        conResSendt = False
        global sidsteBeskedTid
        global forskelITidTOLERANCE

        while (True):

                beskedFraKlienten = modtag()

                '''MAX 25 beskeder per sekund -starttid opdateres ved den første besked'''
                if (maxTaeller == 0):
                    starttid = time.time()

                '''MAX 25 beskeder per sekund. For mange, sendes FEJL til klienten'''
                if(maxTaeller == 25):
                    elapsed = time.time() - starttid
                    if (elapsed <  1.0):
                        print("S: For mange beskeder")
                        svarTilMsg(2, klientadressen)


                if(beskedFraKlienten):

                    maxTaeller += 1
                    '''TOLERANCE: tid mellem beskeder udregnes og sidsteBeskedTid opdateres'''
                    forskelITidTOLERANCE = time.time()-sidsteBeskedTid
                    sidsteBeskedTid = time.time()

                    '''Klienten kvitterer max per sekund og forbindelsen lukkes'''
                    if(beskedFraKlienten[0].decode().__eq__("con-res 0xFF")):
                        print("C: " + beskedFraKlienten[0].decode())
                        serverSocket.close()
                        sys.exit(0)
                        return

                    elif(beskedFraKlienten[0].decode().__eq__("con-h 0x00")):
                        '''Serveren modtager heartbeat og sender ok'''
                        svarTilMsg(3,klientadressen)
                        print("modtager con-h")

                    else:

                        '''Serveren svarer enten res (1) eller FEJL (2) afhængig af, 
                           om protokollen er overholdt'''
                        infoTuble = SplitBesked.splitBeskeden(beskedFraKlienten, "=", "C: ")
                        if(infoTuble):
                            if (infoTuble[0].__eq__("msg") and infoTuble[1].__eq__(str(taeller))):
                                svarTilMsg(1, klientadressen)
                            else:
                                svarTilMsg(2, klientadressen)


'''svaret til klienten sendes, efter at beskeden fra klienten er behandlet
i den forrige funktion'''
def svarTilMsg(valg, klientAdresse):

    if(valg==1):
        '''protokollen er overholdt, så res til klienten. 
        Taeller opdateres med 2 til næste omgang.'''
        global taeller;
        svarTilMsg = "res-" + str(taeller+1) + "=Jeg er serveren"
        sendTilKlient = str.encode(svarTilMsg)
        taeller = taeller + 2
        serverSocket.sendto(sendTilKlient, klientAdresse);

    if(valg ==2):
        '''protokollen er ikke overholdt, så FEJL til klienten'''
        print("S: Fejl")
        svarTilMsg = "FEJL"
        sendTilKlient = str.encode(svarTilMsg)
        serverSocket.sendto(sendTilKlient, klientAdresse)

        '''Når klienten har lukket, lukkes serveren også'''
        if (ConnectionError):
            serverSocket.close()
            sys.exit(0)

    if(valg == 3):
        '''Serveren anderkender heartbeat'''
        svarTilMsg = "okhb"
        sendTilKlient = str.encode(svarTilMsg)
        serverSocket.sendto(sendTilKlient, klientAdresse)



'''Undersøger hvert 4.sekund, om der er sket noget siden sidst. 
    Er der blevet sendt beskeder, sover den bare igen.
    Hvis der ikke er sket noget, skal tolerance træde i kraft.'''

def checkTolerance():

        global forskelITidTOLERANCE
        global sidsteBeskedTid
        global klientadressen
        conResIkkeSendt = True
        sidsteForskelMlBeskeder = 0.0

        while(conResIkkeSendt):
            try:
                time.sleep(4)

                if(sidsteForskelMlBeskeder == forskelITidTOLERANCE):
                    '''Der er ikke sket noget siden sidst. ForskelITid udregnes igen.
                    Forskellen udregnes ikke i handshake, så hvis forskellen er 0.0 siden sidst, 
                    er det fordi vi er lige kommet ud af handshake. 
                    Så begynder vi at udregne både sidsteBeskedTid og forskel.  
                    Ellers er forskellen blevet over 4 og vi går til næste punkt.'''

                    forskelITidTOLERANCE = time.time() - sidsteBeskedTid
                    sidsteBeskedTid = time.time()

                if (forskelITidTOLERANCE > 4 and conResIkkeSendt == True and klientadressen != ()):
                    '''lukning sendes kun en gang og hvis handshake er udført, dvs. der er klientadressen'''

                    print("S: con-res 0xFE")
                    sendTilKlienten = str.encode("con-res 0xFE")
                    serverSocket.sendto(sendTilKlienten, klientadressen)
                    conResIkkeSendt = False
                    return

            except OSError as e:
                print("Programmet afsluttes")
                serverSocket.close()
                sys.exit(1)

            '''Opdateres for at tjekke, om der er sket noget siden'''
            sidsteForskelMlBeskeder = forskelITidTOLERANCE




'''Serveren kører i to tråde: main og tolerance.'''
def udfoerMain():
    print("Venter på klientens besked i IP-adressen {} ved porten {} ".format(*adressen))
    if (handshake()):
        behandlBeskeder()

if __name__ == '__main__':
    server = Thread(target = udfoerMain).start()
    tolerance = Thread(target=checkTolerance).start()













