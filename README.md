# derp-me
DEvice Remote Persistent MEmory

Key-value storage, with network access.
Mainly used for developing smart devices in Linux environments.

## Install

Simply execute:

```
pip install .
```

## Available Services

### Get

Returns the value stored in a given key from the in fast key-value storage.

`{uri_namespace}.get`

where `uri_namespace` defaults to `derpme`.

### Set

Sets the value of a given key.

`{uri_namespace}.set`

where `uri_namespace` defaults to `derpme`.

### MGet

Returns the value of multiple keys from the storage.

`{uri_namespace}.mget`

where `uri_namespace` defaults to `derpme`.

### MSet

Sets the value of multiple keys.

`{uri_namespace}.mset`

where `uri_namespace` defaults to `derpme`.

### LGet

Returns the value stored in a list.

`{uri_namespace}.lget`

where `uri_namespace` defaults to `derpme`.

### LSet

Sets the value of a list, given it's name.

`{uri_namespace}.lset`

where `uri_namespace` defaults to `derpme`.

### Flush

Flushes storage. Can select between flushing runtime memory or persistent
memory.

`{uri_namespace}.flush`

where `uri_namespace` defaults to `derpme`.
