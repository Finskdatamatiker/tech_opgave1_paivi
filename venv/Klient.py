import socket, struct,sys
import SplitBesked

'''
   Her laver jeg UDP-socket for klienten. Se resten af 
   forklaringer til variablerne i filen Server. 
'''

klientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
serverIP = "127.0.0.1"
serverPort = 3030
serverAdressen = (serverIP, serverPort)
bufferSize = 4096
taeller = 0

'''
   Funktionen returnerer en besked, som serveren har sendt, i en tuple, 
   hvor det første element er beskeden, det andet element er 
   adressen til serverens socket. 
'''

def modtag():
    svarFraServer = klientSocket.recvfrom(bufferSize)

    testSubstring = svarFraServer[0][0:4].decode()

    if(testSubstring.__eq__("FEJL")):
        print(testSubstring + ":serveren lukker forbindelsen.")
        klientSocket.close()
        sys.exit(0)

    return svarFraServer

'''
   Klienter begynder handshake ved at sende connection request. 
   Beskeden skal encodes, dvs. konverteres til binære tal, inden den sendes.
   Så læses svar fra serveren. Metoden splitBeskeden() fordeler svaret i 
   forskellige elementer, sådan at vi kan tjekke, at protokollen overholdes. 
   Hvis serverens besked godkendes, sender klienten svar tilbage med com-0 accept
   Hvis det ikke lykkes at etablere forbindelse, lukker klienten systemet. 
'''

def handshake():

        while(True):
            beskedFraKlient = "com-" + str(taeller) + " " + serverIP
            print("C: " + beskedFraKlient)
            sendTilServer = str.encode(beskedFraKlient)
            klientSocket.sendto(sendTilServer, serverAdressen)
            svarFraServer = modtag()
            if(svarFraServer):

                    infoTuple = SplitBesked.splitBeskeden(svarFraServer, " ", "S: ");
                    #metoden splitBeskeden() returnerer alt efter com-1 som en samlet besked. Men her
                    #skal vi tjekke, som der først står accept, så jeg splitter den. ServerIp har vi i index 3.
                    acceptDelen = infoTuple[2].split()
                    accept = acceptDelen[0];

                    if(infoTuple[0].__eq__("com") & infoTuple[1].__eq__(str(taeller)) & accept.__eq__("accept") & infoTuple[3][0].__eq__(serverIP)):
                        ack = "com-" + str(taeller) + " accept"
                        print("C: " + ack)
                        sendSvarTilServer = str.encode(ack)
                        klientSocket.sendto(sendSvarTilServer, serverAdressen)

                        return True
                        break

                    else:
                        return False

'''
   Denne funktion er til at sende beskeder. 
   input() læser beskeden fra console. 
   Taeller bliver ikke opdateret i allerførste besked (den skal være msg-0)
   og derefter opdateres den hver gang når en besked er sendt i modtageRes()
   Beskeden skal encodes, inden den sendes. 
'''

def sendBeskeder():

        print("Skriv en ny besked.")
        indtast = input()
        msg = "msg-" + str(taeller) + "=" + indtast
        sendBesked = str.encode(msg)
        klientSocket.sendto(sendBesked, serverAdressen)

'''
   Denne funktion læser serverens res-beskeden. Metoden splitBeskeden()
   fordeler beskeden igen i forskellige elementer, sådan at vi kan tjekke protokollen.
   Index i res-beskeden skal være 1 større end sidst, klienten sendte en besked. 
   Hvis protokollen er godkendt, tilføjer vi 2 til taeller og sender en ny besked. 
   Hvis protokollen ikke er godkendt (der kommer fx besked FEJL fra serveren), 
   beder vi klienten om at starte forfra med at sende en besked. Taeller 
   bliver ikke opdateret før klienten sender en ny besked. 
'''

def modtageRes():

        while(True):
            resFraServer = modtag()
            if(resFraServer):
                global taeller;
                infoTuple = SplitBesked.splitBeskeden(resFraServer,"=", "S: ");

                if(infoTuple[0].__eq__("res") & infoTuple[1].__eq__(str(taeller+1))):

                    taeller = taeller + 2
                    sendBeskeder()

                else:
                    print("Fejl i beskeden")
                    sendBeskeder()

'''
   Hvis handshake er gået godt, sender vi først en besked. 
   Derefter kører kommunikationen i modtageRes(), fordi inden 
   vi sender en ny besked, skal svaret fra serveren tjekkes. 
'''

if(handshake()):
     sendBeskeder()
     modtageRes()








