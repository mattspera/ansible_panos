from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import ast

from ansible.errors import AnsibleError, AnsibleFilterError

def dev_dict_parser(a, *args, **kw):
    '''Custom parser which loops through API 'show dg/template' output,
    finds dg/template instances that contain a single device (in dict)
    and converts that dict to a list containing that dict. This allows
    Ansible to loop through dg/template inhabiting devices whether
    there be a single or multiple devices within dg/template'''
    # if string, convert to Python literal
    if isinstance(a, str):
        a = ast.literal_eval(a)

    if not isinstance(a, list):
        raise AnsibleFilterError('Object not a list.')

    for item in a:
        if 'devices' in item:
            if isinstance(item['devices']['entry'], dict):
                item['devices']['entry'] = [item['devices']['entry']]

    return json.dumps(a)

class FilterModule(object):
    ''' PAN parser filters '''

    def filters(self):
        return {
            "dev_dict_parser": dev_dict_parser
        }