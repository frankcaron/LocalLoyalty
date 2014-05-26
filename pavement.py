import os

from paver.easy import cmdopts
from paver.easy import needs
from paver.easy import task
from optparse import make_option
from subprocess import call

@task
@cmdopts([
    make_option('-d', '--database_file', help='Database File', default='/tmp/test.db'),
])
def delete_db(options):
    try:
        os.remove(options.delete_db.database_file)
    except Exception:
        pass
    print 'Database Removed'


@task
@cmdopts([
    make_option('-c', '--config_file', help='Config File', default='/Users/david.park/dev/LocalLoyalty/config/local.cfg'),
])
def set_config(options):
    os.environ["CONFIG"] = options.set_config.config_file
    print 'CONFIG Set to: ', os.environ["CONFIG"]


@task
@cmdopts([
    make_option('-n', '--ngrok_url', help='Ngrok URL', default='https://3103585.ngrok.com'),
])
def set_ngrok_url(options):
    os.environ["NGROK_URL"] = options.set_ngrok_url.ngrok_url
    print 'NGROK URL Set to: ', os.environ["NGROK_URL"]


@task
@cmdopts([
    make_option('-p', '--path', help='Ngrok Path', default='/usr/local/bin/ngrok'),
])
def runngrok(options):
    call([options.runngrok.path, '5000'])


@task
@needs(['delete_db'])
def runserver(options):
    if not os.environ["CONFIG"]:
        raise Exception("You need to set the CONFIG")
    if not os.environ["NGROK_URL"]:
        raise Exception("You need to set the NGROK_URL")
    call(["python", "app.py"])
