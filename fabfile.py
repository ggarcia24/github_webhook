from fabric.api import lcd, local, sudo, cd, put
from fabric.contrib.files import exists
from fabric.operations import open_shell

PROJECT_NAME = 'github_webhook'


def prepare(branch_name='master'):
    local('~/VirtualEnvs/{}/bin/activate'.format(PROJECT_NAME))
    local('manage.py test {}'.format())
    local('git add -p && git commit')


def local_deploy():
    with lcd('.'):
        local('python manage.py migrate {}'.format(PROJECT_NAME))
        local('python manage.py test {}'.format(PROJECT_NAME))
        sudo('service apache2 restart')


def remote_deploy():
    repo_url = 'git@github.com:ggarcia24/{}.git'.format(PROJECT_NAME)
    remote_dir = '/var/www/{}'.format(PROJECT_NAME)
    virtual_env_dir = '/var/local/virtualenvs/{}'.format(PROJECT_NAME)
    depkey_remote_location = '~/deployment.key'
    git_ssh_cmd = 'GIT_SSH_COMMAND="ssh -i {} -o StrictHostKeyChecking=no"'.format(depkey_remote_location)
    supervisord_confd_dir = '/etc/supervisor/conf.d/'
    celery_beat_file = '{}/celery_beat.conf'.format(supervisord_confd_dir)
    celery_worker_file = '{}/celery_worker.conf'.format(supervisord_confd_dir)

    if not exists(depkey_remote_location):
        put("./deployment.key", "~/")

    # Clone repo
    if not exists(remote_dir):
        sudo('mkdir "{}"'.format(remote_dir), user="www-data")

    with cd(remote_dir):
        if not exists(".git"):
            sudo('{} git clone "{}" "{}"'.format(git_ssh_cmd, repo_url, remote_dir), user="www-data")
        else:
            sudo('{} git pull --progress --ff-only --no-commit origin master'.format(git_ssh_cmd), user="www-data")

        # If does not exist create virtualenv
        if not exists(virtual_env_dir):
            # TODO: The python version should be a parameter
            sudo('virtualenv -p python3.5 "{}"'.format(virtual_env_dir), user="www-data")

        sudo('source {}/bin/activate && pip install -r "{}/requirements.txt"'.format(virtual_env_dir, remote_dir))

        while not exists('{}/settings.ini'.format(PROJECT_NAME)):
            print('{}/settings.ini file does not exists, please create one from settings.ini.tpl'.format(PROJECT_NAME))
            open_shell("cd {}".format(remote_dir))

        # Please notice that makemigrations is not run, so migration files should be commited on the repository
        sudo('source {}/bin/activate && python manage.py migrate'.format(virtual_env_dir),
             user="www-data")

        sudo('source {}/bin/activate && python manage.py collectstatic --noinput'.format(virtual_env_dir),
             user="www-data")

        # Copy the configuration files for the worker and the beat
        if not exists(celery_beat_file):
            put('./extras/celery_beat.conf', celery_beat_file, mode=0o600, use_sudo=True)

        if not exists(celery_worker_file):
            put('./extras/celery_worker.conf', celery_worker_file, mode=0o600, use_sudo=True)

        # Reload the config and restart all the processes
        sudo('supervisorctl update')

        sudo('service apache2 restart')
