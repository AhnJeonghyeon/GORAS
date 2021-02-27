"""
    Declaration of SC2 units
"""

import os
import yaml

dir_name = os.path.dirname(__file__)
files = os.listdir(dir_name)
unit_files = [os.path.join(dir_name, unit_file) for unit_file in files if '.unit' in unit_file]

def load_units(list_units):
    units = {}
    for unit in list_units:
        with open(unit, 'r') as file:
            spec_str = file.read()
            contents = yaml.load(spec_str)
            contents = contents[0]
            
            assert 'id' in contents
            units[contents['id']] = contents

    return units


units = load_units(unit_files)