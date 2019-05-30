#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ec2_instance_type_facts
short_description: Gather facts about ec2 instance types in AWS
description:
    - Parse HTML page to get information about instance types 
    - The module doesn't refer to Amazon cloud for information
author:
    - Shvetcova Valeriya
requirements: [ "urllib3", "beautifulsoup4" ]
options:

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
'''

RETURN = '''
'''

try:
    import urllib3
    from bs4 import BeautifulSoup as soup
    import string
    HAS_LIB = True
except:
    HAS_LIB = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec


def list_ec2_instance_types(module):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    http = urllib3.PoolManager()
    content = http.request('GET', module.params.get('ec2_instance_types_url'))
    mp = soup(content.data, 'html.parser')

    # find the raw by id
    type_tag = mp.find(id=module.params.get('default_instance_type_name'))
    # take the table of the raw
    imx = type_tag.parent.parent
    trs = imx.find_all('tr')

    headers = None
    instancetypes = []
    for tag in trs:
        if not headers:
            ths = tag.find_all('th')
            headers = [next(iter(obj.attrs.get('class'))) for obj in ths]
        else:
            tds = tag.find_all('td')
            instancetypes.append(dict((next(iter(td.attrs.get('class'))),
                                       td.text.translate({ord(c): None for c in string.whitespace})) for td in tds))

    for t in instancetypes:
        for k, v in t.items():
            v_low = v.lower()
            if v_low == 'unknown' or v_low == 'unavailable' or v_low == 'n/a':
                t[k] = None
    return instancetypes


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            ec2_instance_types_url=dict(default='https://www.ec2instances.info/', type='str'),
            default_instance_type_name=dict(default='t2.micro', type='str')
        )
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_LIB:
        result = dict(
            msg='Error importing library from requirements. Please check module requirements'
        )
        module.fail_json(**result)

    instancetypes = list_ec2_instance_types(module)
    response = dict(
        amazon_instance_types=instancetypes
    )

    module.exit_json(ansible_facts=response)


if __name__ == '__main__':
    main()