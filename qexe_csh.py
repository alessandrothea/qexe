#!/usr/bin/env python

import tempfile
import os.path
import sys
import stat
import optparse

usage = 'usage: %prog -t <tag> "commands"'
parser = optparse.OptionParser(usage)
parser.add_option('-t','--tag'   ,dest='tag'    , help='Tag '  , default=None)
parser.add_option('-q','--queue' ,dest='queue'  , help='Queue' , default='short.q')
parser.add_option('-n','--dryrun',dest='dryrun' , help='Dryrun', default=False, action='store_true')

(opt, args) = parser.parse_args()
if opt.tag is None:
    parser.error('Tag not defined!')

tag = opt.tag
queue = opt.queue

cmd = ' '.join(args)
print 'Preparing the execution of',cmd,'on the batch system'

prefix = os.getenv("HOME")+'/tmp/qexe/'
os.system('mkdir -p '+prefix)
# tmpdir = tempfile.mkdtemp(prefix=prefix+'tmp_'+tag+'_')
tmpdir = prefix+'/'+tag+'_qexe'
if not os.path.exists(tmpdir):
    os.makedirs(tmpdir)

cwd = os.getcwd()

# dump the current environment
env = open(tmpdir+'/environment.csh','w')
env.write('#!/bin/tcsh\n')
for k,v in os.environ.iteritems():
    env.write('setenv %s "%s"\n' % (k,v))
env.close()


stdout = tmpdir+'/out.txt'
if os.path.exists(stdout):
    os.remove(stdout)

stderr = tmpdir+'/err.txt'
if os.path.exists(stderr):
    os.remove(stderr)
# prepare the script
script ='''#!/bin/tcsh
set START_TIME=`date`
mkdir -p $TMP
cd {tmpdir}
source environment.csh
cd {cwd}
set CMD="{cmd}"
echo $CMD
{cmd}
set res=$?
echo =========================================================
echo Exit code: $res
echo =========================================================
echo `date` - $res -  {tag} [started: $START_TIME ]>> qexe.log
'''
# print script.format(tmpdir = tmpdir, cwd = cwd, cmd=cmd, tag=tag)
run = open(tmpdir+'/run.csh','w')
run.write(script.format(tmpdir = tmpdir, cwd = cwd, cmd=cmd, tag=tag))
run.close()
# set the correct flags
os.chmod(tmpdir+'/run.csh',stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
# lauch it on qsub
if not opt.dryrun:
    os.system('qsub -q '+queue+' -j y -N '+tag+' -o '+tmpdir+'/out.txt -e '+tmpdir+'/err.txt '+tmpdir+'/run.csh')
print tmpdir

