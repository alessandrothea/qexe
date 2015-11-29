#!/usr/bin/env python

import tempfile
import shutil
import os
import sys
import stat
import argparse
import subprocess

from os.path import exists,join,realpath

# usage = 'usage: %prog'
parser = argparse.ArgumentParser()
parser.add_argument('jid',help='Job ID', default=None)
parser.add_argument('-w','--workdir',dest='workdir', default=None, help='Work directory')
parser.add_argument('-q','--queue',dest='queue',help='Queue', default='short.q')
parser.add_argument('-n','--dryrun',dest='dryrun' , help='Dryrun', default=False, action='store_true')
parser.add_argument('cmd', metavar='cmd', nargs='+',
                   help='Commands')
# Let's go
args = parser.parse_args()
if args.jid is None:
    parser.error('Job ID not defined!')

# cmd = ' '.join(args)
cmd = ' '.join(args.cmd)
print 'Preparing the execution of \''+cmd+'\' on the batch system'

cwd = os.getcwd()

# Create a local directory where to store jobs
qdir = join(realpath(args.workdir) if args.workdir is not None else cwd,'qexe',args.jid)

print qdir
# sys.exit(0)

# Cleanup
if exists(qdir):
    shutil.rmtree(qdir)
    print 'Old directory',qdir,'deleted'

# And remake the directory
os.makedirs(qdir)

# Dump the current environment
with open(join(qdir,'environment.sh'),'w') as env:
    for k,v in os.environ.iteritems():
        # Strange patch....
        if k.startswith('BASH_FUNC_module'): continue

        env.write('export '+k+'="'+v+'"\n')

# Script template
script = '''
#!/bin/bash
START_TIME=`date`
cd {qdir}
source environment.sh
cd {cwd}
CMD="{cmd}"
echo $CMD
{cmd}
res=$?
echo Exit code: $res
echo Done on `date` \| $res -  {jid} [started: $START_TIME ]>> qexe.log
'''

stdout = join(qdir,'out.txt')
stderr = join(qdir,'stderr.txt')
runsh = join(qdir,'run.sh')

# print script.format(qdir = qdir, cwd = cwd, cmd=cmd, jid=args.jid)
with open(runsh,'w') as runfile:
    runfile.write(script.format(qdir = qdir, cwd = cwd, cmd=cmd, jid=args.jid))

# set the correct flags
os.chmod(runsh,stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)

# Build qsum command
qcmd = ' '.join([
    # Qsub...
    'qsub',
    # Queue name
    '-q '+args.queue,
    # Not sure, but it must be useful
    '-j y',
    # job id
    '-N '+args.jid,
    # Stdout and stderr destination
    '-o '+stdout,
    '-e '+stderr,
    # And the shell script
    runsh
    ])


print qcmd
# lauch it on qsub
if not args.dryrun:
    subprocess.call(qcmd.split())

