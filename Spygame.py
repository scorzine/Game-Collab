import os, sys, random, time, math, socket
from PodSixNet.Connection import ConnectionListener, connection
import Stats
import pickle
#this is a line of code
# os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
f = open(os.devnull, 'w')
# old = sys.stdout
#   HERE COMES THE MOUNTAIN
sys.stdout = f
import pygame.mixer
import pygame
sys.stdout = sys.__stdout__


class Game(ConnectionListener):

    #network command handler functions
    def connect(self):
        # address=input("Address of Server: ")
        address="localhost:8004"#"10.0.1.52:8002" #10.0.1.5?
        try:
            if not address:
                host, port="localhost", 8004 #10.0.1.5?
            else:
                host,port=address.split(":")
            self.Connect((host, int(port)))
            self.connected_to_server = True
            self.pump()
        except:
            print ("Error Connecting to Server")
            print ("Usage:", "host:port")
            print ("e.g.", "localhost:31425")
            exit()
        print ("Connected to server")

        self.delete_main_menu()

    #ping stuff
    def Network_ping(self, data):
        # print("got:", data)
        # if data["count"] < 10:
        connection.Send(data)
        # else:


    #end ping stuff

    def Network_connectedPlayers(self, data):
        self.connected_to_player = True
        self.gameid=data["gameid"]
        self.player=data["player"]

        

        if self.player:
            self.enemy = 0
        else:
            self.enemy = 1 

        print("Connected to player")

        self.game_board()

        # self.create_board(12, 12, 0.85)


    def create_board(self, dim_x, dim_y, mountain_threshold):
        self.dim_x = dim_x
        self.dim_y = dim_y
        mountain_threshold = 0.85

        if not self.player:

            boardid = ""
            # self.grass_tiles
            # self.mountain_tiles = 0
            # print((self.dim_x*self.dim_y)/2)
            for x in range(0, int((self.dim_x*self.dim_y)/2)):
                num = random.random()
                if num > mountain_threshold:
                    boardid += "m"
                    # self.mountain_tiles += 1
                else:
                    boardid += "g"
                    # self.grass_tiles += 1

            # boardid_flip = boardid[::-1]
            # boardid += boardid_flip]

            self.Send({"action": "recieveCommand", "msg":12, "gameid":self.gameid, "boardid":boardid})
        

    def recieveGameBoard(self, data):
        boardid=data["boardid"]
        self.board_textures = []

        self.grass_tiles = 0
        self.mountain_tiles = 0

        index = 0
        flip = False
        for x in range(0, self.dim_x):
            row = []
            for y in range(0, self.dim_y):
                if index == len(boardid):
                    boardid = boardid[::-1]
                    index = 0
                    flip = True #remove thise line to have it flip diagonally instead of along the x axis

                if boardid[index] == "g":
                    terrain = "grass"
                    self.grass_tiles += 1
                elif boardid[index] == "m":
                    terrain = "mountain"
                    self.mountain_tiles += 1

                # print("y: ", y, "x: ", x, "terrain: ", terrain)

                # print(boardid[index])

                # self.board_textures[y][x] = terrain

                row.append(terrain)

                index += 1

            if flip:
                row.reverse()

            self.board_textures.append(row)

        self.draw_game_board(self.dim_x, self.dim_y)

        self.endCommand()

    def Network_recieveCommand(self, data):
        # if data["msg"] == 4:
        #     self.msg_stack.insert(0, data)
        # else:
        # if data["msg"] == 2:
        #     print("recieved command time elapsed: ", time.time() - self.start_time)

        self.msg_stack.append(data)
        # self.msg_stack.insert(0, data)
        if self.curr_msg is None:
            self.msg_pop()
        else:
            pass

    def endCommand(self):
        self.curr_msg = None
        if self.msg_stack:
            self.msg_pop()

    def msg_pop(self):
        data = self.msg_stack.pop()
        self.curr_msg = data #?????????
        if data["msg"] == 0: #change state
            self.changeState(data)
        elif data["msg"] == 1: #populate
            self.populateUnits(data)
        elif data["msg"] == 2: #place
            # if self.start_time is not None:
            #     print("recieved unit place message: ", time.time() - self.start_time)
            self.placeUnitTile(data)
        elif data["msg"] == 3: #step move
            # for obj in self.moving_objects:
            #     if obj.moving_tile_path:
            self.stepMove(data)
                # break
        elif data["msg"] == 4: #setup move
            self.setupUnitMove(data)
        elif data["msg"] == 5: #setup atk
            self.setupUnitAttack(data)
        elif data["msg"] == 6: #setup ability
            self.setupUnitAbility(data)
        elif data["msg"] == 7: #end turn
            if self.game_state == "setup_units":
                self.endPlacement(data)
            else:
                self.endTurn(data)
        elif data["msg"] == 9: #triggered abilities
            self.trapTrigger(data)
        elif data["msg"] == 10: #adjust unit stats
            self.changeStats(data)
        elif data["msg"] == 11: #alt ability
            self.setupAltAbility(data)
        elif data["msg"] == 12: #alt ability
            self.recieveGameBoard(data)

        self.standby = False


    #functions called by the network
    def changeState(self, data):
        if data["state"] == 0:
            if self.both_ready:
                self.both_ready = False
                self.game_state = "setup_units"
                self.placement_done = False
                self.enemy_placement_done = False
                self.highlight_box(0, self.red, None)
                self.selected_sprite_box = 0
                self.deployed_sprite_boxes = []
            else:
                self.both_ready = True
        elif data["state"] == 1 and data["player"] == self.player:
            for unit in self.ally_deployed_units:
                unit.move_props["range"] = unit.move_props["max_range"]
                self.movable_units.append(unit)
                self.attackable_units.append(unit)
                self.activatable_units.append(unit)
                self.moving_objects = []
                self.waiting_objects = []
                self.attacking_units = []
                self.activating_units = []
            self.moving_unit = None 
            self.curr_destination = None
            self.game_state = "upkeep"
            self.upkeep()
        elif data["state"] == 2:
            self.game_state = "main_phase"
            self.main_phase()
        elif data["state"] == 3:
            self.game_state = "end_phase"
            self.endTurn(data)
        #     if data["player"] == self.player:
        #         for unit in self.ally_deployed_units:
        #             if unit.movable:
        #                 self.movable_units.append(unit)   
        #     self.moving_unit = None 
        #     self.curr_destination = None
        #     self.game_state = "move_units"
        # elif data["state"] == 3:
        #     if data["player"] == self.player:
        #         for unit in self.ally_deployed_units:
        #             if unit.attack_ready:
        #                 self.attacking_units.append(unit)
        #     self.attacking_unit = None
        #     self.attack_target = None
        #     self.game_state = "attack_units"
        self.endCommand()

    def populateUnits(self, data):
        new_unit = Unit(self, self.screen, data["x1"], data["y1"], data["x2"], data["y2"], data["player"], data["nameid"])
        self.units.append(new_unit)
        # self.all_sprites_list.add(new_unit)
        self.hidden_units.add(new_unit)
        # self.visible_units.add(new_unit)
        if data["player"] == self.player:
            self.ally_units.append(new_unit)
            self.ally_unit_pool.append(new_unit)
        else:
            self.enemy_units.append(new_unit)
            self.enemy_unit_pool.append(new_unit)
        self.endCommand()

    def placeUnitTile(self, data):
        unit = self.get_unit_by_id(data["unitid"])
        tile = self.get_tile_by_id(data["tileid"])
        if unit.player == self.player:
            unit.visible = True
        unit.move_to_tile(tile, True, True, True) #final tile
        # unit.final_tile = tile
        unit.draw()
        if unit.player != self.player:
            # self.enemy_unit_pool.remove(unit)
            self.enemy_deployed_units.append(unit)
        else:
            self.play_sound('click_001')
            # self.ally_unit_pool.remove(unit)
            self.ally_deployed_units.append(unit)

            unit.sprite_index = self.selected_sprite_box
            self.select_next_sprite_box()

        # print("placed unit time: ", time.time() - self.start_time)
        # self.start_time = time.time()

        self.endCommand()

    def stepMove(self, data):
        started_moving = []
        still_waiting = []
        for command in self.waiting_objects:
            move = False
            obj = list(command.keys())[0]
            if obj not in self.moving_objects:
                # if obj.obj_type == "projectile":
                #     if obj.unit.visible:
                #         self.play_sound(obj.unit.atk_sound)
                #     move = True
                #     obj.visible = True
                #     obj.move_to_tile(obj.unit.tile, True, False, True)

                if obj.obj_type == "projectile":
                    if obj.unit.tile == obj.tile and obj.unit not in self.moving_objects:#obj.unit.move_freq == 0:

                        if obj.unit.visible:
                            self.play_sound(obj.sound)

                        # if obj.unit not in self.moving_objects:
                        move = True
                        obj.visible = True
                        obj.move_to_tile(obj.unit.tile, True, False, False) #no final tile
                        obj.draw()
                else:
                    move = True

            if move:
                obj.tile_destination = command[obj]["tile_destination"]
                obj.curr_destination = command[obj]["curr_destination"]
                obj.moving_tile_path = command[obj]["moving_tile_path"]
                obj.move_freq = command[obj]["move_freq"]

                obj.x_incr = command[obj]["x_incr"]
                obj.y_incr = command[obj]["y_incr"]
                self.moving_objects.append(obj)
                started_moving.append(obj)
                # self.highlight_path(2, obj.moving_tile_path, color)
                if obj.player == self.player:
                    path = obj.moving_tile_path + [obj.curr_destination]
                    self.highlight_path_edge(2, path, self.green, True)
                    command[obj]["start_tile"].highlight_redux(0, "set_layer")
                
            else:
                still_waiting.append({obj:command[obj]})
        self.waiting_objects = still_waiting

        for obj in started_moving:
            if obj.obj_type == "projectile":
                # angle = self.get_angle(obj.moving_tile_path[0].x1, obj.moving_tile_path[0].y1, obj.tile.x1, obj.tile.y1)
                angle = self.get_angle(obj.curr_destination.x1, obj.curr_destination.y1, obj.tile.x1, obj.tile.y1)
                obj.face_angle(angle)
                # if obj.moving_tile_path[0].y1 < obj.unit.tile.y1:
                #     obj.unit.face_direction("up")
                # elif obj.moving_tile_path[0].y1 > obj.unit.tile.y1:
                #     obj.unit.face_direction("down")
                # if obj.moving_tile_path[0].x1 < obj.unit.tile.x1:
                #     obj.unit.face_direction("left")
                # elif obj.moving_tile_path[0].x1 > obj.unit.tile.x1:
                #     obj.unit.face_direction("right")

            obj.moving_index = 0
            # obj.curr_destination = obj.moving_tile_path.pop()

            # if obj.obj_type == "unit": #UNCOMMENT THESE TWO LINES IF YOU WANT VISION TO UPDATE BEFORE UNIT MOVEMENT
            #     self.update_unit_vision(obj, obj.curr_destination, obj.vision_range, obj.player)

            # if obj.move_freq != 0:
            #     obj.x_incr = (obj.curr_destination.x1 - (obj.x1))/obj.move_freq
            #     obj.y_incr = (obj.curr_destination.y1 - (obj.y1))/obj.move_freq
            # else:
            #     obj.x_incr = 0
            #     obj.y_incr = 0

            if obj.obj_type == "unit":
                if round(obj.x_incr) < 0:
                    obj.face_direction("left")
                elif round(obj.x_incr) > 0:
                    obj.face_direction("right")
                elif round(obj.y_incr) < 0:
                    obj.face_direction("up")
                elif round(obj.y_incr) > 0:
                    obj.face_direction("down")

        self.endCommand()


    #preps variables used for movement#################################################################################################################################
    def setupUnitMove(self, data):
        # self.standby = True
        # self.hover = False
        #extract data
        unit = self.get_unit_by_id(data["unitid"])
        tile = self.get_tile_by_id(data["tileid"])
        #assign movement object and destination
        start_tile = unit.tile

        tile_destination = tile
        curr_destination = unit.tile

        unit.final_tile = tile

        #calculate path and speed
        ghost = False
        final_tiles = []
        # for ally in self.ally_deployed_units:
        #     if ally.final_tile != ally.tile:
        #         final_tiles.append(ally.final_tile)
            # if ally in self.moving_objects and ally != unit:
            #     ghost = True
            #     break
        ghost = True
        if ghost:
            old_targets = unit.move_props["targets"].copy()
            old_ptargets = unit.move_props["player_target"].copy()
            unit.move_props["targets"] = ["tile", "unit"]
            unit.move_props["player_target"] = [unit.player]
        # if self.player != self.player_turn: #uncomment this and include the line below? -1 move bug change pos
        self.get_tiles_by_unit(start_tile, unit, unit.move_props) #this isnt resetting the tile numbering for the shortest path properly for the other player, 
                                                      #moving play doesnt see this at all which works

        
        moving_tile_path = self.get_shortest_path(unit.tile, tile)


        # x_tiles = {} #yikes
        # for ally in self.ally_deployed_units:
        #     if ally.final_tile != ally.tile:
        #         if ally.final_tile in moving_tile_path:
        #             ally.final_tile.terrain
        #             x_tiles[ally.final_tile] = ally.final_tile.terrain
        #             ally.final_tile.terrain = "blocked"
        #     else:
        #         if ally.tile in moving_tile_path:
        #             x_tiles[ally.tile] = ally.tile.terrain
        #             ally.tile.terrain = "blocked"

        # print("len adsf asdf")
        # print(len(x_tiles.keys()))
        # print(x_tiles)
        # if len(x_tiles.keys()) > 0:
        #     self.get_tiles_by_unit(unit, unit.move_props)
        #     moving_tile_path = self.get_shortest_path(unit.tile, tile)
        #     print("redo path")
        #     print("ASPUITAISUBDGUBAISDIPGIUAOS:DBGIUAIS")
        #     print(len(moving_tile_path))

        #     for x_tile in x_tiles.keys():
        #         x_tile.terrain = x_tiles[x_tile]


        move_freq = 40

        # unit.move_props["targets"] = ["tile"]
        # unit.move_props["player_target"] = None
        if ghost:
            unit.move_props["targets"] = old_targets
            unit.move_props["player_target"] = old_ptargets


        #remove starting tile from path
        if unit.tile in moving_tile_path:
            moving_tile_path.remove(unit.tile)

        #highlight path correct color
        if self.player == self.player_turn:
            color = self.main_color
        else:
            color = self.enemy_color
        

        #waitint was here

        #subtract
        unit.move_props["range"] -= len(moving_tile_path)

        #initiate stepmove
        path = moving_tile_path.copy()
        path.reverse()
        covered_path = []
        for tile in path:
            covered_path.append(tile)
            if tile.trapped:
                new_dest = self.halt_movement(unit, tile)
                if new_dest is not None:
                    tile_destination = new_dest
                    covered_path.reverse()
                    moving_tile_path = covered_path
                # if self.player_turn == self.player:
                #     tileid = tile.tileid
                #     unitid = unit.unitid
                #     self.Send({"action": "recieveCommand", "msg":9, "gameid":self.gameid, "unitid":unitid, "tileid":tileid})
            unit.move_to_tile(tile, False, True, True) #no final tile #might have fixed the unit not showing in vision issue?
            if tile == tile_destination:
                # if self.selected_unit is not None:
                #     if self.selected_unit == unit:
                self.deselect(False)
                self.select_unit("m1", tile)
                break

        if unit.player == self.player:
            path = moving_tile_path + [curr_destination] + [start_tile]
            self.highlight_path_edge(2, path, self.yellow, True)
        # print("moving tile path", moving_tile_path)
        # print("start_tile", start_tile)
        # print("first item in path", moving_tile_path[0])
        # moving_tile_path.reverse()
        # print("last item in path", moving_tile_path[0])
        curr_destination = moving_tile_path.pop()
        # moving_tile_path.reverse()
        # print("dest", dest)
        # print(unit.tile)
        # print(unit.tile in moving_tile_path)

        x_incr = math.floor(abs((start_tile.x1 - curr_destination.x1)/move_freq))
        if start_tile.x1 > curr_destination.x1:
            x_incr = x_incr * -1
        y_incr = math.floor(abs((start_tile.y1 - curr_destination.y1)/move_freq))
        if start_tile.y1 > curr_destination.y1:
            y_incr = y_incr * -1

        # print("x incr, y incr", x_incr, y_incr)

        if x_incr != 0:
            move_freq = abs((start_tile.x1 - curr_destination.x1)/x_incr)
        elif y_incr != 0:
            move_freq = abs((start_tile.y1 - curr_destination.y1)/y_incr)

        # print(move_freq)

        # print("curr_destination: ", curr_destination)
        # print("tile_destination: ", tile_destination)

        self.waiting_objects.append({unit:{"tile_destination":tile_destination,"curr_destination":curr_destination,
            "moving_tile_path":moving_tile_path,"move_freq":move_freq,"x_incr":x_incr,"y_incr":y_incr,"start_tile":start_tile}})

        if self.player_turn == self.player:
            self.standby = True
            self.Send({"action": "recieveCommand", "msg":3, "gameid":self.gameid})

        # self.standby = False

        self.endCommand()

    def setupUnitAttack(self, data):
        unit = self.get_unit_by_id(data["unitid"])
        if unit.final_tile is not None: ###THIS LINE RIGHT HERE (and the 3 below it ofc) COULD SERIOUSLY mess things up in the future, but for now we just test...
            unit.tile.unit = None
            unit.tile = unit.final_tile
            unit.final_tile.unit = unit
        start_tile = unit.tile
        tile = self.get_tile_by_id(data["tileid"])

        # old_unit_tile = unit.tile

        # if curr_tile != unit.tile:
        #     unit.tile = curr_tile

        atk = unit.basic_atk()
        self.hidden_projectiles.add(atk)

        if tile.unit is not None:
            target = tile.unit
            atk.unit_targets = target.unitid

        atk.tile_targets = [tile]
        


        self.attacking_units.append(unit)

        if unit.atk_props["area_type"] == "circle" and unit.atk_props["target_type"] == "single":
            moving_tile_path = [tile]
            if tile != unit.tile:
                move_freq = self.get_tile_dist(unit.tile, tile)*atk.proj_speed #unit.atk_props["proj_speed"]#50
            else:
                move_freq = 0

        tile_destination = moving_tile_path[0]
        curr_destination = unit.tile

        curr_destination = moving_tile_path.pop()

        x_incr = math.floor(abs((start_tile.x1 - curr_destination.x1)/move_freq))
        if start_tile.x1 > curr_destination.x1:
            x_incr = x_incr * -1
        y_incr = math.floor(abs((start_tile.y1 - curr_destination.y1)/move_freq))
        if start_tile.y1 > curr_destination.y1:
            y_incr = y_incr * -1

        if x_incr != 0 and y_incr != 0:
            if abs(x_incr) > abs(y_incr):
                move_freq = abs((start_tile.x1 - curr_destination.x1)/x_incr)
            else:
                move_freq = abs((start_tile.y1 - curr_destination.y1)/y_incr)
        elif x_incr != 0:
            move_freq = abs((start_tile.x1 - curr_destination.x1)/x_incr)
        elif y_incr != 0:
            move_freq = abs((start_tile.y1 - curr_destination.y1)/y_incr)

        unit.attack_ready = False

        for tile in moving_tile_path:
            if tile.unit is not None:
                if not unit.atk_props["unit_pierce"]:
                    break

        if unit.tile in moving_tile_path:
            moving_tile_path.remove(unit.tile)

        self.waiting_objects.append({atk:{"tile_destination":tile_destination,"curr_destination":curr_destination,
            "moving_tile_path":moving_tile_path,"move_freq":move_freq,"x_incr":x_incr,"y_incr":y_incr,"start_tile":start_tile}})


        self.deselect(False)
        self.select_unit("m1", unit.tile)
        
        if self.player_turn == self.player:
            self.standby = True
            self.Send({"action": "recieveCommand", "msg":3, "gameid":self.gameid})

            self.Send({"action": "recieveCommand", "msg":10, "gameid":self.gameid, "unitid":unit.unitid, 
                "effect":"attack", "stat_type":"curr_hp", "groupid":target.unitid, "display_hp":False})

        # unit.tile = old_unit_tile

        self.endCommand()

    def setupUnitAbility(self, data):
        unit = self.get_unit_by_id(data["unitid"])
        if unit.final_tile is not None: ###THIS LINE (and the 3 below it ofc) RIGHT HERE COULD SERIOUSLY mess things up in the future, but for now we just test...
            unit.tile.unit = None
            unit.tile = unit.final_tile
            unit.final_tile.unit = unit

        start_tile = unit.tile
        tile = self.get_tile_by_id(data["tileid"])

        # old_unit_tile = unit.tile

        # if curr_tile != unit.tile:
        #     unit.tile = curr_tile
        

        atk = unit.activate()
        # if unit.visible:
        #     self.play_sound(unit.ability_sound)
        groupid = ""
        # path, aoe_tiles = self.get_ability_tiles(unit, tile)
        # if unit.ability_props["target_type"] == "aoe":
        #     print("Checking aoe tiles in setup")
        #     # old_tile = unit.tile
        #     # old_range = unit.ability_props["range"]

        #     # unit.tile = tile

        #     if unit.player != self.player:
        #         self.set_ability_tiles(unit)
        #     path, aoe_tiles = self.get_ability_tiles(unit, tile)

        #     # props = unit.ability_props.copy()
        #     # props["range"] = unit.ability_props["radius"]

        #     # if props["aoe_shape"] == "circle":
        #     #     props["area_type"] = "circle"
        #     # elif props["aoe_shape"] == "line":
        #     #     props["area_type"] = "line"
        #     #     if props["aoe_direction"] == "perpendicular":
        #     #         cardinal = self.get_cardinal_direction(start_tile, tile)
        #     #         if "E" in cardinal or "W" in cardinal:
        #     #             props["aoe_direction"] = ["top", "bottom"]
        #     #         elif "N" in cardinal or "S" in cardinal:
        #     #             props["aoe_direction"] = ["left", "right"]

        #     # print("Props player target", props["player_target"])

        #     # aoe_tiles = self.get_tiles_by_unit(tile, unit, props)

        #     atk.tile_targets = aoe_tiles

        #     # unit.tile = old_tile

        #     for aoe_tile in aoe_tiles:
        #         if aoe_tile.unit is not None:
        #             groupid += aoe_tile.unit.unitid + " "

        #     # old_tile = unit.tile
        #     # old_range = unit.ability_props["range"]


        #     # unit.tile = tile
        #     # unit.ability_props["range"] = unit.ability_props["radius"]

        #     # aoe_tiles = self.get_tiles_by_unit(unit, unit.ability_props)

        #     # unit.ability_props["range"] = old_range

        #     # atk.tile_targets = aoe_tiles

        #     # unit.tile = old_tile

        #     # for aoe_tile in aoe_tiles:
        #     #     if aoe_tile.unit is not None:
        #     #         groupid += aoe_tile.unit.unitid + " "
        # else:
        #     atk.tile_targets = [tile]

        if unit.player != self.player:
                self.set_ability_tiles(unit)

        path, aoe_tiles = self.get_ability_tiles(unit, tile)
        atk.tile_targets = aoe_tiles
        for aoe_tile in aoe_tiles:
            if aoe_tile.unit is not None:
                groupid += aoe_tile.unit.unitid + " "

        atk.unit_targets = groupid


        self.activating_units.append(unit)

        if unit.ability_props["area_type"] == "circle": 
            if unit.ability_props["target_type"] == "single" or unit.ability_props["target_type"] == "aoe":
                moving_tile_path = [tile]#self.get_tiles_by_unit(unit, unit.atk_props)
                if unit.tile != tile:
                    move_freq = self.get_tile_dist(unit.tile, tile)*atk.proj_speed #unit.ability_props["proj_speed"]#50
                else:
                    move_freq = 0
            # elif unit.ability_props["target_type"] == "aoe":
            #     moving_tile_path = [tile]
            #     move_freq = self.get_tile_dist(unit.tile, tile)*unit.ability_props["proj_speed"]#50 #aoe and single the same?
        elif unit.ability_props["area_type"] == "line":
            for line in self.get_tiles_by_unit(start_tile, unit, unit.ability_props):
                if tile in line:
                    moving_tile_path = line
                    moving_tile_path.reverse()
                    move_freq = atk.proj_speed #unit.ability_props["proj_speed"]#50
                    # atk.tile_targets = [moving_tile_path[0]]
                    break

        tile_destination = moving_tile_path[0]
        curr_destination = unit.tile

        curr_destination = moving_tile_path.pop()

        x_incr = math.floor(abs((start_tile.x1 - curr_destination.x1)/move_freq))
        if start_tile.x1 > curr_destination.x1:
            x_incr = x_incr * -1
        y_incr = math.floor(abs((start_tile.y1 - curr_destination.y1)/move_freq))
        if start_tile.y1 > curr_destination.y1:
            y_incr = y_incr * -1

        if x_incr != 0 and y_incr != 0:
            if abs(x_incr) > abs(y_incr):
                move_freq = abs((start_tile.x1 - curr_destination.x1)/x_incr)
            else:
                move_freq = abs((start_tile.y1 - curr_destination.y1)/y_incr)
        elif x_incr != 0:
            move_freq = abs((start_tile.x1 - curr_destination.x1)/x_incr)
        elif y_incr != 0:
            move_freq = abs((start_tile.y1 - curr_destination.y1)/y_incr)

        unit.ability_props["cooldown"] == unit.ability_props["max_cooldown"]
        unit.ability_ready = False

        for tile in moving_tile_path:
            if tile.unit is not None:
                if not unit.atk_props["unit_pierce"]:
                    break

        # if groupid == "":
        #     for tile in moving_tile_path:
        #         if tile.unit is not None and tile.unit is not unit:
        #             groupid = groupid + " " + tile.unit.unitid

        # atk.unit_targets = groupid

        self.waiting_objects.append({atk:{"tile_destination":tile_destination,"curr_destination":curr_destination,
            "moving_tile_path":moving_tile_path,"move_freq":move_freq,"x_incr":x_incr,"y_incr":y_incr,"start_tile":start_tile}})

        self.deselect(False)
        self.select_unit("m1", unit.tile)
        if self.player_turn == self.player:
            self.standby = True
            self.Send({"action": "recieveCommand", "msg":3, "gameid":self.gameid})

            if groupid != "":
                self.Send({"action": "recieveCommand", "msg":10, "gameid":self.gameid, "unitid":unit.unitid, 
                    "effect":"ability", "stat_type":"curr_hp", "groupid":groupid, "display_hp":False})

        # unit.tile = old_unit_tile


        self.endCommand()

    def disconnect(self):
        print("Closing Connection")
        connection.Close()

    def quit(self):
        print("Quitting Game")
        # self.master.destroy()
        self.running = False
        exit()

    def endTurn(self, data):
        if self.ally_deployed_units == [] or self.enemy_deployed_units == []:
            self.disconnect()
            self.quit()
            # self.Send({"action": "close", "gameid":self.gameid})
        else:
            print("Ending Turn")
            for tile in self.tiles: #reset all temp highlighted tiles
                # tile.highlight("reset", tile.base_color, ["right", "left", "top", "bottom"], "center_edges")
                tile.highlight_redux(0, "set_layer")

            self.deselect(True)

            self.selected_tile = None

            self.movable_units = []
            self.attackable_units = []
            self.activatable_units = []

            if self.player_turn != self.player: #reset all movement ranges and attack/activation tracking
                for unit in self.ally_deployed_units:
                    unit.move_props["range"] = unit.move_props["max_range"]
                    unit.attack_ready = True
                    unit.ability_ready = True
                    
            else:
                for unit in self.enemy_deployed_units:
                    unit.move_props["range"] = unit.move_props["max_range"]
                    unit.attack_ready = True
                    unit.ability_ready = True
                    if unit.ability_props["cooldown"] > 0:
                        unit.ability_props["cooldown"] -= 1

            self.player_turn = not self.player_turn

            if self.player == self.player_turn:
                self.end_turn_button.change_text(0, "End Turn", None)
                # self.canvas.itemconfig(self.end_turn_button.text, text="End Turn")
            else:
                self.end_turn_button.change_text(0, "Waiting for Opponent", None)
                # self.canvas.itemconfig(self.end_turn_button.text, text="Waiting for Opponent")
            # if self.player_turn:
            #     self.player_turn = 0
            # else:
            #     self.player_turn = 1
            self.endCommand()

    def endPlacement(self, data):
        player = data["player"]

        if player == self.player:
            self.placement_done = not self.placement_done
            if self.placement_done:
                self.end_turn_button.highlight(None, self.green, True)
                self.end_turn_button.base_color = self.green
                # self.canvas.itemconfig(self.end_turn_button.box, fill="green")
            else:
                self.end_turn_button.highlight(None, self.white, True)
                self.end_turn_button.base_color = self.white
                # self.canvas.itemconfig(self.end_turn_button.box, fill="white")
        else:
            self.enemy_placement_done = not self.enemy_placement_done

        if self.placement_done and self.enemy_placement_done:
            # self.highlight_path(2, self.allied_territory, self.black)
            # self.highlight_path(1, self.allied_territory, self.black)
            self.highlight_path(0, self.allied_territory, self.black)
            self.highlight_path(0, self.allied_territory, "set_layer")
            if self.player == self.player_turn:
                self.end_turn_button.change_text(0, "End Turn", None)
                # self.canvas.itemconfig(self.end_turn_button.text, text="End Turn")
            else:
                self.end_turn_button.change_text(0, "Waiting for Opponent", None)
                # self.canvas.itemconfig(self.end_turn_button.text, text="Waiting for Opponent")
            self.standby = True

            self.end_turn_button.highlight(None, self.white, True)
            self.end_turn_button.base_color = self.white
            # self.canvas.itemconfig(self.end_turn_button.box, fill="white")

            self.Send({"action": "recieveCommand", "msg":0, "gameid":self.gameid, "state":1, "player":self.player})

        self.endCommand()

    def trapTrigger(self, data):
        unit = self.get_unit_by_id(data["unitid"])
        tile = self.get_tile_by_id(data["tileid"])

        self.halt_movement(unit)

    def changeStats(self, data):
        unit = self.get_unit_by_id(data["unitid"])
        effect = data["effect"]
        stat_type = data["stat_type"]
        groupid = data["groupid"]
        display_hp = data["display_hp"]

        if effect == "attack":
            amount = unit.atk_props["dmg"]
        elif effect == "ability":
            amount = unit.ability_props["dmg"]

        if " " in groupid:
            targets = groupid.split()
            for unitid in targets:
                unit = self.get_unit_by_id(unitid)
                if stat_type == "curr_hp":
                    new_hp = unit.curr_hp - amount
                    if new_hp > unit.max_hp:
                        new_hp = unit.max_hp

                    unit.curr_hp = new_hp
                    unit.visible_hp.insert(0, new_hp)
                    if unit.curr_hp <= 0:
                        unit.targetable = False

                    if display_hp:
                        unit.hp_check()
        else:
            unit = self.get_unit_by_id(groupid)
            if stat_type == "curr_hp":
                new_hp = unit.curr_hp - amount
                if new_hp > unit.max_hp:
                    new_hp = unit.max_hp

                unit.curr_hp = new_hp
                unit.visible_hp.insert(0, new_hp)
                if unit.curr_hp <= 0:
                    unit.targetable = False

                if display_hp:
                    unit.hp_check()

        self.endCommand()

    def setupAltAbility(self, data):
        unit = self.get_unit_by_id(data["unitid"])
        tile = self.get_tile_by_id(data["tileid"])
        groupid = data["groupid"]
        groupid_list = groupid.split()
        targets = []
        for target in groupid_list:
            obj = self.get_unit_by_id(target)
            if obj != None:
                targets.append(obj)
            else:
                obj = self.get_tile_by_id(target)
                if obj != None:
                    targets.append(obj)

        unit.ability_props["cooldown"] == unit.ability_props["max_cooldown"]
        unit.ability_ready = False

        unit.ability_func(self, unit, tile, targets)

        self.deselect(False)
        self.select_unit("m1", unit.tile)

        self.endCommand()

    def halt_movement(self, obj, curr_tile):        
        #remove obj from waiting
        if obj in self.waiting_objects:
            self.waiting_objects.remove(obj)
        #remove obj from moving
        # obj.tile_destination = obj.curr_destination  #trigger mid move down below
        # self.next_tile(obj) #same as above line
        obj.move_props["range"] = 0
        return(curr_tile)
        # if obj in self.moving_objects:
        #     self.moving_objects.remove(obj)
        #reset moving_tile_path
        # obj.moving_tile_path = []
        #lower remaining move range to 0? (put in another command?)


    #initial game setup functions######################################################################################################################################
    def __init__(self):
        # self.master=master
        pad=0
        pygame.init()

        infoObject = pygame.display.Info()
        #use settings to save previous game size and recreate it like that?
        # self.screen = pygame.display.set_mode((infoObject.current_w, infoObject.current_h))
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) #fullscreen works!!

        # print(self.screen.get_size())
        # print(pygame.display.get_surface().get_size())

        # size = (700, 500)
        # self.screen = pygame.display.set_mode(size)

        pygame.display.set_caption("SGame")
        self.get_screen_size() #actual screen size: (1791, 1074)

        self.connected_to_server = False
        self.connected_to_player = False
        self.standby = False
        self.menu_mode = False
        self.game_start = False
        self.msg_stack = []
        self.curr_msg = None
        self.upkeep_stack = []
        self.cleanup_stack = []

        self.drawn_elements = []
        self.animated_elements = []
        self.drawn_ui = []
        self.extra_info = []

        self.drawn_animations = []
        # self.ui_boxes = {}
        # self.ui_values = {}
        self.hover_color = "Blue"

        # self.master.bind("<Button-1>", self.m1)
        # self.master.bind("<B1-Motion>", self.m1_drag)
        # self.master.bind('<ButtonRelease-1>', self.m1_release)
        # self.master.bind('<Shift-Button-1>', self.m1_shift)
        # self.master.bind("<Button-2>", self.m2)
        # self.master.bind('<Motion>', self.hover) #motion for click and drag too
        # self.master.bind('<Enter>', self.hover) 
        # self.master.bind('a', self.a)
        # self.master.bind('q', self.q)
        # self.master.bind('s', self.s)
        # self.master.bind('w', self.w)

        self.shift_held = False
        self.click_past_edge_lock = False

        self.hovered_button = None

        self.hovered_tile = None
        self.hovered_box = None


        self.hovered_box_lock = False

        self.select_drag_unit = None
        self.select_drag_tile = None

        self.sprite_selection_adj = []
        self.sprite_selection = []

        self.max_production_points = 10
        self.curr_production_points = self.max_production_points

        self.unlocked_units = Stats.num_units()

        self.load_settings()

        

        

        def on_closing():
            print("Window Close")
            if self.connected_to_server:
                self.disconnect()
            # if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.quit()
            # self.quit()

        # self.master.protocol("WM_DELETE_WINDOW", on_closing)s

        

        # self.start_clock() #undo after ping stuff
        running = True
        clock = pygame.time.Clock()
        self.black = pygame.Color("black")
        self.dark_grey = (100, 100, 100)
        self.darker_grey = (70, 70, 70)
        self.light_grey = (170, 170, 170)
        self.lighter_grey = (200, 200, 200)
        self.lightest_grey = (230, 230, 230)
        self.white = pygame.Color("white")
        self.green = pygame.Color("green")
        self.light_green = pygame.Color("#78ff78")
        self.red = pygame.Color("red")
        self.light_red = pygame.Color("#ff7878")
        self.blue = pygame.Color("blue")
        self.light_blue = pygame.Color("#78ffff")
        self.purple = pygame.Color("purple")
        self.light_purple = pygame.Color("#7878ff")
        self.yellow = pygame.Color("yellow")
        self.light_yellow = pygame.Color("#ffff78")
        x = 0   

        # self.screen.fill(self.white)

        # self.rect = pygame.draw.rect(self.screen, self.red, [55, 200, 100, 70],0)
        # pygame.draw.line(self.screen, self.green, [x, 10], [100+x, 100], 5)
        # pygame.draw.ellipse(self.screen, self.black, [0,0,1700,1000], 2)


        # tile = Tile(self.red, self.x(100), self.y(100))

        # tile.rect.x = 200
        # tile.rect.y = 300
        


        self.all_sprites_list = pygame.sprite.Group()
        self.text_buttons = pygame.sprite.Group()
        self.hidden_buttons = pygame.sprite.Group()
        self.visible_units = pygame.sprite.Group()
        self.hidden_units = pygame.sprite.Group()
        self.visible_projectiles = pygame.sprite.Group()
        self.hidden_projectiles = pygame.sprite.Group()
        self.misc_drawings = []
        self.misc_texts = []
        # self.all_sprites_list.add(tile)

        self.main_menu()

        # self.misc_texts.append(self.new_text(500, 500, 550, 700, "Test text test text test text test text test text test text test text", 30))
        # self.player = 1
        # self.enemy = 0
        # self.ally_unit_pool = []
        # self.main_color = self.blue
        # self.test_unit = Unit(self, self.screen, 500, 500, 700, 700, 1, 1)
        # self.visible_units.add(self.test_unit)

        game_time = 0
        self.selected_unit = None
        self.e_index = -1
        self.m1_pressed = False


        while running:
            # --- Main event loop
            for event in pygame.event.get(): # User did something
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.m1_pressed = True
                        self.m1(event.pos)
                    elif event.button == 3:
                        self.m2(event.pos)
                if event.type==pygame.MOUSEMOTION:
                    self.hover()
                    if self.m1_pressed:
                        self.m1_drag()
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.m1_pressed = False
                        self.m1_release()

                if event.type == pygame.QUIT: #close game
                    running = False

                elif event.type==pygame.KEYDOWN:
                    if event.unicode in ['!','@','#','$','%','^','&','*','(',')']:
                        event.unicode = str(['!','@','#','$','%','^','&','*','(',')'].index(event.unicode)+1)
                    if event.unicode.isdigit():
                        self.num_press(int(event.unicode))
                    elif event.key==pygame.K_a: #select all units
                        self.a()
                    elif event.key==pygame.K_e: #cycle through attack targets
                        self.e()
                    elif event.key==pygame.K_m: #toggle music
                        self.m()
                    elif event.key==pygame.K_n: #toggle sfx
                        self.n()
                    elif event.key==pygame.K_q: #cycle through units
                        self.q()
                    elif event.key==pygame.K_r: #place unit/return unit/attack target
                        self.r()
                    elif event.key==pygame.K_s: #toggle locked multi unit movement paths
                        self.s()
                    elif event.key==pygame.K_w: #toggle attack and move targeting vs ability targeting
                        self.w()
                    elif event.key==pygame.K_x: #quit the game
                        running = False
                    elif event.key==pygame.K_RSHIFT or event.key==pygame.K_LSHIFT:
                        self.shift_held = True
                    elif event.key==pygame.K_RETURN:
                        if not self.connected_to_server:
                            self.play_sound('click_001')
                            self.connect()
                            self.menu_mode = False
                        elif self.connected_to_player:
                            if self.game_state == "setup_units":
                                if len(self.ally_deployed_units) > 0:
                                    self.Send({"action": "recieveCommand", "msg":7, "gameid":self.gameid, "player":self.player})
                            elif self.player_turn == self.player:
                                self.standby = True
                                self.Send({"action": "recieveCommand", "msg":7, "gameid":self.gameid, "player":self.player})
                    elif event.key==pygame.K_UP:
                        self.up()
                    elif event.key==pygame.K_DOWN:
                        self.down()
                    elif event.key==pygame.K_LEFT:
                        self.left()
                    elif event.key==pygame.K_RIGHT:
                        self.right()

                elif event.type==pygame.KEYUP:
                    if event.key==pygame.K_RSHIFT or event.key==pygame.K_LSHIFT:
                        self.shift_held = False

            self.screen.fill(self.white)

            self.all_sprites_list.draw(self.screen)
            self.blit_text(self.text_buttons)

            for drawing in self.misc_drawings:
                pygame.draw.rect(self.screen, self.dark_grey, drawing)

            if self.game_start:
                self.draw_extra(self.tiles)

                self.visible_units.draw(self.screen)
                for unit in self.visible_units:
                    unit.draw_hp()
                self.visible_projectiles.draw(self.screen)

            if self.game_start and self.game_state == "main_phase":
                self.main_phase()
            
            if self.animated_elements:
                self.animate(game_time % 3 == 0)

            for text_item in self.misc_texts:
                self.screen.blit(text_item[0], text_item[1])

            if self.connected_to_server:
                self.pump()


            pygame.display.update() #refresh screen

            game_time += clock.tick(60) #60 fps
     
        pygame.quit()

    def blit_text(self, group):
        for button in group:
            self.screen.blit(button.box, button.box_rect)
            for index in range(0, len(button.secondary_surfaces)):
                if isinstance(button.secondary_surfaces[index], list):
                    for tindex in range(0, len(button.secondary_surfaces[index])):
                        self.screen.blit(button.secondary_surfaces[index][tindex], button.secondary_rects[index][tindex])
                else:
                    self.screen.blit(button.secondary_surfaces[index], button.secondary_rects[index])

    def draw_text(self, group):
        for button in group:
            pygame.draw.rect(button.image, self.black, button.image_rect)
            pygame.draw.rect(button.text_surface, self.black, button.text_rect)

    def draw_extra(self, items):
        for item in items:
            item.blit_extra()


    def loadify(img):
        return pygame.image.load(img).convert_alpha()


    def get_screen_size(self):
        self.screen_width, self.screen_height = pygame.display.get_surface().get_size()
        self.xpix = self.screen_width/1792#1680
        self.ypix = self.screen_height/1120#1050


    def get_tile_dist(self, start, end):
        y = abs(start.posy - end.posy)
        x = abs(start.posx - end.posx)
        return math.sqrt(y**2 + x**2)

    def x(self, value):
        return(value*self.xpix)

    def y(self, value):
        return(value*self.ypix)

    def cenx(self):
        return(self.screen_width/2)

    def ceny(self):
        return(self.screen_height/2)

    def main_menu(self):
        self.menu_mode = True
        pygame.mixer.init()
        self.set_music_volume(0.25)
        self.play_curr_song()
        self.draw_main_menu()

    def new_line(self, x1, y1, x2, y2, color, width):
        return pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), width)

    def new_text(self, x1, y1, x2, y2, text, font_size):
        font = pygame.font.Font('freesansbold.ttf', round(font_size))
        surface = font.render(text, True, pygame.Color("black"), pygame.Color("white"))
        surface.set_colorkey(pygame.Color("white"))

        rect = surface.get_rect()
        rect.center = ((x1+x2)/2, (y1+y2)/2)

        return [surface, rect]

    def draw_main_menu(self):
        self.connect_button = self.new_button(self.screen_width-self.y(105), self.screen_height-self.y(300), self.screen_width-self.y(5), self.screen_height-self.y(200), self.dark_grey, self.lighter_grey, True, "Connect", 1, True)
        # self.all_sprites_list.add(self.connect_button)
        self.text_buttons.add(self.connect_button)

        self.save_button = self.new_button(self.y(5), self.screen_height-self.y(300), self.y(105), self.screen_height-self.y(200), self.dark_grey, self.lighter_grey, True, "Save Squad", 1, True)
        # self.all_sprites_list.add(self.save_button)
        self.text_buttons.add(self.save_button)

        self.load_button = self.new_button(self.y(105), self.screen_height-self.y(300), self.y(205), self.screen_height-self.y(200), self.dark_grey, self.lighter_grey, True, "Load Squad", 1, True)
        # self.all_sprites_list.add(self.load_button)
        self.text_buttons.add(self.load_button)

        self.clear_button = self.new_button(self.y(205), self.screen_height-self.y(300), self.y(305), self.screen_height-self.y(200), self.dark_grey, self.lighter_grey, True, "Clear", 1, True)
        # self.all_sprites_list.add(self.clear_button)
        self.text_buttons.add(self.clear_button)

        # label_font = tkinter.font.Font(family='TkDefaultFont', size=30)
        text = "Production Points: " + str(self.curr_production_points)
        self.production_button = self.new_button(self.y(5), self.screen_height-self.y(400), self.y(305), self.screen_height-self.y(300), self.dark_grey, self.lighter_grey, True, text, 1.2, True)
        # self.all_sprites_list.add(self.production_button)
        self.text_buttons.add(self.production_button)

        self.create_tribal_bonus_ui()

        x = self.x(100)
        y = self.y(100)
        self.shown_unit_img = []
        self.selected_unit_img = []
        self.sprite_selection = []
        self.selected_sprites = []
        self.unit_selection_totals = []

        self.unit_display_names = []

        self.misc_drawings.append(self.new_line(0, self.screen_height-self.y(200), self.screen_width, self.screen_height-self.y(200), self.dark_grey, 4))

        for unit_id in self.unlocked_units:
            stats = Stats.unit_stats(unit_id)

            unit_color = stats["unit_color"]
            unit_name = stats["unit_name"]
            size_mult = stats["size_mult"]
            cost = stats["cost"]

            item_list = []

            if unit_color == "variable":
                img_str = "./Assets/Units/blue_"+unit_name+".png"
            elif unit_color == "constant":
                img_str = "./Assets/Units/"+unit_name+".png"

            item_list.append(img_str)

            item_list.append(str(cost))

            item_list.append("")

            box = self.new_button(x-self.y(75), y-self.y(75), x+self.y(75), y+self.y(75), self.dark_grey, self.lighter_grey, True, item_list, size_mult, False)
            # box = self.canvas.create_rectangle(x-75, y-75, x+75, y+75, outline="black", width=4, fill=None)

            self.drawn_elements.append(box)

            self.sprite_selection.append(box)

            # self.all_sprites_list.add(box)
            self.text_buttons.add(box)

            box.change_text(1, str(cost), 1.5)
            box.change_text(2, "", 1.5)

            if isinstance(box.secondary_rects[1], list):
                for rect in box.secondary_rects[1]:
                    rect.x = x-self.y(65)
                    rect.y = y-self.y(65)
            else:
                box.secondary_rects[1].x = x-self.y(65)
                box.secondary_rects[1].y = y-self.y(65)

            if isinstance(box.secondary_rects[2], list):
                for rect in box.secondary_rects[2]:
                    rect.x = x+self.y(60)
                    rect.y = y-self.y(65)
            else:
                box.secondary_rects[2].x = x+self.y(60)
                box.secondary_rects[2].y = y-self.y(65)

            # box.secondary_rects[2].x = x+self.y(60)
            # box.secondary_rects[2].y = y-self.y(65)

            self.shown_unit_img.append([img_str, size_mult])

            x += self.x(160)

        self.load_comp()

    def create_tribal_bonus_ui(self):
        tribes = ["Vaux", "Nox", "Other"]
        self.tribe_count = {}

        text = "Current Tribal Composition: \n"

        for tribe in tribes:
            self.tribe_count[tribe] = [tribe+" Units: ", 0]

            text += self.tribe_count[tribe][0] + str(self.tribe_count[tribe][1]) + "\n"

        box = self.new_button(self.y(405), self.screen_height-self.y(400), self.y(805), self.screen_height-self.y(300), self.dark_grey, self.lighter_grey, True, text, 1.2, True)

        self.text_buttons.add(box)

    def select_sprite(self, sprite_box):
        index = self.sprite_selection.index(sprite_box)
        stats = Stats.unit_stats(index+1)
        if stats["cost"] <= self.curr_production_points:
            self.play_sound("drop_004")

            self.curr_production_points -= stats["cost"]
            text = "Production Points: " + str(self.curr_production_points)
            self.production_button.change_text(0, text, None)

            text = sprite_box.secondary_texts[2]
            if text == "":
                text = "0"
            text = int(text) + 1
            sprite_box.change_text(2, str(text), None)

            unit_img = self.shown_unit_img[index]

            x = self.x(self.screen_width- 80 -(160*(len(self.selected_sprites))))
            y = self.screen_height-self.y(75)
            
            sprite = self.new_button(x-self.y(75), y-self.y(75), x+self.y(75), y+self.y(75), None, None, False, unit_img[0], unit_img[1], False)
            self.all_sprites_list.add(sprite)

            self.selected_sprites.append(sprite)

            for x in range(0, len(self.sprite_selection)):
                cost = Stats.unit_stats(x+1)["cost"]
                if cost > self.curr_production_points:
                    sprite_box = self.sprite_selection[x]
                    sprite_box.highlight(self.red, None, True)
                    # self.canvas.itemconfig(sprite_box, outline="red")

            self.reset_displayed_sprites()
            self.display_sprite_list()


    def deselect_sprite(self, sprite_box):
        index = self.sprite_selection.index(sprite_box)
        stats = Stats.unit_stats(index+1)

        base_sprite = self.sprite_selection[index]

        img = base_sprite.secondary_texts[0]

        for sprite in self.selected_sprites:
            if sprite.secondary_texts[0] == img:
                self.play_sound("drop_003")
                self.reset_displayed_sprites()
                self.selected_sprites.remove(sprite)
                self.all_sprites_list.remove(sprite)
                self.curr_production_points += stats["cost"]
                text = "Production Points: " + str(self.curr_production_points)

                self.production_button.change_text(0, text, None)

                num = base_sprite.secondary_texts[2]
                text = int(num) - 1
                if text == 0:
                    text = ""
                self.sprite_selection[index].change_text(2, str(text), None)

                self.display_sprite_list()
                break



        for x in range(0, len(self.sprite_selection)):
            cost = Stats.unit_stats(x+1)["cost"]
            if cost <= self.curr_production_points:
                sprite_box = self.sprite_selection[x]
                sprite_box.highlight(sprite_box.base_border_color, None, True)

    def reset_displayed_sprites(self):
        x = self.x(self.screen_width-160)
        for sprite in self.selected_sprites:
            sprite.rect.x = x
            x += self.x(160)

    def create_sprite_tracker(self):
        self.tracked_units = []
        x = self.x(60)#1401
        y = self.y(60)#590
        self.sprite_selection_line = []
        for unit_id in self.initial_unit_pop:
            stats = Stats.unit_stats(unit_id)

            unit_color = stats["unit_color"]
            unit_name = stats["unit_name"]
            size_mult = stats["size_mult"]
            display_name = stats["display_name"]

            if unit_color == "variable":
                if self.player:
                    img_str = "./Assets/Units/red_"+unit_name+".png"
                else:
                    img_str = "./Assets/Units/blue_"+unit_name+".png"
            elif unit_color == "constant":
                img_str = "./Assets/Units/"+unit_name+".png"

            # img_str = "./Assets/"+self.main_color+"_"+unit_name+".png"

            desc_box = self.new_button(x-self.x(50), y-self.y(50), self.board_x1-self.x(10), y+self.y(50), self.dark_grey, self.lighter_grey, True, display_name, 1, False)

            self.text_buttons.add(desc_box)

            self.sprite_selection_adj.append(desc_box)

            text_box = desc_box.secondary_rects[0]
            if isinstance(text_box, list):
                text_box = text_box[0]
            text_box.x = x+self.y(50)+self.x(10)

            box = self.new_button(x-self.x(50), y-self.y(50), x+self.y(50), y+self.y(50), self.dark_grey, self.lighter_grey, True, img_str, size_mult, False)

            self.text_buttons.add(box)

            self.drawn_elements.append(box)

            self.sprite_selection.append(box)

            y += self.y(110)


    def display_sprite_list(self):
        x = self.x(self.screen_width-160)
        for sprite in self.selected_sprites:
            sprite.rect.x = x
            x -= self.x(160)

        self.display_tribal_bonus()

    def display_tribal_bonus(self):
        tribe_count = {}
        for base_sprite in self.sprite_selection:
            index_id = self.sprite_selection.index(base_sprite)
            img = base_sprite.secondary_texts[0]
            for sprite in self.selected_sprites:
                if sprite.secondary_texts[0] == img:
                    tribe = Stats.unit_stats(index_id+1)["tribe"]
                    if tribe in tribe_count.keys():
                        tribe_count[tribe] += 1
                    else:
                        tribe_count[tribe] = 1
        
        #update tribal text display information here

        # for tribe in self.tribe_count:




    def save_settings(self):
        settings_list = [self.music, self.sfx]

        pickle.dump(settings_list, open("settings.p", "wb"))

    def load_settings(self):
        try:
            settings_list = pickle.load(open("settings.p", "rb"))
        except (OSError, IOError) as e:
            settings_list = [True, True]
            pickle.dump(settings_list, open("settings.p", "wb"))
        

        self.music = settings_list[0]

        self.sfx = settings_list[1]


    def save_comp(self):
        sprite_index = []

        for base_sprite in self.sprite_selection:
            index = self.sprite_selection.index(base_sprite)
            img = base_sprite.secondary_texts[0]
            for sprite in self.selected_sprites:
                if sprite.secondary_texts[0] == img:
                    sprite_index.append(index)


        pickle.dump(sprite_index, open("comp.p", "wb"))

    def load_comp(self):
        self.clear_comp()

        try:
            sprite_index = pickle.load(open("comp.p", "rb"))
        except (OSError, IOError) as e:
            sprite_index = []
            pickle.dump(sprite_index, open("comp.p", "wb"))
        
        if sprite_index is not None:
            sprite_index.reverse()

            x = self.x(self.screen_width- 80 -(160*(len(self.selected_sprites))))
            y = self.screen_height-self.y(75)

            for index in sprite_index:
                stats = Stats.unit_stats(index+1)

                self.curr_production_points -= stats["cost"]
                text = "Production Points: " + str(self.curr_production_points)
                self.production_button.change_text(0, text, None)

                num = self.sprite_selection[index].secondary_texts[2]
                if num == "":
                    num = "0"
                text = int(num) + 1
                self.sprite_selection[index].change_text(2, str(text), None)

                unit_img = self.shown_unit_img[index]
                
                sprite = self.new_button(x-self.y(75), y-self.y(75), x+self.y(75), y+self.y(75), None, None, False, unit_img[0], unit_img[1], False)
                self.all_sprites_list.add(sprite)

                self.selected_sprites.append(sprite)

                x -= self.x(160)

            for x in range(0, len(self.sprite_selection)):
                cost = Stats.unit_stats(x+1)["cost"]
                if cost > self.curr_production_points:
                    sprite_box = self.sprite_selection[x]
                    sprite_box.highlight(self.red, None, True)

        self.reset_displayed_sprites()
        self.display_sprite_list()

    def clear_comp(self):
        for base_sprite in self.sprite_selection:
            index = self.sprite_selection.index(base_sprite)
            img = base_sprite.secondary_texts[0]

            base_sprite.change_text(2, "", None)
            base_sprite.highlight(base_sprite.border_color, base_sprite.fill_color, True)

            keep_list = []
            for sprite in self.selected_sprites:
                if sprite.secondary_texts[0] == img:
                    stats = Stats.unit_stats(index + 1)
                    cost = stats["cost"]
                    self.all_sprites_list.remove(sprite)
                    self.curr_production_points += stats["cost"]
                    text = "Production Points: " + str(self.curr_production_points)
                    self.production_button.change_text(0, text, None)

                else:
                    keep_list.append(sprite)

            self.selected_sprites = keep_list

        self.selected_sprites = []


    def new_button(self, x1, y1, x2, y2, border_color, fill_color, hover_highlight, text, size_mult, center_text):
        new_button = Button(self.screen, x1, y1, x2, y2, border_color, fill_color, hover_highlight, text, size_mult, center_text)
        self.drawn_elements.append(new_button)
        return(new_button)

    def delete_main_menu(self):
        self.initial_unit_pop = []
        for base_sprite in self.sprite_selection:
            index_id = self.sprite_selection.index(base_sprite)
            img = base_sprite.secondary_texts[0]
            for sprite in self.selected_sprites:
                if sprite.secondary_texts[0] == img:
                    self.initial_unit_pop.append((index_id+1))

        self.connect_button.delete()
        self.save_button.delete()
        self.load_button.delete()
        self.clear_button.delete()
        self.drawn_elements.remove(self.connect_button)
        self.drawn_elements.remove(self.save_button)
        self.drawn_elements.remove(self.load_button)
        self.drawn_elements.remove(self.clear_button)

        self.text_buttons.remove(self.connect_button)
        self.text_buttons.remove(self.save_button)
        self.text_buttons.remove(self.load_button)
        self.text_buttons.remove(self.clear_button)

        self.connect_button = None
        self.save_button = None
        self.load_button = None
        self.clear_button = None

        new_elements = []
        for element in self.drawn_elements:
            if element not in self.selected_sprites:
                self.all_sprites_list.remove(element)
                # if element in self.text_buttons:
                #     self.text_buttons.remove(element)
                self.misc_drawings = []
            else:
                new_elements.append(element)

        self.text_buttons = pygame.sprite.Group()


        self.drawn_elements = new_elements

        self.shown_unit_img = []
        self.sprite_selection = []
        self.sprite_selection_adj = []

        self.select_drag_unit = None
        self.select_drag_tile = None

    def game_board(self):
        self.player_turn = 0
        if self.player:
            self.main_color = self.red
            self.enemy_color = self.blue
        else:
            self.main_color = self.blue
            self.enemy_color = self.red
        self.both_ready = False
        
        for sprite in self.selected_sprites:
            sprite.kill()
        self.selected_sprites = []

        self.game_state = "standby"
        self.dim_x = 12
        self.dim_y = 12
        self.board = [[None for x in range(self.dim_x)] for y in range(self.dim_y)]
        self.tiles = []
        self.movement_tiles = []
        self.all_movement_tiles = []
        self.attack_tiles = []
        self.attack_tile_edge = []
        self.all_attack_tiles = []
        self.ability_tiles = []
        self.all_ability_tiles = []
        self.ability_hover_tiles = []
        self.ability_lines = []

        self.temp_hover_tiles = []

        self.visible_tiles = []

        self.allied_territory = []
        self.allied_x = self.dim_x
        self.allied_y = 5

        self.selected_tile = None
        self.selected_unit = None
        self.selected_units = []

        # self.board[4][1].trapped = True

        self.create_board(self.dim_x, self.dim_y, 0.85)

    def draw_game_board(self, dim_x, dim_y):
        self.total_num_tiles = dim_x*dim_y
        self.mountain_threshold = 0.90
        self.bh = self.screen_height-self.y(10)-self.y(dim_y*2)#self.y(994-dim_x*2) #max = 995
        self.bw = self.screen_height-self.y(10)-self.y(dim_x*2)#self.y(994-dim_y*2) #both dimensions use self.y to make them squares

        self.tiles = []
        self.draw_game_grid(dim_x, dim_y)

        if not self.check_board_textures():
            self.delete_tiles()
            self.create_board(self.dim_x, self.dim_y, 0.85)

        else:
            self.end_turn_button = self.new_button(self.board_x2+self.x(10), self.y(850), self.screen_width-self.x(5), self.screen_height-self.y(5), self.dark_grey, self.lighter_grey, True, "Lock Unit Placement", 1.5, True)
            self.text_buttons.add(self.end_turn_button)
            self.draw_toggle_ui()

            self.create_sprite_tracker()

            self.populate_unit_pool()
            self.create_highlight_ui()
            # self.hide_unit_info()
            self.highlight_path_edge(0, self.allied_territory, self.purple, True)
            self.game_start = True
            self.play_curr_song()

    def delete_tiles(self):
        for tile in self.tiles:
            tile.delete()
            del tile

    def check_board_textures(self):
        for tile in self.tiles:
            tile.search_num = 0

        search_num = 1
        start_tile = self.tiles[0]
        start_tile.search_num = search_num
        edge_tiles = start_tile.adj.values()
        next_edges = []
        tiles_in_range = []
        grass_tiles = 0
        if start_tile.terrain == "grass":
            grass_tiles += 1

        while search_num < self.total_num_tiles:
            search_num += 1
            for tile in edge_tiles:
                if tile != "edge":
                    if tile.terrain in ["grass"] and tile not in tiles_in_range:

                        tile.search_num = search_num
                        tiles_in_range.append(tile)
                        grass_tiles += 1

                        for adj_tile in tile.adj.values():
                            if adj_tile != "edge":
                                if adj_tile.search_num == 0 and adj_tile != start_tile:
                                    next_edges.append(adj_tile)

            edge_tiles = next_edges.copy()
            next_edges = []
            if not edge_tiles:
                break

        return grass_tiles == self.grass_tiles


    def draw_game_grid(self, dim_x, dim_y):
        self.board_y1 = self.y(5)
        start_y = self.board_y1
        self.tile_width = math.floor(self.bh/dim_y)
        self.tile_height = math.floor(self.bh/dim_y)
        for y_axis_base in range(0, dim_y):
            if self.player == 0:
                y_axis = y_axis_base
            else:
                y_axis = dim_y-y_axis_base-1
            self.board_x1 = self.cenx()-self.bw/2-self.x(dim_x)
            start_x = self.board_x1
            for x_axis in range(0, dim_x):
                terrain = self.board_textures[y_axis][x_axis]
                new_tile = Tile(self, self.screen, start_x, start_y, start_x+self.bw/dim_x, start_y+self.bh/dim_y, x_axis, y_axis, self.x(2), terrain)
                self.drawn_elements.append(new_tile)
                self.all_sprites_list.add(new_tile)
                self.board[y_axis][x_axis] = new_tile
                self.tiles.append(new_tile)
                start_x += math.floor(self.bw/dim_x + self.y(2))
                if y_axis < 5 and self.player:
                    self.allied_territory.append(new_tile)
                elif y_axis > 6 and not self.player:
                    self.allied_territory.append(new_tile)
            start_y += math.floor(self.bh/dim_y + self.y(2))
            self.board_x2 = start_x
        self.board_y2 = start_y

        for y_axis_base in range(0, dim_y):
            if self.player == 0:
                y_axis = y_axis_base
            else:
                y_axis = dim_y-y_axis_base-1
            for x_axis in range(0, dim_x):
                if y_axis == 0:
                    self.board[y_axis][x_axis].adj["top"] = "edge"
                else:
                    self.board[y_axis][x_axis].adj["top"] = self.board[y_axis-1][x_axis]
                if y_axis == dim_y-1:
                    self.board[y_axis][x_axis].adj["bottom"] = "edge"
                else:
                    self.board[y_axis][x_axis].adj["bottom"] = self.board[y_axis+1][x_axis]
                if x_axis == 0:
                    self.board[y_axis][x_axis].adj["right"] = "edge"
                else:
                    self.board[y_axis][x_axis].adj["right"] = self.board[y_axis][x_axis-1]
                if x_axis == dim_x-1:
                    self.board[y_axis][x_axis].adj["left"] = "edge"
                else:
                    self.board[y_axis][x_axis].adj["left"] = self.board[y_axis][x_axis+1]

    def populate_unit_pool(self): #find
        self.units = []
        self.ally_units = []
        self.enemy_units = []
        self.ally_unit_pool = []
        self.enemy_unit_pool = []
        self.ally_deployed_units = []
        self.enemy_deployed_units = []
        self.movable_units = []
        self.attackable_units = []
        self.activatable_units = []

        self.standby = True
        for nameid in self.initial_unit_pop:
            self.Send({"action": "recieveCommand", "msg":1, "gameid":self.gameid, "x1":0, "y1":0, "x2":self.tile_width, "y2":self.tile_height, "nameid":nameid, "player":self.player})
        self.Send({"action": "recieveCommand", "msg":0, "gameid":self.gameid, "state":0, "player":self.player})
        self.game_state = "standby"

    def declare_winner(self):
        # for tile in self.tiles:
        #     tile.delete_border()

        self.reveal_map()

        if self.ally_deployed_units == []:
            text = "You Lose"
        elif self.enemy_deployed_units == []:
            text = "You Win"

        button = self.new_button(self.screen_width/2 - self.x(100), self.screen_height/2 - self.y(100), self.screen_width/2 + self.x(100), self.screen_height/2 + self.y(100), self.dark_grey, self.lighter_grey, True,  text, 1, True)

        self.text_buttons.add(button)

        self.end_turn_button.change_text(0, "Quit Game", None)

    def upkeep(self):
        if self.game_state == "upkeep":
            if self.upkeep_stack:
                if not self.msg_stack:
                    self.msg_stack = self.upkeep_stack
                    self.upkeep_stack = []
                    self.msg_pop()
            elif self.player_turn == self.player:
                self.standby = True
                self.Send({"action": "recieveCommand", "msg":0, "gameid":self.gameid, "state":2, "player":self.player})
                # self.game_state = "standby"

    def main_phase(self):
        if self.moving_objects:
            for obj in self.moving_objects:
                if obj.curr_destination is not None: #changed curr to tile when switching to array of moving objects...
                    self.move_object()
                    break


    def animate(self, pop):
        if self.animated_elements:
            still_animating = []

            for obj in self.animated_elements:
                if obj.cycle_sprites:
                    if pop:
                        image = obj.cycle_sprites.pop()
                    else:
                        image = obj.cycle_sprites[-1]
                else:
                    image = None

                for rect in obj.animated_rects:
                    if image is not None:
                        if obj not in still_animating:
                            still_animating.append(obj)
                        self.screen.blit(image, rect)

                    else:
                        obj.delete()

            self.animated_elements = still_animating

    def pump(self):
        self.Pump()
        connection.Pump()

    def move_object(self):
        for obj in self.moving_objects:
            obj.incr_move(obj.x_incr, obj.y_incr)
            obj.draw()
            if obj.moving_index >= obj.move_freq-1:
                self.next_tile(obj)
            else:
                if obj.obj_type == "unit" and obj.moving_index % 20 == 0:
                    self.play_sound(obj.move_sound)
                obj.moving_index += 1

    def next_tile(self, obj):
        if obj.player == self.player:
            self.highlight_path_edge(2, obj.moving_tile_path, self.green, True)
            obj.curr_destination.highlight_redux(1, "set_layer")

        if obj.curr_destination != obj.tile_destination:
            if obj.obj_type == "unit":
                self.update_unit_vision(obj, obj.curr_destination, obj.vision_range, obj.player)

            obj.moving_index = 0
            obj.x_incr = 0
            obj.y_incr = 0

            next_destination = obj.moving_tile_path.pop()
            if obj.obj_type == "unit":
                if obj.curr_destination.adj["left"] == next_destination:
                    obj.face_direction("right")
                elif obj.curr_destination.adj["right"] == next_destination:
                    obj.face_direction("left")
                elif obj.curr_destination.adj["top"] == next_destination:
                    if not self.player:
                        obj.face_direction("up") #original
                    else:
                        obj.face_direction("down")
                elif obj.curr_destination.adj["bottom"] == next_destination:
                    if not self.player:
                        obj.face_direction("down") #original
                    else:
                        obj.face_direction("up")

            obj.x_incr = math.floor(abs((obj.curr_destination.x1 - next_destination.x1)/obj.move_freq))
            if  obj.curr_destination.x1 > next_destination.x1:
                obj.x_incr = obj.x_incr * -1
            obj.y_incr = math.floor(abs((obj.curr_destination.y1 - next_destination.y1)/obj.move_freq))
            if  obj.curr_destination.y1 > next_destination.y1:
                obj.y_incr = obj.y_incr * -1

            if obj.x_incr != 0:
                obj.move_freq = abs((next_destination.x1 - obj.curr_destination.x1)/obj.x_incr)
            elif obj.y_incr != 0:
                obj.move_freq = abs((next_destination.y1 - obj.curr_destination.y1)/obj.y_incr)

            obj.curr_destination = next_destination 

            # if obj.obj_type == "unit": #UNCOMMENT THESE TWO LINES IF YOU WANT VISION TO UPDATE BEFORE UNIT MOVEMENT
            #     self.update_unit_vision(obj, obj.curr_destination, obj.vision_range, obj.player)

            if obj.obj_type != "unit":
                angle = self.get_angle(obj.curr_destination.x1, obj.curr_destination.y1, obj.tile.x1, obj.tile.y1)
                obj.face_angle(angle)
            # self.endCommand()
        else:
            # obj.move_freq = 0
            # unit.final_tile = obj.curr_destination
            # obj.moving_index = 0
            obj.x_incr = 0
            obj.y_incr = 0
            
            if obj.obj_type == "projectile":
                self.moving_objects.remove(obj)
                self.standby = False

                groupid = obj.unit_targets
                if groupid != None:
                    for unitid in groupid.split():
                        unit = self.get_unit_by_id(unitid)
                        unit.hp_check()

                if obj.curr_destination.foggy:
                    obj.destroy()
                else:
                    obj.end_animation()
            else:
                obj.move_to_tile(obj.curr_destination, True, True, False) #final tile
                obj.draw()
                self.moving_objects.remove(obj)
                self.standby = False

            if self.player_turn == self.player and obj.obj_type == "unit":
                if obj.move_props["max_range"] <= 0:
                    self.movable_units.remove(obj)
            obj.curr_destination = None
            if self.waiting_objects:
                self.stepMove("")
            # self.endCommand()


    #visual/ui functions###############################################################################################################################################
    def highlight_path(self, layer, path, color):
        if color == "set_layer":
            for tile in path:
                tile.highlight_redux(layer, "set_layer")
        else:
            for tile in path:
                tile.highlight_redux(layer, [color]*5)

    def highlight_path_edge(self, layer, path, color, center):
        for tile in path:
            curr_colors = tile.color_layers[layer]

            if tile.adj["left"] not in path:
                curr_colors[0] = color

            if tile.adj["right"] not in path:
                curr_colors[1] = color

            if self.player:
                if tile.adj["bottom"] not in path:
                    curr_colors[2] = color

                if tile.adj["top"] not in path:
                    curr_colors[3] = color

            else:
                if tile.adj["top"] not in path:
                    curr_colors[2] = color

                if tile.adj["bottom"] not in path:
                    curr_colors[3] = color

            if center:
                curr_colors[4] = color

            tile.highlight_redux(layer, curr_colors)


    def highlight_box(self, index, border_color, fill_color):
        self.sprite_selection[index].highlight(border_color, fill_color, True)
        self.sprite_selection_adj[index].highlight(border_color, fill_color, True)


    def create_highlight_ui(self):
        texts = ["ABILITY", "ATTACK", "MOVEMENT", "HEALTH"]
        num_boxes = len(texts)
        x = self.board_x2 + self.x(10)
        y = self.y(10)
        width = self.screen_width - x - self.x(10)
        height = self.y(50)
        self.main_unit_info = []

        for i in range(0, num_boxes):
            text = texts.pop()
            # box = self.canvas.create_rectangle(x, y, x + width, y + height, width=3, outline='black', fill=None)
            # label = self.canvas.create_text(x+self.x(20), y+self.y(height/2), anchor=W, text=text, activefill='red')
            # value = self.canvas.create_text(x+self.x(240), y+self.y(height/2), anchor=E, text="", activefill='red')

            items = [text, ""]
            box = self.new_button(x, y, x+width, y+height, self.light_grey, self.light_grey, True, items, 1.2, True)

            self.hidden_buttons.add(box)
            self.main_unit_info.append(box)
            # self.drawn_elements.append(box)
            # self.drawn_elements.append(label)
            # self.drawn_elements.append(value)

            # self.drawn_ui.append(box)
            # self.drawn_ui.append(label)
            # self.drawn_ui.append(value)

            # self.ui_boxes[text] = box
            # self.ui_values[text] = value
            y += height+  self.y(5)#82.5


        height = self.y(200)

        self.desc_box = self.new_button(x, y, x+width, y+height, self.dark_grey, self.lighter_grey, True, "", 1.2, False)

        self.desc_box.dynamic_box_height = True

        self.hidden_buttons.add(self.desc_box)

        # box = self.canvas.create_rectangle(x, y, x + width, y + height, width=3, outline='black', fill=None)
        # text1 = self.canvas.create_text(x+self.x(15), y+self.y(20), anchor=W, text="test")
        # text2 = self.canvas.create_text(x+self.x(15), y+self.y(40), anchor=W, text="test")
        # text3 = self.canvas.create_text(x+self.x(15), y+self.y(60), anchor=W, text="test")
        # text4 = self.canvas.create_text(x+self.x(15), y+self.y(80), anchor=W, text="test")

        # self.drawn_ui.append(box)
        # self.drawn_ui.append(text1)
        # self.drawn_ui.append(text2)
        # self.drawn_ui.append(text3)
        # self.drawn_ui.append(text4)

        # self.extra_info.append(box)
        # self.extra_info.append(text1)
        # self.extra_info.append(text2)
        # self.extra_info.append(text3)
        # self.extra_info.append(text4) 


    def show_unit_info(self, unit):
        text = "HEALTH: " + str(unit.curr_hp) + "/" + str(unit.max_hp)

        if unit.curr_hp/unit.max_hp > 0.67:
            color = self.light_green
        elif unit.curr_hp/unit.max_hp > 0.34:
            color = self.light_yellow
        elif unit.curr_hp/unit.max_hp > 0:
            color = self.light_red
        else:
            color = self.light_grey

        self.main_unit_info[0].change_text(0, text, None)
        self.main_unit_info[0].highlight(None, color, True)
        self.main_unit_info[0].base_color = color


        text = "MOVEMENT RANGE: " + str(unit.move_props["range"]) + "/" + str(unit.move_props["max_range"])
        
        if unit.move_props["range"]/unit.move_props["max_range"] > 0.67:
            color = self.light_green
        elif unit.move_props["range"]/unit.move_props["max_range"] > 0.34:
            color = self.light_yellow
        elif unit.move_props["range"]/unit.move_props["max_range"] > 0:
            color = self.light_red
        else:
            color = self.light_grey

        self.main_unit_info[1].change_text(0, text, None)
        self.main_unit_info[1].highlight(None, color, True)
        self.main_unit_info[1].base_color = color

        if unit.atk_props["dmg"] > 0:
            text = "ATTACK: " + str(unit.atk_props["dmg"]) + " DMG " + str(unit.atk_props["range"]) + " Range"
        elif unit.atk_props["dmg"] < 0:
            text = "ATTACK: " + str(unit.atk_props["dmg"]*-1) + " HEAL " + str(unit.atk_props["range"]) + " Range"

        if unit.attack_ready:
            color = self.light_green
        else:
            color = self.light_grey

        self.main_unit_info[2].change_text(0, text, None)
        self.main_unit_info[2].highlight(None, color, True)
        self.main_unit_info[2].base_color = color

        # text = str(unit.ability_props["dmg"]) + " DMG " + str(unit.ability_props["range"]) + " Range"
        if unit.ability_props["dmg"] > 0:
            text = "ABILITY: " + str(unit.ability_props["dmg"]) + " DMG " + str(unit.ability_props["cooldown"]) + " Cooldown" #str(unit.ability_props["range"]) + " Range" + 
        elif unit.ability_props["dmg"] < 0:
            text = "ABILITY: " + str(unit.ability_props["dmg"]*-1) + " HEAL " + str(unit.ability_props["cooldown"]) + " Cooldown" #str(unit.ability_props["range"]) + " Range" + 

        if unit.ability_ready and unit.ability_props["cooldown"] == 0:
            color = self.light_green
        else:
            color = self.light_grey

        self.main_unit_info[3].change_text(0, text, None)
        self.main_unit_info[3].highlight(None, color, True)
        self.main_unit_info[3].base_color = color

        for box in self.main_unit_info:
            if box not in self.text_buttons:
                self.text_buttons.add(box)
            if box in self.hidden_buttons:
                self.hidden_buttons.remove(box)

    def hide_unit_info(self):
        for box in self.main_unit_info:
            if box not in self.hidden_buttons:
                self.hidden_buttons.add(box)
            if box in self.text_buttons:
                self.text_buttons.remove(box)

        if self.desc_box not in self.hidden_buttons:
            self.hidden_buttons.add(self.desc_box)
        if self.desc_box in self.text_buttons:
            self.text_buttons.remove(self.desc_box)

    def show_extra_info(self, unit, i):
        text = ""

        if i == 0:
            if unit.curr_hp == unit.max_hp:
                text = "Unit is currently at full health!"
            else:
                text = "Currently at " + str(unit.curr_hp) + " health out of " + str(unit.max_hp) + " max."
                text += "\nIf this units health drops to zero, it will be removed from the game."

        elif i == 1:
            text = "Targets one Tile.\nHas a range of " + str(unit.move_props["range"]) + " of " + str(unit.move_props["max_range"]) + " max."
            text += "\n"
            if unit.atk_props["terrain_pierce"]:
                if unit.atk_props["unit_pierce"]:
                    text += "Can pass through both Units and Terrain."
                else:
                    text += "Can pass through Terrain."
            elif unit.atk_props["unit_pierce"]:
                text += "Can pass through Units."
            else:
                text += "Cannot pass through Units or Terrain."


        elif i == 2:
            text = "Targets one Unit."
            text += "\nHas a range of " + str(unit.atk_props["range"]) + "."
            text += "\nDeals " + str(unit.atk_props["dmg"]) + " damage on hit."
            if unit.atk_props["terrain_pierce"]:
                if unit.atk_props["unit_pierce"]:
                    text += "\nCan pierce both Units and Terrain."
                else:
                    text += "\nCan pierce Terrain."
            elif unit.atk_props["unit_pierce"]:
                text += "\nCan pierce Units."
            else:
                text += "\nCannot pierce Units or Terrain."
        else:
            if unit.ability_props["area_type"] == "line":
                text += "Targets one line of Tiles."
                if unit.atk_props["unit_pierce"]:
                    text += "\nDeals " + str(unit.ability_props["dmg"]) + " damage to all Units hit."
                else:
                    text += "\nDeals " + str(unit.ability_props["dmg"]) + " damage to the first Unit hit."
            elif unit.ability_props["target_type"] == "single":
                text += "\nTargets one Tile."
                text += "\nDeals " + str(unit.ability_props["dmg"]) + " damage on hit."
            text += "\nHas a range of " + str(unit.ability_props["range"]) + "."
            if unit.atk_props["terrain_pierce"]:
                if unit.atk_props["unit_pierce"]:
                    text += "\nCan pierce both Units and Terrain."
                else:
                    text += "\nCan pierce Terrain."
            elif unit.atk_props["unit_pierce"]:
                text += "\nCan pierce Units."
            else:
                text += "\nCannot pierce Units or Terrain."

        self.desc_box.change_text(0, text, None)

        if self.desc_box not in self.text_buttons:
            self.text_buttons.add(self.desc_box)
        if self.desc_box in self.hidden_buttons:
            self.hidden_buttons.remove(self.desc_box)

    def hide_extra_info(self):
        if self.desc_box not in self.hidden_buttons:
            self.hidden_buttons.add(self.desc_box)
        if self.desc_box in self.text_buttons:
            self.text_buttons.remove(self.desc_box)

    def update_unit_vision(self, unit, start_tile, vision_range, player):
        for tile in self.tiles:
            tile.search_num = 0
        search_num = 1
        start_tile.search_num = search_num
        edge_tiles = start_tile.adj.values()
        next_edges = []
        tiles_in_range = [start_tile]
        visible_units = []
        while search_num < vision_range+1:
            search_num += 1
            for tile in edge_tiles:
                if tile != "edge":
                    tile.search_num = search_num
                    tiles_in_range.append(tile)
                    if tile.unit is not None:
                        if tile.unit.player != unit.player:
                            visible_units.append(tile.unit)
                    if tile.terrain != "mountain":
                        for adj_tile in tile.adj.values():
                            if adj_tile != "edge":
                                if adj_tile.search_num == 0:
                                    next_edges.append(adj_tile)
            edge_tiles = next_edges.copy()
            next_edges = []

        for enemy in unit.visible_units:
            if enemy not in visible_units:
                if enemy.player != self.player:
                    unit.visible_units.remove(enemy)
                    shared = False
                    for ally in self.ally_deployed_units:
                        if enemy in ally.visible_units:
                            shared = True
                    if not shared:
                        enemy.visible = False
                        enemy.draw()
                if unit in enemy.visible_units:
                    if unit.player != self.player:
                        enemy.visible_units.remove(unit)
                        shared = False
                        for other_enemy in self.enemy_deployed_units:
                            if unit in other_enemy.visible_units:
                                shared = True
                        if not shared:
                            unit.visible = False
                            unit.draw()


        for enemy in visible_units:
            if enemy not in unit.visible_units:
                unit.visible_units.append(enemy)
                enemy.visible = True
                enemy.draw()
            if unit not in enemy.visible_units:
                enemy.visible_units.append(unit)
                unit.visible = True
                unit.draw()

        if player == self.player:
            if unit.visible_tiles:
                new_tile_set = set(tiles_in_range)
                unit_tile_set = set(unit.visible_tiles)
                for tile in new_tile_set - unit_tile_set:
                    tile.toggle_fog(False)
                for tile in unit_tile_set - new_tile_set:
                    shared = False
                    for ally in self.ally_deployed_units:
                        if tile in ally.visible_tiles and ally != unit:
                            shared = True
                            break

                    if not shared:
                        tile.toggle_fog(True)

                unit.visible_tiles = tiles_in_range

            else:
                unit.visible_tiles = tiles_in_range
                self.visible_tiles = self.visible_tiles + unit.visible_tiles
                for tile in tiles_in_range:
                    tile.toggle_fog(False)
                    if tile.unit is not None:
                        if tile.unit.player != unit.player:
                            unit.visible_units.append(tile.unit)


    def draw_toggle_ui(self):
        base_x = self.board_x2 + self.x(10) #self.x(1350)
        x = base_x
        width = self.y(50)
        gap = self.x(15)

        if self.click_past_edge_lock:
            img = "Assets/UI/lockOn.png"
        else:
            img = "Assets/UI/lockOff.png"
        self.s_button = self.new_button(x, self.y(790), x+width, self.y(840), self.dark_grey, self.lighter_grey, True, img, 1, False)
        self.text_buttons.add(self.s_button)

        x += width + gap#66.5

        if self.music:
            img = "Assets/UI/musicOn.png"
        else:
            img = "Assets/UI/musicOff.png"
        self.music_button = self.new_button(x, self.y(790), x+width, self.y(840), self.dark_grey, self.lighter_grey, True, img, 1, False)
        self.text_buttons.add(self.music_button)

        x += width + gap

        if self.sfx:
            img = "Assets/UI/audioOn.png"
        else:
            img = "Assets/UI/audioOff.png"
        self.sfx_button = self.new_button(x, self.y(790), x+width, self.y(840), self.dark_grey, self.lighter_grey, True, img, 1, False)
        self.text_buttons.add(self.sfx_button)

        x += width + gap

        self.ping_button = self.new_button(x, self.y(790), x+width, self.y(840), self.dark_grey, self.lighter_grey, True, "Ping", 1, False)
        self.text_buttons.add(self.ping_button)


    #click response functions###########################################################################################################################################
    def m1_shift(self, event):
        self.shift_held = True
        self.m1(event)

    def m1(self, event):
        self.start_time = time.time()
        if self.menu_mode:
            if self.connect_button.rect.collidepoint(pygame.mouse.get_pos()):
                if self.selected_sprites:
                    self.play_sound('click_001')
                    self.save_comp()
                    self.connect()
                    self.menu_mode = False
                else:
                    print("You need at least one unit in your battalion!")
            elif self.save_button.rect.collidepoint(pygame.mouse.get_pos()):
                # if self.selected_sprites:
                self.play_sound('confirmation_001')
                self.save_comp()
            elif self.load_button.rect.collidepoint(pygame.mouse.get_pos()):
                self.play_sound('click_001')
                self.load_comp()
            elif self.clear_button.rect.collidepoint(pygame.mouse.get_pos()):
                self.play_sound('back_001')
                self.clear_comp()
            else:
                for sprite_box in self.sprite_selection:
                    if sprite_box.rect.collidepoint(pygame.mouse.get_pos()):
                        self.select_sprite(sprite_box)
                        break

        elif self.game_start and not self.standby:
            self.game_mode_m1(event)

        self.shift_held = False

    def play_sound(self, sound):
        if self.sfx:
            sound = pygame.mixer.Sound('Audio/' + sound + '.ogg')
            sound.play()

    def play_curr_song(self):
        if self.music:
            pygame.mixer.music.stop()
            if self.menu_mode:
                self.play_song("incredible")
            elif self.game_start:
                self.play_song("dominusdeus")
        else:
            pygame.mixer.music.stop()

    def play_song(self, song):
        pygame.mixer.music.load('Audio/' + song + '.ogg')
        pygame.mixer.music.play()

    def set_music_volume(self, volume):
        pygame.mixer.music.set_volume(volume)

    def game_mode_m1(self, event):
        self.start_time = time.time()
        
        if self.s_button.rect.collidepoint(pygame.mouse.get_pos()):
            self.s()

        elif self.music_button.rect.collidepoint(pygame.mouse.get_pos()):
            self.m()

        elif self.sfx_button.rect.collidepoint(pygame.mouse.get_pos()):
            self.n()

        elif self.ping_button.rect.collidepoint(pygame.mouse.get_pos()):

            print("Testing Ping")
            self.Send({"action": "recieveCommand", "msg":25, "gameid":self.gameid, "player":self.player})
        else:
            if self.game_state == "setup_units":
                if len(self.ally_deployed_units) > 0 and self.end_turn_button.rect.collidepoint(pygame.mouse.get_pos()):
                    self.Send({"action": "recieveCommand", "msg":7, "gameid":self.gameid, "player":self.player})
                else:#if not self.placement_done:
                    self.place_units_m1(None)

            elif self.player_turn == self.player:
                if self.end_turn_button.rect.collidepoint(pygame.mouse.get_pos()):
                    self.standby = True
                    self.Send({"action": "recieveCommand", "msg":7, "gameid":self.gameid, "player":self.player})
                else:
                    if self.game_state == "main_phase":
                        self.main_phase_click(event, "m1", None)


    def place_units_m1(self, tile):
        #create a stack and pull units from the top of it, show it on the side and highlight the one that is next to be popped, 
        #^^allow the user to select a differet one if they want
        for x in range(0, len(self.initial_unit_pop)):
            box = self.sprite_selection[x]
            box_adj = self.sprite_selection_adj[x]
            if box.rect.collidepoint(pygame.mouse.get_pos()) or box_adj.rect.collidepoint(pygame.mouse.get_pos()):
                self.highlight_box(self.selected_sprite_box, self.sprite_selection[self.selected_sprite_box].base_border_color, None)
                self.highlight_box(x, self.red, None) #zzz
                self.selected_sprite_box = x
                break

        if self.ally_unit_pool:
            if tile is not None:
                self.selected_tile = tile
            else:
                self.selected_tile = None
                for tile in self.tiles:
                    if tile.unit is None and tile in self.allied_territory and self.selected_sprite_box is not None:
                        if tile.rect.collidepoint(pygame.mouse.get_pos()):
                            self.selected_tile = tile
                            break

            if self.selected_tile is not None:
                if self.selected_tile.terrain == "grass" and self.selected_tile.unit is None:
                    unit = self.ally_unit_pool[self.selected_sprite_box]
                    self.highlight_box(self.selected_sprite_box, self.green, None)
                    self.deployed_sprite_boxes.append(self.selected_sprite_box)
                    self.standby = True
                    self.Send({"action": "recieveCommand", "msg":2, "gameid":self.gameid, "unitid":unit.unitid, "tileid":self.selected_tile.tileid})

        for unit in self.ally_deployed_units:
            tile = unit.tile
            if tile.rect.collidepoint(pygame.mouse.get_pos()):
                self.select_drag_unit = unit
                self.select_drag_tile = unit.tile
                return

        self.select_drag_unit = None
        self.select_drag_tile = None

    def select_next_sprite_box(self):
        for x in range(0, len(self.initial_unit_pop)):
            box = self.sprite_selection[x]
            if x not in self.deployed_sprite_boxes:
                self.selected_sprite_box = x
                self.highlight_box(x, self.red, None)
                return

        self.selected_sprite_box = None

    def return_sprite_to_box(self, sprite_index, unit):
        unit.move(unit.x1-2000,unit.y1-2000,unit.x2-2000,unit.y2-2000)

        if unit.player == self.player:
            unit.visible = False

        unit.draw()

        if unit.player != self.player:
            self.enemy_deployed_units.remove(unit)
        else:
            self.ally_deployed_units.remove(unit)

        # tile = unit.tile

        unit.tile.unit = None
        unit.tile = None

        unit.remove_vision()

        # unit.visible_tiles = []

        # self.update_unit_vision(unit, tile, unit.vision_range, self.player)

        if self.selected_sprite_box is not None:
            self.highlight_box(self.selected_sprite_box, self.sprite_selection[self.selected_sprite_box].base_border_color, None)
        self.highlight_box(sprite_index, self.red, None)
        self.selected_sprite_box = sprite_index
        self.deployed_sprite_boxes.remove(self.selected_sprite_box)

    def m1_drag(self):
        if self.select_drag_unit is not None:
            for tile in self.tiles:
                if tile.rect.collidepoint(pygame.mouse.get_pos()):
                    if tile != self.select_drag_tile and tile in self.allied_territory and tile.terrain in self.select_drag_unit.move_props["terrain"]:
                        # self.select_drag_tile.highlight("temp", self.hovered_tile.base_color, ["right", "left", "top", "bottom"], "center_edges")
                        self.select_drag_tile.highlight_redux(0, "set_layer")

                        self.select_drag_tile = tile
                        # self.select_drag_tile.highlight("temp", "blue", ["right", "left", "top", "bottom"], "center_edges")
                        self.select_drag_tile.highlight_redux(2, [self.blue]*5)
                        self.select_drag_unit.move_to_tile(tile, True, False, False)
                        self.select_drag_unit.draw()

    def m1_release(self):
        if self.select_drag_unit is not None and self.select_drag_unit.final_tile != self.select_drag_unit.tile:
            self.play_sound("click_001")
            self.select_drag_unit.move_to_tile(self.select_drag_tile, True, True, True)
            self.select_drag_unit.draw()
            self.select_drag_unit = None
            self.select_drag_tile = None


    def m2(self, event):
        if self.menu_mode:
            for sprite_box in self.sprite_selection:
                if sprite_box.rect.collidepoint(pygame.mouse.get_pos()):
                    self.deselect_sprite(sprite_box)
                    break

        elif self.game_start and not self.standby:
            if self.game_state == "setup_units":
                self.return_units_m2()

            elif self.game_state == "main_phase":
                if self.player_turn == self.player:
                    self.main_phase_click(event, "m2", None)

    def return_units_m2(self):
        for x in range(0, len(self.initial_unit_pop)):
            box = self.sprite_selection[x]
            box_adj = self.sprite_selection_adj[x]
            if box.rect.collidepoint(pygame.mouse.get_pos()) or box_adj.rect.collidepoint(pygame.mouse.get_pos()):
                for unit in self.ally_deployed_units:
                    if unit.sprite_index == x:
                        self.return_sprite_to_box(x, unit)
                        return

        for unit in self.ally_deployed_units:
            tile = unit.tile
            if tile.rect.collidepoint(pygame.mouse.get_pos()):
                self.return_sprite_to_box(unit.sprite_index, unit)
                break


    def main_phase_click(self, event, click, tile):
        if self.selected_unit:
            check = False
            for box in self.main_unit_info: #undo info later
                # box = self.drawn_ui[i]
                # box = self.main_unit_info[i]
                if box.rect.collidepoint(pygame.mouse.get_pos()):
                    check = True
                    self.hovered_box_lock = True
                    self.show_extra_info(self.selected_unit, self.main_unit_info.index(box))

            if not check:
                self.hovered_box_lock = False
                self.hide_extra_info()

            # elif self.main_unit_info.index(box) == len(self.main_unit_info)-1:
            #     self.hovered_box_lock = False
            #     self.hide_extra_info()

            # coords = self.canvas.coords(self.hovered_box)
            # if (coords[2] > event.x > coords[0]) and (coords[3] > event.y > coords[1]):
            # if self.hovered_box.rect.collidepoint(pygame.mouse.get_pos()):
            #     self.hovered_box_lock = True
            # else:
            #     self.hovered_box_lock = False
            #     self.hide_extra_info()

        if tile is not None:
            self.selected_tile = tile
        else:
            self.selected_tile = None
            for tile in self.tiles:
                if tile.rect.collidepoint(pygame.mouse.get_pos()):
                    if (tile.unit is not None and tile.unit.targetable) or tile.unit is None:
                        self.selected_tile = tile
                        break

        if self.selected_tile is not None:

            if len(self.selected_units) > 1:
                self.selected_units.sort(key=lambda unit: unit.get_dist_from_tile(tile))

            if self.movement_tiles and click == "m1":
                if self.selected_tile in self.movement_tiles and len(self.selected_units) == 1 and self.selected_unit.movable():
                    if self.selected_unit.tile != self.selected_tile:

                        unitid = self.selected_unit.unitid
                        tileid = self.selected_tile.tileid

                        self.standby = True
                        self.Send({"action": "recieveCommand", "msg":4, "gameid":self.gameid, "unitid":unitid, "tileid":tileid})

                elif len(self.selected_units) > 1 and not self.shift_held:
                    taken_tiles = []
                    for selected_unit in self.selected_units:
                        if not selected_unit.movable():
                            taken_tiles.append(selected_unit.tile)

                    for selected_unit in self.selected_units:
                        if selected_unit.movable():
                            if selected_unit.predicted_move_tile != selected_unit.tile and selected_unit.predicted_move_tile is not None:

                                unitid = selected_unit.unitid
                                tileid = selected_unit.predicted_move_tile.tileid

                                self.standby = True
                                self.Send({"action": "recieveCommand", "msg":4, "gameid":self.gameid, "unitid":unitid, "tileid":tileid})

                else:
                    self.check_select(click)

            elif self.attack_tiles and click == "m2" and self.selected_tile != self.selected_unit.tile:
                if self.selected_tile in self.attack_tiles and self.selected_tile.unit is not None and self.selected_tile.unit.player in self.selected_unit.atk_props["player_target"]:

                    tileid = self.selected_tile.tileid

                    if len(self.selected_units) > 1:
                        for selected_unit in self.selected_units:
                            attack_tiles = self.get_tiles_by_unit(selected_unit.tile, selected_unit, selected_unit.atk_props)

                            if self.selected_tile in attack_tiles: #predictive health checks to not overkill? 
                                unitid = selected_unit.unitid

                                self.standby = True
                                self.Send({"action": "recieveCommand", "msg":5, "gameid":self.gameid, "unitid":unitid, "tileid":tileid})
                    else:
                        unitid = self.selected_unit.unitid

                        self.standby = True
                        self.Send({"action": "recieveCommand", "msg":5, "gameid":self.gameid, "unitid":unitid, "tileid":tileid})

                else:

                    self.check_select(click)

            elif self.ability_tiles and click == "m2":
                if self.selected_tile in self.ability_tiles:

                    if self.selected_unit.secondary_props is None:
                        unitid = self.selected_unit.unitid
                        tileid = self.selected_tile.tileid
                        if self.selected_unit.ability_type == "pnc":
                            self.standby = True
                            self.Send({"action": "recieveCommand", "msg":6, "gameid":self.gameid, "unitid":unitid, "tileid":tileid})
                        elif self.selected_unit.ability_type == "alt":
                            groupid = ""
                            if tile.unit is not None:
                                groupid += tile.unit.unitid + " "

                            self.standby = True
                            self.Send({"action": "recieveCommand", "msg":11, "gameid":self.gameid, "unitid":unitid, "tileid":tileid, "groupid":groupid})

                    else:
                        if self.selected_unit.cycles == self.selected_unit.secondary_props["cycles"]:
                            unitid = self.selected_unit.unitid
                            tileid = self.selected_tile.tileid

                            groupid = self.selected_unit.secondary_targets

                            self.standby = True
                            self.selected_unit.cycles = 1
                            self.Send({"action": "recieveCommand", "msg":11, "gameid":self.gameid, "unitid":unitid, "tileid":tileid, "groupid":groupid})
                        else:
                            if self.selected_tile.unit is not None:
                                target = self.selected_tile.unit.unitid
                            else:
                                target = self.selected_tile.tileid

                            self.selected_unit.secondary_targets += target + " "

                            if self.selected_unit.secondary_props["target_type"] == "aoe":
                                # old_range = self.selected_unit.secondary_props["range"]
                                # self.selected_unit.seconday_props["range"] = self.selected_unit.secondary_props["radius"]
                                props = self.selected_unit.secondary_props.copy()
                                props["range"] = self.selected_unit.secondary_props["radius"]
                                self.ability_hover_tiles = self.get_tiles_by_unit(self.selected_unit.tile, self.selected_unit, props)
                                # self.selected_unit.seconday_props["range"] = old_range

                            self.ability_tiles = self.get_tiles_by_unit(self.selected_unit.tile, self.selected_unit, self.selected_unit.secondary_props)

                            new_range = []
                            if self.selected_unit.secondary_props["area_type"] == "line":
                                for line in self.ability_tiles:
                                    self.ability_lines.append(line)
                                    for tile in line:
                                        new_range.append(tile)

                                def sort_key(line):
                                    if len(line) > 0:
                                        return line[0].x1
                                    return None
                                self.ability_lines.sort(key=sort_key)
                                self.ability_tiles = new_range


                            self.highlight_path(1, self.ability_tiles, self.purple) ###
                            self.highlight_path(2, self.ability_hover_tiles, self.yellow)

                            self.selected_unit.cycles += 1

                else:
                    self.check_select(click)

            elif self.selected_tile.unit is not None:
                self.check_select(click)

            else:
                self.check_select(click) #might not want to reselect in this else statement in the check select


    def check_select(self, click):
        if not self.shift_held:
            self.deselect(True)

        for obj in self.moving_objects:
            if obj.obj_type == "unit" and obj.final_tile == self.selected_tile:
                obj.tile.unit = None
                self.selected_tile.unit = obj
                obj.tile = self.selected_tile
                break

        self.select_unit(click, self.selected_tile)
                        
    def num_press(self, num):
        if self.menu_mode and num <= len(self.sprite_selection):
            if self.shift_held:
                self.deselect_sprite(self.sprite_selection[num-1])
            else:
                self.select_sprite(self.sprite_selection[num-1])

        elif self.game_start: 
            if self.game_state == "setup_units" and num <= len(self.sprite_selection):
                if self.shift_held:
                    for unit in self.ally_deployed_units:
                        if unit.sprite_index == num-1:
                            self.return_sprite_to_box(num-1, unit)
                else:
                    if self.hovered_tile in self.allied_territory and self.hovered_tile.unit is None:
                        unit = self.ally_unit_pool[num-1]
                        if unit in self.ally_deployed_units:
                            if self.hovered_tile.terrain == "grass":
                                unit.move_to_tile(self.hovered_tile, True, True, True)
                                unit.draw()
                        else:
                            self.highlight_box(self.selected_sprite_box, self.sprite_selection[self.selected_sprite_box].base_border_color, None)
                            self.highlight_box(num-1, self.red, None)
                            self.selected_sprite_box = num-1
                            self.place_units_m1(self.hovered_tile)

            elif self.game_state == "main_phase" and num <= len(self.ally_deployed_units):
                self.play_sound("switch_005")
                selected_tile = self.ally_deployed_units[num-1].tile

                self.select_unit("m1", selected_tile)

                self.force_update_hover(None)


    def a(self):
        if self.game_start and not self.standby and self.player_turn == self.player:
            self.play_sound("switch_005")

            self.multi_select(self.ally_deployed_units)

            self.force_update_hover(None)

    def s(self):
        if self.game_start and not self.standby and self.player_turn == self.player:
            self.click_past_edge_lock = not self.click_past_edge_lock
            self.play_sound("switch_005")

            if self.click_past_edge_lock:
                self.s_button.change_text(0, "Assets/UI/lockOn.png", None)
            else:
                self.s_button.change_text(0, "Assets/UI/lockOff.png", None)

            self.force_update_hover(None)

    def m(self):
        self.play_sound("switch_005")
        self.music = not self.music

        if self.music:
            self.music_button.change_text(0, "Assets/UI/musicOn.png", None)
        else:
            self.music_button.change_text(0, "Assets/UI/musicOff.png", None)

        self.play_curr_song()

        self.save_settings()

        self.force_update_hover(None)

    def n(self):
        self.sfx = not self.sfx
        self.play_sound("switch_005")

        if self.sfx:
            self.sfx_button.change_text(0, "Assets/UI/audioOn.png", None)
        else:
            self.sfx_button.change_text(0, "Assets/UI/audioOff.png", None)

        self.save_settings()

        self.force_update_hover(None)


    def q(self):
        if self.game_start and self.game_state == "main_phase" and not self.standby and self.player_turn == self.player:
            self.hovered_tile = None
            self.e_index = 0
            self.play_sound("switch_005")

            selected_unit = self.ally_deployed_units[0]
            selected_tile = selected_unit.tile

            if self.selected_units:
                index = self.ally_deployed_units.index(self.selected_unit) + 1 #check before indexing
                if index != len(self.ally_deployed_units):
                    selected_unit = self.ally_deployed_units[index]
                    selected_tile = selected_unit.tile
                self.deselect(True)

            if selected_tile != selected_unit.final_tile:
                selected_tile = selected_unit.final_tile

            if (not selected_unit.movable() and not selected_unit.attack_ready) and selected_unit.ability_ready:
                self.main_phase_click(None, "m2", selected_tile)
            else:
                self.main_phase_click(None, "m1", selected_tile)

            self.force_update_hover(None)

    def w(self):
        if self.game_start and not self.standby and self.selected_unit is not None and len(self.selected_units) == 1 and self.player_turn == self.player:
            curr_unit = self.selected_unit
            # print((curr_unit.movable))
            if ((self.attack_tile_edge or self.movement_tiles) or not (curr_unit.movable() or curr_unit.attack_ready)) and curr_unit.ability_ready and not self.ability_tiles:
                self.deselect(False)
                tile = curr_unit.tile
                if tile != curr_unit.final_tile:
                    tile = curr_unit.final_tile
                self.main_phase_click(None, "m2", tile)
                self.play_sound("switch_005")
                self.force_update_hover(None)

            elif self.ability_tiles and (curr_unit.movable or curr_unit.attack_ready):
                self.deselect(False)
                tile = curr_unit.tile
                if tile != curr_unit.final_tile:
                    tile = curr_unit.final_tile
                self.main_phase_click(None, "m1", tile)
                self.play_sound("switch_005")
                self.force_update_hover(None)

            # elif not (curr_unit.movable or curr_unit.attack_ready) and curr_unit.ability_ready:
            #     self.deselect(False)
            #     tile = curr_unit.tile
            #     if tile != curr_unit.final_tile:
            #         tile = curr_unit.final_tile
            #     self.main_phase_click(None, "m2", tile)
            #     self.play_sound("switch_005")
            #     self.force_update_hover(None)

            # elif (curr_unit.movable or curr_unit.attack_ready) and not curr_unit.ability_ready:
            #     self.deselect(False)
            #     tile = curr_unit.tile
            #     if tile != curr_unit.final_tile:
            #         tile = curr_unit.final_tile
            #     self.main_phase_click(None, "m1", tile)
            #     self.play_sound("switch_005")
            #     self.force_update_hover(None)




    def e(self):
        self.hovered_tile = None
        if self.attack_tiles:
            if self.e_index >= len(self.attack_tiles):
                self.e_index = 0
            self.force_update_hover(list(self.attack_tiles)[self.e_index])
            self.e_index += 1
        elif self.ability_tiles:
            if self.ability_lines:
                if self.e_index < 0:
                    self.e_index = 0
                else:
                    if self.shift_held:
                        self.e_index -= 1
                        if self.e_index < 0:
                            self.e_index = len(self.ability_lines)-1
                    else:
                        self.e_index += 1
                        if self.e_index >= len(self.ability_lines):
                            self.e_index = 0

                def sort_key(line):
                    if len(line) > 0:
                        center = self.selected_unit.tile
                        tile = line [0]
                        if tile.posx < center.posx:
                            if (tile.posy < center.posy and not self.player) or (tile.posy > center.posy and self.player):
                                return 8
                            elif tile.posy == center.posy:
                                return 7
                            else:
                                return 6
                        elif tile.posx == center.posx:
                            if (tile.posy < center.posy and not self.player) or (tile.posy > center.posy and self.player):
                                return 1
                            else:
                                return 5
                        else:
                            if (tile.posy < center.posy and not self.player) or (tile.posy > center.posy and self.player):
                                return 2
                            elif tile.posy == center.posy:
                                return 3
                            else:
                                return 4
                    return 100
                self.ability_lines.sort(key=sort_key)


                tile = None
                for x in range(0, len(self.ability_lines)):
                    if len(self.ability_lines[self.e_index]) > 0:
                        tile = self.ability_lines[self.e_index][0]
                        break
                    else:
                        if self.shift_held:
                            self.e_index -= 1
                            if self.e_index < 0:
                                self.e_index = len(self.ability_lines)-1
                        else:
                            self.e_index += 1
                            if self.e_index >= len(self.ability_lines):
                                self.e_index = 0


                if tile is not None:
                    self.force_update_hover(tile)


    def r(self):
        if self.game_state == "setup_units":
            if self.shift_held:
                if self.hovered_tile is not None and self.hovered_tile.unit is not None and self.hovered_tile.unit in self.ally_deployed_units:
                    unit = self.hovered_tile.unit
                else:
                    unit = self.ally_deployed_units[0]
                self.return_sprite_to_box(unit.sprite_index, unit)
            else:
                if self.hovered_tile is not None and len(self.ally_deployed_units) < len(self.initial_unit_pop):
                    self.place_units_m1(self.hovered_tile)

        elif self.game_state == "main_phase":
            if self.attack_tiles:
                if self.hovered_tile is not None and self.hovered_tile in self.attack_tiles:
                    self.main_phase_click(None, "m2", self.hovered_tile)
                    self.hovered_tile = None
                    self.e_index = -1

            elif self.ability_tiles:
                if self.hovered_tile is not None and self.hovered_tile in self.ability_tiles:
                    self.main_phase_click(None, "m2", self.hovered_tile)
                    self.hovered_tile = None
                    self.e_index = -1



    def i(self):
        pass
        #switch the ally deployed units menu to the currently unused menu?

    def up(self):
        if self.game_state == "setup_units":
            if self.hovered_tile is not None:
                if not self.player:
                    tile = self.hovered_tile.adj["top"]
                else:
                    tile = self.hovered_tile.adj["bottom"]

                if tile == "edge" or tile not in self.allied_territory:
                    tile = self.allied_territory[int(self.allied_x*(self.allied_y))-(self.allied_x - self.hovered_tile.posx)]

            else:
                tile = self.allied_territory[int(self.allied_x*(self.allied_y)-self.allied_x/2)-1]

            self.force_update_hover(tile)

        elif self.game_state == "main_phase" and self.selected_unit is not None:
            unit = self.selected_unit
            tile = unit.tile
            if not self.player:
                self.main_phase_click(None, "m1", self.selected_unit.tile.adj["top"])
            else:
                self.main_phase_click(None, "m1", self.selected_unit.tile.adj["bottom"])

            if tile == unit.tile:
                self.main_phase_click(None, "m1", tile)


    def down(self):
        if self.game_state == "setup_units":
            if self.hovered_tile is not None:
                if not self.player:
                    tile = self.hovered_tile.adj["bottom"]
                else:
                    tile = self.hovered_tile.adj["top"]

                if tile == "edge" or tile not in self.allied_territory:
                    tile = self.allied_territory[self.hovered_tile.posx]

            else:
                tile = self.allied_territory[int(self.allied_x/2)-1]
            self.force_update_hover(tile)

        elif self.game_state == "main_phase" and self.selected_unit is not None:
            unit = self.selected_unit
            tile = unit.tile
            if not self.player:
                self.main_phase_click(None, "m1", self.selected_unit.tile.adj["bottom"])
            else:
                self.main_phase_click(None, "m1", self.selected_unit.tile.adj["top"])

            if tile == unit.tile:
                self.main_phase_click(None, "m1", tile)

    def left(self):
        if self.game_state == "setup_units":
            if self.hovered_tile is not None:
                tile = self.hovered_tile.adj["right"]

                if tile == "edge" or tile not in self.allied_territory:
                    tile = self.tiles[int(self.dim_x*(self.dim_y - self.hovered_tile.posy))-1]

            else:
                tile = self.allied_territory[int(self.allied_x*math.ceil(self.allied_y/2))-1]
            self.force_update_hover(tile)

        elif self.game_state == "main_phase" and self.selected_unit is not None:
            unit = self.selected_unit
            tile = unit.tile
            self.main_phase_click(None, "m1", self.selected_unit.tile.adj["right"])

            if tile == unit.tile:
                self.main_phase_click(None, "m1", tile)

    def right(self):
        if self.game_state == "setup_units":
            if self.hovered_tile is not None:
                tile = self.hovered_tile.adj["left"]

                if tile == "edge" or tile not in self.allied_territory:
                    tile = self.tiles[int(self.dim_x*(self.dim_y - self.hovered_tile.posy))-self.dim_x]

            else:
                tile = self.allied_territory[int(self.allied_x*math.ceil(self.allied_y/2))-self.allied_x]
                
            self.force_update_hover(tile)

        elif self.game_state == "main_phase" and self.selected_unit is not None:
            unit = self.selected_unit
            tile = unit.tile
            self.main_phase_click(None, "m1", self.selected_unit.tile.adj["left"])

            if tile == unit.tile:
                self.main_phase_click(None, "m1", tile)

    def multi_select(self, units):
        self.shift_held = True

        for unit in units:
            self.select_unit("m1", unit.tile)

        self.shift_held = False

    def select_unit(self, click, tile):
        if tile.unit is not None and tile == tile.unit.final_tile:
            if not self.shift_held:
                self.selected_units = []
                if self.selected_unit is not None:
                    self.highlight_path(0, self.movement_tiles, "set_layer")
                    self.highlight_path(0, self.attack_tiles, "set_layer")
                    self.highlight_path(0, self.attack_tile_edge, "set_layer")

            self.selected_unit = tile.unit
            self.show_unit_info(tile.unit) #undo comment for info later 

            if tile.unit not in self.selected_units:
                self.selected_units.append(tile.unit)

            # if self.selected_unit:
            #     if self.shift_held:
            #         self.selected_unit = tile.unit
            #         self.selected_units.append(self.selected_unit)
            #     # else:
            # else:
            #     self.selected_unit = tile.unit
            #     self.selected_units.append(self.selected_unit)
            #     self.show_unit_info(self.selected_unit)

            if self.player_turn == self.player:
                if self.selected_unit:
                    tile.highlight_redux(1, [self.main_color]*5)

                    if self.selected_unit in self.ally_deployed_units:
                        if click == "m1":
                            self.movement_tile_sets = []
                            self.attack_tile_sets = []
                            self.attack_tile_edge = []
                            for selected_unit in self.selected_units:

                                if selected_unit.movable():

                                    if len(self.selected_units) > 1: #questionable solution to a unit moving to where another unit was not placed
                                        old_targets = selected_unit.move_props["targets"].copy()
                                        old_ptargets = selected_unit.move_props["player_target"].copy()

                                        selected_unit.move_props["targets"].append("unit")
                                        selected_unit.move_props["player_target"].append(self.player)

                                        selected_unit.movement_tiles = self.get_tiles_by_unit(selected_unit.tile, selected_unit, selected_unit.move_props)
                                        selected_unit.move_props["targets"] = old_targets
                                        selected_unit.move_props["player_target"] = old_ptargets


                                    else: #this line immideatlley below
                                        selected_unit.movement_tiles = self.get_tiles_by_unit(selected_unit.tile, selected_unit, selected_unit.move_props)
                                        
                                    self.movement_tile_sets.extend(selected_unit.movement_tiles)

                                if selected_unit.attack_ready:
                                    selected_unit.attack_tiles = self.get_tiles_by_unit(selected_unit.tile, selected_unit, selected_unit.atk_props)
                                    self.attack_tile_sets.extend(selected_unit.attack_tiles)

                                    old_targets = selected_unit.atk_props["targets"].copy()

                                    selected_unit.atk_props["targets"].append("tile")
                                    selected_unit.attack_tile_edge = (self.get_tiles_by_unit(selected_unit.tile, selected_unit, selected_unit.atk_props))
                                    selected_unit.atk_props["targets"] = old_targets

                                    self.attack_tile_edge.extend(selected_unit.attack_tile_edge)

                            self.movement_tiles = set(self.movement_tile_sets)
                            self.attack_tiles = set(self.attack_tile_sets)


                            self.highlight_path_edge(1, list(self.movement_tiles)+[self.selected_unit.tile], self.blue, True)
                            self.highlight_path_edge(1, list(self.attack_tile_edge)+[self.selected_unit.tile], self.red, False)
                            self.highlight_path_edge(1, list(self.attack_tiles)+[self.selected_unit.tile], self.red, True)
                            self.force_update_hover(None)

                        elif click == "m2":
                            if self.selected_unit.ability_ready and self.selected_unit.ability_props["cooldown"] == 0:
                                # if self.selected_unit.ability_props["target_type"] == "aoe":
                                #     props = self.selected_unit.ability_props.copy()
                                #     props["range"] = self.selected_unit.ability_props["radius"]

                                #     if props["aoe_shape"] == "aoe":
                                #         self.ability_hover_tiles = self.get_tiles_by_unit(self.selected_unit.tile, self.selected_unit, props)


                                # self.ability_tiles = self.get_tiles_by_unit(self.selected_unit.tile, self.selected_unit, self.selected_unit.ability_props)

                                # new_range = []
                                # if self.selected_unit.ability_props["area_type"] == "line":
                                #     for line in self.ability_tiles:
                                #         self.ability_lines.append(line)
                                #         for tile in line:
                                #             new_range.append(tile)
                                #     self.ability_tiles = new_range

                                self.ability_tiles, self.ability_hover_tiles = self.set_ability_tiles(self.selected_unit)

                                self.highlight_path(1, self.ability_tiles, self.purple)
                                # self.highlight_path(2, self.ability_hover_tiles, self.yellow)

    def deselect(self, hide_ui):
        if hide_ui:
            self.hide_unit_info()
        self.highlight_path(0, self.movement_tiles, "set_layer") ### clear move
        self.movement_tiles = []
        self.all_movement_tiles = []
        self.highlight_path(0, self.attack_tiles, "set_layer") ###
        self.attack_tiles = []
        self.highlight_path(0, self.attack_tile_edge, "set_layer") ###
        self.attack_tile_edge = []
        self.all_attack_tiles = []
        self.highlight_path(0, self.ability_tiles, "set_layer") ###
        self.ability_tiles = []
        self.highlight_path(0, self.all_ability_tiles, "set_layer")
        self.all_ability_tiles = []
        self.highlight_path(0, self.ability_hover_tiles, "set_layer")
        self.ability_hover_tiles = []
        self.ability_lines = []

        for unit in self.selected_units:
            unit.movement_tiles = []
            unit.attack_tiles = []

        self.selected_units = []

        if self.selected_unit:
            self.selected_unit.tile.highlight_redux(0, "set_layer")

        self.selected_unit = None
        # self.selected_tile = None

    def color_adjust(self, base_color):
        if base_color == self.light_green:
            return self.green
        elif base_color == self.green:
            return self.light_green

        elif base_color == self.light_red:
            return self.red
        elif base_color == self.red:
            return self.light_red

        elif base_color == self.light_blue:
            return self.blue
        elif base_color == self.blue:
            return self.light_blue

        elif base_color == self.light_purple:
            return self.purple
        elif base_color == self.purple:
            return self.light_purple

        elif base_color == self.light_yellow:
            return self.yellow
        elif base_color == self.yellow:
            return self.light_yellow

        elif base_color == self.lightest_grey:
            return self.lighter_grey
        elif base_color == self.lighter_grey:
            return self.lightest_grey

        elif base_color == self.light_grey:
            return self.dark_grey
        elif base_color == self.dark_grey:
            return self.light_grey

        elif base_color == self.darker_grey:
            return self.black
        elif base_color == self.black:
            return self.darker_grey

        else:
            return None

    #hover response functions
    def hover(self):
        no_button = True
        for button in self.text_buttons:
            if button.rect.collidepoint(pygame.mouse.get_pos()):
                if self.hovered_button is not None:
                    self.hovered_button.highlight(self.hovered_button.border_color, self.hovered_button.fill_color, False)
                    if self.hovered_button in self.sprite_selection_adj:
                        index = self.sprite_selection_adj.index(self.hovered_button)
                        other_button = self.sprite_selection[index]
                        other_button.highlight(other_button.border_color, other_button.fill_color, False)
                    # if self.hovered_button == button:
                    #     self.hovered_button.highlight(self.hovered_button.border_color, self.hovered_button.fill_color)
                    # else:
                    #     self.hovered_button.highlight(self.hovered_button.base_border_color, self.hovered_button.base_color)

                if button.hover_highlight:
                    border_color = self.color_adjust(button.border_color)
                    fill_color = self.color_adjust(button.fill_color)
                    button.highlight(border_color, fill_color, False)
                    if button in self.sprite_selection_adj:
                        index = self.sprite_selection_adj.index(button)
                        other_button = self.sprite_selection[index]
                        other_button.highlight(border_color, fill_color, False)

                self.hovered_button = button
                no_button = False
                break

        if no_button and self.hovered_button is not None:
            self.hovered_button.highlight(self.hovered_button.border_color, self.hovered_button.base_color, False)
            if self.hovered_button in self.sprite_selection_adj:
                    index = self.sprite_selection_adj.index(self.hovered_button)
                    other_button = self.sprite_selection[index]
                    other_button.highlight(other_button.border_color, other_button.fill_color, False)
            self.hovered_button = None

        if self.game_start:
            no_tile = True
            for tile in self.tiles:
                if tile.rect.collidepoint(pygame.mouse.get_pos()):
                    no_tile = False
                    if self.hovered_tile != tile:
                        self.change_hovered_tile(tile)
                        if self.ability_hover_tiles:
                            if tile in self.ability_tiles:
                                # self.move_aoe_tiles(tile)
                                pass
                            else:
                                self.highlight_path(1, self.ability_hover_tiles, "set_layer")
                        break
            if self.selected_unit and not self.hovered_box_lock: #undo entire statement
                check = False
                for box in self.main_unit_info:
                    if box.rect.collidepoint(pygame.mouse.get_pos()):
                        check = True
                        self.hovered_box = box
                        self.show_extra_info(self.selected_unit, self.main_unit_info.index(box))
                        break
                    # elif self.main_unit_info.index(box) == len(self.main_unit_info)-1:
                    #     self.hovered_box = None
                    #     self.hide_extra_info()
                # print("check: ", check)
                # print("check before in box", self.desc_box in self.text_buttons)
                if not check:
                    self.hovered_box = None
                    self.hide_extra_info()
                    # print("hiding unit extra info")

                # print("check after in box", self.desc_box in self.text_buttons)


            mouse_x, mouse_y = pygame.mouse.get_pos()

            if no_tile and self.hovered_tile is not None and not (self.board_x2 > mouse_x > self.board_x1 and self.board_y2 > mouse_y > self.board_y1):
                self.hovered_tile.highlight_redux(1, "set_layer")
                self.hovered_tile = None

    def move_aoe_tiles(self, tile):
        self.highlight_path(1, self.ability_hover_tiles, "set_layer")

        # old_range = self.selected_unit.ability_props["range"]
        # old_tile = self.selected_unit.tile
        # self.selected_unit.ability_props["range"] = self.selected_unit.ability_props["radius"]
        props = self.selected_unit.ability_props.copy()
        props["range"] = self.selected_unit.ability_props["radius"]
        # self.selected_unit.tile = tile

        if props["aoe_shape"] == "aoe":
            self.ability_hover_tiles = self.get_tiles_by_unit(tile, self.selected_unit, props)
        # self.selected_unit.ability_props["range"] = old_range
        # self.selected_unit.tile = old_tile
            self.highlight_path(2, self.ability_hover_tiles, self.yellow)



    def force_update_hover(self, tile):
        if tile is not None:
            if self.hovered_tile is not None:
                self.hovered_tile.highlight_redux(1, "set_layer")
            self.hovered_tile = tile

        if self.hovered_tile is not None:
            tile = self.hovered_tile
            self.change_hovered_tile(tile)
            if self.ability_hover_tiles:
                if tile in self.ability_tiles:
                    # self.move_aoe_tiles(tile)
                    pass
                else:
                    self.highlight_path(1, self.ability_hover_tiles, "set_layer")

            # if self.selected_unit and not self.hovered_box_lock:
            #     for i in [0,3,6,9]:
            #         box = self.drawn_ui[i]
            #         coords = self.canvas.coords(box)
            #         if (coords[2] > event.x > coords[0]) and (coords[3] > event.y > coords[1]):
            #             if self.hovered_box != i:
            #                 self.hovered_box = box
            #                 self.show_extra_info(self.selected_unit, i)
            #             break
            #         elif i == 9:
            #             self.hovered_box = None
            #             self.hide_extra_info()





    def change_hovered_tile(self, tile):
        if self.hovered_tile is not None:
            self.hovered_tile.highlight_redux(1, "set_layer")
            self.highlight_path(1, self.temp_hover_tiles, "set_layer")
            self.temp_hover_tiles = []

            # if self.ability_hover_tiles:
            #     self.highlight_path(1, self.ability_hover_tiles, "set_layer")
            self.highlight_path(1, self.tiles, "set_layer")

        self.hovered_tile = tile
        self.hovered_tile.highlight_redux(2, [self.blue]*5)
        

        if self.hovered_tile in self.attack_tiles:
            self.highlight_path_edge(1, list(self.attack_tiles)+[self.selected_unit.tile], self.red, True)
            self.highlight_path_edge(1, list(self.attack_tile_edge)+[self.selected_unit.tile], self.red, False)
            if self.hovered_tile.unit is not None:
                if self.hovered_tile.unit.player != self.player:
                    self.hovered_tile.highlight_redux(2, [self.yellow]*5)

        if self.movement_tiles:
            if len(self.selected_units) == 1:
                if self.hovered_tile in self.movement_tiles:
                    self.get_tiles_by_unit(self.selected_unit.tile, self.selected_unit, self.selected_unit.move_props)
                    self.temp_hover_tiles = self.get_shortest_path(self.selected_unit.tile, self.hovered_tile) #issue here with hovering over mountain
                    self.temp_hover_tiles.append(self.selected_unit.tile)
                    if len(self.temp_hover_tiles) > 1:
                        # self.selected_unit.tile.highlight_redux(1, [self.black]*5)
                        self.highlight_path(1, self.temp_hover_tiles, "set_layer")
                        self.highlight_path_edge(2, self.temp_hover_tiles, self.yellow, True)

                self.selected_unit.tile.highlight_redux(1, [self.black, self.black, self.black, self.black, self.blue])
                self.selected_unit.tile.highlight_redux(1, "set_layer")
            else:
                unmoved_tiles = []
                taken_tiles = []

                for selected_unit in self.selected_units:
                    selected_unit.predicted_move_tile = None
                    selected_unit.predicted_path = []
                    if selected_unit.movable():
                        dest_tile = self.get_predicted_move_tile(selected_unit, self.hovered_tile, taken_tiles, False)
                        if dest_tile is not None:
                            taken_tiles.append(dest_tile)
                        elif self.click_past_edge_lock:
                            dest_tile = self.get_predicted_move_tile(selected_unit, self.hovered_tile, taken_tiles, True)
                            if dest_tile is not None:
                                taken_tiles.append(dest_tile)
                            else:
                                unmoved_tiles.append(selected_unit.tile)
                        else:
                            unmoved_tiles.append(selected_unit.tile)

                    else:
                        unmoved_tiles.append(selected_unit.tile)

                for selected_unit in self.selected_units:
                    if selected_unit.movable() and selected_unit.predicted_move_tile is not None:

                        if selected_unit.predicted_move_tile in unmoved_tiles:

                            selected_unit.predicted_move_tile = None
                            selected_unit.predicted_path = []

                            dest_tile = self.get_predicted_move_tile(selected_unit, self.hovered_tile, taken_tiles, False)
                            if dest_tile is not None:
                                taken_tiles.append(dest_tile)
                            elif self.click_past_edge_lock:
                                dest_tile = self.get_predicted_move_tile(selected_unit, self.hovered_tile, taken_tiles, True)
                                if dest_tile is not None:
                                    taken_tiles.append(dest_tile)
                                else:
                                    unmoved_tiles.append(selected_unit.tile)
                            else:
                                unmoved_tiles.append(selected_unit.tile)

                            if selected_unit.predicted_move_tile is not None:
                                self.highlight_path_edge(2, selected_unit.predicted_path, self.yellow, True)

                                self.temp_hover_tiles.extend(selected_unit.predicted_path)
                        else:
                            
                            self.highlight_path_edge(2, selected_unit.predicted_path, self.yellow, True)

                            self.temp_hover_tiles.extend(selected_unit.predicted_path)

        elif self.ability_tiles:
            self.temp_hover_tiles, self.ability_hover_tiles = self.get_ability_tiles(self.selected_unit, self.hovered_tile)
            self.highlight_path(2, self.temp_hover_tiles, self.yellow)
            self.highlight_path(2, self.ability_hover_tiles, self.red)

            # if self.selected_unit.ability_props["area_type"] == "line":
            #     for line in self.ability_lines:
            #         if self.hovered_tile in line:
            #             self.temp_hover_tiles = line
            #             self.highlight_path(2, self.temp_hover_tiles, self.yellow) ###

            #             props = self.selected_unit.ability_props.copy()
            #             if props["target_type"] == "aoe":
            #                 props["range"] = self.selected_unit.ability_props["radius"]
            #                 if props["aoe_shape"] == "line":
            #                     self.ability_hover_tiles = []
            #                     if props["aoe_direction"] == "perpendicular":
            #                         cardinal = self.get_cardinal_direction(start_tile, tile)
            #                         if "E" in cardinal or "W" in cardinal:
            #                             props["aoe_direction"] = ["top", "bottom"]
            #                         elif "N" in cardinal or "S" in cardinal:
            #                             props["aoe_direction"] = ["left", "right"]

            #                     print("line stop = ", props["line_stop"])
            #                     if props["line_stop"]:
            #                         sec_lines = self.get_tiles_by_unit(self.hovered_tile, self.selected_unit, props)
            #                     else:
            #                         tile = line[0]
            #                         sec_lines = self.ability_hover_tiles = self.get_tiles_by_unit(tile, self.selected_unit, props)

            #                     for sec_line in sec_lines:
            #                         for sec_tile in sec_line:
            #                             if sec_tile not in self.ability_hover_tiles:
            #                                 self.ability_hover_tiles.append(sec_tile)

            #                     self.highlight_path(2, self.ability_hover_tiles, self.dark_grey)

            #             break

    def set_ability_tiles(self, unit):
        props = unit.ability_props.copy()
        start_tile = unit.tile
        if props["area_type"] == "line":
            self.ability_lines = self.get_tiles_by_unit(start_tile, unit, props)

            self.ability_tiles = []
            for line in self.ability_lines:
                for tile in line:
                    self.ability_tiles.append(tile)

            return self.ability_tiles, []

        elif props["area_type"] == "circle":

            self.ability_tiles = self.get_tiles_by_unit(start_tile, unit, props)

            return self.ability_tiles, []

    def get_ability_tiles(self, unit, hover_tile):
        props = unit.ability_props.copy()
        start_tile = unit.tile
        target_tiles = []
        sec_target_tiles = []

        if props["area_type"] == "line":           

            for line in self.ability_lines:
                if hover_tile in line:
                    target_tiles = line

                    if props["target_type"] == "aoe":
                        props["range"] = props["radius"]
                        # diag = False
                        # if props["direction"] == "diag" or props["direction"] == "all":
                        #     diag = True
                        props["direction"] = props["aoe_direction"]

                        if props["aoe_shape"] == "line":
                            if props["line_stop"]:
                                end_tile = hover_tile
                            else:
                                end_tile = line[-1]


                            if props["direction"] == "perpendicular":
                                cardinal = self.get_cardinal_direction(start_tile, end_tile)

                                if cardinal == "E" or cardinal == "W":
                                    props["direction"] = ["top", "bottom"]
                                elif cardinal == "N" or cardinal == "S":
                                    props["direction"] = ["left", "right"]
                                    #[["top", "right"], ["right", "bottom"], ["bottom", "left"], ["left", "top"]]
                                elif cardinal == "SE":
                                    props["direction"] = [["left", "top"], ["right", "bottom"]]
                                elif cardinal == "NE":
                                    props["direction"] = [["top", "right"], ["bottom", "left"]]
                                elif cardinal == "SW":
                                    props["direction"] = [["top", "right"], ["bottom", "left"]]
                                elif cardinal == "NW":
                                    props["direction"] = [["left", "top"], ["right", "bottom"]]

                            sec_lines = self.get_tiles_by_unit(end_tile, unit, props)
                            sec_target_tiles.append(end_tile)
                            for sec_line in sec_lines:
                                for sec_tile in sec_line:
                                    if sec_tile not in sec_target_tiles:
                                        sec_target_tiles.append(sec_tile)

                    elif props["target_type"] == "single":
                        if props["line_stop"]:
                            end_tile = hover_tile
                        else:
                            end_tile = line[-1]
                        sec_target_tiles = [end_tile]

                    break
            # return target_tiles, sec_target_tiles

        elif props["area_type"] == "circle":
            if props["target_type"] == "aoe":

                props["range"] = props["radius"]

                if props["aoe_shape"] == "circle":
                    sec_target_tiles = self.get_tiles_by_unit(hover_tile, unit, props)
        
        return target_tiles, sec_target_tiles



    def get_cardinal_direction(self, start_tile, end_tile):
        if start_tile.posy < end_tile.posy:
            if start_tile.posx < end_tile.posx:
                return "NW"
            elif start_tile.posx > end_tile.posx:
                return "NE"
            elif start_tile.posx == end_tile.posx:
                return "N"

        elif start_tile.posy > end_tile.posy:
            if start_tile.posx < end_tile.posx:
                return "SW"
            elif start_tile.posx > end_tile.posx:
                return "SE"
            elif start_tile.posx == end_tile.posx:
                return "S"

        elif start_tile.posy == end_tile.posy:
            if start_tile.posx < end_tile.posx:
                return "W"
            elif start_tile.posx > end_tile.posx:
                return "E"

    def get_predicted_move_tile(self, unit, dest_tile, taken_tiles, force_axis):
        if self.click_past_edge_lock:
            x_diff = abs(unit.tile.x1 - dest_tile.x1)
            y_diff = abs(unit.tile.y1 - dest_tile.y1)

            if x_diff > y_diff:
                if not force_axis:
                    axis = "x"
                    min_diff = abs(unit.tile.posx - dest_tile.posx)
                else:
                    axis = "y"
                    min_diff = abs(unit.tile.posy - dest_tile.posy)
            else:
                if not force_axis:
                    axis = "y"
                    min_diff = abs(unit.tile.posy - dest_tile.posy)
                else:
                    axis = "x"
                    min_diff = abs(unit.tile.posx - dest_tile.posx)

            
            min_tile = None
            for move_tile in unit.movement_tiles:
                if move_tile not in taken_tiles:

                    if axis == "x" and move_tile.posy == unit.tile.posy:
                        if abs(move_tile.posx - dest_tile.posx) < min_diff:
                            min_diff = abs(move_tile.posx - dest_tile.posx)
                            min_tile = move_tile

                    elif axis == "y" and move_tile.posx == unit.tile.posx:
                        if abs(move_tile.posy - dest_tile.posy) < min_diff:
                            min_diff = abs(move_tile.posy - dest_tile.posy)
                            min_tile = move_tile

            if min_tile is not None:
                unit.predicted_move_tile = min_tile

                taken_tiles.append(min_tile)

        else:
            min_diff = 99999
            min_tile = None


            for move_tile in unit.movement_tiles:
                if move_tile not in taken_tiles:

                    x_diff = move_tile.x1 - dest_tile.x1

                    y_diff = move_tile.y1 - dest_tile.y1

                    if (abs(y_diff) + abs(x_diff)) < min_diff:
                        min_diff = (abs(y_diff) + abs(x_diff))
                        min_tile = move_tile

            if min_tile is not None:
                unit.predicted_move_tile = min_tile

                taken_tiles.append(min_tile)

        if min_tile is not None:
            old_targets = unit.move_props["targets"].copy()
            old_ptargets = unit.move_props["player_target"].copy()
            unit.move_props["targets"].append("unit")
            unit.move_props["player_target"].append(self.player)

            self.get_tiles_by_unit(unit.tile, unit, unit.move_props)

            unit.move_props["targets"] = old_targets
            unit.move_props["player_target"] = old_ptargets
            unit.predicted_path = self.get_shortest_path(unit.tile, unit.predicted_move_tile)

        return min_tile


    #tile utility functions#############################################################################################################################################
    def get_angle(self, x1, y1, x2, y2):
        x_diff = x1-x2
        y_diff = y1-y2

        if round(x_diff) == 0:
            if round(y_diff) > 0:
                return 180
            elif round(y_diff) < 0:
                return 0
            else:
                return 0

        if round(y_diff) == 0:
            if round(x_diff) > 0:
                return 270
            elif round(x_diff) < 0:
                return 90
            else:
                return 0

        angle = math.degrees(math.atan(x_diff/y_diff))

        if x_diff > 0 and y_diff > 0:
            angle += 180
        if x_diff < 0 and y_diff > 0:
            angle += 180

        return round(angle)


    def get_shortest_simple_path(self, start_tile, end_tile):
        if start_tile != "edge":
            if start_tile == end_tile:
                return [end_tile]
            else:
                hd = start_tile.posx - end_tile.posx
                vd = start_tile.posy - end_tile.posy
                path = None
                if abs(hd) > abs(vd):
                    if hd != 0:
                        if hd > 0:
                            path = self.get_shortest_simple_path(start_tile.adj["right"], end_tile)
                        else:
                            path = self.get_shortest_simple_path(start_tile.adj["left"], end_tile)
                else:
                    if vd != 0:
                        if vd > 0:
                            path = self.get_shortest_simple_path(start_tile.adj["top"], end_tile)
                        else:
                            path = self.get_shortest_simple_path(start_tile.adj["bottom"], end_tile)
                if path is not None:
                    path.append(start_tile)
                    return path

    def get_shortest_path(self, start_tile, end_tile):
        curr_tile = end_tile
        path = [end_tile]
        search_num = end_tile.search_num - 1
        while search_num > 0:
            back_tile = None
            for tile in curr_tile.adj.values():
                if tile != "edge":
                    if tile.terrain in ["grass"]:
                        if tile.search_num == search_num:
                            if back_tile is None:
                                back_tile = tile
                            else:
                                if back_tile == curr_tile.adj["bottom"] or back_tile == curr_tile.adj["top"]:
                                    if abs(start_tile.posx - curr_tile.posx) > abs(start_tile.posy - curr_tile.posy):
                                        back_tile = tile
                                elif back_tile == curr_tile.adj["right"] or back_tile == curr_tile.adj["left"]:
                                    if abs(start_tile.posx - curr_tile.posx) < abs(start_tile.posy - curr_tile.posy):
                                        back_tile = tile
            if back_tile is not None:
                path.append(back_tile)
                curr_tile = back_tile
            search_num -= 1
            
        return path


    def get_tiles_by_unit(self, start_tile, unit, props):
        for tile in self.tiles:
            tile.search_num = 0
        if props["area_type"] == "circle":
            search_num = 1
            # start_tile.search_num = search_num
            # edge_tiles = start_tile.adj.values()
            edge_tiles = [start_tile]
            next_edges = []
            tiles_in_range = []
            # tiles_in_range.append(start_tile)
            # if "self" in props["targets"]:
            #     tiles_in_range.append(unit.tile)
            while search_num < props["range"]+2:
                search_num += 1
                for tile in edge_tiles:
                    if tile != "edge":
                        if tile.terrain in props["terrain"]:
                            # tile.search_num = search_num
                            if tile.unit is not None:
                                if tile == unit.tile and "self" in props["targets"]:
                                    tile.search_num = search_num
                                    tiles_in_range.append(tile)
                                elif "unit" in props["targets"] and tile.unit.targetable and tile.unit.player in props["player_target"]:
                                    tile.search_num = search_num
                                    tiles_in_range.append(tile)

                                # elif "self" in props["targets"] and tile == unit.tile:
                                #     tiles_in_range.append(tile)
                                # else:#if tile != unit.tile:
                                #     tiles_in_range.append(tile)
                            elif "tile" in props["targets"]:#not tile.unit and 
                                tile.search_num = search_num
                                tiles_in_range.append(tile)
                            # for adj_tile in tile.adj.values():
                            #     if adj_tile != "edge":
                            #         # if tile.terrain in props["terrain"] and ((tile.unit != None and "unit" not in props["targets"]) or not tile.unit):
                            #         if adj_tile.search_num == 0:
                            #             # adj_tile.search_num = search_num + 1
                            #             next_edges.append(adj_tile)

                        # if tile in tiles_in_range or tile == start_tile:
                        if tile.terrain in props["terrain_pierce"] and ((tile.unit is not None and props["unit_pierce"]) or tile.unit is None or tile.unit == unit):
                            for adj_tile in tile.adj.values():
                                if adj_tile != "edge" and adj_tile.search_num == 0:
                                    next_edges.append(adj_tile)

                edge_tiles = next_edges.copy()
                next_edges = []
            return tiles_in_range

        elif props["area_type"] == "line":
            final_lines = []
            final_tiles = []
            if props["direction"] == "all" or props["direction"] == "card":
                directions = ["top", "bottom", "right", "left"]
            else:
                directions = []
                for angle in props["direction"]:
                    if angle in ["top", "bottom", "right", "left"]:
                        directions.append(angle)

            for direction in directions:
                line = []
                tile = start_tile
                search_num = 1
                while search_num < props["range"]+1:
                    search_num += 1
                    tile = tile.adj[direction]
                    if tile is not "edge":
                        if tile.terrain in props["terrain"]:
                            if ((tile.unit != None and "unit" in props["targets"] and tile.unit.player != unit.player) or not tile.unit):
                                line.append(tile)
                                final_tiles.append(tile)
                        if not props["unit_pierce"] and tile.unit != None: #moved this and the if below down one tab
                            break
                        if tile.terrain not in props["terrain_pierce"]: #CORRECT TERRAIN PIERCE, break the continuation if hit terrain, but can stop on the terrain itself
                            break
                    else:
                        break
                final_lines.append(line.copy())

            if props["direction"] == "all" or props["direction"] == "diag":
                diag_directions = [["top", "right"], ["right", "bottom"], ["bottom", "left"], ["left", "top"]]
            else:
                diag_directions = []
                for angle in props["direction"]:
                    if angle in [["top", "right"], ["right", "bottom"], ["bottom", "left"], ["left", "top"]]:
                        diag_directions.append(angle)
                # diag_directions = props["diag_direction"]

            for diagonal in diag_directions:
                line = []
                tile = start_tile
                search_num = 1
                while search_num < props["range"]+1:
                    search_num += 1
                    tile = tile.adj[diagonal[0]]
                    if tile is not "edge":
                        tile = tile.adj[diagonal[1]]
                        if tile is not "edge":
                            if tile.terrain in props["terrain"]:
                                if ((tile.unit != None and "unit" in props["targets"] and tile.unit.player != unit.player) or not tile.unit):
                                    line.append(tile)
                                    final_tiles.append(tile)

                            if tile.unit is not None and not props["unit_pierce"]: #moved this and the if below down one tab
                                break
                            if tile.terrain not in props["terrain_pierce"]: #CORRECT TERRAIN PIERCE, break the continuation if hit terrain, but can stop on the terrain itself moved these 
                                break
                        else:
                            break
                    else:
                        break
                final_lines.append(line.copy())

            self.line_range = final_lines
            return final_lines

    def movement_tile_filter(self, tiles):
        final_tiles = []
        for tile in tiles:
            if tile.terrain == "grass" and tile.unit == None:
                final_tiles.append(tile)
        return final_tiles

    def attack_tile_filter(self, lines, props):
        for line in lines:
            block = False
            for tile in line:
                if (tile.terrain != "grass" and props["terrain_pierce"]) or tile.unit != None or block:
                    line.remove(tile)
                    if not block and not passthrough:
                        block = True

        return lines

    def tile_filter(self, tiles, lines, props):
        if tiles:
            for tile in tiles:
                if tile.terrain not in props["terrain"] or (tile.unit != None and "unit" not in props["targets"]):
                    tiles.remove(tile)
            return tiles
        if lines:
            for line in lines:
                block = False
                for tile in line:
                    if not block:
                        if tile.terrain not in props["terrain"]:
                            line.remove(tile)
                            if not props["terrain_pierce"]:
                                block = True
                        if tile.unit != None and "unit" not in props["targets"]:
                            line.remove(tile)
                            if not props["unit_pierce"]:
                                block = True
            return lines

    

    def get_unit_by_id(self, unitid):
        for unit in self.units:
            if unit.unitid == unitid:
                return unit

    def get_tile_by_id(self, tileid):
        for tile in self.tiles:
            if tile.tileid == tileid:
                return tile

    #ability helper functions######################################################################################################################################################
    def teleport_unit(self, unit, tile):
        # unit.final_tile = tile
        unit.move_to_tile(tile, True, True, True)


    def teleport_unit_rand(self, unit, max_range):
        tile = None
        if max_range == 0:
            while True:
                tile = random.choice(self.tiles)
                if tile.terrain in unit.move_props["terrain"]:
                    break

        unit.move_to_tile(tile, True, True, True)

    def reveal_map(self):
        for tile in self.tiles:
            tile.toggle_fog(False)
            if tile.unit is not None:
                tile.unit.visible = True
                tile.unit.draw()


    #other classes######################################################################################################################################################
class Button(pygame.sprite.Sprite):
    def __init__(self, screen, x1, y1, x2, y2, border_color, fill_color, hover_highlight, fill_items, size_mult, center_text):


        self.screen = screen
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

        self.base_border_color = border_color
        self.border_color = border_color
        self.base_color = fill_color
        self.fill_color = fill_color
        self.hover_highlight = hover_highlight

        super().__init__()
        self.box = pygame.Surface([abs(x1-x2), abs(y1-y2)])
        if border_color is not None:
            self.box.fill(border_color)
        if fill_color is not None:
            self.box.fill(fill_color, self.box.get_rect().inflate(-7, -7))

        self.box_rect = self.box.get_rect()
        self.box_rect.x = x1
        self.box_rect.y = y1

        self.rect = self.box_rect

        if not isinstance(fill_items, list):
            fill_items = [fill_items]

        self.center_text = center_text
        self.margin = 10
        self.dynamic_box_height = False


        self.secondary_surfaces = []
        self.secondary_rects = []
        self.secondary_texts = []
        self.secondary_mults = []

        for text in fill_items:
            self.secondary_texts.append(text)
            self.secondary_mults.append(size_mult)

            if ".png" not in text:
                font = pygame.font.Font('freesansbold.ttf', round(14*size_mult))
                if len(text.split(' ')) == 1:
                    surface = font.render(text, True, pygame.Color("black"), pygame.Color("white"))
                    surface.set_colorkey(pygame.Color("white"))
                    rect = surface.get_rect()
                    if self.center_text:
                        rect.center = ((x1+x2)/2, (y1+y2)/2)
                    else:
                        rect.x = x1+self.margin
                        rect.y = y1+self.margin
                else:
                    # if self.center_text:
                    surface, rect = self.prep_text(x1, y1, self.box, text, font)
                    # else:
                    #     surface = font.render(text, True, pygame.Color("black"), pygame.Color("white"))
                    #     surface.set_colorkey(pygame.Color("white"))

                    #     rect = surface.get_rect()
                    #     rect.center = ((x1+x2)/2, (y1+y2)/2)
            else:
                surface = pygame.image.load(text).convert_alpha()
                surface = pygame.transform.scale(surface, (round(abs(x1-x2)*size_mult), round(abs(y1-y2)*size_mult)))

                rect = surface.get_rect()
                rect.center = ((x1+x2)/2, (y1+y2)/2)

            self.secondary_surfaces.append(surface)
            self.secondary_rects.append(rect)

        if border_color is None and fill_color is None:
            self.image = self.secondary_surfaces[0]
        else:
            self.image = self.box

        

        


    def prep_text(self, x1, y1, surface, text, font):
        text_surfaces = []
        text_rects = []

        words = [word.split(' ') for word in text.splitlines()]  # 2D array where each row is a list of words.
        space = font.size(' ')[0]  # The width of a space.
        base_width, base_height = surface.get_size()
        max_width = base_width*0.8
        base_x = x1 + (base_width - max_width)/2
        x, y = base_x, y1
        max_x = x + max_width
        max_line_width = 0

        if text == "":
            line_surface = font.render(text, True, pygame.Color("black"), pygame.Color("white"))
            line_surface.set_colorkey(pygame.Color("white"))
            text_surfaces.append(line_surface)
            text_rect = line_surface.get_rect()
            text_rect.x = base_x
            text_rect.y = y
            text_rects.append(text_rect)
        else:
            for line in words:
                new_line = ""
                line_width = 0
                for word in line:
                    word_surface = font.render(word, 0, pygame.Color("black"))
                    word_width, word_height = word_surface.get_size()
                    if x + word_width > max_x:
                        if line_width > max_line_width:
                            max_line_width = line_width
                        line_width = 0
                        line_surface = font.render(new_line, True, pygame.Color("black"), pygame.Color("white"))
                        line_surface.set_colorkey(pygame.Color("white"))
                        text_surfaces.append(line_surface)
                        text_rect = line_surface.get_rect()
                        text_rect.x = base_x
                        text_rect.y = y
                        text_rects.append(text_rect)

                        new_line = word + " "

                        x = x1
                        if word != line[-1]:
                            y += word_height

                    else:
                        new_line += word + " "
                        x += word_width + space
                        line_width += word_width + space

                        if word == line[-1]:
                            if line_width > max_line_width:
                                max_line_width = line_width
                            line_width = 0
                            line_surface = font.render(new_line, True, pygame.Color("black"), pygame.Color("white"))
                            line_surface.set_colorkey(pygame.Color("white"))
                            text_surfaces.append(line_surface)
                            text_rect = line_surface.get_rect()
                            text_rect.x = base_x
                            text_rect.y = y
                            text_rects.append(text_rect)
                            new_line = ""

                x = x1
                y += word_height


            y_index = 0
            for line_rect in text_rects:
                if self.center_text:
                    line_rect.x = x1 + (base_width - max_line_width)/2
                    y_offset = (base_height - len(text_rects)*word_height)/2
                    line_rect.y += y_offset
                else:
                    line_rect.x = x1+self.margin
                    line_rect.y = y1+self.margin + y_index*word_height
                    y_index += 1
                    # line_rect.center = self.x1, self.y1

                    # print(self.x1, self.x2, self.y1, self.y2)
                    # print(line_rect.center)

            if self.dynamic_box_height:
                self.box = pygame.Surface([abs(self.x1-self.x2), len(text_rects)*word_height+self.margin*2])
                if self.border_color is not None:
                    self.box.fill(self.border_color)
                if self.fill_color is not None:
                    self.box.fill(self.fill_color, self.box.get_rect().inflate(-7, -7))
                self.box_rect = self.box.get_rect()
                self.box_rect.x = x1
                self.box_rect.y = y1
                self.rect = self.box_rect

        return text_surfaces, text_rects


    def change_text(self, index, text, size_mult):
        if "png" not in text:
            # old_coords = self.secondary_rects[index][0].center

            self.secondary_texts[index] = text
            if size_mult is not None:
                self.secondary_mults[index] = size_mult
            else:
                size_mult = self.secondary_mults[index]

            font = pygame.font.Font('freesansbold.ttf', round(14*size_mult))
            # if self.center_text:
            #     # if isinstance(self.secondary_surfaces[index], list):
            #     #     old_coords = self.secondary_rects[index][0].center
            #     self.secondary_surfaces[index], self.secondary_rects[index] = self.prep_text(self.x1, self.y1, self.box, text, font)
            #     # self.secondary_rects[index][0].center = old_coords

            # else:
            #     old_coords = self.secondary_rects[index].center
            #     self.secondary_surfaces[index] = font.render(text, True, pygame.Color("black"), pygame.Color("white"))
            #     self.secondary_surfaces[index].set_colorkey(pygame.Color("white"))
            #     self.secondary_rects[index] = self.secondary_surfaces[index].get_rect()
            #     self.secondary_rects[index].center = old_coords

            if len(text.split(' ')) == 1:
                old_coords = self.secondary_rects[index].center
                self.secondary_surfaces[index] = font.render(text, True, pygame.Color("black"), pygame.Color("white"))
                self.secondary_surfaces[index].set_colorkey(pygame.Color("white"))
                self.secondary_rects[index] = self.secondary_surfaces[index].get_rect()
                if self.center_text:
                    self.secondary_rects[index].center = ((self.x1+self.x2)/2, (self.y1+self.y2)/2)
                else:
                    self.secondary_rects[index].center = old_coords
                    # self.secondary_rects[index].x = self.x1+self.margin
                    # self.secondary_rects[index].y = self.y1+self.margin
            else:
                self.secondary_surfaces[index], self.secondary_rects[index] = self.prep_text(self.x1, self.y1, self.box, text, font)

        else:
            old_coords = self.secondary_rects[index].center

            self.secondary_texts[index] = text
            if size_mult is not None:
                self.secondary_mults[index] = size_mult
            else:
                size_mult = self.secondary_mults[index]

            self.secondary_surfaces[index] = pygame.image.load(text).convert_alpha()
            self.secondary_surfaces[index] = pygame.transform.scale(self.secondary_surfaces[index], (round(abs(self.x1-self.x2)*size_mult), round(abs(self.y1-self.y2)*size_mult)))

            self.secondary_rects[index] = self.secondary_surfaces[index].get_rect()

            self.secondary_rects[index].center = old_coords

    def change_image(self, index, text, size_mult):
        old_coords = self.secondary_rects[index].center

        self.secondary_surfaces[index] = pygame.image.load(text).convert_alpha()
        self.secondary_surfaces[index] = pygame.transform.scale(self.secondary_surfaces[index], (round(abs(x1-x2)*size_mult), round(abs(y1-y2)*size_mult)))

        self.secondary_rects[index] = self.secondary_surfaces[index].get_rect()

        self.secondary_rects[index].center = old_coords

    def highlight(self, border_color, fill_color, set_curr):
        if border_color is not None:
            self.box.fill(border_color)
            if set_curr:
                self.border_color = border_color
        if fill_color is not None:
            self.box.fill(fill_color, self.box.get_rect().inflate(-7, -7))
            if set_curr:
                self.fill_color = fill_color
        else:
            self.box.fill(self.fill_color, self.box.get_rect().inflate(-7, -7))

    def reset_color(self):
        self.box.fill(self.fill_color, self.box.get_rect().inflate(-7, -7))

    def draw_rect(surface, fill_color, outline_color, rect, border=1):
        surface.fill(outline_color, rect)
        surface.fill(fill_color, rect.inflate(-border*2, -border*2))

    def draw(self):
        self.box = self.canvas.create_rectangle(self.x1, self.y1, self.x2, self.y2, width=4, outline='black', fill=self.fill_color)
        self.drawn_elements.append(self.box)
        if self.fill_img is None:
            self.text = self.canvas.create_text(self.x1+(self.x2-self.x1)/2, self.y1+(self.y2-self.y1)/2, anchor=CENTER, text=self.text)
            self.drawn_elements.append(self.text)
        else:
            self.img = self.canvas.create_image(self.x1, self.y1, image=self.fill_img, anchor=NW)
            self.drawn_elements.append(self.img)

        

    def delete(self):
        self.kill()

class Tile(pygame.sprite.Sprite):
    def __init__(self, master, screen, x1, y1, x2, y2, posx, posy, thickness, texture):
        super().__init__()
        self.master = master
        self.screen = screen
        self.obj_type = "tile"
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.posx = posx
        self.posy = posy
        self.texture = texture
        self.search_num = 0
        self.tileid = str(posx) + "|" + str(posy)
        self.base_color = ['black']*5
        if self.texture == "grass": #redo this so all tiles share the same image asset
            tile_no = str(random.randint(1,4))
            img_link = './Assets/Tiles/grass_'+tile_no+'.png'
            fg_img_link = None
            self.terrain = self.texture
        elif self.texture == "mountain":
            img_link = './Assets/Tiles/rocky.png'
            fg_img_link = './Assets/Tiles/mountain.png'
            self.terrain = self.texture
        else:
            bg_img_link = None
            fg_img_link = None

        self.image = pygame.image.load(img_link).convert_alpha()
        self.image = pygame.transform.scale(self.image, (round(abs(x1-x2)), round(abs(y1-y2))))

        self.rect = self.image.get_rect()
        self.rect.center = ((x1+x2)/2, (y1+y2)/2)

        if fg_img_link is not None:
            self.fg_image = pygame.image.load(fg_img_link).convert_alpha()

            self.fg_image = pygame.transform.scale(self.fg_image, (round(abs(x1-x2)), round(abs(y1-y2))))

        else:
            self.fg_image = None

        self.fog_image = pygame.image.load('./Assets/Tiles/fog50.png').convert_alpha()

        self.fog_image = pygame.transform.scale(self.fog_image, (round(abs(x1-x2)), round(abs(y1-y2))))
        self.fog_image.set_alpha(200)

        self.edges = []

        self.rightid = self.master.new_line(self.x2, self.y1, self.x2, self.y2, self.master.dark_grey, 2)
        self.edges.append(self.rightid)

        self.leftid = self.master.new_line(self.x1, self.y1, self.x1, self.y2, self.master.dark_grey, 2)
        self.edges.append(self.leftid)

        self.topid = self.master.new_line(self.x1, self.y1, self.x2, self.y1, self.master.dark_grey, 2)
        self.edges.append(self.topid)

        self.bottomid = self.master.new_line(self.x1, self.y2, self.x2, self.y2, self.master.dark_grey, 2)
        self.edges.append(self.bottomid)

        self.highlight_layer = pygame.Surface([abs(x1-x2), abs(y1-y2)])
        self.highlight_layer.set_alpha(50)

        self.edges.append(self.highlight_layer)

        self.curr_color = self.base_color
        self.curr_edges = ["right", "left", "top", "bottom"]
        self.map_color = self.base_color
        self.map_edges = ["right", "left", "top", "bottom"]
        self.thickness = thickness
        self.drawn_elements = []


        self.color_layers = [[self.master.black]*5, [None]*5, [None]*5]

        self.foggy = True
        self.trapped = False
        self.trap_color = ["green"]*5

        self.unit = None
        self.adj = {
            "right":None,
            "left":None,
            "top":None,
            "bottom":None
        }


    def draw_extra(self):
        if self.foggy:
            pygame.draw.rect(self.fog_image, self.master.black, self.rect)

        if self.fg_image is not None:
            pygame.draw.rect(self.fg_image, self.master.black, self.rect)

        if self.highlight_layer.get_alpha() != 0:
            pygame.draw_rect(self.highlight_layer, self.highlight_colors[4], self.rect)


    def blit_extra(self):
        if self.foggy:
            self.screen.blit(self.fog_image, self.rect)

        if self.fg_image is not None:
            self.screen.blit(self.fg_image, self.rect)

        if self.highlight_layer.get_alpha() != 0:
            self.screen.blit(self.highlight_layer, self.rect)

        self.draw_border()

    def draw_border(self):
        for index in range(0,4):
            color = self.color_layers[2][index]
            if color is not None:
                pygame.draw.rect(self.screen, color, self.edges[index])
            else:
                color = self.color_layers[1][index]
                if color is not None:
                    pygame.draw.rect(self.screen, color, self.edges[index])
                else:
                    color = self.color_layers[0][index]
                    if color is not None:
                        pygame.draw.rect(self.screen, color, self.edges[index])


    def highlight_redux(self, layer, colors):
        #layer = base:0 temporary map highlighting:1 temporary hover highlighting:2
        #self.color_layers = [[None, None, None, None, None], [None, None, None, None, None], [None, None, None, None, None]]
        #colors = list with len 5 ["right", "left", "top", "bottom", "center"], each corresponding to an edge or center fill
        if colors == "set_layer":
            for layer_x in range(layer+1, 3):
                self.color_layers[layer_x] = [None]*5

            colors = self.color_layers[layer]

            if layer > 0:
                for x in range(0, 5):
                    if colors[x] == None:
                        colors[x] = self.color_layers[0][x]

        else:
            self.color_layers[layer] = colors
            
        color = self.color_layers[2][4]
        if color is not None:
            self.highlight_layer.fill(color)
        else:
            color = self.color_layers[1][4]
            if color is not None:
                self.highlight_layer.fill(color)
            else:
                color = self.color_layers[0][4]
                if color is not None:
                    self.highlight_layer.fill(color)

        if color == self.master.black:
            self.highlight_layer.set_alpha(0)
        else:
            self.highlight_layer.set_alpha(50)

    def toggle_fog(self, foggy):
        self.foggy = foggy
        if foggy:
            if self.unit:
                if self.unit.player != self.master.player:
                    self.unit.visible = False
                    self.unit.draw()
        else:
            if self.unit:
                if self.unit.player != self.master.player:
                    self.unit.visible = True
                    self.unit.draw()

    def delete_border(self):
        for edge in self.edges:
            pass

    def delete(self):
        self.kill()

    def place_trap(self, owner):
        self.trap_color = "green"
        self.trapped = True


    def __str__(self):
        return self.tileid

class Unit(pygame.sprite.Sprite):
    def __init__(self, master, screen, x1, y1, x2, y2, player, stats_id):
        super().__init__()
        stats = Stats.unit_stats(stats_id)
        self.ability_type = stats["ability_type"]
        if self.ability_type == "alt":
            self.ability_func = Stats.ability_dict(stats["ability_id"])
        #techinical coding variables
        self.master = master
        self.screen = screen
        self.obj_type = "unit"
        self.visible = False
        self.visible_units = []
        self.targetable = True #change to false before unit gets deployed
        self.player = player
        if self.master.player == self.player:
            self.enemy = self.master.enemy
        else:
            self.enemy = self.master.player

        self.visible_tiles = []

        if player == master.player:
            self.unitid = str(player) + "|" + str(len(master.ally_unit_pool))
        else:
            self.unitid = str(player) + "|" + str(len(master.enemy_unit_pool))
        self.tile = None
        self.final_tile = None
        self.dead = False
        self.attack_ready = True
        self.ability_ready = True
        self.deployed = False

        self.cycles = 1

        self.move_freq = 0
        self.x_incr = 0
        self.y_incr = 0

        #audito variables
        self.move_sound = stats["move_sound"]

        #visual variable
        unit_color = stats["unit_color"]
        self.unit_name = stats["unit_name"]
        self.basic_atk_type = stats["basic_atk_type"]
        self.ability_projectile = stats["ability_projectile"]
        self.size_mult = stats["size_mult"]

        if self.player == self.master.player:
            self.unit_color = master.main_color
            self.fill_color = master.main_color
        else:
            self.unit_color = master.enemy_color
            self.fill_color = master.enemy_color

        self.direction = "up"
        self.angle = 0


        if unit_color == "variable":
            if self.player:
                img_str = "./Assets/Units/red_"+self.unit_name+".png"
            else:
                img_str = "./Assets/Units/blue_"+self.unit_name+".png"
        elif unit_color == "constant":
            img_str = "./Assets/Units/"+self.unit_name+".png"

        # img_str = "./Assets/"+self.unit_color+"_"+self.unit_name+".png"

        self.curr_sprite = None

        self.image = pygame.image.load(img_str).convert_alpha()
        self.image = pygame.transform.scale(self.image, (round(abs(x1-x2)*self.size_mult), round(abs(y1-y2)*self.size_mult)))

        self.rect = self.image.get_rect()
        self.offset = 0
        self.move(x1, y1, x2, y2)
        self.rect.x = x1
        self.rect.y = y1

        self.drawn_elements = []

        self.health_bar = []

        self.visible_hp = []

        #techinical stat variables
        self.max_hp = stats["max_hp"]
        self.curr_hp = self.max_hp
        self.drawn_hp = self.max_hp
        self.vision_range = stats["vision_range"]
        

        self.move_props = stats["move_props"]

        targets = []
        if self.move_props["player_target"] is not None:
            if "ally" in self.move_props["player_target"]:
                targets.append(self.player)
            if "enemy" in self.move_props["player_target"]:
                targets.append(self.enemy)

        self.move_props["player_target"] = targets

        self.atk_props = stats["atk_props"]

        targets = []
        if self.atk_props["player_target"] is not None:
            if "ally" in self.atk_props["player_target"]:
                targets.append(self.player)
            if "enemy" in self.atk_props["player_target"]:
                targets.append(self.enemy)

        self.atk_props["player_target"] = targets

        self.ability_props = stats["ability_props"]

        targets = []
        if self.ability_props["player_target"] is not None:
            if "ally" in self.ability_props["player_target"]:
                targets.append(self.player)
            if "enemy" in self.ability_props["player_target"]:
                targets.append(self.enemy)

        self.ability_props["player_target"] = targets

        if stats["extra_props"]:
            self.secondary_props = stats["secondary_props"]

            targets = []
            if self.secondary_props["player_target"] is not None:
                if "ally" in self.secondary_props["player_target"]:
                    targets.append(self.player)
                if "enemy" in self.secondary_props["player_target"]:
                    targets.append(self.enemy)

            self.secondary_props["player_target"] = targets
        else:
            self.secondary_props = None

        self.secondary_targets = ""

        #draw unit
        self.create_hp()
        self.draw()


    #technical fuctions
    def movable(self):
        return (self.move_props["range"] > 0)

    def move_to_tile(self, tile, redraw, fog, set_final_tile):
        if self.tile is not None:
            self.tile.unit = None
        self.tile = tile
        if set_final_tile:
            if self.final_tile is not None:
                self.final_tile.unit = None
            self.final_tile = tile
            self.final_tile.unit = self
        
        tile.unit = self

        if redraw:
            if self.curr_sprite is None:
                self.offset = (abs(tile.x1-tile.x2) - (abs(tile.x1-tile.x2)*self.size_mult))/2
                self.move(tile.x1+self.offset, tile.y1+self.offset, tile.x2-self.offset, tile.y2-self.offset)

        if fog:
            self.master.update_unit_vision(self, tile, self.vision_range, self.player)

    def get_dist_from_tile(self, tile):
        return self.master.get_tile_dist(self.tile, tile)

    def destroy(self):
        if not self.dead:
            self.targetable = False
            self.delete()
            self.visible = False
            self.tile.unit = None
            self.dead = True

            if self.player == self.master.player:
                self.master.ally_deployed_units.remove(self)
                self.remove_vision()

            else:
                self.master.enemy_deployed_units.remove(self)
                for unit in self.master.ally_deployed_units:
                    if self in unit.visible_units:
                        unit.visible_units.remove(self)

            if self.master.selected_unit is not None:
                selected_unit = self.master.selected_unit
                self.master.deselect(False)
                self.master.select_unit("m1", selected_unit.tile)

            if self.master.enemy_deployed_units == [] or self.master.ally_deployed_units == []:
                self.master.declare_winner()

    def remove_vision(self):
        for unit in self.master.enemy_deployed_units:
            if self in unit.visible_units:
                unit.visible_units.remove(self)

        for tile in self.visible_tiles:
            shared = False
            for unit in self.master.ally_deployed_units:
                if tile in unit.visible_tiles:
                    shared = True
            if not shared:
                tile.toggle_fog(True)

        self.visible_tiles = []

    def move(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def incr_move(self, x, y):
        self.x1 = round(self.x1 + x)
        self.y1 = round(self.y1 + y)
        self.x2 = round(self.x2 + x)
        self.y2 = round(self.y2 + y)

    def __str__(self):
        return self.unitid

    #visual functions
    def face_direction(self, direction):
        if direction != self.direction:
            self.direction = direction

            if direction == "up":
                self.image = pygame.transform.rotate(self.image, (360 - self.angle))
                self.angle = 0
            elif direction == "down":
                self.image = pygame.transform.rotate(self.image, (180 - self.angle))
                self.angle = 180
            elif direction == "left":
                self.image = pygame.transform.rotate(self.image, (90 - self.angle))
                self.angle = 90
            elif direction == "right":
                self.image = pygame.transform.rotate(self.image, (270 - self.angle))
                self.angle = 270

    def face_diagonal(self, direction):
        pass
        #call this if the point the unit is facing has an x-diff to y-diff ratio of 1 (or close to 1?)

    def hp_check(self):
        if self.visible_hp:
            self.drawn_hp = self.visible_hp.pop()
        
        if self.drawn_hp <= 0:
            self.destroy()
        elif not self.dead:
            self.redraw_hp()

    def draw(self):
        self.rect.topleft = (self.x1, self.y1)
        hp_len = (self.master.tile_width)*0.8

        x1 = self.x1 - self.offset + (self.master.tile_width - hp_len)/2
        y1 = self.y1 - self.offset + (self.master.tile_height)/15

        self.border_rect.x = x1
        self.border_rect.y = y1

        for i in range(0, self.max_hp):
            self.hp_rects[i].x = x1+(hp_len/self.max_hp*i)
            self.hp_rects[i].y = y1

        i = 1
        for line in self.divider_lines:
            x = x1+(hp_len/self.max_hp*i)

            line.x = x
            line.y = y1

            i += 1

        if self.visible:
            if self not in self.master.visible_units:
                self.master.visible_units.add(self)
            if self in self.master.hidden_units:
                self.master.hidden_units.remove(self)
        else:
            if self not in self.master.hidden_units:
                self.master.hidden_units.add(self)
            if self in self.master.visible_units:
                self.master.visible_units.remove(self)


    def draw_hp(self):
        self.screen.blit(self.health_border, self.border_rect)

        for i in range(0, self.max_hp):
            self.screen.blit(self.hp_fill[i], self.hp_rects[i])

        for line in self.divider_lines:
            pygame.draw.rect(self.screen, self.master.black, line)
                


    def create_hp(self):
        hp_len = (self.master.tile_width)*0.8

        x1 = self.x1 + (self.master.tile_width - hp_len)/2
        y1 = self.y1 + (self.master.tile_height)/15
        y2 = y1 + hp_len/6

        if self.drawn_hp/self.max_hp == 1:
            hp_color = self.master.green
        elif self.drawn_hp/self.max_hp > 0.5:
            hp_color = self.master.yellow
        else:
            hp_color = self.master.red

        self.health_bar = []
        self.hp_fill = []
        self.hp_rects = []

        self.health_border = pygame.Surface([hp_len, abs(y1-y2)])
        self.health_border.fill(self.master.black)

        self.border_rect = self.health_border.get_rect()
        self.border_rect.x = x1
        self.border_rect.y = y1

        self.divider_lines = []

        for i in range(0, self.max_hp):
            hp_seg = pygame.Surface([hp_len/self.max_hp, abs(y1-y2)])
            hp_seg.fill(hp_color, hp_seg.get_rect().inflate(-6, -6))

            self.hp_fill.append(hp_seg)

            seg_rect = hp_seg.get_rect()

            x = x1+(hp_len/self.max_hp*i)
            seg_rect.x = x
            seg_rect.y = y1

            self.hp_rects.append(seg_rect)

            if i != 0:
                self.divider_lines.append(self.master.new_line(x, y1, x, y2-1, self.master.dark_grey, 3))


    def redraw_hp(self):
        if self.drawn_hp/self.max_hp == 1:
            hp_color = self.master.green
        elif self.drawn_hp/self.max_hp > 0.5:
            hp_color = self.master.yellow
        else:
            hp_color = self.master.red

        for i in range(0, self.max_hp):
            hp_seg = self.hp_fill[i]
            if i+1 <= self.drawn_hp:
                color = hp_color
            else:
                color = self.master.black
            hp_seg.fill(color, hp_seg.get_rect().inflate(-6, -6))
        self.draw()


    def delete_hp(self):
        for element in self.health_bar:
            self.canvas.delete(element)
        self.health_bar = []

    def highlight(self, color):
        self.delete()
        self.draw()

    def delete(self):
        self.kill()

    #technical stat functions
    def basic_atk(self):
        self.projectile = Projectile(self.master, self.screen, self.x1, self.y1,self.x2,self.y2, self.player, self.basic_atk_type, self.unit_color, self.tile, self)
        return self.projectile

    def activate(self):
        self.projectile = Projectile(self.master, self.screen, self.x1, self.y1,self.x2,self.y2, self.player, self.ability_projectile, self.unit_color, self.tile, self)
        return self.projectile

class Projectile(pygame.sprite.Sprite):
    def __init__(self, master, screen, x1, y1, x2, y2, player, stats_id, color, tile, unit):
        super().__init__()
        self.master = master
        self.screen = screen
        self.obj_type = "projectile"
        # self.visible = True
        self.player = player

        stats = Stats.projectile_stats(stats_id)

        self.name = stats["name"]
        self.proj_speed = stats["proj_speed"]
        self.sound = stats["sound"]
        self.end_sound = stats["end_sound"]

        self.color = color
        self.tile = tile
        self.shown_tile = tile
        self.unit = unit
        self.visible = False
        self.drawn_elements = []
        self.unit_targets = None
        self.tile_targets = None

        self.size_mult = 0.6
        self.angle = 0
        self.direction = "up"

        img_str = "./Assets/Proj/"+self.name+".png"

        self.image = pygame.image.load(img_str).convert_alpha()
        self.image = pygame.transform.scale(self.image, (round(abs(x1-x2)*self.size_mult), round(abs(y1-y2)*self.size_mult)))

        self.rect = self.image.get_rect()
        self.move(x1, y1, x2, y2)
        self.rect.center = ((x1+x2)/2, (y1+y2)/2)
        self.cycle_sprites = []
        self.draw()

    def face_direction(self, direction):
        if direction != self.direction:
            self.direction = direction

            if direction == "up":
                self.image = pygame.transform.rotate(self.image, (360 - self.angle))
                self.angle = 0
            elif direction == "down":
                self.image = pygame.transform.rotate(self.image, (180 - self.angle))
                self.angle = 180
            elif direction == "left":
                self.image = pygame.transform.rotate(self.image, (90 - self.angle))
                self.angle = 90
            elif direction == "right":
                self.image = pygame.transform.rotate(self.image, (270 - self.angle))
                self.angle = 270

    def face_angle(self, angle):
        if self.angle != angle:
            self.image = pygame.transform.rotate(self.image, (360 - self.angle))
            self.angle = angle
            self.image = pygame.transform.rotate(self.image, (self.angle))


    def draw(self):
        self.rect.center = ((self.x1+self.x2)/2, (self.y1+self.y2)/2)
        if self.visible:
            if self not in self.master.visible_projectiles:
                self.master.visible_projectiles.add(self)
            if self in self.master.hidden_projectiles:
                self.master.hidden_projectiles.remove(self)
        else:
            if self not in self.master.hidden_projectiles:
                self.master.hidden_projectiles.add(self)
            if self in self.master.visible_projectiles:
                self.master.visible_projectiles.remove(self)


    def move(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def incr_move(self, x, y):
        self.x1 = self.x1 + x
        self.y1 = self.y1 + y
        self.x2 = self.x2 + x
        self.y2 = self.y2 + y

    def move_to_tile(self, tile, redraw, fog, set_tile):
        self.tile = tile
        # self.offset = (abs(tile.x1-tile.x2) - (abs(tile.x1-tile.x2)*self.size_mult))/2
        # self.offset = 0
        # self.move(tile.x1+self.offset, tile.y1+self.offset, tile.x2+self.offset, tile.y2+self.offset)
        self.move(tile.x1, tile.y1, tile.x2, tile.y2)

    def setup_animation(self):
        for x in range(1, 8):

            img_str = "./Assets/Effects/explosion"+str(x)+".png"

            image = pygame.image.load(img_str).convert_alpha()
            image = pygame.transform.scale(image, (round(abs(self.tile.x1-self.tile.x2)*self.size_mult), round(abs(self.tile.y1-self.tile.y2)*self.size_mult)))

            self.cycle_sprites.append(image)


    def end_animation(self):
        self.visible = False
        self.draw()
        self.setup_animation()

        if self.unit.visible:
            self.master.play_sound(self.end_sound)

        self.master.animated_elements.append(self)

        self.animated_rects = []

        image = self.cycle_sprites[0]

        for tile in self.tile_targets:

            rect = image.get_rect()
            rect.center = ((tile.x1+tile.x2)/2, (tile.y1+tile.y2)/2)
            self.animated_rects.append(rect)

    def destroy(self):
        self.delete()
        self.visible = False

    def delete(self):
        self.kill()


#LARGE GOALS:
#fog of war! different thickness of fog? thick fog shows nothing, thin fog will show a shadow of a unit but not which unit is there
#after seeing an enemy unit, they will remain in "thin" fog until the end of the turn, even if the ally unit that spotted them moves out of vision
#click and drag to select tiles, expand the box by checking for any tile that is adjacent to two or more tiles
#have key to hold down 'a' that allows you to see what your attack/ability range is when deciding where to move, 
#^^ overlay the attack grid over the move grid from the new tile
#critical hits? as a buff effectively. i would either use criticals, or static dmg number buffs, probably not both? then again adding and multiplying is fun
#history bar of all actions taken? or just attacks/abilities?
#hex board????
#highlight units with queued abilities/attacks/movement with a corresponding color (ability:purple, attack:red/orange, movement:blue)

#coding goals
#possibly keep full history of all unit's actions/all general action history and then queue through them to execute the commands in order. this will keep 
#history which is useful for stats/debug/future ability design and also probably a more consistent way to keep track of everything thats going on by having one central action hub
#
#gravity affected projectiles that arc over the grid, (shooting straight up would result in the projectile getting larger to simulate vertical distance)
#make thin/thick fog
#make sure that units cannot "see" through fog around corners. 
#^^ make it so the unit vision cannot check left-adj tiles if they have already gone to a right-adj tile this path
#keep list of all "marks" a unit (or tile?) may have, bounties and any effects
#change ALL draw methods besides the first to use MOVE instead of DELETE and CREATE, it moves by x and y amount not to location x and y...
#code stack/message readiness, EX:
#move command is sent to both players
#move command is put on stack
#stack pops move command resolving its first iteration
#move command is sent to both players
#tile trigger is sent to both players
#move command is put on the stack
#tile trigger is put on the stack

#Game notes: double right click to actiavte abilities with nontraditional targets, also highlight/hover highlight all affected elements
#Eg. Activate to heal all allies = highlight all allies in purple, and then hovering over any of them would highlight them all yellow

#known bugs
#sometimes units moving into enemy vision are not shown visible
#some tiles remain highlighted after a unit has pathed through them. fixed?
#fix tile clicking to be more inclusive of clicks along the edge of a tile, either use the hovered tile data, or expand padding around clickable area
#katies computer bugs: renders all grass sprites as blue, tiles merge along edges based on cerain ways they overlap, changes with hover
#activated line shot ability of soldier does not deal damage when standing next to the target
#inputting arrow key movement too fast will cause the unit to move from where it was a tile earlier


#semi fixed bugs
#hard coded the direction to flip

#cleanup
#remove extra self.delete calls in unit and tile and projectile
#change hovertext to use the "width" feature to keep all lines of text in one text object, it automatically seperates them into lines less than the width
#redo grass image in this so all tiles share the same image asset
#highlight units with available actions
#when hovering over a movement path, display how many movement tiles the player is using for that unit, and how many movement tiles they have left


#OTHER GAME design ideas:
#digital tactic miniature game on a grid
#fog of war with stage hazards water/mountiants
#roll dice as mana?
#abilities that cost certain dice rolls to activate
#abilities that allow you to roll more dice
#form a "deck" of units that you have constant access to, perhaps organized in different categories on the side
#deck must not go over a certain point limit
#start the game by placing all/SOME of your units on the battlefield, up to a certain point threshhold, possibly different based on fog of war?
#on left display all units that you control, on the right side display all enemy units you can see, but also keep track of all enemy units you HAVE seen 
#but grey them out if they are currently unseen
#have units that give you special abilities you can use? like spells in your "hand"
#best two of three rounds, each round pick from a larger pool to make your squad each time, if any of your units die you cant use them for the next round
#capture the flag style?
#3 phases each turn? movement -> special ability -> basic attack
#special abilities have turn cooldowns?
#right click a unit to bring up menu of their activated skills, hovering over a skill displays what it does in the "effect text box" somewhere on the side
#stationary "construct" type of units that cant move and provide another type of aura bonus or attack, 
#have regular solider (builder/engineer tribe?) units be able to decrease the "casting cost" of constructs when you bulid your "deck" ???
#press "a" to select all friendly units to mass move/attack?


game = Game()
