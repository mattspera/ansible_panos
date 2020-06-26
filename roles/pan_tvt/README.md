pan_tvt
=========

An Ansible Role developed to facilitate the automation of technical verification testing on Palo Alto Networks devices.

Requirements
------------

The following Python libraries are required to use this Role:

- pantest (https://github.com/mattspera/pantest)

Role Variables
--------------

- `pan_user`: Palo Alto device username
- `pan_pass`: Palo Alto device password
- `baseline_file`: relative file path to save/import baseline facts to/from file (.json). Variable consumed by the following task files:
  - `baseline_firewall.yml`
  - `tvt_firewall.yml`
- `tvt_file`: relative file path to save tvt test report to file (.html). Variable consumed by the following task files:
  - `tvt_firewall.yml`

Dependencies
------------

The following Ansible Collections are required to be installed as a prerequisite to using this Role:

- paloaltonetworks.panos (https://galaxy.ansible.com/paloaltonetworks/panos)
- mattlab.panos (https://github.com/mattspera/ansible_panos)

Example Playbook
----------------

    - hosts: all
      vars:
        pan_user: "{{ ansible_user }}"
        pan_pass: "{{ ansible_password }}"

      tasks:

        - include_role:
            name: pan_tvt
            tasks_from: baseline_firewall
          vars:
            baseline_file: "{{ inventory_hostname }}_bl.json"

        - include_role:
            name: pan_tvt
            tasks_from: tvt_firewall
          vars:
            baseline_file: "{{ inventory_hostname }}_bl.json"
            tvt_file: "{{ inventory_hostname }}_tvt.html"

License
-------

BSD

Author Information
------------------

Matthew Spera (@mattspera)
