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
module: panos_ping_nexthop

short_description: Ping the nexthop of each route in routing table from a PAN firewall.

description:
    - Ping the nexthop of each route in routing table from a PAN firewall.
    - Return packet-loss percentage results.
    
requirements:
    - netmiko can be obtained from PyPi (https://pypi.org/project/netmiko)
    - pandevice can be obtained from PyPi (https://pypi.org/project/pandevice)

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

author:
    - Matthew Spera (@mattspera)
'''

EXAMPLES = '''
'''

RETURN = '''
packet_loss:
    description: After performing the ping test, returns the packet-loss percentage.
message:
    description: The output message generated.
'''

import json
import ssl
import re

from ansible.module_utils.basic import AnsibleModule

# To disable ssl certificate verification (required for Centos7/RHEL - Python 2.7.5)
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
# Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
# Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

try:
    from pandevice.base import PanDevice
    from pandevice.errors import PanDeviceError
    from netmiko import ConnectHandler
    from netmiko import NetMikoTimeoutException, NetMikoAuthenticationException
    import xmltodict

    HAS_LIB = True
except ImportError:
    HAS_LIB = False

def main():
    module_args = dict(
        ip_address=dict(required=True),
        username=dict(default='admin'),
        password=dict(no_log=True)
    )

    result = dict(
        changed=False,
        packet_loss='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        #support_check_mode=False
    )

    if not HAS_LIB:
        module.fail_json(msg='Missing required libraries: pandevice, netmiko, xmltodict')

    try:
        device = PanDevice.create_from_device(
            module.params['ip_address'],
            module.params['username'],
            module.params['password']
        )
    except PanDeviceError as e:
        module.fail_json(msg=e.message)

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

    route_table_dict = xmltodict.parse(device.op('show routing route', xml=True))['response']['result']
    route_interface_dict = xmltodict.parse(device.op('show routing interface', xml=True))['response']['result']

    nexthops = []
    nexthop_interfaces = []

    if 'entry' in route_table_dict:
        for entry in route_table_dict['entry']:
            if (
                'A' in entry['flags'] and
                not 'C' in entry['flags'] and
                not 'H' in entry['flags'] and
                entry['nexthop'] != 'discard' and
                not entry['nexthop'] in nexthops
            ):
                nexthops.append(entry['nexthop'])
                nexthop_interfaces.append(entry['interface'])

    interface_ip_map_dict = {}

    if 'interface' in route_interface_dict:
        for interface in route_interface_dict['interface']:
            if 'address' in interface:
                interface_ip_map_dict[interface['name']] = interface['address']
            else:
                interface_ip_map_dict[interface['name']] = ''

    nexthop_interface_ips = []

    for nexthop_int in nexthop_interfaces:
        for int_name, int_ip in interface_ip_map_dict.items():
            if nexthop_int == int_name:
                nexthop_int = int_ip
                nexthop_interface_ips.append(nexthop_int[:-3])
                break

    packet_loss_dict = {}

    for nexthop, source in list(zip(nexthops, nexthop_interface_ips)):
        if source:
            cmd = 'ping source {} count 2 host {}'.format(source, nexthop)
            raw_text_ping = conn.send_command(cmd, expect_string=r'(unknown)|(syntax)|(bind)|(\d{1,3})%').strip('ping\n')
            re_packet_loss = re.search(r'(\d{1,3})%', raw_text_ping)

            if re_packet_loss:
                packet_loss_dict[nexthop] = re_packet_loss.group(0)

    result['packet_loss'] = json.dumps(packet_loss_dict)
    result['message'] = 'Done'
    result['changed'] = True

    conn.disconnect()

    module.exit_json(**result)

if __name__ == "__main__":
    main()