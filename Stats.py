
def num_units():
	return range(1,6)

#ability types? currently only set up for point and click (pnc), 
#but other types could be non-targetting effects where you click on itself (global) 
#and abilities that still target via point and click, but dont have immidiate or traditional effects after activating (alt), such as a delayed air strike

def unit_stats(id):
	if id == 1: #basic soldier
		return {
			"cost":1,
			"unit_color":"variable",
			"unit_name":"soldier",
			"tribe":"Vaux",
			"display_name":"Vaux Soldier",
			"basic_atk_type":1,
			"ability_projectile":3,
			"ability_type":"pnc",
			"size_mult":0.6,
			"max_hp":3,
			"vision_range":3,
			"extra_props":False,
			"move_sound":"footstep09",
			# "atk_sound":"maximize_004",
			# "ability_sound":"error_006",


			"move_props":{"range":3,"max_range":3,"targets":["tile"],"player_target":None,"terrain":["grass"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"circle","target_type":"path"},

        	"atk_props":{"range":3,"dmg":1,"targets":["unit"],"player_target":"enemy","terrain":["grass"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"circle","target_type":"single"},

        	"ability_props":{"range":3,"dmg":2,"max_cooldown":1,"cooldown":0,"targets":["tile", "unit"],"player_target":["enemy"],"terrain":["grass", "mountain"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"line","direction":"all","line_stop":False,"target_type":"single"}
		}
	elif id == 2:
		return {
			"cost":2,
			"unit_color":"variable",
			"unit_name":"commando",
			"tribe":"Vaux",
			"display_name":"Vaux Commando",
			"basic_atk_type":1,
			"ability_projectile":3,
			"ability_type":"pnc",
			"size_mult":0.7,
			"max_hp":5,
			"vision_range":3,
			"extra_props":False,
			"move_sound":"footstep09",

			"move_props":{"range":3,"max_range":3,"targets":["tile"],"player_target":None,"terrain":["grass"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"circle","target_type":"path"},

        	"atk_props":{"range":3,"dmg":2,"targets":["unit"],"player_target":"enemy","terrain":["grass"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"circle","target_type":"single"},

        	"ability_props":{"range":4,"dmg":3,"max_cooldown":3,"cooldown":0,"targets":["tile", "unit"],"player_target":["enemy"],"terrain":["grass"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"line","direction":"all","line_stop":False,"target_type":"single"}
		}
	elif id == 3:
		return {
			"cost":3,
			"unit_color":"variable",
			"unit_name":"meguard",
			"tribe":"Vaux",
			"display_name":"Vaux Meguard",
			"basic_atk_type":1,
			"ability_projectile":4,
			"ability_type":"pnc",
			"size_mult":0.8,
			"max_hp":5,
			"vision_range":3,
			"extra_props":False,
			"move_sound":"footstep09",

			"move_props":{"range":3,"max_range":3,"targets":["tile"],"player_target":None,"terrain":["grass"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"circle","target_type":"path"},

        	"atk_props":{"range":3,"dmg":2,"targets":["unit"],"player_target":"enemy","terrain":["grass"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"circle","target_type":"single"},

        	"ability_props":{"range":3,"dmg":4,"max_cooldown":4,"cooldown":0,"targets":["tile", "unit", "self"],"player_target":["ally", "enemy"],"terrain":["grass", "mountain"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"circle","target_type":"aoe","aoe_shape":"circle","radius":1}
		}
	elif id == 4:
		return {
			"cost":3,
			"unit_color":"constant",
			"unit_name":"green_medic",
			"tribe":"Nox",
			"display_name":"Nox Medic",
			"basic_atk_type":2,
			"ability_projectile":2,
			"ability_type":"alt",
			"ability_id":2,
			"size_mult":0.8,
			"max_hp":5,
			"vision_range":3,
			"extra_props":True,
			"move_sound":"footstep09",

			"move_props":{"range":3,"max_range":3,"targets":["tile"],"player_target":None,"terrain":["grass"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"circle","target_type":"path"},

        	"atk_props":{"range":3,"dmg":-1,"targets":["unit"],"player_target":"ally","terrain":["grass"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"circle","target_type":"single"},

        	"ability_props":{"range":2,"dmg":3,"max_cooldown":1,"cooldown":0,"targets":["unit"],"player_target":"ally","terrain":["grass"],"unit_pierce":False,"terrain_pierce":False,"area_type":"circle","target_type":"single"},

        	"secondary_props":{"range":2,"dmg":3,"max_cooldown":1,"cooldown":0,"targets":["tile"],"player_target":["ally"],"terrain":["grass"],"unit_pierce":False,"terrain_pierce":False,"area_type":"circle","target_type":"single","cycles":2},
		}
	elif id == 5:
		return {
			"cost":2,
			"unit_color":"constant",
			"unit_name":"small_tank",
			"tribe":"Other",
			"display_name":"Tank",
			"basic_atk_type":4,
			"ability_projectile":2,
			"ability_type":"pnc",
			"ability_id":5,
			"size_mult":0.5,
			"max_hp":5,
			"vision_range":3,
			"extra_props":False,
			"move_sound":"footstep09",

			"move_props":{"range":3,"max_range":3,"targets":["tile"],"player_target":None,"terrain":["grass"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"circle","target_type":"path"},

        	"atk_props":{"range":3,"dmg":2,"targets":["unit"],"player_target":"enemy","terrain":["grass"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"circle","target_type":"single"},

        	# "ability_props":{"range":3,"dmg":1,"max_cooldown":0,"cooldown":0,"targets":["self", "unit"],"player_target":"ally","terrain":["grass"],"unit_pierce":False,"terrain_pierce":False,"area_type":"circle","target_type":"single","cycles":2},
        	"ability_props":{"range":3,"dmg":3,"max_cooldown":3,"cooldown":0,"targets":["tile", "unit"],"player_target":["ally","enemy"],"terrain":["grass"],"unit_pierce":False,"terrain_pierce":["grass"],"area_type":"line","direction":"all","line_stop":False,"target_type":"aoe","aoe_shape":"line","aoe_direction":"perpendicular","radius":1}
		}



def projectile_stats(id):
	if id == 1: #basic soldier
		return {
			"name":"laser",
			"proj_speed":15,
			"sound":"laser1",
			"end_sound":"maximize_004"
		}
	elif id == 2: #basic soldier
		return {
			"name":"green_laser",
			"proj_speed":15,
			"sound":"laser6",
			"end_sound":"maximize_004"
		}
	elif id == 3: #basic soldier
		return {
			"name":"rocket",
			"proj_speed":30,
			"sound":"error_006",
			"end_sound":"explosion_001"
		}
	elif id == 4: #basic soldier
		return {
			"name":"missile",
			"proj_speed":30,
			"sound":"error_006",
			"end_sound":"explosion_001"
		}

def ability_dict(id):
	if id == 5:
		return tank_ability
	elif id == 1:
		return teleport_target_rand
	elif id == 2:
		return teleport_target

def tank_ability(master, unit, tile, targets):
	if master.player == unit.player:

		groupid = ""
		for enemy_unit in master.enemy_deployed_units:
			groupid = groupid + " " + enemy_unit.unitid

		master.Send({"action": "recieveCommand", "msg":10, "gameid":master.gameid, "unitid":unit.unitid, "effect":"ability", "stat_type":"curr_hp", "groupid":groupid, "display_hp":True})

def teleport_target_rand(master, unit, tile, targets):
	master.teleport_unit_rand(unit, 0)

def teleport_target(master, unit, tile, targets):
	for obj in targets:
		master.teleport_unit(obj, tile)

def trap_stats(id):
	if id == 0:
		return {
			"effect":"unit.move_props['range'] = 0"
		}