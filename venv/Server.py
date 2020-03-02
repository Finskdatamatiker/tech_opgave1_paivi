import socket
import SplitBesked

'''UDPserversocket laves her og serveren venter på klienten.
   AF_INET er en tuple med IP-adresse og port. 
   SOCK_DGRAM refererer til socket-typen datagram, som pakkerne hedder i UDP.
   serverSocket bindes til adressen.
   buffetSøttelse er max 8192, dvs. man kan kun sende en bestemt mængde data ad gangen gennem UDP
   Taeller indekserer beskederne og begynder med 0.  
   '''

serverSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
serverIP = "127.0.0.1"
serverPort = 3030
adressen = (serverIP, serverPort)
serverSocket.bind(adressen)
bufferStoerrelse = 4096
taeller = 0

'''Denne funktion returnerer en besked, som socket har modtaget. 
   I format() kan jeg vælge alle elementer i tuplen med * i stedet for at skrive adressen[0],adressen[1])
   recvfrom() returnerer en tuple, hvor det første element er beskeden, det andet element er 
   adressen til klientens socket (gemt i en ny tuple)'''

def modtag():
    print("Venter på klientens besked i IP-adressen {} ved porten {} ".format(*adressen))
    beskedFraKlienten = serverSocket.recvfrom(bufferStoerrelse)
    return beskedFraKlienten

'''Denne funktion laver en handshake. Den bruger funktionen slitBeskeden() til at fordele
   beskeden i forskellige elementer gemt i en tuple. 
   Først tjekkes, om klientens besked begynder med com-0 (tælleren er 0 på dette tidspunkt). 
   a) Hvis beskeden fra klienten er connection request, sendes der et svar til kklienten. 
   Svaret til klienten skal encodes, dvs. pakkes i binære tal, inden den sendes. 
   sendTo() har beskeden og adressen til klientens socket som sine parametre. 
   b ) Hvis beskeden er klientens accept, returnerer metoden true() for 
   vellykket handshake og while stoppes. 
   c ) ellers lukkes forbindelsen, fordi handshake ikke lykkedes og klienten 
   må lave en ny connection request. 
'''

def handshake():
    while (True):
        beskedFraKlienten = modtag()
        if(beskedFraKlienten):

            infoTuble = SplitBesked.splitBeskeden(beskedFraKlienten, " ", "C: ");

            if(infoTuble[0].__eq__("com") & infoTuble[1].__eq__(str(taeller))):

                if(infoTuble[2].__eq__(serverIP)):
                    svarFraServeren = "com-" + str(taeller) + " accept " + serverIP
                    print("S: " + svarFraServeren)
                    beskedTilKlient = str.encode(svarFraServeren)
                    serverSocket.sendto(beskedTilKlient, infoTuble[3])

                if (infoTuble[2].__eq__("accept")):
                    print("Klienten har accepteret og forbindelsen er etableret")
                    return True
                    break
            else:
               serverSocket.close()

'''
   Denne funktion håndterer beskeder, som klienten sender (efter handshake). 
   Funktionen splitBeskeden() splitter den modtagne besked ad. 
   Den returner en tuple, hvor de forskellige elementer i beskeden er gemt. 
   Hvis beskeden begynder med msg og dens indeksering matcher med taeller (som 
   hele tiden opdateres i takt med at der kommer beskeder), returnerer funktionen True. 
   Ellers False.
   Det er funktionen svarTilsMsg(), som kalder på modtageBeskeder() og sender et svar. 
'''

def modTageBeskeder():
        while (True):
            beskedFraKlienten = modtag()
            if (beskedFraKlienten):
                infoTuble = SplitBesked.splitBeskeden(beskedFraKlienten, "=", "C: ");

                if (infoTuble[0].__eq__("msg") & infoTuble[1].__eq__(str(taeller))):
                    svarTilMsg(True, infoTuble[3])

                else:
                    svarTilMsg(False, infoTuble[3])

'''Her sender vi svar til klienten afhængig af, om modtageBeskeder() modtog en 
   besked, som overholder protokollen eller ej. 
   Hvis ja) Jeg bruger variabel taeller inde i en funktion, så jeg skal markere den global.
   Når serveren svarer, skal taeller i svarbeskeden være 1 større end da den modtog beskeden.
   Så serveren sender et svar, som består af res-(taeller+1)=Jeg er serveren
   Svaret skal encodes først. 
   Næste gang når der kommer en besked, skal der svares med indeks, som er 2 større end i dette
   svar, så jeg tilføjer 2 til taeller, sådan at den hele tiden er opdateret. 
   Hvis nej) Taeller opdateres ikke og jeg sender besked FEJL til klienten. '''

def svarTilMsg(bool, klientAdresse):

    if(bool == True):
        global taeller;
        svarTilMsg = "res-" + str(taeller+1) + "=Jeg er serveren"
        sendTilKlient = str.encode(svarTilMsg)
        taeller = taeller + 2
        print(type(klientAdresse))
        print(klientAdresse)
        serverSocket.sendto(sendTilKlient, klientAdresse);

    else:
        print("S: Fejl i beskeden")
        svarTilMsg = "FEJL"
        sendTilKlient = str.encode(svarTilMsg)
        serverSocket.sendto(sendTilKlient, klientAdresse)

'''
   Her kalder jeg på funktionerne, dvs. hvis handshake er
   gået vel, begynder serveren at modtage beskeder fra klienten'''

if(handshake()):
    modTageBeskeder()





