#!/usr/bin/env python
#
# author "Alessandro Thea"
# version = "1.0.0"
# maintainer "Alessandro Thea"
# email "alessandro.thea@cern.ch"
#

import tempfile
import shutil
import os
import sys
import stat
import argparse
import subprocess

from os.path import exists,join,realpath


#
# Runners
#
class RunnerBase(object):

    def __init__(self, queue, jid, outpath, errpath, script ):
        
        self._queue = queue
        self._jid = jid
        self._outpath = outpath
        self._errpath = errpath
        self._scriptpath = script

    def run(self, go=True):
        cmd = self.getCmd();
        print cmd
        # lauch it on qsub
        if go:
            subprocess.call(cmd.split())

#
# Qsub runner
#
class QRunner(RunnerBase):

    def __init__(self, *args, **kwargs):
        super(QRunner, self).__init__(*args, **kwargs)

    def getCmd(self):
        # Build qsum command
        qcmd = ' '.join([
            # Qsub...
            'qsub',
            # Queue name
            '-q '+self._queue,
            # Not sure, but it must be useful
            '-j y',
            # job id
            '-N '+self._jid,
            # Stdout and stderr destination
            '-o '+self._outpath,
            '-e '+self._errpath,
            # And the shell script
            self._scriptpath
            ])

        return qcmd

#
# Bsub runner
#
class BRunner(RunnerBase):

    def __init__(self, *args, **kwargs):
        super(BRunner, self).__init__(*args, **kwargs)

    def getCmd(self):
        # Build qsum command
        bcmd = ' '.join([
            # Qsub...
            'bsub',
            # Queue name
            '-q '+self._queue,
            # job id
            '-J '+self._jid,
            # Stdout and stderr destination
            '-o '+self._outpath,
            '-e '+self._errpath,
            # And the shell script
            self._scriptpath
            ])

        return bcmd


#
# Writers
#
class ScriptWriterBase(object):

    def __init__(self, qdir, cwd, cmd, jid):
        self._qdir = qdir
        self._cwd  = cwd 
        self._cmd = cmd
        self._jid = jid

    @property
    def stdout(self):
        return join(self._qdir,'out.txt')

    @property
    def stderr(self):
        return join(self._qdir,'stderr.txt')

    def writeRunScript(self):
        template = self.getRunTemplate();
        # print script.format(qdir = qdir, cwd = cwd, cmd=cmd, jid=args.jid)
        with open(self.runsh,'w') as runfile:
            runfile.write(template.format(qdir = self._qdir, cwd = self._cwd, cmd = self._cmd, jid = self._jid))

        # Set correct flags
        os.chmod(self.runsh,
            stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR |
            stat.S_IRGRP | stat.S_IXGRP |
            stat.S_IROTH | stat.S_IXOTH )

#
#  Bash script writer
#
class BashScriptWriter(ScriptWriterBase):

    def __init__(self, *args, **kwargs):
        super(BashScriptWriter, self).__init__(*args, **kwargs)

    @property
    def runsh(self):
        return join(self._qdir,'run.sh')

    def writeEnv(self):
        # Dump current environment
        with open(join(qdir,'environment.sh'),'w') as env:
            env.write('#!/bin/bash\n')
            for k,v in os.environ.iteritems():
                # Strange patch....
                if k.startswith('BASH_FUNC_module'): continue

                env.write('export '+k+'="'+v+'"\n')


    def getRunTemplate(self):
        # Script template
        script = '''#!/bin/bash
START_TIME=`date`
cd {qdir}
source environment.sh
cd {cwd}
CMD="{cmd}"
echo $CMD
{cmd}
res=$?
echo =========================================================
echo Exit code: $res
echo =========================================================
echo Done on `date` \| $res -  {jid} [started: $START_TIME ]>> qexe.log
'''

        return script

#
# TCSH script writer
#
class TcshScriptWriter(ScriptWriterBase):

    def __init__(self, *args, **kwargs):
        super(TcshScriptWriter, self).__init__(*args, **kwargs)

    @property
    def runsh(self):
        return join(self._qdir,'run.csh')

    def writeEnv(self):
        # Dump current environment
        with open(qdir+'/environment.csh','w') as env:
            env.write('#!/bin/tcsh\n')
            for k,v in os.environ.iteritems():
                # Strange patch....
                if k.startswith('BASH_FUNC_module'): continue

                env.write('setenv %s "%s"\n' % (k,v))

    def getRunTemplate(self):
        # prepare the script
        script ='''#!/bin/tcsh
set START_TIME=`date`
cd {qdir}
source environment.csh
cd {cwd}
set CMD="{cmd}"
echo $CMD
{cmd}
set res=$?
echo =========================================================
echo Exit code: $res
echo =========================================================
echo Done on `date` - $res -  {jid} [started: $START_TIME ]>> qexe.log
'''

        return script


runnerMap = {
    'qsub': QRunner,
    'bsub': BRunner,
}


# usage = 'usage: %prog'
parser = argparse.ArgumentParser()
parser.add_argument('jid',help='Job ID', default=None)
parser.add_argument('-w','--workdir',dest='workdir', default=None, help='Work directory')
parser.add_argument('-q','--queue',dest='queue',help='Queue', default='short.q')
parser.add_argument('-n','--dryrun',dest='dryrun' , help='Dryrun', default=False, action='store_true')
parser.add_argument('-e','--engine',dest='engine' , choices=['qsub','bsub'], help='Engine', default='qsub')
parser.add_argument('cmd', metavar='cmd', nargs='+',help='Commands')
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

# Cleanup
if exists(qdir):
    shutil.rmtree(qdir)
    print 'Old directory',qdir,'deleted'

# And remake the directory
os.makedirs(qdir)

writer = BashScriptWriter(qdir, cwd, cmd, args.jid);
# writer = TcshScriptWriter(qdir, cwd, cmd, args.jid);

# Dump current environment
writer.writeEnv()

# Write run script
writer.writeRunScript()

# Create a runner object
runner = runnerMap[args.engine](args.queue, args.jid, writer.stdout, writer.stderr, writer.runsh)

# And Go!
runner.run( not args.dryrun )

