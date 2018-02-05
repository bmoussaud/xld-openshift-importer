#!/usr/bin/env python
import os
from ruamel import yaml
import time
import datetime
import zipfile
import re


class OpenshitImporter:
    deployable_template = """<{type} name="{name}" file="{file}"/>"""

    manifest_template = """<?xml version="1.0" encoding="UTF-8"?>
<udm.DeploymentPackage version="{version}" application="{application}">
    <deployables>
       {deployables}       
    </deployables></udm.DeploymentPackage>
    """

    def __init__(self, application_name, file_path, work_directory="./work"):
        self.file_path = file_path
        self.application_name = application_name
        self.work_directory = work_directory
        if not os.path.exists(self.work_directory):
            os.makedirs(self.work_directory)

    def _deployables(self):
        deployables = []
        with open(self.file_path, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
                # print(data)
                if data['kind'] == 'List':
                    for item in data['items']:
                        deployable = self.dump_resource(item)
                        if deployable is not None:
                            deployables.append(deployable)
                if data['kind'] == 'Template':
                    for item in data['objects']:
                        deployable = self.dump_resource(item)
                        if deployable is not None:
                            deployables.append(deployable)
            except yaml.YAMLError as exc:
                print(exc)

        return deployables

    def process(self):
        deployables = self._deployables()
        ts = time.time()
        version = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H-%M-%S')
        manifest_content = self.generate_manifest_content(self.application_name, version, deployables)
        # print(manifest_content)
        with open("{0}/deployit-manifest.xml".format(self.work_directory), "w") as text_file:
            print(manifest_content, file=text_file)

        self.zip()

    def dump_resource(self, item):

        # https://www.programcreek.com/python/example/104725/yaml.add_representer
        def str_presenter(dumper, data):
            pattern = r'(.*)\$({\w*})(.*)'
            match_obj = re.match(pattern, data)
            if match_obj:
                data = "{0}{{{1}}}{2}".format(match_obj.group(1), match_obj.group(2), match_obj.group(3))
            return dumper.represent_scalar('tag:yaml.org,2002:str', data.strip())

        managed_resources = ['Route', 'DeploymentConfig', 'Service', 'PersistentVolumeClaim','ImageStream']
        if item['kind'] in managed_resources:
            name = "{0}-{1}".format(item['kind'], item['metadata']['name']).lower()
            filename = "{1}/{0}.yaml".format(name, self.work_directory).lower()
            with open(filename, 'w') as outfile:
                yaml.add_representer(str, str_presenter)
                yaml.dump(item, outfile, default_flow_style=False)
            return {'type': 'openshift.ResourcesFile', 'name': name, 'file': filename}
        else:
            print("NOT SUPPORTED {0}".format(item['kind']))
            return None

    def generate_manifest_content(self, application_name, version, deployables):
        xdeployables = [self.deployable_template.format(**deployable) for deployable in deployables]
        manifest_data = {'deployables': ' '.join(xdeployables), 'version': version, 'application': application_name}
        return self.manifest_template.format(**manifest_data)

    def zip(self):
        zf = zipfile.ZipFile('package.dar', mode='w')
        try:
            zf.write("{0}/deployit-manifest.xml".format(self.work_directory), arcname="deployit-manifest.xml")
            for deployable in self._deployables():
                zf.write(deployable['file'])
        finally:
            zf.close()


OpenshitImporter("coolstore", "test/coolstore-template.yaml").process()
