"""
    Goal class
    This describes and stores (sub-)goals and their relationships
    Types,
        Conjunctive: achieving both sub goal A and B can attain the parent goal
        Disjunctive: achieving more than one of the sub goals satisfies attainment of the parent goal

    States of a goal
-----------------------------------------------------
STATE        | TRIGGER                  | NEXT_STATE
=====================================================
NOT_ASSIGNED | more than one agent      | ASSIGNED
             | is assigned              |
-----------------------------------------------------
ASSIGNED     | start conditions are met | ACTIVE
-----------------------------------------------------
ACTIVE       | end conditions are met   | ACHIEVED
             | ????                     | FAILED
-----------------------------------------------------


    Task class

    Types,
        General: General task except Query tasks
        Query: Find required information in knowledge


    States of a task
-----------------------------------------------------
STATE        | Description              | NEXT_STATE
=====================================================
READY        | General task    --->     | PING
             | Query task      --->     | ACTIVE
-----------------------------------------------------
Ping         | The agent who has higher | ACTIVE
             | priority takes the task  |
-----------------------------------------------------
ACTIVE       | Task Succeeded           | DONE
             | ????                     | FAILED
-----------------------------------------------------


"""
GOAL_STATE_NOT_ASSIGNED = 'not_assigned'
GOAL_STATE_ASSIGNED = 'assigned'
GOAL_STATE_ACTIVE = 'active'
GOAL_STATE_ACHIEVED = 'achieved'
GOAL_STATE_FAILED = 'failed'

'''
    Create a goal from a given description
    Format:
        <<goal>>::<<goal_name>>
                  <<require>>
                  <<trigger>>
                  <<satisfy>>
                  <<precedent>>
        <<require>>::<<task>>
                     <<goal>>
        <<trigger>>::<<knowledge>>
        <<satisfy>>::<<knowledge>>
    example: {
        'goal': 'say hello',
        'trigger': [],
        'satisfies':
        'require': [['say', 'hello']]}
'''
def create_goal_set(description_dict):
    assert 'goal' in description_dict

    g = Goal(description_dict['goal'])
    if 'trigger' in description_dict:
        g.set_triggers(description_dict['trigger'])
    if 'satisfies' in description_dict:
        g.set_satisfies(description_dict['satisfies'])
    if 'require' in description_dict:
        dependents = description_dict['require']
        for dependent in dependents:
            if isinstance(dependent, list):  # Task
                g.set_required_task(Task(dependent[0], dependent[1], dependent[2]))
            elif isinstance(dependent, dict): # Goal
                g.set_required_goal(create_goal_set(dependent))
            else:
                pass
    else:
        # A goal with no tasks that satisfy it
        return None

    return g


class Goal(object):
    def __init__(self, goal_name=''):
        self.name = goal_name
        self.tasks = []
        self.subgoals = []
        self.triggers = []
        self.satisfies = []
        self.goal_state = GOAL_STATE_NOT_ASSIGNED
        self.working_worker = []
        self.required_worker = 1


    def __repr__(self):
        return '%s with %s tasks and %s dependents' % (self.name, self.tasks, self.subgoals)
    """
    def _get_leaf_tasks(self):
        if len(self.subgoals) == 0:
            return self.tasks
        else:
            for subgoal in self.subgoals:
                if subgoal.goal_state != GOAL_STATE_ACHIEVED and subgoal.goal_state != GOAL_STATE_FAILED:
                    return subgoal._get_leaf_tasks()
            return self.tasks
    """

    def _get_leaf_goal_and_tasks(self):
        if len(self.subgoals) == 0:
            return self, self.tasks
        else:
            for subgoal in self.subgoals:
                if subgoal.goal_state != GOAL_STATE_ACHIEVED and subgoal.goal_state != GOAL_STATE_FAILED and subgoal.goal_state != GOAL_STATE_ACTIVE:
                    return subgoal._get_leaf_goal_and_tasks()
            return self, self.tasks

            # check the goal is active

    def can_be_active(self):

        # check subgoals
        for subgoal in self.subgoals:
            if not subgoal.can_be_active():
                # print('>>', self.name, 'CAN NOT be active yet >>', self.goal_state)
                return False

        is_active = True
        for task in self.tasks:
            if task.state == 'Ready':
                is_active = False
                break

        if is_active is False:
            return False

        self.goal_state = 'active'
        # print('>>', self.name, 'CAN be active now >>', self.goal_state)
        return True

    # receive the agent's knowledge to check end condition
    def can_be_achieved(self):

        #check subgoals
        for subgoal in self.subgoals:
            if not subgoal.can_be_achieved():
                #print('>>', self.name, 'CAN NOT be achieved yet >>', self.goal_state)
                return False

        #check task
        for task in self.tasks:
            if task.state != 'Done':
                #print('>>', self.name, 'CAN NOT be achieved yet >>', self.goal_state)
                return False

        self.goal_state = 'achieved'
        #print('>>', self.name, 'CAN be achieved now >>', self.goal_state)
        return True


    def set_goal_name(self, goal_name):
        self.name = goal_name

    def set_required_task(self, task):
        self.tasks.append(task)

    def set_required_goal(self, goal):
        self.subgoals.append(goal)

    def set_triggers(self, triggers):
        self.triggers = triggers

    def set_satisfies(self, satisfies):
        self.satisfies = satisfies

    def get_tasks(self):
        return self.tasks
    """
    def get_available_tasks(self):
        tasks = self._get_leaf_tasks()
        return tasks
    """

    def get_available_goal_and_tasks(self):
        leaf_goal, tasks = self._get_leaf_goal_and_tasks()
        return leaf_goal, tasks

    def get_available_tasks(self):
        leaf_goal, tasks = self._get_leaf_goal_and_tasks()
        return tasks

    def get_goal(self):
        if len(self.subgoals) > 0:
            return self.subgoals[0]
        else:
            return None

class Task(object):
    def __init__(self, task_name='', arguments={}, type=''):
        self.__name__ = task_name
        self.arguments = arguments
        self.arguments['task_name'] = task_name
        self.state = 'Ready'
        self.type = type

    def __repr__(self):
        return '[Task \'%s\' with \'%s\']' % (self.__name__, self.arguments)

    def set_arguments(self, arguments):
        self.arguments = arguments
