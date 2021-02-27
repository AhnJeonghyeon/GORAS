self.goal = {'goal': 'I have GG Pylon',
             'trigger': [],
             'satisfy': [
                 ('type2', 'i', 'have', ['100 minerals'])
             ],
             'precedent': [],
             'require': [
                 {'goal': 'I have pylon 1',
                  'require': [
                      ['gather 1', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                      # target: unit
                      ['gather 2', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                      ['gather 3', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                      ['gather 4', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                      ['build_pylon 1', {'target': 'point', 'pos_x': 39, 'pos_y': 29}, 'General'],
                      ['check mineral 1', {'target': 'minerals', 'amount': 100}, 'Query'],
                      ['built pylon 1', {'target': 'pylons', 'built': 2}, 'Query'],
                      {'goal': 'I have pylon 2',
                       'require': [
                           ['gather 5', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                           # target: unit
                           ['gather 6', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                           ['gather 7', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                           ['gather 8', {'target': 'unit', 'unit_tag': list_minerals[0]}, 'General'],
                           ['build_pylon 2', {'target': 'point', 'pos_x': 39, 'pos_y': 27}, 'General'],
                           ['check mineral 2', {'target': 'minerals', 'amount': 150}, 'Query'],
                           ['built pylon 2', {'target': 'pylons', 'built': 1}, 'Query'],
                       ]
                       },
                  ],
                  },
             ]
             }


def set_init_kn(self):
    self.initial_knowledge = {self.goal['goal']: {'is': 'Not Assigned'},
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
                              'built pylon 1': {'is': 'Ready'},
                              'built pylon 2': {'is': 'Ready'},
                              }




