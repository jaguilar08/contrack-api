from os import path
from paramiko import SSHClient, AutoAddPolicy
from sys import argv

SHOST, SUSER, SPWD, BRANCH = argv[1:5]
DIR_DEPLOY = path.basename(path.dirname(path.realpath(__file__)))  # directorio root api
with SSHClient() as ssh:
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    if 'test' in argv:
        command = 'pwd;'
    else:
        command = """
        cd "$(find applications/ -type d -name %s)";
        git checkout %s;
        pwd;
        git branch;
        git pull;
        git status;
        docker compose up --build
        """ % (DIR_DEPLOY, BRANCH)
    ssh.connect(SHOST, 22, SUSER, SPWD)
    stdin, stdout, stderr = ssh.exec_command(command)
    info_out = str(stdout.read().decode('utf8'))
    info_err = str(stderr.read().decode('utf8'))
    print(info_out, info_err)
