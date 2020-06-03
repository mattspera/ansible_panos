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
module: panos_test

short_description: Palo Alto Networks test-suite module.

description:
    - Palo Alto Networks test-suite module.
    
requirements:
    - pantest (can be found at https://github.com/mattspera/pantest)

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
    test_devices_connected:
        description:
            - Panorama test.
            - Input parameter retrieved during baseline of device.
            - List containing hostnames of connected devices.
        type: list
    test_log_collectors_connected:
        description:
            - Panorama test.
            - Input parameter retrieved during baseline of device.
            - List containing hostnames of connected log collectors.
        type: list
    test_wf_appliances_connected:
        description:
            - Panorama test.
            - Input parameter retrieved during baseline of device.
            - List containing hostnames of connected wildfire appliances.
        type: list
    test_shared_policy_sync:
        description:
            - Panorama test.
            - Input parameter retrieved during baseline of device.
            - Dictionary containing the shared policy sync status for each device group for each vsys of each connected device.
    test_template_sync:
        description:
            - Panorama test.
            - Input parameter retrieved during baseline of device.
            - Dictionary containing the template sync status for each template of each connected device.
    test_log_collector_config_sync:
        description:
            - Panorama test.
            - Input parameter retrieved during baseline of device.
            - Dictionary containing the config sync status for each connected log collector.
    test_wf_appliance_config_sync:
        description:
            - Panorama test.
            - Input parameter retrieved during baseline of device.
            - Dictionary containing the config sync status for each connected wildfire appliance.
    test_ha_peer_up_pano:
        description:
            - Panorama test.
            - Input parameter retrieved during baseline of device.
            - String containing the HA peer status of the device, either 'up' or 'down'.
    test_ha_match_pano:
        description:
            - Panorama test.
            - Input parameter retrieved during baseline of device.
            - String containing the HA App & AV compatibility status of the device and its HA peer, either 'Match' or 'Mismatch'.
    test_ha_config_synched_pano:
        description:
            - Panorama test.
            - Input parameter retrieved during baseline of device.
            - String containing the HA config sync status of the device and its HA peer, either 'synchronized' or 'not-synchronized'.
    test_system_env_alarms_pano:
        description:
            - Panorama test.
            - Input parameter retrieved during baseline of device.
            - Bool containing the thermal, fan and power environmentals alarm status of the device.
    test_interfaces_up:
        description:
            - Firewall test.
            - Input parameter retrieved during baseline of device.
            - List containing the names of interfaces in an 'up' state.
        type: list
    test_traffic_log_forward:
        description:
            - Firewall test.
            - Bool either 'True' to execute test or 'False' to not execute test.
        type: bool
    test_panorama_connected:
        description:
            - Firewall test.
            - Input parameter retrieved during baseline of device.
            - String containing the Panorama connection status of the device, either 'yes' or 'no'.
    test_ha_peer_up:
        description:
            - Firewall test.
            - Input parameter retrieved during baseline of device.
            - String containing the HA peer status of the device, either 'up' or 'down'.
    test_ha_match:
        description:
            - Firewall test.
            - Input parameter retrieved during baseline of device.
            - String containing the HA App AV, threat & GP client compatibility status of the device and its HA peer, either 'Match' or 'Mismatch'.
    test_ha_config_synched:
        description:
            - Firewall test.
            - Input parameter retrieved during baseline of device.
            - String containing the HA config sync status of the device and its HA peer, either 'synchronized' or 'not-synchronized'.
    test_connectivity:
        description:
            - Firewall test.
            - Input parameter retrieved during baseline of device.
            - Dictionary containing the packet-loss percentage for each unique next-hop present in the routing table for the device.
    test_system_env_alarms_fw:
        description:
            - Firewall test.
            - Input parameter retrieved during baseline of device.
            - Bool containing the thermal, fan and power environmentals alarm status of the device.
    test_ha_enabled:
        description:
            - General test.
            - Input parameter retrieved during baseline of device.
            - String containing the HA enabled status of the device, either 'yes' or 'no'.
    test_system_version:
        description:
            - General test.
            - String containing a PAN-OS software version.
    test_config_diff:
        description:
            - General test.
            - Input parameter retrieved during baseline of device.
            - String containing either a file path to a file containing the SET command configuration for the device, or
            - String containing the SET comand configuration for the device.

author:
    - Matthew Spera (@mattspera)
'''

EXAMPLES = '''
# Run components of the Panorama test-suite
- name: PANORAMA TEST-SUITE
  panos_test:
    ip_address: 192.168.0.254
    username: admin
    password: admin
    test_devices_connected: '{{ bl_devices_connected }}'
    test_shared_policy_sync: '{{ bl_shared_policy_sync_dict }}'
    test_template_sync: '{{ bl_template_sync_dict }}'
'''

RETURN = '''
stdout:
    description: Test-suite result output.
message:
    description: Displays the overall result of the test-suite, either a 'PASS' or 'FAIL'.
'''

import json
import ssl
import logging
from datetime import datetime

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
    from pantest.testcases import GeneralTestCases
    from pantest.testcases import FirewallTestCases
    from pantest.testcases import PanoramaTestCases

    HAS_LIB = True
except ImportError:
    HAS_LIB = False

def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

def main():
    module_args = dict(
        ip_address=dict(required=True),
        username=dict(default='admin'),
        password=dict(no_log=True),
        test_devices_connected=dict(type='list'),
        test_log_collectors_connected=dict(type='list'),
        test_wf_appliances_connected=dict(type='list'),
        test_shared_policy_sync=dict(),
        test_template_sync=dict(),
        test_log_collector_config_sync=dict(),
        test_wf_appliance_config_sync=dict(),
        test_ha_peer_up_pano=dict(),
        test_ha_match_pano=dict(),
        test_ha_config_synced_pano=dict(),
        test_system_env_alarms_pano=dict(),
        test_interfaces_up=dict(type='list'),
        test_traffic_log_forward=dict(type='bool'),
        test_panorama_connected=dict(),
        test_ha_peer_up=dict(),
        test_ha_match=dict(),
        test_ha_config_synced=dict(),
        test_connectivity=dict(),
        test_system_env_alarms_fw=dict(),
        test_ha_enabled=dict(),
        test_system_version=dict(),
        test_config_diff=dict()
    )

    result = dict(
        changed=False,
        stdout='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        #support_check_mode=False
    )

    if not HAS_LIB:
        module.fail_json(msg='Missing required libraries: pantest')

    # Lowering paramiko logging level to prevent unnecessary logging in main log file
    logging.getLogger('paramiko').setLevel(logging.WARNING)

    dt = datetime.now().strftime(r'%y%m%d_%H%M')
    logging.basicConfig(filename='{}_{}_tvt.log'.format(module.params['ip_address'], dt), level=logging.INFO)

    device_info = {
        'ip' : module.params['ip_address'],
        'username' : module.params['username'],
        'password' : module.params['password']    
    }

    pano_tester = PanoramaTestCases(device_info)
    fw_tester = FirewallTestCases(device_info)
    gen_tester = GeneralTestCases(device_info)

    test_output_list = []

    # Panorama Tests

    if module.params['test_devices_connected']:
        output = pano_tester.t_devices_connected(module.params['test_devices_connected'])
        test_output_list.append(output)

    if module.params['test_log_collectors_connected']:
        output = pano_tester.t_log_collectors_connected(module.params['test_log_collectors_connected'])
        test_output_list.append(output)

    if module.params['test_wf_appliances_connected']:
        output = pano_tester.t_wf_appliances_connected(module.params['test_wf_appliances_connected'])
        test_output_list.append(output)

    if module.params['test_shared_policy_sync']:
        output = pano_tester.t_shared_policy_sync(module.params['test_shared_policy_sync'])
        test_output_list.append(output)

    if module.params['test_template_sync']:
        output = pano_tester.t_template_sync(module.params['test_template_sync'])
        test_output_list.append(output)

    if module.params['test_log_collector_config_sync']:
        output = pano_tester.t_log_collector_config_sync(module.params['test_log_collector_config_sync'])
        test_output_list.append(output)

    if module.params['test_wf_appliance_config_sync']:
        output = pano_tester.t_wf_appliance_config_sync(module.params['test_wf_appliance_config_sync'])
        test_output_list.append(output)

    if module.params['test_ha_peer_up_pano']:
        output = pano_tester.t_ha_peer_up_pano(module.params['test_ha_peer_up_pano'])
        test_output_list.append(output)

    if module.params['test_ha_match_pano']:
        output = pano_tester.t_ha_match_pano(module.params['test_ha_match_pano'])
        test_output_list.append(output)

    if module.params['test_ha_config_synced_pano']:
        output = pano_tester.t_ha_config_synced_pano(module.params['test_ha_config_synced_pano'])
        test_output_list.append(output)

    if module.params['test_system_env_alarms_pano']:
        output = pano_tester.t_system_env_alarms_pano(str(module.params['test_system_env_alarms_pano']))
        test_output_list.append(output)

    # Firewall Tests

    if module.params['test_panorama_connected']:
        output = fw_tester.t_panorama_connected(module.params['test_panorama_connected'])
        test_output_list.append(output)

    if module.params['test_interfaces_up']:
        output = fw_tester.t_interfaces_up(module.params['test_interfaces_up'])
        test_output_list.append(output)

    if module.params['test_ha_peer_up']:
        output = fw_tester.t_ha_peer_up(module.params['test_ha_peer_up'])
        test_output_list.append(output)

    if module.params['test_ha_match']:
        output = fw_tester.t_ha_match(module.params['test_ha_match'])
        test_output_list.append(output)

    if module.params['test_ha_config_synced']:
        output = fw_tester.t_ha_config_synced(module.params['test_ha_config_synced'])
        test_output_list.append(output)

    if module.params['test_system_env_alarms_fw']:
        output = fw_tester.t_system_env_alarms_fw(str(module.params['test_system_env_alarms_fw']))
        test_output_list.append(output)

    if module.params['test_connectivity']:
        output = fw_tester.t_connectivity(module.params['test_connectivity'])
        test_output_list.append(output)

    if module.params['test_traffic_log_forward']:
        output = fw_tester.t_traffic_log_forward()
        test_output_list.append(output)

    # General Tests

    if module.params['test_ha_enabled']:
        output = gen_tester.t_ha_enabled(module.params['test_ha_enabled'])
        test_output_list.append(output)

    if module.params['test_system_version']:
        output = gen_tester.t_system_version(module.params['test_system_version'])
        test_output_list.append(output)

    if module.params['test_config_diff']:
        if 'config_set' in module.params['test_config_diff']:
            with open(module.params['test_config_diff'], 'r') as file_obj:
                config_set_list = file_obj.read().decode('utf-8').splitlines()

            output = gen_tester.t_config_diff(config_set_list)
        else:
            output = gen_tester.t_config_diff(module.params['test_config_diff'])

        test_output_list.append(output)

    result['stdout'] = json.dumps(test_output_list, indent=4, default=set_default)

    for test in test_output_list:
        if not test['result']:
            result['message'] = 'FAIL'
            module.exit_json(**result)

    result['message'] = 'PASS'

    module.exit_json(**result)

if __name__ == '__main__':
    main()