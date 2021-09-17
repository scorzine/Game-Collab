import PodSixNet.Channel
import PodSixNet.Server
from time import sleep
from time import time
class ClientChannel(PodSixNet.Channel.Channel):
    def Network(self, data):
        print(data)
    def Network_readyStatus(self, data):
        self._server.readyStatus(data)
    def Network_recieveCommand(self, data):
        self._server.start_time = time()
        self._server.recieveCommand(data)

    #ping stuff
    # def __init__(self, *args, **kwargs):
        # PodSixNet.Channel.__init__(self, *args, **kwargs)
        # self.count = 0
        # self.times = []

    def Network_ping(self, data):
        print(self, "ping %d round trip time was %f" % (data["count"], time() - self.times[data["count"]]))
        if self.count == 10:
            self.count = 0
            self.times = []
        else:
            self.Ping()
    
    def Ping(self):
        # print(self, "Ping:", self.count)
        self.times.append(time())
        self.Send({"action": "ping", "count": self.count})
        self.count += 1
    #end ping stuff


    # def Network_moveUnitTile(self, data):
    #     self._server.moveUnitTile(data)
    # def Network_nextPhase(self, data):
    #     self._server.nextPhase(data)

    # def Network_place(self, data):
    #     #deconsolidate all of the data from the dictionary
     
    #     #horizontal or vertical?
    #     hv = data["is_horizontal"]
    #     #x of placed line
    #     x = data["x"]
     
    #     #y of placed line
    #     y = data["y"]
     
    #     #player number (1 or 0)
    #     num=data["num"]
     
    #     #id of game given by server at start of game
    #     self.gameid = data["gameid"]
     
    #     #tells server to place line
    #     self._server.placeLine(hv, x, y, data, self.gameid, num)
    def Close(self):
        self._server.close(self.gameid)
class BoxesServer(PodSixNet.Server.Server):
 
    channelClass = ClientChannel
    def __init__(self, *args, **kwargs):
        PodSixNet.Server.Server.__init__(self, *args, **kwargs)
        self.games = []
        self.queue = None
        self.currentIndex=0

    def Connected(self, channel, addr):
        print('new connection:', channel)
        if self.queue==None:
            self.currentIndex+=1
            channel.gameid=self.currentIndex
            self.queue=Game(channel, self.currentIndex)
        else:
            channel.gameid=self.currentIndex
            self.queue.player1=channel
            print("Connecting to BOTH players")
            self.queue.player0.Send({"action": "connectedPlayers","player":0, "gameid": self.queue.gameid})
            self.queue.player1.Send({"action": "connectedPlayers","player":1, "gameid": self.queue.gameid})
            self.games.append(self.queue)
            self.queue=None

        channel.count = 0
        channel.times = []
        self.start_time = 0
        # channel.Ping() #ping line

    def readyStatus(self, data):
        game = [a for a in self.games if a.gameid==data["gameid"]]
        if len(game)==1:
            game[0].readyStatus(data)

    def recieveCommand(self, data):
        game = [a for a in self.games if a.gameid==data["gameid"]]
        if len(game)==1:
            game[0].recieveCommand(data)

            print("Time taken to finish server operations", time() - self.start_time)

    # def moveUnitTile(self, data):
    #     game = [a for a in self.games if a.gameid==data["gameid"]]
    #     if len(game)==1:
    #         game[0].moveUnitTile(data)

    # def nextPhase(self, data):
    #     game = [a for a in self.games if a.gameid==data["gameid"]]
    #     if len(game)==1:
    #         game[0].nextPhase(data)

    # def placeLine(self, is_h, x, y, data, gameid, num):
    #     game = [a for a in self.games if a.gameid==gameid]
    #     if len(game)==1:
    #         game[0].placeLine(is_h, x, y, data, num)
    def close(self, gameid):
        try:
            game = [a for a in self.games if a.gameid==gameid][0]
            game.player0.Send({"action":"close"})
            game.player1.Send({"action":"close"})
        except:
            pass
    def tick(self):
        # Check for any wins
        # Loop through all of the squares
        
        # index=0
        # change=3
        # for game in self.games:
        #     change=3
        #     for time in range(2):
        #         for y in range(6):
        #             for x in range(6):
        #                 if game.boardh[y][x] and game.boardv[y][x] and game.boardh[y+1][x] and game.boardv[y][x+1] and not game.owner[x][y]:
        #                     if self.games[index].turn==0:
        #                         self.games[index].owner[x][y]=2
        #                         game.player1.Send({"action":"win", "x":x, "y":y})
        #                         game.player0.Send({"action":"lose", "x":x, "y":y})
        #                         change=1
        #                     else:
        #                         self.games[index].owner[x][y]=1
        #                         game.player0.Send({"action":"win", "x":x, "y":y})
        #                         game.player1.Send({"action":"lose", "x":x, "y":y})
        #                         change=0
        #     self.games[index].turn = change if change!=3 else self.games[index].turn
        #     game.player1.Send({"action":"yourturn", "torf":True if self.games[index].turn==1 else False})
        #     game.player0.Send({"action":"yourturn", "torf":True if self.games[index].turn==0 else False})
        #     index+=1
        self.Pump()
class Game:
    def __init__(self, player0, currentIndex):
        # whose turn (1 or 0)
        self.turn = 0
        #owner map
        self.owner=[[False for x in range(6)] for y in range(6)]
        # Seven lines in each direction to make a six by six grid.
        self.boardh = [[False for x in range(6)] for y in range(7)]
        self.boardv = [[False for x in range(7)] for y in range(6)]
        #initialize the players including the one who started the game
        self.player0=player0
        self.player1=None
        #gameid of game
        self.gameid=currentIndex
    def readyStatus(self, data):
        self.player0.Send({"action": "readyStatus", "player":data["player"]})
        self.player1.Send({"action": "readyStatus", "player":data["player"]})

    def recieveCommand(self, data):
        if data["msg"] in [0]:
            self.player0.Send({"action": "recieveCommand", "msg":data["msg"], "state":data["state"], "player":data["player"]})
            self.player1.Send({"action": "recieveCommand", "msg":data["msg"], "state":data["state"], "player":data["player"]})
        elif data["msg"] in [1]:
            self.player0.Send({"action": "recieveCommand", "msg":data["msg"], "x1":data["x1"], "y1":data["y1"], "x2":data["x2"], "y2":data["y2"], "nameid":data["nameid"], "player":data["player"]})
            self.player1.Send({"action": "recieveCommand", "msg":data["msg"], "x1":data["x1"], "y1":data["y1"], "x2":data["x2"], "y2":data["y2"], "nameid":data["nameid"], "player":data["player"]})
        elif data["msg"] in [2, 4, 5, 6, 9]:# == 2 or data["msg"] == 4 or data["msg"] == 5 or data["msg"] == 6:
            self.player0.Send({"action": "recieveCommand", "msg":data["msg"], "unitid":data["unitid"], "tileid":data["tileid"]})
            self.player1.Send({"action": "recieveCommand", "msg":data["msg"], "unitid":data["unitid"], "tileid":data["tileid"]})
        elif data["msg"] in [3]:# or data["msg"] == 6:
            self.player0.Send({"action": "recieveCommand", "msg":data["msg"]})
            self.player1.Send({"action": "recieveCommand", "msg":data["msg"]})
        elif data["msg"] in [7]:
            self.player0.Send({"action": "recieveCommand", "msg":data["msg"], "player":data["player"]})
            self.player1.Send({"action": "recieveCommand", "msg":data["msg"], "player":data["player"]})
        elif data["msg"] in [10]:
            self.player1.Send({"action": "recieveCommand", "msg":data["msg"], "unitid":data["unitid"], "effect":data["effect"], "stat_type":data["stat_type"], "groupid":data["groupid"], "display_hp":data["display_hp"]})
            self.player0.Send({"action": "recieveCommand", "msg":data["msg"], "unitid":data["unitid"], "effect":data["effect"], "stat_type":data["stat_type"], "groupid":data["groupid"], "display_hp":data["display_hp"]})
        elif data["msg"] in [11]:# == 2 or data["msg"] == 4 or data["msg"] == 5 or data["msg"] == 6:
            self.player0.Send({"action": "recieveCommand", "msg":data["msg"], "unitid":data["unitid"], "tileid":data["tileid"], "groupid":data["groupid"]})
            self.player1.Send({"action": "recieveCommand", "msg":data["msg"], "unitid":data["unitid"], "tileid":data["tileid"], "groupid":data["groupid"]})
        elif data["msg"] in [12]:
            self.player0.Send({"action": "recieveCommand", "msg":data["msg"], "boardid":data["boardid"]})
            self.player1.Send({"action": "recieveCommand", "msg":data["msg"], "boardid":data["boardid"]})




        elif data["msg"] in [25]:
            self.player0.Ping() #ping line
            self.player1.Ping() #ping line
        


    # def moveUnitTile(self, data):
    #     self.player0.Send({"action": "moveUnitTile", "unitid":data["unitid"], "tileid":data["tileid"]})
    #     self.player1.Send({"action": "moveUnitTile", "unitid":data["unitid"], "tileid":data["tileid"]})

    # def nextPhase(self, data):
    #     self.player0.Send({"action": "nextPhase", "player":data["player"]})
    #     self.player1.Send({"action": "nextPhase", "player":data["player"]})

    def placeLine(self, is_h, x, y, data, num):
        #make sure it's their turn
        if num==self.turn:
            self.turn = 0 if self.turn else 1
            self.player1.Send({"action":"yourturn", "torf":True if self.turn==1 else False})
            self.player0.Send({"action":"yourturn", "torf":True if self.turn==0 else False})
            #place line in game
            if is_h:
                self.boardh[y][x] = True
            else:
                self.boardv[y][x] = True
            #send data and turn data to each player
            self.player0.Send(data)
            self.player1.Send(data)
print("STARTING SERVER ON LOCALHOST")
# try:
# address=input("Host:Port (localhost:8002): ")
address="localhost:8004"#"10.0.1.52:8002" this should be my local ip address anyway with the same port of 8002 but the server errors when started with the ip instad of localhost
if not address:
    host, port="localhost", 8004
else:
    host,port=address.split(":")
boxesServe = BoxesServer(localaddr=(host, int(port)))
while True:
    boxesServe.tick()
    sleep(0.01)
