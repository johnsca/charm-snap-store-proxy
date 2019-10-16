from subprocess import run, PIPE

import yaml
from charms.reactive import when, when_not, set_flag, endpoint_from_name
from charmhelpers.core import hookenv

from charms import layer


@when_not('snap.installed.snap-store-proxy')
def install():
    layer.status.maintenance('Installing snap-store-proxy')
    layer.snap.install('snap-store-proxy', channel='candidate')


@when_not('db.connected')
def wait_for_db():
    try:
        goal_state = hookenv.goal_state()
    except NotImplementedError:
        goal_state = {}

    if 'db' in goal_state.get('relations', {}):
        layer.status.waiting('Waiting for Postgres')
    else:
        layer.status.blocked('Missing postgresql:db-admin relation')


@when('db.connected')
@when_not('snap-store-proxy.db.requested')
def request_db():
    layer.status.maintenance('Requesting database')
    db = endpoint_from_name('db')
    db.set_database('snap_store_proxy')
    db.set_extensions('btree_gist')
    set_flag('snap-store-proxy.db.requested')


@when('db.master.available')
@when('snap.installed.snap-store-proxy')
@when_not('snap-store-proxy.configured')
def configure():
    layer.status.maintenance('Configuring snap-proxy')
    db = endpoint_from_name('db')
    public_ip = hookenv.unit_public_ip()
    run(['snap-proxy', 'config', f'proxy.db.connection={db.master.uri}'],
        check=True)
    run(['snap-proxy', 'config', f'proxy.domain={public_ip}'],
        check=True)
    run(['snap-proxy', 'generate-keys'], check=True)

    hookenv.open_port(80)
    set_flag('snap-store-proxy.configured')


@when('snap-store-proxy.configured')
@when_not('snap-store-proxy.registered')
def check_registration():
    try:
        result = run(['snap-proxy', 'status'], check=True, stdout=PIPE)
    except Exception:
        layer.status.maintenance('Failed to run "snap-proxy status"; will retry')
        return
    else:
        data = yaml.safe_load(result.stdout.decode('utf8'))

    store_id = data.get('Store ID')
    if not store_id or 'not registered' in store_id:
        layer.status.blocked(f'Please run: '
                             f'juju ssh {hookenv.local_unit()} '
                             f'"sudo snap-proxy register"')
    else:
        domain = hookenv.unit_public_ip()
        layer.status.active(f'curl -s http://{domain}/v2/auth/store/assertions'
                            f' | sudo snap ack /dev/stdin ; '
                            f'sudo snap set core proxy.store={store_id}')
        set_flag('snap-store-proxy.registered')
