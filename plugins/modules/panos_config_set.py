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
module: panos_config_set

short_description: Retrieve the running configuration in set command format of a PAN firewall.

description:
    - Retrieve the running configuration in set command format of a PAN firewall.
    
requirements:
    - netmiko can be obtained from PyPi (https://pypi.org/project/netmiko)

options:
    ip_address:
        description:
            - IP address or hostname of PAN-OS device.
        required: true
    username:
        description:
            - Username for authentication for PAN-OS device.
        default: 'admin'
    password:
        description:
            - Password for authentication for PAN-OS device.
    save:
        description:
            - Save configuration to file.
        type: bool
        default: False

author:
    - Matthew Spera (@mattspera)
'''

EXAMPLES = '''
'''

RETURN = '''
config_set:
    description: Running config in set command format.
message:
    description: The output message generated.
'''

import json
from datetime import datetime

from ansible.module_utils.basic import AnsibleModule

try:
    from netmiko import ConnectHandler
    from netmiko import NetMikoTimeoutException, NetMikoAuthenticationException

    HAS_LIB = True
except ImportError:
    HAS_LIB = False

def run_module():
    module_args = dict(
        ip_address=dict(required=True),
        username=dict(default='admin'),
        password=dict(no_log=True),
        save=dict(type='bool', default=False)
    )

    result = dict(
        changed=False,
        config_set='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        #support_check_mode=False
    )

    if not HAS_LIB:
        module.fail_json(msg='Missing required libraries: netmiko')

    auth = {
        'device_type' : 'paloalto_panos',
        'ip' : module.params['ip_address'],
        'username' : module.params['username'],
        'password' : module.params['password']    
    }

    try:
        conn = ConnectHandler(**auth)
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        module.fail_json(msg=e)

    conn.send_command('set cli config-output-format set')
    conn.config_mode()
    running_config_set = conn.send_command_timing('show', delay_factor=10)
    conn.exit_config_mode()

    if module.params['save']:
        dt = datetime.now().strftime(r'%y%m%d_%H%M')
        file_name = 'config_set_{}_{}.txt'.format(module.params['ip_address'], dt)
        with open(file_name, 'wb') as file_obj:
            file_obj.write(running_config_set.encode('utf-8'))
        result['config_set'] = file_name
    else:
        running_config_set_list = running_config_set.splitlines()
        result['config_set'] = json.dumps(running_config_set_list)

    result['message'] = 'Done'
    result['changed'] = True

    conn.disconnect()

    module.exit_json(**result)

def main():
    run_module()

if __name__ == "__main__":
    main()