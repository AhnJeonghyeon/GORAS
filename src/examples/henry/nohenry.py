#!/usr/bin/python3

"""
    Dummy Agent to test single agent using communicator.py
    This dummy communicates with the agent,
        - receive a message from the agent and check the agent's task
        - send a message(result) to the agent after checking the agent's message

    The agents need to change their goal state to Achieved/Failed state
    when the task is completed.

"""

import sys
import time
import logging
sys.path.append('../../')
from utils.communicator import Communicator
from agent_henry import *


"""
    For testing
"""

def find_Happy_Henry(goals):
    for goal in goals:
        if goal.name != 'Happy Henry':
            find_Happy_Henry(goal.subgoals)
        else:
            for task in goal.tasks:
                if task.__name__=='watch':
                    task.state='Done'


if __name__ == '__main__':

    goal = {'goal': 'Make Henry Kimoti',
            'require': [
                ['do', {'words': 'SKDJ'}],
                {'goal': 'project finished',
                    'require': [
                        ['coding', {'words': 'Persona'}],
                        ['coding', {'words': 'Emma'}],
                        {'goal': 'Happy Henry',
                            'require': [
                                ['watch', {'words': 'Twice MV'}],
                                ['find', {'words': 'Henry'}]
                                ]}
                            ]
                    }
                ]
            }

    nohenry = Agent()
    nohenry.spawn(1,84,
        initial_knowledge=[
                ('type1', 'my_name', ['probe']),
                ('type2', 'i', 'say', ['my_name']),
                ],
            initial_goals=[create_goal_set(goal)]
            )
    print('Let\'s make Henry kimoti...')
    try:
        find_Happy_Henry(nohenry.goals)
        nohenry.run()
    except KeyboardInterrupt:
        pass
    nohenry.destroy()
    print('We are Emma and Persona!!Bye...')
