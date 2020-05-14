from toscatranslator.common.translator_to_configuration_dsl import translate as common_translate
from toscatranslator import shell
import os
import yaml
import copy

from toscatranslator.common.utils import deep_update_dict
from toscatranslator.common.tosca_reserved_keys import PROVIDERS, ANSIBLE, TYPE, \
    IMPORTS, TOSCA_DEFINITIONS_VERSION, ATTRIBUTES, PROPERTIES, CAPABILITIES, REQUIREMENTS, TOPOLOGY_TEMPLATE, NODE_TEMPLATES


class BaseAnsibleProvider:
    TESTING_TEMPLATE_FILENAME = 'examples/testing-example.yaml'
    NODE_NAME = 'server_master'
    DEFAULT_TEMPLATE = {
        TOSCA_DEFINITIONS_VERSION: "tosca_simple_yaml_1_0",
        IMPORTS: [
            "toscatranslator/common/TOSCA_definition_1_0.yaml"
        ],
        TOPOLOGY_TEMPLATE: {
            NODE_TEMPLATES: {
                NODE_NAME: {
                    TYPE: "tosca.nodes.Compute"
                }
            }
        }
    }

    def write_template(self, template, filename=None):
        if not filename:
            filename = self.TESTING_TEMPLATE_FILENAME
        with open(filename, 'w') as f:
            f.write(template)

    def delete_template(self, filename=None):
        if not filename:
            filename = self.TESTING_TEMPLATE_FILENAME
        if os.path.exists(filename):
            os.remove(filename)

    def parse_yaml(self, content):
        r = yaml.load(content)
        return r

    def parse_all_yaml(self, content):
        r = yaml.full_load_all(content)
        return r

    def prepare_yaml(self, content):
        r = yaml.dump(content)
        return r

    def test_provider(self):
        assert hasattr(self, 'PROVIDER') is not None
        assert self.PROVIDER in PROVIDERS

    def get_ansible_output(self, template, template_filename = None):
        if not template_filename:
            template_filename = self.TESTING_TEMPLATE_FILENAME
        self.write_template(self.prepare_yaml(template))
        r = common_translate(template_filename, False, self.PROVIDER, ANSIBLE)
        print(r)
        self.delete_template(template_filename)
        playbook = self.parse_yaml(r)
        return playbook

    def get_k8s_output(self, template, template_filename = None):
        if not template_filename:
            template_filename = self.TESTING_TEMPLATE_FILENAME
        self.write_template(self.prepare_yaml(template))
        r = common_translate(template_filename, False, self.PROVIDER, 'kubernetes')
        print(r)
        manifest = list(self.parse_all_yaml(r))
        return manifest

    def update_node_template(self, template, node_name, update_value, param_type):
        update_value = {
            TOPOLOGY_TEMPLATE: {
                NODE_TEMPLATES: {
                    node_name: {
                        param_type: update_value
                    }
                }
            }
        }
        return deep_update_dict(template, update_value)


    def update_template_property(self, template, node_name, update_value):
        return self.update_node_template(template, node_name, update_value, PROPERTIES)

    def update_template_attribute(self, template, node_name, update_value):
        return self.update_node_template(template, node_name, update_value, ATTRIBUTES)

    def update_template_capability(self, template, node_name, update_value):
        return self.update_node_template(template, node_name, update_value, CAPABILITIES)

    def update_template_capability_properties(self, template, node_name, capability_name, update_value):
        uupdate_value = {
            capability_name: {
                PROPERTIES: update_value
            }
        }
        return self.update_template_capability(template, node_name, uupdate_value)

    def update_template_capability_attributes(self, template, node_name, capability_name, update_value):
        uupdate_value = {
            capability_name: {
                ATTRIBUTES: update_value
            }
        }
        return self.update_node_template(template, node_name, uupdate_value, CAPABILITIES)

    def update_template_requirement(self, template, node_name, update_value):
        return self.update_node_template(template, node_name, update_value, REQUIREMENTS)


class TestAnsibleProvider (BaseAnsibleProvider):
    def test_full_translating(self):
        shell.main(['--template-file', 'examples/tosca-server-example.yaml', '--provider', self.PROVIDER])

    def test_meta(self):
        if hasattr(self, 'check_meta'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = ["master=true"]
            testing_parameter = {
                "meta": testing_value
            }
            template = self.update_template_attribute(template, self.NODE_NAME, testing_parameter)
            playbook = self.get_ansible_output(template)

            assert next(iter(playbook), {}).get('tasks')
            tasks = playbook[0]['tasks']

            self.check_meta(tasks, testing_value)

    def test_private_address(self):
        if hasattr(self, 'check_private_address'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = "192.168.12.25"
            testing_parameter = {
                "private_address": testing_value
            }
            template = self.update_template_attribute(template, self.NODE_NAME, testing_parameter)
            playbook = self.get_ansible_output(template)

            assert next(iter(playbook), {}).get('tasks')
            tasks = playbook[0]['tasks']

            self.check_private_address(tasks, testing_value)

    def test_public_address(self):
        if hasattr(self, 'check_public_address'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = "10.100.115.15"
            testing_parameter = {
                "public_address": testing_value
            }
            template = self.update_template_attribute(template, self.NODE_NAME, testing_parameter)
            playbook = self.get_ansible_output(template)

            assert next(iter(playbook), {}).get('tasks')

            tasks = playbook[0]['tasks']
            self.check_public_address(tasks, testing_value)

    def test_network_name(self):
        if hasattr(self, 'check_network_name'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = "test-two-routers"
            testing_parameter = {
                "networks": {
                    "default": {
                        "network_name": testing_value
                    }
                }
            }
            template = self.update_template_attribute(template, self.NODE_NAME, testing_parameter)
            playbook = self.get_ansible_output(template)

            assert next(iter(playbook), {}).get('tasks')

            tasks = playbook[0]['tasks']
            self.check_network_name(tasks, testing_value)

    def test_host_capabilities(self):
        if hasattr(self, 'check_host_capabilities'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_parameter = {
                "num_cpus": 1,
                "disk_size": "5 GiB",
                "mem_size": "1024 MiB"
            }
            template = self.update_template_capability_properties(template, self.NODE_NAME, "host", testing_parameter)
            playbook = self.get_ansible_output(template)

            assert next(iter(playbook), {}).get('tasks')

            tasks = playbook[0]['tasks']
            self.check_host_capabilities(tasks)

    def test_endpoint_capabilities(self):
        if hasattr(self, 'check_endpoint_capabilities'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_parameter = {
                "endpoint": {
                    "properties": {
                        "protocol": "tcp",
                        "port": 1000,
                        "initiator": "target"
                    },
                    "attributes": {
                        "ip_address": "0.0.0.0"
                    }
                }
            }
            template = self.update_template_capability(template, self.NODE_NAME, testing_parameter)
            playbook = self.get_ansible_output(template)
            assert next(iter(playbook), {}).get('tasks')

            tasks = playbook[0]['tasks']
            self.check_endpoint_capabilities(tasks)

    def test_os_capabilities(self):
        if hasattr(self, 'check_os_capabilities'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_parameter = {
                "architecture": "x86_64",
                "type": "ubuntu",
                "distribution": "xenial",
                "version": 16.04
            }
            template = self.update_template_capability_properties(template, self.NODE_NAME, "os", testing_parameter)
            playbook = self.get_ansible_output(template)
            assert next(iter(playbook), {}).get('tasks')

            tasks = playbook[0]['tasks']
            self.check_os_capabilities(tasks)

