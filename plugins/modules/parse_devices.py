#!/usr/bin/python

# Copyright: (c) 2019, Matthew Spera <speramatthew@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: parse_devices

short_description: Custom parser for Palo Alto API.

description:
    - Custom parser for Palo Alto API.

options:
    parse:
        description:
            - Palo Alto API object to parse.
        required: true

author:
    - Matthew Spera (@mattspera)
'''

EXAMPLES = '''
'''

RETURN = '''
'''

import json
import ast

from ansible.module_utils.basic import AnsibleModule

def main():
    module_args = dict (
        parse=dict(required=True)
    )

    result = dict(
        changed=False,
        output='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args
    )

    if isinstance(module.params['parse'], str):
        module.params['parse'] = ast.literal_eval(module.params['parse'])

    for item in module.params['parse']:
        if 'devices' in item:
            if isinstance(item['devices']['entry'], dict):
                item['devices']['entry'] = [item['devices']['entry']]

    result['message'] = 'Done'
    result['output'] = json.dumps(module.params['parse'])

    module.exit_json(**result)

if __name__ == "__main__":
    main()