cloudify-cli-fabric-tasks
=========================

Cloudify's CLI provides an interface to running premade [fabric](http://www.fabfile.org/) tasks on the management server.

As fabric is one of the cli's dependencies, you don't have to install it separately.

Note that the functions don't have to be decorated with the `@task` decorator as they're directly called from the cli's code just like any other python function.

```shell
cfy dev --tasks-file my_tasks.py -v my_task --arg1=something --arg2=otherthing ...
cfy dev -v my_task arg1_value arg2_value ...
```

`--tasks-file my_tasks.py` can be omitted if a `tasks.py` file exists in your current working directory.

So for instance, if you want to echo something in your currently running manager, all you have to do is supply a tasks.py file with the following:

```python
from fabric.api import run

def echo(text):
    run('echo {0}'.format(text))
```

and then run:
```shell
cfy dev echo something!
```

Note that the `dev` command doesn't appear in cfy by default when running `cfy -h`.
You can run `cfy dev -h` for a command reference.

Cloudify provides a tasks [repo]({{ page.cli_fabric_tasks_repo }}) from which users can obtain tasks and to which developers should contribute for the benefit of all.