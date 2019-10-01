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
relations:
  - [snap-store-proxy, postgresql:db-admin]
```

Once deployed, the charm will prompt via status to perform the manual
registration step using `juju ssh {unit} "sudo snap-proxy register"`.
Once registration completes, the status will give you the commands
to activate the snap store proxy on your machine, which are:

```
curl -s http://{domain}/v2/auth/store/assertions | sudo snap ack /dev/stdin
sudo snap set core proxy.store={store_id}
```

The `{domain}` is the public address of this charm, and the `{store_id}` will
be included in the status, or can be retrieved with `juju ssh {unit} "snap-proxy status"`.


[snap-store-proxy]: https://docs.ubuntu.com/snap-store-proxy/en/
