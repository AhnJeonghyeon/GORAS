#!/usr/bin/python3
#-*- coding: utf-8 -*- 

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
sys.path.append('../')
from units import units
from utils.communicator import Communicator

from action_henry import Action, get_basic_actions
from knowledge_base import Knowledge
from goal import Goal, create_goal_set


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

class Agent(object):
    def __init__(self):
        self.discrete_time_step = 1 # sec
        self.alive = False
        self.state = MentalState()

        self.actions = get_basic_actions()
        self.knowledge = []
        self.goals = []

    def _load_knowledge(self, knowledge):
        for k in knowledge:
            self.knowledge.append(Knowledge(k))

    def _load_goals(self, goals):
        self.goals = goals

    def spawn( self, spawn_id, unit_id, initial_knowledge=[], initial_goals=[]):
        assert unit_id in units

        # Identifier for the unit
        self.spawn_id = spawn_id

        # Load basic characteristics of the unit
        self.load_unit(units[unit_id])

        # Set initial statements in knowledge
        self._load_knowledge(initial_knowledge)

        # Store initial goals
        self._load_goals(initial_goals)

        # Initialize communications
        self.init_comm_env()
        self.init_comm_agents()

        # Give it a life
        self.alive = True

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
        self.comm_agents = Communicator(self.id)

    def deinit_comm_agents(self):
        # It may need to send 'good bye' to others
        self.comm_agents.close()

    '''
        Destroy myself
    '''
    def destroy(self):
        # Close communications
        self.deinit_comm_env()
        self.deinit_comm_agents()
        self.alive = False

    '''
        Sense information from its surroundings and other agents
    '''
    def perceive(self):
        # Perceive from the environment (i.e., SC2)

        # Perceive from other agents
        message = self.comm_agents.read()
        if message:
            # Put the message into knowledge base
            #self.knowledge
            pass

    '''
        Information / actions going to simulator
    '''
    def act(self, action, task):
        self.state.change_state()
        task.state = 'Active'
        logger.info('%s %s is performing %s' % (self.name,self.spawn_id, action) )
        action.set_arguments(task.arguments)
        if action.__name__=='say':
            words = action.require['words']
            self.tell(words, 'dummy')
        elif action.__name__=='block':
            words = action.require['words']
            logger.info('I am finding Henry...')
            action.perform()
        elif action.__name__=='do':
            words = action.require['words']
            logger.info('Sorry.....')
            action.perform()
        elif action.__name__=='coding':
            words = action.require['words']
            logger.info('Coding at KSQ')
            action.perform()
        elif action.__name__=='find':
            words = action.require['words']
            logger.info('Where is Henry..?')
            action.perform()
        elif action.__name__=='watch':
            words = action.require['words']
            logger.info('Wait for 2 minutes~')
            action.perform()
        else:
            action.perform()
        return True

    '''
        Delivering information to other agents
    '''
    def tell(self, statement, who):
        logger.info('I am telling %s to %s' % (statement, who))
        self.comm_agents.send(who, statement)

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
                return action
        return None

    '''
        Returns available actions based on the desires in the current situation
    '''
    def next_action(self, current_goal, current_knowledge):
        list_actions = []
        if len(current_goal) == 0:
            # TODO: is an action always triggered by a goal?
            return None, None

        # TODO: all the goals may need to be examined
        for goal in current_goal:
            # Method name is dirty
            leaf_goal, tasks = goal.get_available_goal_and_tasks()
            if len(tasks) != 0:
                leaf_goal.goal_state = 'assigned'
            for task in tasks:
                if task.state == 'Ready':
                    action = self._has_action_for_task(task)
                    if action is not None:
                        list_actions.append((action, task))

        # g = current_goal.pop() #list에는 더 이상 존재하지 않음...ㅜ.ㅜ pop보다는 그냥 refernce
        # logger.info('current goal is %s' % (g,))
        # #g.goal_state = 'Active'

        # # List up possible actions that can achieve the goal
        # # If the agent knows how to attain the goal
        # for task in g.get_tasks():
        #     action = self._has_action_for_task(task)
        #     if action is not None:
        #         list_actions.append(action)
        #         g.goal_state = 'Assigned'

        # Select actions from the list of actions in terms of the current
        if len(list_actions) == 0:
            return None, None

        return_action = list_actions[0]

        #TODO : which agent should take the 

        # Return the most beneficial action from the selected actions
        return return_action

    '''
        Main logic runs here (i.e., reasoning)
    '''
    def run(self):
        while self.alive:
            # For debugging
            logger.info('%s is ticking' % (self.name,))
            print()
            # Check if something to answer
            # query = self.check_being_asked():
            # if query:
            #     self.answer(query)

            # Perceive environment
            self.perceive()

            for goal in self.goals:
                if goal.name == 'introduce myself':
                    print('>>', goal.name, 'is', goal.goal_state)

            #check every goal whether now achieved.
            for goal in self.goals:
                print('>> Start checking goal tree... root goal is', goal.name)
                goal.can_be_achieved()
            
            if self.state.state == 'working':
                continue

            # Reason next action
            selected_action, selected_task = self.next_action(self.goals, self.knowledge)

            # Perform the action
            if selected_action is not None:
                #if : check the start condition(assinged? available? ) -> check goal instance in knowledge base
                #selected_goal.goal_state = 'active'
                print('>> Now tring to do %s' % (selected_action)) #Active
                if not self.act(selected_action, selected_task):
                    # Action failed, put the goal back to the queue
                    selected_task.state = 'failed' #다음 상태를 고를 그냥 쉬어가는 state라고 생각
                    #self.goals.append(selected_goal) 일단은 append하지 말고 그냥 failed로 둡시다..... available한 goal로 그냥 두기
                else:#제일 위로가야한다고 생각/ 주변환경을 물어보고 end condition을 만족했을 때, goal 중 완성된 것이 있나 확인 한 후 achieve로 바꿔줌
                    #act하고 다시 run할 때 생각
                    #TODO : selected_goal should be leaf goal that act selected_action...?
                    selected_task.state = 'Done'
                    print('>>', selected_task.__name__, 'is Done')

            else:
                break
            # May need to tell others the action that is about to be performed
            # self.tell('%d performs %s' % (self.id, action))
            # Or
            # May tell others the action has performed

            # Sleep a while to prevent meaningless burst looping
            self.state.__init__()
            time.sleep(self.discrete_time_step)

        # Stopped thinking
        # Means it is dead
        # bye bye

'''
    For testing
'''
if __name__ == '__main__':

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
