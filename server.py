import PodSixNet.Channel
import PodSixNet.Server
from time import sleep
from time import time
class ClientChannel(PodSixNet.Channel.Channel):
    '''client channel class docstring to do'''

    def Network(self, data: dict):  # Function name isn't very descriptive!
        '''Console log. Prints data dictionary'''

        print(data)

    def Network_readyStatus(self, data: dict):
        '''Feeds data into PodSixNet server object?'''

        self._server.readyStatus(data)

    def Network_recieveCommand(self, data: dict):
        '''Pushes data into PodSixNet server objects'''

        self._server.start_time = time()    #    testing latency
        self._server.recieveCommand(data)

    ####    ping stuff  ####
    # def __init__(self, *args, **kwargs):
        # PodSixNet.Channel.__init__(self, *args, **kwargs)
        # self.count = 0
        # self.times = []

    def Network_ping(self, data: dict) -> None:
        '''Pings the player and prints out the result on the server.'''

        print(self, "ping %d round trip time was %f" % (data["count"], time() - self.times[data["count"]]))
        if self.count == 10:    #   Replace this with a while loop
            self.count = 0
            self.times = []
        else:
            self.Ping()
    
    def Ping(self) -> None:
        '''Pings itself. Sends a message dictionary?'''

        # print(self, "Ping:", self.count)
        self.times.append(time())
        self.Send({"action": "ping", "count": self.count})
        self.count += 1 #   Move this counter to Network_ping
    ####    end ping stuff  ####
    
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
        '''Closes the server (which then closes the clients).'''

        self._server.close(self.gameid)

class BoxesServer(PodSixNet.Server.Server):
 
    channelClass = ClientChannel
    def __init__(self, *args, **kwargs):
        PodSixNet.Server.Server.__init__(self, *args, **kwargs)
        self.games: list = []
        self.current_game: Game = None
        self.currentIndex: int = 0

    def Connected(self, channel, addr):
        '''
        Matches players with each other as they connect.
        Creates Game objects as needed.
        '''

        print('new connection:', channel)

        if self.current_game==None:
            self.currentIndex+=1
            channel.gameid=self.currentIndex
            self.current_game=Game(channel, self.currentIndex)
        else:
            channel.gameid=self.currentIndex
            self.current_game.player1=channel
            print("Connecting to BOTH players")
            self.current_game.player0.Send({"action": "connectedPlayers","player":0, "gameid": self.current_game.gameid})
            self.current_game.player1.Send({"action": "connectedPlayers","player":1, "gameid": self.current_game.gameid})
            self.games.append(self.current_game)
            self.current_game=None

        channel.count = 0
        channel.times = []
        self.start_time = 0
        # channel.Ping() #ping line

    def readyStatus(self, data: dict):    # Redundant? Message commands already
                                    # Message commands already exist in Game
        '''
        Passes on message to game instance.
        '''
        game = [a for a in self.games if a.gameid==data["gameid"]]
        if len(game)==1:
            game[0].readyStatus(data)

    def recieveCommand(self, data: dict): # Redundant? Message commands already
                                    # Message commands already exist in Game
        '''
        Passes on message to game instance.
        '''
        # why use set building notation?
        game = [a for a in self.games if a.gameid==data["gameid"]]

        if len(game)==1:
            game[0].recieveCommand(data)

            # print("Time taken to finish server operations", time() - self.start_time)

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
        '''
        Closes the game instance and sends message to each player to close.
        '''
        try:
            game = [a for a in self.games if a.gameid==gameid][0]
            game.player0.Send({"action":"close"})
            game.player1.Send({"action":"close"})
        except: #   Should we be letting things silently fail?
                #   Investigate what exceptions are thrown.
            pass

    def tick(self):
        '''Pumps the game. Wrapper function around Channel.pump()'''
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
        self.turn = 0   # Refers to player0 or player1.
                        # 0 and 1 is too ambiguous.
                        # Set the value to an enumerated value.

        #owner map
        self.owner: list = [[False for x in range(6)] for y in range(6)]
            #   Why are we making a 6x6 matrix full of False values?

        #initialize the players including the one who started the game
        self.player0 = player0
        self.player1 = None
        self.gameid = currentIndex
        #gameid of game

    def readyStatus(self, data: dict):
        '''Sends ready status to each player and starts the game.'''

        self.player0.Send({"action": "readyStatus", "player":data["player"]})
        self.player1.Send({"action": "readyStatus", "player":data["player"]})

    def recieveCommand(self, data: dict): # Refactor
        '''
        [WIP]
        Sends Player 0 and Player 1 data from the server.

        Matches the {msg: opcode} to its corresponding action.
        Basically a switch state.
        
        Redundant function? Yes, but we'll use this system.
        '''
        #   Maybe change this if-elif-chain into a dictionary.
        #   Not sure how Python optimizes if-elif chains,
        #   but we can use the hash-table nature of dictionaries
        #   for O(1) performance.

        #   The {key: value} would be (enumIndex, functionAction() )?
        #   Is the overhead of calling another function too high?
        #   Need to find a way to benchmark times
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


    # def placeLine(self, is_h, x, y, data, num):
    #     #make sure it's their turn
    #     if num==self.turn:
    #         self.turn = 0 if self.turn else 1
    #         self.player1.Send({"action":"yourturn", "torf":True if self.turn==1 else False})
    #         self.player0.Send({"action":"yourturn", "torf":True if self.turn==0 else False})
    #         #place line in game
    #         if is_h:
    #             self.boardh[y][x] = True
    #         else:
    #             self.boardv[y][x] = True
    #         #send data and turn data to each player
    #         self.player0.Send(data)
    #         self.player1.Send(data)

# try:
# address=input("Host:Port (localhost:8002): ")


def start_server() -> None:
    '''
    Starts server.
    '''
    address="localhost:8004"    # "10.0.1.52:8002" this should be my local ip address
                                # anyway with the same port of 8002 but the server errors
                                # when started with the ip instad of localhost
    print("STARTING SERVER ON " + address)
    if not address:
        host, port="localhost", 8004
    else:
        host,port=address.split(":")
    boxesServe = BoxesServer(localaddr=(host, int(port)))
    while True:
        boxesServe.tick()
        sleep(0.01)

if __name__ == '__main__':
    start_server()