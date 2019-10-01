from subprocess import run, PIPE

import yaml
from charms.reactive import when, when_not, set_flag, endpoint_from_name
from charmhelpers.core import hookenv

from charms import layer


@when_not('installed')
def install():
    layer.snap.install('snap-store-proxy')
    layer.status.waiting('Waiting for Postgres')
    set_flag('installed')


@when('db.connected')
def request_db():
    db = endpoint_from_name('db')
    db.set_database('snap_store_proxy')
    db.set_extensions('btree_gist')


@when('db.master.available')
@when_not('configured')
def configure():
    db = endpoint_from_name('db')
    public_ip = hookenv.unit_public_ip()
    run(['snap-proxy', 'config', f'proxy.db.connection={db.master.uri}'],
        check=True)
    run(['snap-proxy', 'config', f'proxy.domain={public_ip}'],
        check=True)
    run(['snap-proxy', 'generate-keys'], check=True)
    hookenv.open_port(80)
    layer.status.blocked(f'Please run: '
                         f'juju ssh {hookenv.local_unit()} '
                         f'"sudo snap-proxy register"')
    set_flag('configured')


@when('configured')
@when_not('registered')
def check_registration():
    result = run(['snap-proxy', 'status'], check=True, stdout=PIPE)
    data = yaml.safe_load(result.stdout.decode('utf8'))
    if data.get('Store ID'):
        domain = hookenv.unit_public_ip()
        store_id = data['Store ID']
        layer.status.active(f'curl -s http://{domain}/v2/auth/store/assertions'
                            f' | sudo snap ack /dev/stdin ; '
                            f'sudo snap set core proxy.store={store_id}')
        set_flag('registered')
