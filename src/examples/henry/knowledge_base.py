"""
    Knowledge base class
    This stores statements formed from observations/communications
    Atomic forms are
        type1: noun, noun/adjective                e.g., (apple, red)
        type2: noun, verb [objective]              e.g., (probe, gather, the mineral)
        type3: verb, (noun/verb noun/adjective)    e.g., (attack, (target, hurt)), (attack, (drain, my_energy))
"""

class Knowledge(object):
    def __init__(self, knowledge_type, *args):
        if knowledge_type == 'type1':
            assert len(args) == 2
            self.type = knowledge_type
            self.n = args[0]
            self.na = args[1]
        elif knowledge_type == 'type2':
            assert len(args) == 3
            self.type = knowledge_type
            self.n = args[0]
            self.v = args[1]
            self.o = args[2]
        elif knowledge_type == 'type3':
            pass
        else:
            # unknown type
            pass
