#!/usr/bin/python

# Copyright: (c) 2018, Matthew Spera <speramatthew@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: panos_ping

short_description: Ping specific host from a PAN FW.

description:
    - Ping specific host from a PAN FW.
    
requirements:
    - netmiko can be obtained from PyPi (https://pypi.org/project/netmiko)
    - ipaddress can be obtained from PyPi (https://pypi.org/project/ipaddress)

options:
    ip_address:
        description:
            - IP address of hostname of the PAN-OS device.
        required: true
    username:
        description:
            - Username for authentication to the PAN-OS device.
        default: 'admin'
    password:
        description:
            - Password for authentication to the PAN-OS device.
    host:
        description:
            - Hostname or IP address of remote host.
        required: true
    source:
        description:
            - Source address of echo request.
    count:
        description:
            - Number of requests to send (packets).
        type: 'int'
        default: 2
    size:
        description:
            - Size of request packets (0..65468 bytes).
        type: 'int'
    log:
        description:
            - File path to dump ping test results.
author:
    - Matthew Spera (@mattspera)
'''

EXAMPLES = '''
# Ping specific host
- name: Ping host
  panos_ping:
    ip_address: 192.168.0.250
    username: admin
    password: admin
    host: 10.0.1.10
    source: 10.0.1.1
    
# Ping specific host and dump ping test result to file
- name: Ping host with logging
  panos_ping:
    ip_address: 192.168.0.250
    username: admin
    password: admin
    host: 10.0.1.10
    source: 10.0.1.1
    log: /home/admin/log/ping_test.log
    
# Ping specific host 10 times with a packet size of 80 bytes and log results
- name: Ping host with custom ping specs
  panos_ping:
    ip_address: 192.168.0.250
    username: admin
    password: admin
    host: 10.0.1.10
    source: 10.0.1.1
    count: 10
    size: 80
    log: /home/admin/log/ping_test.log
'''

RETURN = '''
packet_loss:
    description: After performing the ping test, returns the packet loss percentage.
message:
    description: The output message generated.
'''

import re
from datetime import datetime
from ansible.module_utils.basic import AnsibleModule

try:
    import ipaddress
    from netmiko import ConnectHandler
    from netmiko import NetMikoTimeoutException, NetMikoAuthenticationException
    
    HAS_LIB = True
except ImportError:
    HAS_LIB = False

def run_module():
    module_args = dict(
        ip_address = dict(required=True),
        username = dict(default='admin'),
        password = dict(no_log=True),
        source = dict(),
        host = dict(required=True),
        count = dict(type='int', default=2),
        size = dict(type='int'),
        log = dict()
    )

    result = dict(
        changed=False,
        command='',
        packet_loss='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )
    if not HAS_LIB:
        module.fail_json(msg='Missing required library: netmiko and/or ipaddress')
        
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

        
    command = 'ping '
    
    if module.params['source'] and ipaddress.ip_address(module.params['source']):
        command += 'source ' + module.params['source'] + ' '
        
    if module.params['size']:
        command += 'size ' + str(module.params['size']) + ' '
        
    command += 'count ' + str(module.params['count']) + ' host ' + module.params['host']
    result['command'] = command

    try:        
        raw_text_ping = conn.send_command(command, expect_string='(unknown)|(syntax)|(bind)|(\d{1,3})%').strip('ping\n')
    except NetMikoTimeoutException as e:
        module.fail_json(msg=e)
      
    if module.params['log']:
        with open(module.params['log'], 'a+') as f:
            f.write('==============================================================\n')
            f.write('HOST: ' + module.params['ip_address'] + '\nTIMESTAMP: ' + datetime.now().strftime('%d/%m/%y %H:%M.%S') + '\n\n')
            f.write('CMD:\n\n' + command + '\n\nRESULT:\n' + raw_text_ping + '\n')
            f.write('==============================================================\n')
            f.write('==============================================================\n\n')
        result['message'] = 'Ping test complete, results output to ' + module.params['log']
    else:
        result['message'] = 'Ping test complete, no logging of results'
        
    re_search_success = re.search(r'(\d{1,3})%', raw_text_ping)
    re_search_source_error = re.search(r'(bind)', raw_text_ping)
    re_search_host_error = re.search(r'(unknown)', raw_text_ping)
    #re_search_syntax_error = re.search('(syntax)', raw_text_ping)
    
    if re_search_success:
        result['packet_loss'] = re_search_success.group(0)
    elif re_search_source_error:
        module.fail_json(msg='Ping test failed due to invalid source address')
    elif re_search_host_error:
        module.fail_json(msg='Ping test failed due to unknown host')
    else:
        module.fail_json(msg='Ping test failed due to unknown error')
               
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()