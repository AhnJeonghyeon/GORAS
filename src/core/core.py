#!/usr/bin/python3

"""
    This is a core module that supports fundamental componets to run simulation.
"""

import logging
import threading
import os
import time
import sys
import json

sys.path.append('../agent')
from agent import Agent
from goal import Goal, create_goal_set

from sc2_comm import sc2
from s2clientprotocol import sc2api_pb2 as sc_pb
from s2clientprotocol import raw_pb2 as raw_pb

from utils.communicator import Communicator, proxy

from google.protobuf import json_format

from utils.jsonencoder import PythonObjectEncoder

FORMAT = '%(asctime)s %(module)s %(levelname)s %(lineno)d %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


class Core(object):
    def __init__(self):
        self.comm_sc2 = sc2()
        self.port = 5000

        if sys.platform == "darwin":  # Mac OS X
            self.launcher_path = "/Applications/StarCraft\ II/Support/SC2Switcher.app/Contents/MacOS/SC2Switcher\
                                  --listen 127.0.0.1\
                                  --port %s" % self.port
            self.map_path = os.getcwd() + '/../../resource/Maps/GorasMap_GG.SC2Map'

        elif sys.platform == "win32":  # Windows

            self.launcher_path = 'C:\\"Program Files (x86)"\\"StarCraft II"\\"Support"\SC2Switcher.exe --listen 127.0.0.1 --port %s"' % self.port
            self.map_path = os.getcwd() + '/../../resource/Maps/GorasMap.SC2Map'

        else:
            logger.error("Sorry, we cannot start on your OS.")

        # Communicator between the core and agents.
        self.comm_agents = Communicator(topic='core')

        # Set the Proxy and Agents Threads.
        self.thread_proxy = threading.Thread(target=proxy)
        self.threads_agents = []

        # for test two agent sys
        self.spawned_agent = 0

        # Set the dictionary to save the information from SC2 client.
        self.dict_probe = {}
        self.dict_mineral = {}
        self.dict_nexus = {}
        self.next_pylon_pos = (27, 33)

    def init(self):

        # execute SC2 client.
        try:
            os.system(self.launcher_path)

            time.sleep(5)  # need time to connect after launch app.

        except:
            logger.error("Failed to open sc2.")

        # connection between core and sc2_client using sc2 protobuf.
        self.comm_sc2.open()

    def deinit(self):
        self.comm_agents.close()
        self.comm_sc2.close()

    '''
        Collection of Requests to SC2 client.

            Includes,
            - _start_new_game
                    After starting SC2 client, to start the game, we have to select the map and request to open the game.
                    Set the game configuration, and request to join that game.
            - _leave_game
                    When the goal-oriented simulation is finished, Leave the game to end program.
            - _quit_sc2
                    Quit the SC2 client program.
            - _train_probe
                    Train a probe in nexus.
                    It doesn't wait for spawning a probe, so cannot start a new agent thread.
            - _build_pylon
                    Build the pylon on storage_area which is start from (x,y) = (27,33), add 2 to x after that.
            - _req_playerdata
                    Request the basic information data to SC2 client.
                    Update some data 'dict_probe', 'dict_pylon', 'dict_nexus'.
                    Return the tuple that includes 'the amount of minerals', 'food capacity', 'food used'
    '''

    def _start_new_game(self):

        # create a game
        try:
            map_info = sc_pb.LocalMap()

            map_info.map_path = self.map_path
            create_game = sc_pb.RequestCreateGame(local_map=map_info)
            create_game.player_setup.add(type=1)
            # create_game.player_setup.add(type=2)

            create_game.realtime = True

            # send Request
            print(self.comm_sc2.send(create_game=create_game))
            # print (test_client.comm.read())

            logger.info('New game is created.')
        except Exception as ex:
            logger.error('While creating a new game: %s' % str(ex))

        # join the game
        try:
            interface_options = sc_pb.InterfaceOptions(raw=True, score=True)
            join_game = sc_pb.RequestJoinGame(race=3, options=interface_options)

            # send Request
            print(self.comm_sc2.send(join_game=join_game))

            logger.info('Success to join the game.')
        except Exception as ex:
            logger.error('While joining the game: %s' % str(ex))

        # Game Start
        try:
            # print(self.comm_sc2.send(step=sc_pb.RequestStep(count=1)))

            logger.info('Game is Started.')
        except Exception as ex:
            logger.error('While starting a new game: %s' % str(ex))

    def _leave_game(self):
        print(self.comm_sc2.send(leave_game=sc_pb.RequestLeaveGame()))
        logger.info('Leave the Game.')

    def _quit_sc2(self):
        print(self.comm_sc2.send(quit=sc_pb.RequestQuit()))
        logger.info("Quit the SC2 client")

    def _train_probe(self, nexus_tag):

        unit_command = raw_pb.ActionRawUnitCommand(ability_id=1006)
        unit_command.unit_tags.append(nexus_tag)
        action_raw = raw_pb.ActionRaw(unit_command=unit_command)
        action = sc_pb.RequestAction()
        action.actions.add(action_raw=action_raw)
        t = self.comm_sc2.send(action=action)

    def _build_pylon(self, probe_tag):
        # build_pylon
        unit_command = raw_pb.ActionRawUnitCommand(ability_id=881)
        unit_command.unit_tags.append(probe_tag)
        unit_command.target_world_space_pos.x = 38
        unit_command.target_world_space_pos.y = 29
        action_raw = raw_pb.ActionRaw(unit_command=unit_command)
        action = sc_pb.RequestAction()
        action.actions.add(action_raw=action_raw)
        self.comm_sc2.send(action=action)

    def _req_playerdata(self):
        observation = sc_pb.RequestObservation()
        t = self.comm_sc2.send(observation=observation)
        num_pylon = 0

        for unit in t.observation.observation.raw_data.units:

            if unit.unit_type == 84:  # Probe tag

                # Already exists
                if unit.tag in self.dict_probe:
                    self.dict_probe[unit.tag] = (unit.pos.x, unit.pos.y, unit.pos.z)
                else:
                    # new probe
                    if self.spawned_agent >= 4:
                        continue

                    self.dict_probe[unit.tag] = (unit.pos.x, unit.pos.y, unit.pos.z)

                    # new thread starts -> spawn a new probe.
                    self.threads_agents.append(Agent())

                    # If the agent have to know their name
                    # send_knowledge={}
                    # send_knowledge.update(self.initial_knowledge)
                    # send_knowledge.update({''})

                    self.threads_agents[-1].spawn(unit.tag, 84,
                                                  initial_knowledge=self.initial_knowledge,
                                                  initial_goals=[create_goal_set(self.goal)]
                                                  )

                    self.threads_agents[-1].start()
                    self.spawned_agent += 1

            if unit.unit_type == 341:  # Mineral tag

                # Already exists
                if unit.tag in self.dict_mineral:
                    self.dict_mineral[unit.tag] = (unit.pos.x, unit.pos.y, unit.pos.z)
                else:
                    # new pylon
                    self.dict_mineral[unit.tag] = (unit.pos.x, unit.pos.y, unit.pos.z)

            if unit.unit_type == 60:
                num_pylon += 1

            if unit.unit_type == 59:
                # Already exists
                if unit.tag in self.dict_mineral:
                    self.dict_nexus[unit.tag] = (unit.pos.x, unit.pos.y, unit.pos.z)
                else:
                    # new nexus
                    self.dict_nexus[unit.tag] = (unit.pos.x, unit.pos.y, unit.pos.z)

        minerals = t.observation.observation.player_common.minerals
        food_cap = t.observation.observation.player_common.food_cap
        food_used = t.observation.observation.player_common.food_used
        print('Minerals: ', minerals)
        print('Population: %d/%d' % (food_used, food_cap))
        print('Pylons: ', num_pylon)
        return (minerals, food_cap, food_used, num_pylon)

    '''
        Connection methods to broadast and receive msg.

            Includes,
            - _start_proxy
                    Start the proxy that is broker among the agents, also between core and agents.
            - broadcast
                    Usually use 'broadcast' to 'agents' from 'core' to send the status of player in SC2.
            - perceive_request
                    To get requests from agents, such as to move probe, to gather minerals.
    '''

    def _start_proxy(self):
        logger.info("Try to turn on proxy...")
        self.thread_proxy.start()
        time.sleep(1)  # wait for turn on proxy

    def broadcast(self, msg):
        self.comm_agents.send(msg, broadcast=True)

    def perceive_request(self):
        return self.comm_agents.read()

    def set_goal(self):
        observation = sc_pb.RequestObservation()
        t = self.comm_sc2.send(observation=observation)

        list_minerals = []

        for unit in t.observation.observation.raw_data.units:
            if unit.unit_type == 341:  # Mineral tag
                list_minerals.append(unit.tag)


        self.goal = {'goal': 'I have GG Pylon',
                     'trigger': [],
                     'satisfy': [
                         ('type2', 'i', 'have', ['100 minerals'])
                     ],
                     'precedent': [],
                     'require': [
                         {'goal': 'I have G 1',
                          'require': [
                         {'goal': 'I have pylon 1',
                          'require': [
                              {'goal': 'I have pylon 2',
                               'require': [
                                   {'goal': 'I have pylon 3',
                                    'require': [
                                        {'goal': 'I have pylon 4',
                                         'require': [
                                             {'goal': 'I have pylon 5',
                                              'require': [
                                                  {'goal': 'I have pylon 6',
                                                   'require': [
                                                       {'goal': 'I have pylon 7',
                                                        'require': [
                                                            {'goal': 'I have pylon 8',
                                                             'require': [
                                                                 {'goal': 'I have pylon 9',
                                                                  'require': [
                                                                      {'goal': 'I have pylon 10',
                                                                       'require': [
                                                                           {'goal': 'gather 100 minerals 10',
                                                                            'require': [
                                                                                ['gather 37', {'target': 'unit',
                                                                                               'unit_tag':
                                                                                                   list_minerals[0]},
                                                                                 'General'],
                                                                                # target: unit
                                                                                ['gather 38', {'target': 'unit',
                                                                                               'unit_tag':
                                                                                                   list_minerals[0]},
                                                                                 'General'],
                                                                                ['gather 39', {'target': 'unit',
                                                                                               'unit_tag':
                                                                                                   list_minerals[0]},
                                                                                 'General'],
                                                                                ['gather 40', {'target': 'unit',
                                                                                               'unit_tag':
                                                                                                   list_minerals[0]},
                                                                                 'General'],
                                                                                ['check mineral 10',
                                                                                 {'target': 'minerals', 'amount': 100},
                                                                                 'Query'],
                                                                            ]
                                                                            },
                                                                           ['build_pylon 10',
                                                                            {'target': 'point', 'pos_x': 30,
                                                                             'pos_y': 36},
                                                                            'General'],
                                                                           ['built pylon 10',
                                                                            {'target': 'pylons', 'built': 1}, 'Query'],

                                                                       ]
                                                                       },

                                                                      {'goal': 'gather 100 minerals 9',
                                                                       'require': [
                                                                           ['gather 33', {'target': 'unit',
                                                                                          'unit_tag': list_minerals[0]},
                                                                            'General'],
                                                                           # target: unit
                                                                           ['gather 34', {'target': 'unit',
                                                                                          'unit_tag': list_minerals[0]},
                                                                            'General'],
                                                                           ['gather 35', {'target': 'unit',
                                                                                          'unit_tag': list_minerals[0]},
                                                                            'General'],
                                                                           ['gather 36', {'target': 'unit',
                                                                                          'unit_tag': list_minerals[0]},
                                                                            'General'],
                                                                           ['check mineral 9',
                                                                            {'target': 'minerals', 'amount': 100},
                                                                            'Query'],
                                                                       ]
                                                                       },
                                                                      ['build_pylon 9',
                                                                       {'target': 'point', 'pos_x': 32, 'pos_y': 36},
                                                                       'General'],
                                                                      ['built pylon 9',
                                                                       {'target': 'pylons', 'built': 2}, 'Query'],

                                                                  ]
                                                                  },
                                                                 {'goal': 'gather 100 minerals 8',
                                                                  'require': [
                                                                      ['gather 29',
                                                                       {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                       'General'],
                                                                      # target: unit
                                                                      ['gather 30',
                                                                       {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                       'General'],
                                                                      ['gather 31',
                                                                       {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                       'General'],
                                                                      ['gather 32',
                                                                       {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                       'General'],
                                                                      ['check mineral 8',
                                                                       {'target': 'minerals', 'amount': 100},
                                                                       'Query'],
                                                                  ]
                                                                  },
                                                                 ['build_pylon 8',
                                                                  {'target': 'point', 'pos_x': 32, 'pos_y': 34},
                                                                  'General'],
                                                                 ['built pylon 8', {'target': 'pylons', 'built': 3},
                                                                  'Query'],

                                                             ]
                                                            },
                                                            {'goal': 'gather 100 minerals 7',
                                                             'require': [
                                                                 ['gather 25',
                                                                  {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                  'General'],
                                                                 # target: unit
                                                                 ['gather 26',
                                                                  {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                  'General'],
                                                                 ['gather 27',
                                                                  {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                  'General'],
                                                                 ['gather 28',
                                                                  {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                  'General'],
                                                                 ['check mineral 7',
                                                                  {'target': 'minerals', 'amount': 100},
                                                                  'Query'],
                                                             ]
                                                             },
                                                            ['build_pylon 7',
                                                             {'target': 'point', 'pos_x': 30, 'pos_y': 32},
                                                             'General'],
                                                            ['built pylon 7', {'target': 'pylons', 'built': 4},
                                                             'Query'],

                                                        ]
                                                        },
                                                       {'goal': 'gather 100 minerals 6',
                                                        'require': [
                                                            ['gather 21',
                                                             {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                             'General'],
                                                            # target: unit
                                                            ['gather 22',
                                                             {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                             'General'],
                                                            ['gather 23',
                                                             {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                             'General'],
                                                            ['gather 24',
                                                             {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                             'General'],
                                                            ['check mineral 6', {'target': 'minerals', 'amount': 100},
                                                             'Query'],
                                                        ]
                                                        },
                                                       ['build_pylon 6', {'target': 'point', 'pos_x': 28, 'pos_y': 32},
                                                        'General'],
                                                       ['built pylon 6', {'target': 'pylons', 'built': 5}, 'Query'],

                                                   ]

                                                  },
                                                  {'goal': 'gather 100 minerals 5',
                                                   'require': [
                                                       ['gather 17', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                        'General'],
                                                       # target: unit
                                                       ['gather 18', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                        'General'],
                                                       ['gather 19', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                        'General'],
                                                       ['gather 20', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                        'General'],
                                                       ['check mineral 5', {'target': 'minerals', 'amount': 100},
                                                        'Query'],
                                                   ]
                                                   },
                                                  ['build_pylon 5', {'target': 'point', 'pos_x': 26, 'pos_y': 34},
                                                   'General'],
                                                  ['built pylon 5', {'target': 'pylons', 'built': 6}, 'Query'],
                                              ]
                                              },
                                             {'goal': 'gather 100 minerals 4',
                                              'require': [
                                                  ['gather 13', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                   'General'],
                                                  # target: unit
                                                  ['gather 14', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                   'General'],
                                                  ['gather 15', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                   'General'],
                                                  ['gather 16', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                   'General'],
                                                  ['check mineral 4', {'target': 'minerals', 'amount': 100}, 'Query'],
                                              ]
                                              },
                                             ['build_pylon 4', {'target': 'point', 'pos_x': 26, 'pos_y': 36},
                                              'General'],
                                             ['built pylon 4', {'target': 'pylons', 'built': 7}, 'Query'],

                                         ]

                                         },
                                        {'goal': 'gather 100 minerals 3',
                                         'require': [
                                             ['gather 9', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                             # target: unit
                                             ['gather 10', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                             ['gather 11', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                             ['gather 12', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                             ['check mineral 3', {'target': 'minerals', 'amount': 100}, 'Query'],
                                         ]
                                         },
                                        ['build_pylon 3', {'target': 'point', 'pos_x': 26, 'pos_y': 38}, 'General'],
                                        ['built pylon 3', {'target': 'pylons', 'built': 8}, 'Query'],

                                    ]
                                    },
                                   {'goal': 'gather 100 minerals 2',
                                    'require': [
                                        ['gather 5', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                        # target: unit
                                        ['gather 6', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                        ['gather 7', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                        ['gather 8', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                        ['check mineral 2', {'target': 'minerals', 'amount': 100}, 'Query'],
                                    ]
                                    },
                                   ['build_pylon 2', {'target': 'point', 'pos_x': 28, 'pos_y': 40}, 'General'],
                                   ['built pylon 2', {'target': 'pylons', 'built': 9}, 'Query'],
                               ]
                               },
                              ]
                          },
                         {'goal': 'gather 100 minerals 1',
                          'require': [
                              ['gather 1', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                              # target: unit
                              ['gather 2', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                              ['gather 3', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                              ['gather 4', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                              ['check mineral 1', {'target': 'minerals', 'amount': 100}, 'Query'],
                          ]
                          },
                         ['build_pylon 1', {'target': 'point', 'pos_x': 30, 'pos_y': 40}, 'General'],
                         ['built pylon 1', {'target': 'pylons', 'built': 10}, 'Query'],
                     ]
                     },
                         {'goal': 'I have G 2',
                          'require': [
                              {'goal': 'I have pylon 11',
                               'require': [
                                   {'goal': 'I have pylon 12',
                                    'require': [
                                        {'goal': 'I have pylon 13',
                                         'require': [
                                             {'goal': 'I have pylon 14',
                                              'require': [
                                                  {'goal': 'I have pylon 15',
                                                   'require': [
                                                       {'goal': 'I have pylon 16',
                                                        'require': [
                                                            {'goal': 'I have pylon 17',
                                                             'require': [
                                                                 {'goal': 'I have pylon 18',
                                                                  'require': [
                                                                      {'goal': 'I have pylon 19',
                                                                       'require': [
                                                                           {'goal': 'I have pylon 20',
                                                                            'require': [
                                                                                {'goal': 'gather 100 minerals 20',
                                                                                 'require': [
                                                                                     ['gather 77', {'target': 'unit',
                                                                                                    'unit_tag':
                                                                                                        list_minerals[
                                                                                                            0]},
                                                                                      'General'],
                                                                                     # target: unit
                                                                                     ['gather 78', {'target': 'unit',
                                                                                                    'unit_tag':
                                                                                                        list_minerals[
                                                                                                            0]},
                                                                                      'General'],
                                                                                     ['gather 79', {'target': 'unit',
                                                                                                    'unit_tag':
                                                                                                        list_minerals[
                                                                                                            0]},
                                                                                      'General'],
                                                                                     ['gather 80', {'target': 'unit',
                                                                                                    'unit_tag':
                                                                                                        list_minerals[
                                                                                                            0]},
                                                                                      'General'],
                                                                                     ['check mineral 20',
                                                                                      {'target': 'minerals',
                                                                                       'amount': 100},
                                                                                      'Query'],
                                                                                 ]
                                                                                 },
                                                                                ['build_pylon 20',
                                                                                 {'target': 'point', 'pos_x': 39,
                                                                                  'pos_y': 36},
                                                                                 'General'],
                                                                                ['built pylon 11',
                                                                                 {'target': 'pylons', 'built': 11},
                                                                                 'Query'],

                                                                            ]
                                                                            },

                                                                           {'goal': 'gather 100 minerals 19',
                                                                            'require': [
                                                                                ['gather 73', {'target': 'unit',
                                                                                               'unit_tag':
                                                                                                   list_minerals[0]},
                                                                                 'General'],
                                                                                # target: unit
                                                                                ['gather 74', {'target': 'unit',
                                                                                               'unit_tag':
                                                                                                   list_minerals[0]},
                                                                                 'General'],
                                                                                ['gather 75', {'target': 'unit',
                                                                                               'unit_tag':
                                                                                                   list_minerals[0]},
                                                                                 'General'],
                                                                                ['gather 76', {'target': 'unit',
                                                                                               'unit_tag':
                                                                                                   list_minerals[0]},
                                                                                 'General'],
                                                                                ['check mineral 19',
                                                                                 {'target': 'minerals', 'amount': 100},
                                                                                 'Query'],
                                                                            ]
                                                                            },
                                                                           ['build_pylon 19',
                                                                            {'target': 'point', 'pos_x': 41,
                                                                             'pos_y': 36},
                                                                            'General'],
                                                                           ['built pylon 19',
                                                                            {'target': 'pylons', 'built': 12}, 'Query'],

                                                                       ]
                                                                       },
                                                                      {'goal': 'gather 100 minerals 18',
                                                                       'require': [
                                                                           ['gather 69',
                                                                            {'target': 'unit',
                                                                             'unit_tag': list_minerals[0]},
                                                                            'General'],
                                                                           # target: unit
                                                                           ['gather 70',
                                                                            {'target': 'unit',
                                                                             'unit_tag': list_minerals[0]},
                                                                            'General'],
                                                                           ['gather 71',
                                                                            {'target': 'unit',
                                                                             'unit_tag': list_minerals[0]},
                                                                            'General'],
                                                                           ['gather 72',
                                                                            {'target': 'unit',
                                                                             'unit_tag': list_minerals[0]},
                                                                            'General'],
                                                                           ['check mineral 18',
                                                                            {'target': 'minerals', 'amount': 100},
                                                                            'Query'],
                                                                       ]
                                                                       },
                                                                      ['build_pylon 18',
                                                                       {'target': 'point', 'pos_x': 41, 'pos_y': 34},
                                                                       'General'],
                                                                      ['built pylon 18',
                                                                       {'target': 'pylons', 'built': 13},
                                                                       'Query'],

                                                                  ]
                                                                  },
                                                                 {'goal': 'gather 100 minerals 17',
                                                                  'require': [
                                                                      ['gather 65',
                                                                       {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                       'General'],
                                                                      # target: unit
                                                                      ['gather 66',
                                                                       {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                       'General'],
                                                                      ['gather 67',
                                                                       {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                       'General'],
                                                                      ['gather 68',
                                                                       {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                       'General'],
                                                                      ['check mineral 17',
                                                                       {'target': 'minerals', 'amount': 100},
                                                                       'Query'],
                                                                  ]
                                                                  },
                                                                 ['build_pylon 17',
                                                                  {'target': 'point', 'pos_x': 39, 'pos_y': 32},
                                                                  'General'],
                                                                 ['built pylon 17', {'target': 'pylons', 'built': 14},
                                                                  'Query'],

                                                             ]
                                                             },
                                                            {'goal': 'gather 100 minerals 16',
                                                             'require': [
                                                                 ['gather 61',
                                                                  {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                  'General'],
                                                                 # target: unit
                                                                 ['gather 62',
                                                                  {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                  'General'],
                                                                 ['gather 63',
                                                                  {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                  'General'],
                                                                 ['gather 64',
                                                                  {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                                  'General'],
                                                                 ['check mineral 16',
                                                                  {'target': 'minerals', 'amount': 100},
                                                                  'Query'],
                                                             ]
                                                             },
                                                            ['build_pylon 16',
                                                             {'target': 'point', 'pos_x': 37, 'pos_y': 32},
                                                             'General'],
                                                            ['built pylon 16', {'target': 'pylons', 'built': 15},
                                                             'Query'],

                                                        ]

                                                        },
                                                       {'goal': 'gather 100 minerals 15',
                                                        'require': [
                                                            ['gather 57',
                                                             {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                             'General'],
                                                            # target: unit
                                                            ['gather 58',
                                                             {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                             'General'],
                                                            ['gather 59',
                                                             {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                             'General'],
                                                            ['gather 60',
                                                             {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                             'General'],
                                                            ['check mineral 15', {'target': 'minerals', 'amount': 100},
                                                             'Query'],
                                                        ]
                                                        },
                                                       ['build_pylon 15', {'target': 'point', 'pos_x': 35, 'pos_y': 34},
                                                        'General'],
                                                       ['built pylon 15', {'target': 'pylons', 'built': 16}, 'Query'],
                                                   ]
                                                   },
                                                  {'goal': 'gather 100 minerals 14',
                                                   'require': [
                                                       ['gather 53', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                        'General'],
                                                       # target: unit
                                                       ['gather 54', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                        'General'],
                                                       ['gather 55', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                        'General'],
                                                       ['gather 56', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                        'General'],
                                                       ['check mineral 14', {'target': 'minerals', 'amount': 100},
                                                        'Query'],
                                                   ]
                                                   },
                                                  ['build_pylon 14', {'target': 'point', 'pos_x': 35, 'pos_y': 36},
                                                   'General'],
                                                  ['built pylon 14', {'target': 'pylons', 'built': 17}, 'Query'],

                                              ]

                                              },
                                             {'goal': 'gather 100 minerals 13',
                                              'require': [
                                                  ['gather 49', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                   'General'],
                                                  # target: unit
                                                  ['gather 50', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                   'General'],
                                                  ['gather 51', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                   'General'],
                                                  ['gather 52', {'target': 'unit', 'unit_tag': list_minerals[0]},
                                                   'General'],
                                                  ['check mineral 13', {'target': 'minerals', 'amount': 100}, 'Query'],
                                              ]
                                              },
                                             ['build_pylon 13', {'target': 'point', 'pos_x': 35, 'pos_y': 38},
                                              'General'],
                                             ['built pylon 13', {'target': 'pylons', 'built': 18}, 'Query'],

                                         ]
                                         },
                                        {'goal': 'gather 100 minerals 12',
                                         'require': [
                                             ['gather 45', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                             # target: unit
                                             ['gather 46', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                             ['gather 47', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                             ['gather 48', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                             ['check mineral 12', {'target': 'minerals', 'amount': 100}, 'Query'],
                                         ]
                                         },
                                        ['build_pylon 12', {'target': 'point', 'pos_x': 37, 'pos_y': 40}, 'General'],
                                        ['built pylon 12', {'target': 'pylons', 'built': 19}, 'Query'],
                                    ]
                                    },
                               ]
                               },
                              {'goal': 'gather 100 minerals 11',
                               'require': [
                                   ['gather 41', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                   # target: unit
                                   ['gather 42', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                   ['gather 43', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                   ['gather 44', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                   ['check mineral 11', {'target': 'minerals', 'amount': 100}, 'Query'],
                               ]
                               },
                              ['build_pylon 11', {'target': 'point', 'pos_x': 39, 'pos_y': 40}, 'General'],
                              ['built pylon 11', {'target': 'pylons', 'built': 20}, 'Query'],
                          ]
                          },

                     ]

                     }

    def set_init_kn(self):
        self.initial_knowledge = {self.goal['goal']: {'is': 'Not Assigned'},
                                      'I have G 1': {'is': 'Not Assigned'},
                                      'I have G 2': {'is': 'Not Assigned'},
                                      'gather 100 minerals 1': {'is': 'Not Assigned'},
                                      'gather 100 minerals 2': {'is': 'Not Assigned'},
                                      'gather 100 minerals 3': {'is': 'Not Assigend'},
                                      'gather 100 minerals 4': {'is': 'Not Assigned'},
                                      'gather 100 minerals 5': {'is': 'Not Assigend'},
                                      'gather 100 minerals 6': {'is': 'Not Assigned'},
                                      'gather 100 minerals 7': {'is': 'Not Assigned'},
                                      'gather 100 minerals 8': {'is': 'Not Assigend'},
                                      'gather 100 minerals 9': {'is': 'Not Assigned'},
                                      'gather 100 minerals 10': {'is': 'Not Assigend'},
                                      'gather 100 minerals 11': {'is': 'Not Assigned'},
                                      'gather 100 minerals 12': {'is': 'Not Assigned'},
                                      'gather 100 minerals 13': {'is': 'Not Assigend'},
                                      'gather 100 minerals 14': {'is': 'Not Assigned'},
                                      'gather 100 minerals 15': {'is': 'Not Assigend'},
                                      'gather 100 minerals 16': {'is': 'Not Assigned'},
                                      'gather 100 minerals 17': {'is': 'Not Assigned'},
                                      'gather 100 minerals 18': {'is': 'Not Assigend'},
                                      'gather 100 minerals 19': {'is': 'Not Assigned'},
                                      'gather 100 minerals 20': {'is': 'Not Assigend'},
                                      'I have pylon 1': {'is': 'Not Assigned'},
                                      'I have pylon 2': {'is': 'Not Assigned'},
                                      'I have pylon 3': {'is': 'Not Assgiend'},
                                      'I have pylon 4': {'is': 'Not Assigned'},
                                      'I have pylon 5': {'is': 'Not Assgiend'},
                                      'I have pylon 6': {'is': 'Not Assigned'},
                                      'I have pylon 7': {'is': 'Not Assigned'},
                                      'I have pylon 8': {'is': 'Not Assgiend'},
                                      'I have pylon 9': {'is': 'Not Assigned'},
                                      'I have pylon 10': {'is': 'Not Assgiend'},
                                      'I have pylon 11': {'is': 'Not Assigned'},
                                      'I have pylon 12': {'is': 'Not Assigned'},
                                      'I have pylon 13': {'is': 'Not Assgiend'},
                                      'I have pylon 14': {'is': 'Not Assigned'},
                                      'I have pylon 15': {'is': 'Not Assgiend'},
                                      'I have pylon 16': {'is': 'Not Assigned'},
                                      'I have pylon 17': {'is': 'Not Assigned'},
                                      'I have pylon 18': {'is': 'Not Assgiend'},
                                      'I have pylon 19': {'is': 'Not Assigned'},
                                      'I have pylon 20': {'is': 'Not Assgiend'},
                                      'gather 1': {'is': 'Ready'},
                                      'gather 2': {'is': 'Ready'},
                                      'gather 3': {'is': 'Ready'},
                                      'gather 4': {'is': 'Ready'},
                                      'gather 5': {'is': 'Ready'},
                                      'gather 6': {'is': 'Ready'},
                                      'gather 7': {'is': 'Ready'},
                                      'gather 8': {'is': 'Ready'},
                                      'gather 9': {'is': 'Ready'},
                                      'gather 10': {'is': 'Ready'},
                                      'gather 11': {'is': 'Ready'},
                                      'gather 12': {'is': 'Ready'},
                                      'gather 13': {'is': 'Ready'},
                                      'gather 14': {'is': 'Ready'},
                                      'gather 15': {'is': 'Ready'},
                                      'gather 16': {'is': 'Ready'},
                                      'gather 17': {'is': 'Ready'},
                                      'gather 18': {'is': 'Ready'},
                                      'gather 19': {'is': 'Ready'},
                                      'gather 20': {'is': 'Ready'},
                                      'gather 21': {'is': 'Ready'},
                                      'gather 22': {'is': 'Ready'},
                                      'gather 23': {'is': 'Ready'},
                                      'gather 24': {'is': 'Ready'},
                                      'gather 25': {'is': 'Ready'},
                                      'gather 26': {'is': 'Ready'},
                                      'gather 27': {'is': 'Ready'},
                                      'gather 28': {'is': 'Ready'},
                                      'gather 29': {'is': 'Ready'},
                                      'gather 30': {'is': 'Ready'},
                                      'gather 31': {'is': 'Ready'},
                                      'gather 32': {'is': 'Ready'},
                                      'gather 33': {'is': 'Ready'},
                                      'gather 34': {'is': 'Ready'},
                                      'gather 35': {'is': 'Ready'},
                                      'gather 36': {'is': 'Ready'},
                                      'gather 37': {'is': 'Ready'},
                                      'gather 38': {'is': 'Ready'},
                                      'gather 39': {'is': 'Ready'},
                                      'gather 40': {'is': 'Ready'},
                                      'gather 41': {'is': 'Ready'},
                                      'gather 42': {'is': 'Ready'},
                                      'gather 43': {'is': 'Ready'},
                                      'gather 44': {'is': 'Ready'},
                                      'gather 45': {'is': 'Ready'},
                                      'gather 46': {'is': 'Ready'},
                                      'gather 47': {'is': 'Ready'},
                                      'gather 48': {'is': 'Ready'},
                                      'gather 49': {'is': 'Ready'},
                                      'gather 50': {'is': 'Ready'},
                                      'gather 51': {'is': 'Ready'},
                                      'gather 52': {'is': 'Ready'},
                                      'gather 53': {'is': 'Ready'},
                                      'gather 54': {'is': 'Ready'},
                                      'gather 55': {'is': 'Ready'},
                                      'gather 56': {'is': 'Ready'},
                                      'gather 57': {'is': 'Ready'},
                                      'gather 58': {'is': 'Ready'},
                                      'gather 59': {'is': 'Ready'},
                                      'gather 60': {'is': 'Ready'},
                                      'gather 61': {'is': 'Ready'},
                                      'gather 62': {'is': 'Ready'},
                                      'gather 63': {'is': 'Ready'},
                                      'gather 64': {'is': 'Ready'},
                                      'gather 65': {'is': 'Ready'},
                                      'gather 66': {'is': 'Ready'},
                                      'gather 67': {'is': 'Ready'},
                                      'gather 68': {'is': 'Ready'},
                                      'gather 69': {'is': 'Ready'},
                                      'gather 70': {'is': 'Ready'},
                                      'gather 71': {'is': 'Ready'},
                                      'gather 72': {'is': 'Ready'},
                                      'gather 73': {'is': 'Ready'},
                                      'gather 74': {'is': 'Ready'},
                                      'gather 75': {'is': 'Ready'},
                                      'gather 76': {'is': 'Ready'},
                                      'gather 77': {'is': 'Ready'},
                                      'gather 78': {'is': 'Ready'},
                                      'gather 79': {'is': 'Ready'},
                                      'gather 80': {'is': 'Ready'},
                                      'build_pylon 1': {'is': 'Ready'},
                                      'build_pylon 2': {'is': 'Ready'},
                                      'build_pylon 3': {'is': 'Ready'},
                                      'build_pylon 4': {'is': 'Ready'},
                                      'build_pylon 5': {'is': 'Ready'},
                                      'build_pylon 6': {'is': 'Ready'},
                                      'build_pylon 7': {'is': 'Ready'},
                                      'build_pylon 8': {'is': 'Ready'},
                                      'build_pylon 9': {'is': 'Ready'},
                                      'build_pylon 10': {'is': 'Ready'},
                                      'build_pylon 11': {'is': 'Ready'},
                                      'build_pylon 12': {'is': 'Ready'},
                                      'build_pylon 13': {'is': 'Ready'},
                                      'build_pylon 14': {'is': 'Ready'},
                                      'build_pylon 15': {'is': 'Ready'},
                                      'build_pylon 16': {'is': 'Ready'},
                                      'build_pylon 17': {'is': 'Ready'},
                                      'build_pylon 18': {'is': 'Ready'},
                                      'build_pylon 19': {'is': 'Ready'},
                                      'build_pylon 20': {'is': 'Ready'},
                                      'built pylon 1': {'is': 'Ready'},
                                      'built pylon 2': {'is': 'Ready'},
                                      'built pylon 3': {'is': 'Ready'},
                                      'built pylon 4': {'is': 'Ready'},
                                      'built pylon 5': {'is': 'Ready'},
                                      'built pylon 6': {'is': 'Ready'},
                                      'built pylon 7': {'is': 'Ready'},
                                      'built pylon 8': {'is': 'Ready'},
                                      'built pylon 9': {'is': 'Ready'},
                                      'built pylon 10': {'is': 'Ready'},
                                      'built pylon 11': {'is': 'Ready'},
                                      'built pylon 12': {'is': 'Ready'},
                                      'built pylon 13': {'is': 'Ready'},
                                      'built pylon 14': {'is': 'Ready'},
                                      'built pylon 15': {'is': 'Ready'},
                                      'built pylon 16': {'is': 'Ready'},
                                      'built pylon 17': {'is': 'Ready'},
                                      'built pylon 18': {'is': 'Ready'},
                                      'built pylon 19': {'is': 'Ready'},
                                      'built pylon 20': {'is': 'Ready'},
                                      'check mineral 1': {'is': 'Ready'},
                                      'check mineral 2': {'is': 'Ready'},
                                      'check mineral 3': {'is': 'Ready'},
                                      'check mineral 4': {'is': 'Ready'},
                                      'check mineral 5': {'is': 'Ready'},
                                      'check mineral 6': {'is': 'Ready'},
                                      'check mineral 7': {'is': 'Ready'},
                                      'check mineral 8': {'is': 'Ready'},
                                      'check mineral 9': {'is': 'Ready'},
                                      'check mineral 10': {'is': 'Ready'},
                                      'check mineral 11': {'is': 'Ready'},
                                      'check mineral 12': {'is': 'Ready'},
                                      'check mineral 13': {'is': 'Ready'},
                                      'check mineral 14': {'is': 'Ready'},
                                      'check mineral 15': {'is': 'Ready'},
                                      'check mineral 16': {'is': 'Ready'},
                                      'check mineral 17': {'is': 'Ready'},
                                      'check mineral 18': {'is': 'Ready'},
                                      'check mineral 19': {'is': 'Ready'},
                                      'check mineral 20': {'is': 'Ready'},
                                      }

        """
        self.goal = {'goal': 'I have two Pylon',
                     'trigger': [],
                     'satisfy': [
                         ('type2', 'i', 'have', ['100 minerals'])
                     ],
                     'precedent': [],
                     'require': [
                         {'goal': 'I have pylon 1',
                          'require': [
                              {'goal': 'gather 100 minerals 1',
                               'require': [
                                   ['gather 1', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                   # target: unit
                                   ['gather 2', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                   ['gather 3', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                   ['gather 4', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                   ['check mineral 1', {'target': 'minerals', 'amount': 100}, 'Query'],
                                   # ['check mineral 2', {'target': 'minerals', 'amount': 20}, 'Query'],
                               ]
                               },
                              ['build_pylon 1', {'target': 'point', 'pos_x': 39, 'pos_y': 29}, 'General'],
                          ]
                          },
                         {'goal': 'I have pylon 2',
                          'require': [
                              {'goal': 'gather 100 minerals 2',
                               'require': [
                                   ['gather 5', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                   # target: unit
                                   ['gather 6', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                   ['gather 7', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                   ['gather 8', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                                   ['check mineral 2', {'target': 'minerals', 'amount': 150}, 'Query'],
                               ]
                               },
                              ['build_pylon 2', {'target': 'point', 'pos_x': 39, 'pos_y': 27}, 'General'],
                          ]
                          },

                     ]

                     }

    def set_init_kn(self):
        self.initial_knowledge = {self.goal['goal']: {'is': 'Not Assigned'},
                                  'gather 100 minerals 1': {'is': 'Not Assigned'},
                                  'gather 100 minerals 2': {'is': 'Not Assigned'},
                                  'I have pylon 1': {'is': 'Not Assigned'},
                                  'I have pylon 2': {'is': 'Not Assigned'},
                                  'gather 1': {'is': 'Ready'},
                                  'gather 2': {'is': 'Ready'},
                                  'gather 3': {'is': 'Ready'},
                                  'gather 4': {'is': 'Ready'},
                                  'gather 5': {'is': 'Ready'},
                                  'gather 6': {'is': 'Ready'},
                                  'gather 7': {'is': 'Ready'},
                                  'gather 8': {'is': 'Ready'},
                                  'build_pylon 1': {'is': 'Ready'},
                                  'build_pylon 2': {'is': 'Ready'},
                                  'check mineral 1': {'is': 'Ready'},
                                  'check mineral 2': {'is': 'Ready'},
                                  }
    """

    '''
        The Main Part of Core.
    '''

    def run(self):

        self._start_new_game()
        self._start_proxy()
        self.set_goal()
        self.set_init_kn()

        while True:

            logger.info('%s is ticking' % ('core'))

            minerals, food_cap, food_used, num_pylon = self._req_playerdata()

            # Tell game data to everyone.
            data = {}
            data['minerals'] = {}
            data['pylons'] = {}
            data['pylons']['built'] = str(num_pylon)
            data['minerals']['gathered'] = str(minerals)
            data['minerals']['are'] = list(self.dict_mineral.items())
            data['food'] = {}
            data['food']['has'] = str(food_cap)
            data['food']['used'] = str(food_used)
            # data['probes']={'are':self.dict_probe.items()}
            # data['nexus']={'are':self.dict_nexus.items()}

            json_string = json.dumps(data, cls=PythonObjectEncoder)
            self.broadcast(json_string)

            if minerals >= 5000:  # End option <- Should be delete

                # Should be delete! Cause when the goal is achieved, the agent destroy itself.
                for probe in self.threads_agents:
                    probe.destroy()

                self._leave_game()
                self._quit_sc2()
                break

            # Get Requests from agents.

            for i in range(len(self.threads_agents)):
                req = self.perceive_request()
                if req.startswith('core'):
                    req = req[5:]
                    req = json_format.Parse(req, sc_pb.RequestAction())
                    # json.loads(req)
                    self.comm_sc2.send(action=req)

            # TODO : Randomly Occured Error...
            # self._train_probe(list(self.dict_nexus.keys())[0])

            time.sleep(0.5)

        print("Test Complete")
        self.comm_agents.context.term()


if __name__ == '__main__':
    core = Core()
    logger.info('Core initializing...')
    core.init()
    logger.info('Core running...')
    core.run()
    logger.info('Core deinitializing...')
    core.deinit()
    logger.info('Core terminated.')