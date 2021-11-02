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

`{uri_namespace}.derpme.get`

### Set

Sets the value of a given key.

`{uri_namespace}.derpme.set`

### MGet

Returns the value of multiple keys from the storage.

`{uri_namespace}.derpme.mget`

### MSet

Sets the value of multiple keys.

`{uri_namespace}.derpme.mset`

### LGet

Returns the value stored in a list.

`{uri_namespace}.derpme.lget`

### LSet

Sets the value of a list, given it's name.

`{uri_namespace}.derpme.lset`

### Flush

Flushes storage. Can select between flushing runtime memory or persistent
memory.

`{uri_namespace}.derpme.flush`
