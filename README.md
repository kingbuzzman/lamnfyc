# LAMNFYC

## Introduction

This is a complete and total environment isolation for your project. In your project root you create a `lamnfyc.yaml` file and specify any and all dependencies you have, like so:

```
packages:
  - name: python
    version: 2.7.9

  - name: postgres
    version: 9.1.0.0

  - name: node
    version: 6.5.0

  - name: redis
    version: 3.2.3

environment:
  required:
    - SECRET_KEY
    - AWS_ACCESS_KEY_ID

  defaults:
    PGUSER: "postgres"
    PGHOST: "127.0.0.1"
```

Then create an environment: `lamnfyc env`

It will first ask you to set the environment variables, it will default the ones you specified, and ask for the rest.

This will create a folder very much like a `virtualenv` the only difference is that it will have 0 external dependencies.

Are you using `virtualenvwrapper`? Then do `lamnfyc $WORKON_HOME/env`

## Some goodies

Like what you're used to, `source ..../environment_name/bin/activate` sets everything up, and I mean everything. (or `workon environment_name`)

* got postgres? -- it gets started
* got redis? -- it gets started
* got extra environment variables? -- they get initialized

What about `deactivate`? What about it? It works just as you would expect, with the added bonus that it stops the postgres/redis/any other dependency it initialized and any other environment variable it initialized keeping your shell's `env` clean.

## Q & A

Q. Whats with the name?

> working title, not important, carry on.

Q. Why is this?

> this is FULL environment isolation

Q. Why not use `virtualbox` or `vagrant` or `docker`?

> you can, the idea here is that there is no extra layer here + you get the isolation.

Q. Why not use `virtualenv` or `n`/`nvm` or ...?

> you can, this just isolates other dependencies as well, such as redis, postgres..

Q. How fast is this?

> as fast as your computer is

Q. Why not just install just install postgres and redis on my machine globally? Why do I need this?

> simple, you have a lot of projects, and will have more what happens to that project you abandoned when the latest version of postgres was 9.0 but now they're on 10.0 and you want to kick it back up? But your environment has changed, this makes a snapshot and keeps you isolated. Or maybe you have two projects, one of them is using postgres 9.1 and the other is using 9.4, what do you do now?

Q. Can I use this in linux?

> no.

Q. Can I use this in windows?

> no.
