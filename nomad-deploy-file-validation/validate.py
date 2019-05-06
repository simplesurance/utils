#!/usr/bin/env python3

# The script expects a list  of application directories as argument.
# It checks that each application directory has a deploy/job.hcl.j2 file.
# It validates the syntax for each hcl.j2 and *.yml files in deploy/.

import argparse
import glob2
import hcl
import io
import os
import sys
import yaml

from ansible.template.template import AnsibleJ2Template
from functools import reduce, namedtuple
from jinja2schema import infer, model

deploy_dir = 'deploy/'
deploy_job_file = 'job.hcl.j2'

# stubs definition of macros that are not default for jinja templates
_macro_stubs = '''
{%- macro lookup(lookup_type, lookup_key) %}{{ lookup_key }}{% endmacro -%}
'''


class ConfigTemplate(namedtuple('config', ['path', 'content'])):

    def __str__(self):
        return self.path


def deploy_config_template(filename):
    replace_map = [
        ('|ternary', '|int'),
        ('|to_json', '|trim'),
        ('.iteritems()', '')
    ]

    with open(filename) as f:
        return ConfigTemplate(
            path=filename,
            content=reduce(lambda content, target: content.replace(*target), replace_map, f.read())
        )


def deploy_job_filet(deploy_dir):
    return os.path.isfile(
        os.path.join(deploy_dir, deploy_job_file)
    )


class StubValue:
    """ Stub class for rendering fake values for templates """

    def __init__(self, infer_value):
        self._infer_value = infer_value

    def __iter__(self):
        return iter([StubValue(self._infer_value)])

    def __getattr__(self, item):
        """ covers case of nested values in templates """
        return StubValue(self._infer_value)

    def __str__(self):
        if isinstance(self._infer_value, model.Scalar):
            return '1'

        return ''


def render_ansible_template(templ):
    template = _macro_stubs + templ.content
    result = infer(template)

    def wrap_stub_value(variable):
        """ Usually needs to wrap iterable objects, as an example:
        {% for country,host in sisu_hosts.iteritems()|sort %}{{ host }},{% endfor %}
        """
        if isinstance(variable, model.Tuple):
            return (wrap_stub_value(sub_value) for sub_value in variable.items)

        if isinstance(variable, model.List):
            return [wrap_stub_value(variable.item)]

        return StubValue(variable)

    # try to render ansible template
    jinja_template = AnsibleJ2Template(template)
    return jinja_template.render(
        {key: wrap_stub_value(value) for key, value in result.items()}
    )


def validate_hcl(hcl_cfg):
    json_config = hcl.load(io.StringIO(hcl_cfg))
    assert isinstance(json_config, dict), "not valid json configuration format, root value must be an object"
    assert 'job' in json_config, "configuration has not 'Job' definition inside a root object"


def validate_yaml(file):
    with open(file) as f:
        yaml.safe_load(f)


def validate_j2_hcl(file):
    template = deploy_config_template(file)
    hcl_content = render_ansible_template(template)
    validate_hcl(hcl_content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="show which files validates successfully, instead of only errors",
    )

    parser.add_argument(
        "-i",
        "--ignore-missing-job-file",
        action="store_true",
        help="do not check if the %s/%s file is missing" %
             (deploy_dir, deploy_job_file)
    )

    parser.add_argument(
        'appdir',
        nargs='+',
        help="application directories, " +
             "deploy files must be in a 'deploy' subdirectory",
    )

    args = parser.parse_args()

    error_cnt = 0
    file_validation_cnt = 0
    dir_validation_cnt = 0

    for app_dir in args.appdir:
        deploy_path = os.path.join(app_dir, deploy_dir)

        dir_validation_cnt += 1

        job_file = os.path.join(deploy_path, deploy_job_file)
        if not args.ignore_missing_job_file and not os.path.isfile(job_file):
            print("%s: file missing" % (job_file))
            error_cnt += 1

        deploy_files = glob2.glob(os.path.join(deploy_path, "**"))
        for file in deploy_files:
            if not os.path.isfile(file):
                continue

            try:
                file_validation_cnt += 1
                if file.endswith("hcl.j2"):
                    validate_j2_hcl(file)
                elif file.endswith(".yml"):
                    validate_yaml(file)
                else:
                    if args.debug:
                        print("skipping file in unsupported format: %s" % file)
                    continue

                if args.debug:
                    print("%s: ok" % file)
            except Exception as e:
                error_cnt += 1
                print("%s: validation failed: %s " % (file, e))

    print("* validated %s files in %s directories, %s issues found " %
          (file_validation_cnt, dir_validation_cnt, error_cnt))
    if error_cnt > 0:
        sys.exit(1)


main()
