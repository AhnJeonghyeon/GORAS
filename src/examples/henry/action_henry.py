"""
    Action class
    This lists all possible actions of a unit
    Actions can be performed under conditions and events
"""


'''
    Returns basic acitons of an agent
'''
def get_basic_actions():
    actions = []
    finding = """print(\'Henry!!! Henry!!! Henry!!!!!!!\')"""
    infinite_loop = """print(\'LIKEY!!! LIKEY!!!!!\')\nwhile True: \n continue""" 
    coding = """print(words, \'is hard working\')"""
    doing = """print(\'Henry is doing\',words)"""

    actions.append(Action(action_name='find', actual_code=finding, require={'words': 'string'}))
    actions.append(Action(action_name='watch', actual_code=infinite_loop, require={'words': 'string'}))
    actions.append(Action(action_name='coding', actual_code=coding, require={'words': 'string'}))
    actions.append(Action(action_name='do', actual_code=doing, require={'words': 'string'}))
    return actions


class Action(object):
    def __init__(self, action_name, actual_code, require={}, sc_action_id=9999):
        self.__name__ = action_name
        self.code = actual_code
        self.sc2_id = sc_action_id
        self.require = require

    def __repr__(self):
        return 'Action %s with id %d requires %s ' % (self.__name__, self.sc2_id, self.require)

    def set_arguments(self, args):
        self.require.update(args)

    def can_perform(self, task_name):
        if task_name == self.__name__:
            return True
        else:
            return False

    def perform(self):
        # Pass arguments
        for param in self.require:
            param_str = '%s=\'%s\'' % (param, self.require[param])
            exec(param_str)

        # Perform the action in real
        exec(self.code)
