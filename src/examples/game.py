from s2clientprotocol import sc2api_pb2 as sc_pb
from s2clientprotocol import raw_pb2 as raw_pb
from s2clientprotocol import score_pb2 as score_pb

import sys
sys.path.append('../core')
from sc2_comm import sc2
from core import Core

"""Initialize"""
# Try to make a connection with SC2
test_client = Core()
test_client.init()
test_client._start_new_game()

#Get Data
"""

data = sc_pb.RequestData()
data.ability_id=True
data.unit_type_id=True
test_client.comm.send(data=data)
#print(test_client.comm.read())

"""

"""Action"""
"""
unit_tag_list=[]

observation = sc_pb.RequestObservation()
t=test_client.comm.send(observation=observation)

for unit in t.observation.observation.raw_data.units:
    if unit.unit_type == 84: # Probe unit_type_tag
        unit_tag_list.append(unit.tag)

unit_command = raw_pb.ActionRawUnitCommand()
unit_command.ability_id = 16 # Move Ability
unit_command.target_unit_tag = unit_tag_list[0]
unit_command.unit_tags.append(unit_tag_list[1])
action_raw = raw_pb.ActionRaw(unit_command = unit_command)

action = sc_pb.RequestAction()
action.actions.add(action_raw = action_raw)
test_client.comm.send(action=action)

"""

"""Move Units"""

"""
unit_tag_list=[]

observation = sc_pb.RequestObservation()
t=test_client.comm.send(observation=observation)

for unit in t.observation.observation.raw_data.units:
    if unit.unit_type == 84: # Probe unit_type_tag
        unit_tag_list.append(unit.tag)

unit_command = raw_pb.ActionRawUnitCommand()
unit_command.ability_id = 16 # Move Ability
unit_command.target_world_space_pos.x = 30
unit_command.target_world_space_pos.y = 30
for i in range(0,12):
    unit_command.unit_tags.append(unit_tag_list[i])
action_raw = raw_pb.ActionRaw(unit_command = unit_command)

action = sc_pb.RequestAction()
action.actions.add(action_raw = action_raw)
test_client.comm.send(action=action)

#conn.close()

"""

"""Gather Mules"""

list_unit_tag = []
list_mineral_tag = []
observation = sc_pb.RequestObservation()
t = test_client.comm.send(observation=observation)

# make list of units_tags for probe and mineral
for unit in t.observation.observation.raw_data.units:
    if unit.unit_type == 84:  # Probe unit_type_tag
        list_unit_tag.append(unit.tag)
    if unit.unit_type == 341:  # Mineral unit_type_tag
        list_mineral_tag.append(unit.tag)

unit_command = raw_pb.ActionRawUnitCommand()
unit_command.ability_id = 166  # Gather Mule]

for unit_tag in list_unit_tag:
    unit_command.unit_tags.append(unit_tag)

unit_command.target_unit_tag = list_mineral_tag[0]

action_raw = raw_pb.ActionRaw(unit_command=unit_command)
action = sc_pb.RequestAction()
action.actions.add(action_raw=action_raw)
test_client.comm.send(action=action)

# 12 units keep gethering mules until minerals are over 200
while True:

    # request information about collected_minerals
    get_mineral = test_client.comm.send(observation=observation)
    collected_minerals = get_mineral.observation.observation.score.score_details.collected_minerals
    print(collected_minerals)

    # if collected_minerals are over 200, all units is stop
    if collected_minerals >= 50:
        break
print ("Stop")
unit_command = raw_pb.ActionRawUnitCommand()
unit_command.ability_id = 4  # Stop Ability
for unit_tag in list_unit_tag:
    unit_command.unit_tags.append(unit_tag)

action_raw = raw_pb.ActionRaw(unit_command=unit_command)
action.actions.add(action_raw=action_raw)

test_client.comm.send(action=action)

#conn.close()
