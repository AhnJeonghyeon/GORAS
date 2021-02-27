#!/usr/bin/python3

"""
    Class Agent
    This contains core components,
        - knowledge: manages statements (e.g., I am at (x, y))
        - action: lists possible actions
        - goal: explains details of goals
        - reasoning: the brain
        - comm: ability to communicate with others
"""
import sys
import time
import logging
import threading
import json

sys.path.append('../')
from units import units
from utils.communicator import Communicator

from action import Action, get_basic_actions
from knowledge_base import Knowledge
from goal import Goal, create_goal_set

from utils.jsonencoder import PythonObjectEncoder, as_python_object

FORMAT = '%(asctime)s %(module)s %(levelname)s %(lineno)d %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


class MentalState(object):
    '''
        State machine
            Idle: Agent performs nothing, no action needed

    '''

    def __init__(self):
        self.state = 'idle'

    def change_state(self):
        self.state = 'working'


class Agent(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.discrete_time_step = 0.5  # sec
        self.alive = False
        self.state = MentalState()

        self.actions = get_basic_actions()
        self.knowledge = Knowledge()
        self.goals = []
        self.messages = []

    def _load_knowledge(self, knowledge):
        for key, value in knowledge.items():
            self.knowledge[key] = value
            # self.tuple_to_knowledge(k)
            # self.knowledge.append(k)

    def _load_goals(self, goals):
        self.goals = goals

    def spawn(self, spawn_id, unit_id, initial_knowledge={}, initial_goals=[]):
        logging.info(str(spawn_id) + ' is being spawned...')

        assert unit_id in units

        # Identifier for the unit
        self.spawn_id = spawn_id
        print("{} is spawned".format(spawn_id))

        # Load basic characteristics of the unit
        self.load_unit(units[unit_id])

        # Set initial statements in knowledge
        self._load_knowledge(initial_knowledge)
        #print(self.knowledge)

        # Store initial goals
        self._load_goals(initial_goals)

        # Give it a life
        self.alive = True

        logging.info(str(spawn_id) + ' has spawned.')

    def load_unit(self, spec):
        self.id = spec['id']
        self.name = spec['name']

        for action in spec['actions']:
            assert 'id' in action
            assert 'name' in action
            assert 'require' in action

            self.actions.append(
                Action(
                    action_name=action['name'],
                    actual_code='',
                    require=action['require'],
                    sc_action_id=action['id']))

    '''
        Communication to simulator
    '''

    def init_comm_env(self):
        pass

    def deinit_comm_env(self):
        pass

    '''
        Communication to other agents
    '''

    def init_comm_agents(self):
        # self.comm_agents = Communicator(self.spawn_id)
        self.comm_agents = Communicator()

    def deinit_comm_agents(self):
        # It may need to send 'good bye' to others
        self.comm_agents.close()

    '''
        Destroy myself
        Assumption : When the agent check that the goal is achieved, destory itself.
    '''

    def destroy(self):
        # Need to broadcast "I am destroying"
        msg = "{} destroy".format(self.spawn_id)
        self.comm_agents.send(msg)
        # Close communications
        self.deinit_comm_env()
        self.deinit_comm_agents()
        self.alive = False

        self.join()

    '''
        Sense information from its surroundings and other agents
    '''

    def perceive(self):
        # Perceive from the environment (i.e., SC2)

        # Perceive from other agents
        message = self.comm_agents.read()
        if message.startswith('broadcasting'):
            message = message[13:]
            self.knowledge.update(json.loads(message, object_hook=as_python_object))

    """
        Change msg(str) to Knowledge
    """

    def msg_to_knowledge(self, message):
        splited_msg = message.split()
        tuple_msg = tuple(splited_msg)
        if splited_msg is not None:
            if len(splited_msg) == 2:
                self.knowledge.append(Knowledge('type1', tuple_msg[0], [tuple_msg[1]]))
            elif len(splited_msg) == 3:
                self.knowledge.append(Knowledge('type2', tuple_msg[0], tuple_msg[1], [tuple_msg[2]]))
            else:
                pass
        else:
            pass

    """
        Change tuple to Knowledge
    """

    def tuple_to_knowledge(self, tuple_msg):
        if tuple_msg is not None:
            if len(tuple_msg) == 3:
                self.knowledge.append(Knowledge(tuple_msg[0], tuple_msg[1], tuple_msg[2]))
            elif len(tuple_msg) == 4:
                self.knowledge.append(Knowledge(tuple_msg[0], tuple_msg[1], tuple_msg[2], tuple_msg[3]))
            else:
                pass
        else:
            pass

    '''
        Information / actions going to simulator
    '''

    def act(self, action, task):
        self.state.change_state()

        # Update task state
        self.knowledge[task.__name__].update({'is': 'Active'})

        logger.info('%s %s is performing %s' % (self.name, self.spawn_id, action))
        if action.__name__ == 'move':
            req = action.perform(self.spawn_id)
            self.comm_agents.send(req, who='core')
        elif action.__name__ == 'gather':
            req = action.perform(self.spawn_id)
            self.comm_agents.send(req, who='core')
        elif action.__name__ == 'build_pylon':
            req = action.perform(self.spawn_id)
            self.comm_agents.send(req, who='core')
            # do gather after build_pylon
            # time.sleep(self.discrete_time_step)
            # for act in self.actions:
            #     if act.__name__ == 'gather':
            #         req = act.perform(self.spawn_id)

        elif action.__name__ == 'check':
            self.mineral_query(task.__name__, task.arguments['target'], task.arguments['amount'])
            # action.perform_query()
            return False
        elif action.__name__ == 'built':
            self.built_query(task.__name__, task.arguments['target'], task.arguments['built'])
            return False
        else:
            pass
            #print('act function --> else ERROR!!!!!!')
        return True

    def mineral_query(self, task_name, target, amount):
        # find knowledgebase

        if target in self.knowledge:
            current_amount = self.knowledge[target]['gathered']
            if int(current_amount) >= int(amount):
                #print("성취됨!!!!!!!!!!!!!")
                # knowledgebase update
                self.knowledge[task_name].update({'is': 'Done'})
                self.state.__init__()

    def built_query(self, task_name, target, built):
        if target in self.knowledge:
            current_built = self.knowledge[target]['built']
            if int(current_built) >= int(built):
                #print("성취됨!!!!!!!!!!!!")
                self.knowledge[task_name].update({'is': 'Done'})
                self.state.__init__()

    '''
        Delivering information to other agents
    '''

    def tell(self, statement):
        #logger.info('%d is telling "%s" to the agents' % (self.spawn_id, statement))
        # msg = str(self.spawn_id) + " is " + self.state.state
        #print(">> {} is telling : {}".format(self.spawn_id, statement))
        self.comm_agents.send(statement, broadcast=True)

    '''
        Query to other agents
    '''

    def ask(self, query, wait_timeout=3):
        pass

    '''
        Returns an action that can perform the task
    '''

    def _has_action_for_task(self, task):
        for action in self.actions:
            if action.can_perform(task.__name__):
                action.set_arguments(task.arguments)
                return action
        return None

    """
           Check the goal tree recursively and update KB if it is active.
       """

    def check_goal_active(self, goal):
        if goal is not None:
            if goal.can_be_active():
                print('뭐 좀 찍어볼까?????')
                self.knowledge[goal.name].update({'is': 'active'})
                print(goal.name)
                print(self.knowledge[goal.name]['is'])
            for subgoal in goal.subgoals:
                if subgoal.can_be_active():
                    print('뭐 좀 찍어볼까?????')
                    self.knowledge[subgoal.name].update({'is': 'active'})
                    print(subgoal.name)
                    print(self.knowledge[subgoal.name]['is'])
                    self.check_goal_active(subgoal)
        return None

    """
        Check the goal tree recursively and update KB if it is achieved.
    """

    def check_goal_achieved(self, goal):
        if goal is not None:
            if goal.can_be_achieved():
                #print('뭐 좀 찍어볼까?????')
                self.knowledge[goal.name].update({'is': 'achieved'})
                #print(goal.name)
                #print(self.knowledge[goal.name]['is'])
            for subgoal in goal.subgoals:
                if subgoal.can_be_achieved():
                    #print('뭐 좀 찍어볼까?????')
                    self.knowledge[subgoal.name].update({'is': 'achieved'})
                    #print(subgoal.name)
                    #print(self.knowledge[subgoal.name]['is'])
                    self.check_goal_achieved(subgoal)
        return None

    '''
        Returns available actions based on the desires in the current situation
    '''

    def next_action(self, current_goal, current_knowledge, mentalstate):
        list_actions = []
        #print("####NEXT_ACTION: CURRENT GOAL's length: %s" % (len(current_goal)))
        if len(current_goal) == 0:
            # TODO: is an action always triggered by a goal?
            return None, None

        # TODO: all the goals may need to be examined
        for goal in current_goal:
            # Method name is dirty
            leaf_goal, tasks = goal.get_available_goal_and_tasks()


            # When the Query task is Done, the agent's mentalstate is Idle
            for task in tasks:
                if task.type == 'Query' and self.knowledge[task.__name__]['is'] == 'Done':
                    self.state.__init__()


            if len(tasks) != 0:
                if leaf_goal.goal_state != 'achieved':
                    leaf_goal.goal_state = 'assigned'
                    self.knowledge[leaf_goal.name].update({'is': 'assigned'})
            for task in tasks:

                if mentalstate == 'idle':
                    # ping
                    if task.type == 'General':
                        if task.state == 'Ready':
                            task.state = 'Ping'
                            pinglist = set()
                            pinglist.add(self.spawn_id)
                            self.knowledge[task.__name__].update({'is': 'Ping'})
                            self.knowledge[task.__name__].update({'ping': pinglist})

                            '''
                            #TODO - SangUk will do!
                            self.knowledge[task.__name__].update({'is' : ('Ping', self.spawn_id)})
                            '''
                            break

                        elif task.state == 'Ping':
                            pinglist = self.knowledge[task.__name__]['ping']

                            amImin = True
                            for ping in pinglist:
                                if int(self.spawn_id) > int(ping):
                                    amImin = False
                                    break

                            if amImin:
                                if int(self.spawn_id) not in pinglist:
                                    pinglist.add(self.spawn_id)
                                self.knowledge[task.__name__].update({'ping': pinglist})

                                action = self._has_action_for_task(task)
                                if action is not None:
                                    list_actions.append((action, task))
                                    break
                            else:
                                continue
                                #return None, None

                        elif task.state == 'Active':
                            return None, None

                elif mentalstate == 'working':
                    if task.type == 'Query' and (task.state == 'Ready' or task.state == 'Active'):
                        # Check whether query task is done
                        action = self._has_action_for_task(task)
                        if action is not None:
                            list_actions.append((action, task))

        # Select actions from the list of actions in terms of the current
        if len(list_actions) == 0:
            return None, None

        return_action = list_actions[0]
        # Return the most beneficial action from the selected actions
        return return_action

    def update_goal_tree(self, knowledge, goal):

        if goal.name in knowledge:
            if goal.goal_state != 'achieved':
                goal.goal_state = knowledge[goal.name]['is']

        # check subgoals
        for subgoal in goal.subgoals:
            self.update_goal_tree(knowledge, subgoal)

        # check task
        for task in goal.tasks:
            if task.__name__ in knowledge:
                #print("!!", self.spawn_id, task.__name__, task.state, "-->", knowledge[task.__name__]['is'])
                if knowledge[task.__name__]['is'] == 'Done':
                    knowledge[task.__name__]['ping'] = []
                task.state = knowledge[task.__name__]['is']

        return True

    '''
        Main logic runs here (i.e., reasoning)
    '''

    def run(self):
        # Initialize communications
        self.init_comm_agents()
        self.init_comm_env()

        while self.alive:
            # For debugging
            logger.info('%s %d is ticking' % (self.name, self.spawn_id))
            #print()

            #for k in self.knowledge:
            #    print(k)

            # Check if something to answer
            # query = self.check_being_asked():
            # if query:
            #     self.answer(query)

            # Perceive environment
            self.perceive()
            self.perceive()
            self.perceive()
            self.perceive()
            self.perceive()

            # check task state and change the agent's mentalstate


            # check knowledge and update the goal tree
            """
            tasks = []
            for g in self.goals:
                tasks = g.get_available_tasks()

            for k in self.knowledge:
                if k.type == 'type1':
                    for goal in self.goals:
                        if k.n == goal.name:
                            goal.goal_state = k.na
                    for task in tasks:
                        if k.n == task.__name__:
                            task.state = k.na
            """

            # check knowledge and update the goal tree
            for goal in self.goals:
                self.update_goal_tree(self.knowledge, goal)

            """
            #check every goal whether now achieved.
            for goal in self.goals:
                if goal.can_be_achieved():
                    print('뭐 좀 찍어볼까????')
                    self.knowledge[goal.name].update({'is' : 'achieved'})
                    print(goal.name)
                    print(self.knowledge[goal.name]['is'])
                for subgoal in goal.subgoals:  #update subgoal's state in KB
                    if subgoal.can_be_achieved(): #check the goal state
                        print('뭐 좀 찍어볼까?????')
                        self.knowledge[subgoal.name].update({'is' : 'achieved'})
                        print(subgoal.name)
                        print(self.knowledge[subgoal.name]['is'])
            """
            # check every goal whether now achieved.
            for goal in self.goals:
                self.check_goal_achieved(goal)

            # # check every goal whether now active.
            # for goal in self.goals:
            #     self.check_goal_active(goal)

            # Reason next action
            selected_action, selected_task = self.next_action(self.goals, self.knowledge, self.state.state)
            #print(self.spawn_id, "다음은!!! ", selected_action, selected_task)
            # Perform the action
            if selected_action is not None:
                if not self.act(selected_action, selected_task):
                    # Query task come here!
                    pass
                else:
                    # General task come here!
                    selected_task.state = 'Done'
                    # if selected_task.__name__.startswith('built'):
                    #     for act in self.actions:
                    #         if act.__name__ == 'gather':
                    #             req = act.perform(self.spawn_id)
                    #             self.comm_agents.send(req, who='core')
                    self.knowledge[selected_task.__name__]['ping'] = []
                    self.knowledge[selected_task.__name__].update({'is': 'Done'})
                    # Have to change agent's state to idle after finishing the task
                    # self.state.__init__()

            else:
                #print('다 됐다!!!!!!!!!!!!!!!!!!!')
                if self.goals[0].goal_state == 'achieved':
                    #print('여기 들어옴?? ???????')
                    """
                    for act in self.actions:
                        if act.__name__ == 'move':
                            req=act.perform(self.spawn_id)
                            self.comm_agents.send(req,who='core')
                    """
                    # self.destroy()
                    # break
                pass

            # TODO for Tony : Please Broadcast knowledge...
            self.tell(json.dumps(self.knowledge, cls=PythonObjectEncoder))

            time.sleep(self.discrete_time_step)


'''
    For testing
'''
if __name__ == '__main__':
    """
    goal = {'goal': 'introduce myself',
            'require': [
                ['say', {'words': 'hello'}],
                {'goal': 'say hello',
                 'require': [
                     ['say', {'words': 'myname'}],
                     ['say', {'words': 'hehe'}],
                     {'goal': 'say hajime',
                      'require': [
                          ['say', {'words': 'hajime'}]
                      ]}
                 ]
                 }
            ]
            }

    goal = {'goal': 'gather 100 minerals',
            'trigger': [],
            'satisfy': [
                ('type2', 'i', 'have', ['100 minerals'])
            ],
            'precedent': [],
            'require': [
                ['move', {'target': 'point', 'pos_x': 10, 'pos_y': 10}],
                ['gather', {'target': 'unit', 'unit_tag': 'list_mineral_tag[0]'}],
            ]
            }

    probe = Agent()
    probe.spawn(1,84,
        initial_knowledge=[
            ('type1', 'my_name', ['probe']),
            ('type2', 'i', 'say', ['my_name']),
            ],
        initial_goals=[create_goal_set(goal)]
        )
    print('Agent is running...')
    try:
        probe.run()
    except KeyboardInterrupt:
        pass
    probe.destroy()
    print('The agent is terminated.')
    """