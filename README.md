# Snap Store Proxy charm

This charm is for basic testing with the [snap-store-proxy][].

It requires postgresql and can be deployed with:

```yaml
series: bionic
applications:
  postgresql:
    charm: cs:postgresql
    num_units: 1
  snap-store-proxy:
    charm: /path/to/snap-store-proxy
    num_units: 1
    expose: true
relations:
  - [snap-store-proxy, postgresql:db-admin]
```

Once deployed, the charm will prompt via status to perform the manual
registration step using:

```
juju ssh {unit} "sudo snap-proxy register"
```

Once registration completes, the status will give you the commands
to activate the snap store proxy on your machine, which are:

```
curl -s http://{domain}/v2/auth/store/assertions | sudo snap ack /dev/stdin
sudo snap set core proxy.store={store_id}
```

The `{domain}` is the public address of this charm, and the `{store_id}` will
be included in the status, or can be retrieved using:

```
juju ssh {unit} "snap-proxy status"
```

You can then create or delete overrides using the actions:

```
juju run-action --wait {unit} create-override snap=kubectl channel=1.16/stable rev=1202
juju run-action --wait {unit} delete-override snap=kubectl channel=1.16/stable
```


[snap-store-proxy]: https://docs.ubuntu.com/snap-store-proxy/en/
