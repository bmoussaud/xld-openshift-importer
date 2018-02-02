#!/usr/bin/env python
import os
import yaml
import time
import datetime
import zipfile


class OpenshitImporter:
    deployable_template = """<{type} name="{name}" file="{file}"/>"""

    manifest_template = """<?xml version="1.0" encoding="UTF-8"?>
<udm.DeploymentPackage version="{version}" application="{application}">
    <deployables>
       {deployables}       
    </deployables></udm.DeploymentPackage>
    """

    def __init__(self, file_path, work_directory="./work"):
        self.file_path = file_path
        self.work_directory = work_directory
        if not os.path.exists(self.work_directory):
            os.makedirs(self.work_directory)

    def _deployables(self):
        deployables = []
        with open(self.file_path, 'r') as stream:
            try:
                data = yaml.load(stream)
                print(data)
                if data['kind'] == 'List':
                    for item in data['items']:
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
        manifest_content = self.generate_manifest_content('parksmap', version, deployables)
        with open("{0}/deployit-manifest.xml".format(self.work_directory), "w") as text_file:
            print(manifest_content, file=text_file)

        self.zip()

    def dump_resource(self, item):
        managed_resources = ['Route', 'DeploymentConfig', 'Service']
        if item['kind'] in managed_resources:
            name = "{0}-{1}".format(item['kind'], item['metadata']['name']).lower()
            filename = "{1}/{0}.yaml".format(name, self.work_directory).lower()
            with open(filename, 'w') as outfile:
                yaml.dump(item, outfile, default_flow_style=False)
            return {'type': 'openshift.ResourcesFile', 'name': name, 'file': filename}
        else:
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


OpenshitImporter("./test/workshop-parksmap.yaml").process()
