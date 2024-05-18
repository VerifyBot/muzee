# muzee

----

## Running

Run as a module

### Development

#### Run the Webapp

```shell
# Be in /muzee
sanic server:dev --port 6969 --host 0.0.0.0
```

using --single-process because otherwise before_server_close
does not trigger...

### Production

Follow `setup-instructions.md` for setting up the server.

#### Run the Webapp

```shell
# Be in /muzee
sanic server:prod --port 6969 --host 0.0.0.0 --single-process
```
