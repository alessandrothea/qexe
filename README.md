qexe
====

Helper script to submit jobs on qsub batch system.
```
usage: qexe.py [-h] [-w WORKDIR] [-q QUEUE] [-n] jid cmd [cmd ...]

positional arguments:
  jid                   Job ID
  cmd                   Commands

optional arguments:
  -h, --help            show this help message and exit
  -w WORKDIR, --workdir WORKDIR
                        Work directory
  -q QUEUE, --queue QUEUE
                        Queue
  -n, --dryrun          Dryrun
```
