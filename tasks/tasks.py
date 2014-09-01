from contextlib import contextmanager as _contextmanager
from os.path import dirname

from fabric.api import *  # NOQA
from fabric.contrib import files

MANAGER_BRANCH = 'master'

# root of synched folder with cloudify github repositories
CODE_BASE = '/home/vagrant/cloudify'

# path to different cloudify components relative to 'CODE_BASE'
CLOUDIFY_MANAGER = 'cloudify-manager'
MANAGER_REST = 'cloudify-manager/rest-service/manager_rest'
WORKER_INSTALLER = 'cloudify-manager/plugins/agent-installer/worker_installer'
PLUGIN_INSTALLER = 'cloudify-manager/plugins/plugin-installer/plugin_installer'
W_WORKER_INSTALLER = 'cloudify-manager/plugins/windows-agent-installer/windows_agent_installer'  # NOQA
W_PLUGIN_INSTALLER = 'cloudify-manager/plugins/windows-plugin-installer/windows_plugin_installer'  # NOQA
WORKFLOWS = 'cloudify-manager/workflows/workflows'
SYSTEM_WORKFLOWS = 'cloudify-manager/workflows/system_workflows'
DSL_PARSER = 'cloudify-dsl-parser/dsl_parser'
CLOUDIFY_COMMON = 'cloudify-plugins-common/cloudify'
REST_CLIENT = 'cloudify-rest-client/cloudify_rest_client'

# agent package details
VIRTUALENV_PACKAGE = '/home/vagrant/package'
VIRTUALENV_PARENT = '{0}/linux'.format(VIRTUALENV_PACKAGE)
VIRTUALENV_PATH = '{0}/env'.format(VIRTUALENV_PARENT)
AGENT_PACKAGE_PATH = '/opt/manager/resources/packages/agents/Ubuntu-agent.tar.gz'  # NOQA
VIRTUALENV_PATH_MANAGER = '/opt/celery/cloudify.management__worker/env'

# file server paths
PACKAGES_PATH = '/opt/manager/resources/packages'
AGENTS_PATH = '{0}/agents'
SCRIPTS_PATH = '{0}/scripts'
AGENTS_PATH = '{0}/templates'

# packages to install (in this order) for the agent package virtual env
AGENT_PACKAGES = [
    dirname(package) for package in [
        REST_CLIENT,
        CLOUDIFY_COMMON,
        WORKER_INSTALLER,
        PLUGIN_INSTALLER,
        W_WORKER_INSTALLER,
        W_PLUGIN_INSTALLER
    ]
]

AGENT_DEPENDENCIES = [
    'celery==3.0.24'
]

# links to host machine source code for the agent virtualenv
AGENT_LINKS = {
    '{}/lib/python2.7/site-packages'.format(VIRTUALENV_PATH): {
        'cloudify': CLOUDIFY_COMMON,
        'cloudify_rest_client': REST_CLIENT,
        'plugin_installer': PLUGIN_INSTALLER,
        'worker_installer': WORKER_INSTALLER,
        'windows_agent_installer': W_WORKER_INSTALLER,
        'windows_plugin_installer': W_PLUGIN_INSTALLER,
    }
}

# links to host machine source code for the rest-service
# and celery management virtualenvs
MANAGER_LINKS = {
    '/opt/manager': {
        'cloudify-manager-{}'.format(MANAGER_BRANCH): CLOUDIFY_MANAGER,
    },
    '/opt/manager/lib/python2.7/site-packages': {
        'dsl_parser': DSL_PARSER,
        'manager_rest': MANAGER_REST,
    },
    '/opt/celery/cloudify.management__worker/env': {
        'cloudify-manager-{}'.format(MANAGER_BRANCH): CLOUDIFY_MANAGER,
    },
    '/opt/celery/cloudify.management__worker/env/lib/python2.7/site-packages': {  # NOQA
        'cloudify': CLOUDIFY_COMMON,
        'plugin_installer': PLUGIN_INSTALLER,
        'worker_installer': WORKER_INSTALLER,
        'cloudify_rest_client': REST_CLIENT,
        'system_workflows': SYSTEM_WORKFLOWS,
        'workflows': WORKFLOWS,
    }
}

# services to stop (and start in reverse order) when starting (and ending)
# setup_env task
managed_services = [
    'manager',
    'celeryd-cloudify-management'
]


def setup_env(link_manager=True, create_package=True):
    _stop_services()
    _update_agent_package(create_package)
    _link_manager(link_manager)
    _start_services()


def restart():
    _stop_services()
    _start_services()


def _stop_services():
    for service in managed_services:
        sudo('stop {}'.format(service))


def _start_services():
    for service in managed_services[::-1]:
        sudo('start {}'.format(service))


def _link_manager(link_manager):
    if link_manager:
        _link(MANAGER_LINKS)


def _update_agent_package(create_package):
    if not files.exists(VIRTUALENV_PARENT):
        run('mkdir -p {0}'.format(VIRTUALENV_PARENT))
        run('virtualenv {0}'.format(VIRTUALENV_PATH))
        with virtualenv(VIRTUALENV_PATH):
            for package in AGENT_PACKAGES:
                _pip_install('{}/{}'.format(CODE_BASE, package))
            for dependency in AGENT_DEPENDENCIES:
                _pip_install(dependency)
        with virtualenv(VIRTUALENV_PATH_MANAGER):
            for package in AGENT_PACKAGES:
                _pip_install('{}/{}'.format(CODE_BASE, package))
            for dependency in AGENT_DEPENDENCIES:
                _pip_install(dependency)
        _link(AGENT_LINKS)
    if create_package:
        run('tar czf package.tar.gz package --dereference')
        sudo('cp package.tar.gz {}'.format(AGENT_PACKAGE_PATH))


def _link(links):
    for base, sublinks in links.items():
        for sublink, target in sublinks.items():
            source = '{}/{}'.format(base, sublink)
            target = '{}/{}'.format(CODE_BASE, target)
            if files.is_link(source):
                continue
            run(' && '.join([
                'sudo rm -rf {}'.format(source),
                'cd $(dirname {})'.format(source),
                'sudo ln -s {} $(basename {})'.format(target, source)
                ]))


def _pip_install(package):
    run('pip install {}'.format(package))


@_contextmanager
def virtualenv(VIRTUALENV_PATH):
    with prefix('source {}/bin/activate'.format(VIRTUALENV_PATH)):
        yield


def upload_agent_to_manager():
    """see instructions for creating your own agent at http://getcloudify.org
    under Guides - Creating a Cloudify agent.
    """
    put('/cloudify-agent/centos-agent.tar.gz',
        '/opt/manager/resources/packages/agents/')
    put('/cloudify-agent/centos-celeryd-cloudify.init.template',
        '/opt/manager/resources/packages/templates/')
    put('/cloudify-agent/centos-celeryd-cloudify.conf.template',
        '/opt/manager/resources/packages/templates/')
    put('/cloudify-agent/centos-agent-disable-requiretty.sh',
        '/opt/manager/resources/packages/scripts/')
