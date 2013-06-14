# Python script to submit jobs to SGE where those jobs involve 
# invoking a command on a file, where variables in the file 
# should loop as a function of the job.
# Also allows a specific number of jobs to be submitted and 
# compresses the results of each batch
# Guy Billings 2012
# TODO: -implement full path handling (e.g. specification of location of package files
#       in the payload file). Currently assumed to be in working dir.

import subprocess
import sys
import math
import os
import time
import itertools
import user_variables as uv
import support as fns

slots=1  # Ensure nodes register the number of CPUs used per job
if uv.reconstruct_name is not '':
  reconstruct=True
else:
  reconstruct=False

if reconstruct:
  output_base=uv.reconstruct_name
  print 'Attempting to resume: '+output_base
else:
  now = time.localtime(time.time())
  tstr= time.strftime("%Y-%m-%d.%H-%M-%S", now)
  output_base=uv.output_base+tstr
  fns.output('Setting up jobs at '+tstr+'\n')

# Build index for variables by unrolling 
# the implied loops in uv.var
index=[]
for i in reduce(fns.product,uv.var):
  index.append(i)
index=fns.flatten(index)
n_vars=len(uv.var)	
rshape=[[] for i in range(len(index)/n_vars)]
indexcnt=0
for i in rshape:
  for j in range(n_vars):
    i.append(index[indexcnt])
    indexcnt=indexcnt+1
index=rshape

if reconstruct:
  print "looking for completed jobs..."
  jlist=fns.jobstatus(uv.sc_path,output_base,uv.outex,index,uv.failchar)
  if jlist[2]>0:
    print "found "+str(jlist[2])+" jobs."
    newindex=fns.listcomp(index,jlist[0])
    index=newindex
    print str(len(index))+" jobs remaining."
  else:
    print "failed to find jobs "+output_base+" compatible with variables in configuration file."
    sys.exit(0)

completed=[]
n_jobs=len(index)
n_completed=0
n_failed=0;
n_total=0;
submitted=[]
cleared_up=[]

if uv.localmachine ==1:
  uv.nodes_to_use=n_jobs

jobs_due_this_batch=min(uv.nodes_to_use,n_jobs)
while n_completed<n_jobs:
  #Loop over batch
  for job in range(jobs_due_this_batch):
    istr=fns.indexstr(index[job])
    fns.output("Submitting jobs...")
    fns.output('Generating application files...\n')
    paystr=fns.generate_file(index[job],uv.varstr,uv.payload,uv.appfile,uv.working_dir) 
    payfile=output_base+istr+uv.appex
    pf=open(uv.working_dir+payfile,mode='w') 
    pf.write(paystr) 
    pf.close()
    paystr=fns.generate_file(['"'+uv.sc_path+output_base+istr+uv.outex+'"'],uv.outstr,payfile,uv.appfile,uv.working_dir) 
    pf=open(uv.working_dir+payfile,mode='w') 
    pf.write(paystr) 
    pf.close()
    fns.output('Generating submission scripts...\n')
    commandstr=uv.command+uv.working_dir+payfile+uv.cmdterminator
    batchfile=output_base+istr+uv.scriptex     
    bf=open(uv.working_dir+batchfile,mode='w')
    bf.write(commandstr)
    bf.close()
    fns.output('Submitting job '+batchfile+'\n')
    if uv.localmachine==1:
      subprocess.call('chmod a+x '+batchfile,shell=True)
      subprocess.call('./'+batchfile,shell=True)
    else:  
      subprocess.call('qsub -v LD_LIBRARY_PATH -e '+uv.output_path+' -o '+uv.output_path+' -l h_rt='+str(uv.seconds)+
                      ' -l tmem='+str(uv.mem)+'G'+' '+batchfile,shell=True)
    time.sleep(0.2)
  
  if uv.localmachine==1:
    n_completed=n_jobs
  else:  
    for s in index[0:jobs_due_this_batch]:
      present=False
      for k in submitted:
        if k==s:
          present=True
      if not present:  
        submitted.append(s)
    index=index[jobs_due_this_batch:len(index)]
  
    time.sleep(10)
    qs=fns.qsize(output_base) 
    while qs>=uv.nodes_to_use:
      qs=fns.qsize(output_base)  
      time.sleep(2)
       
    fns.output('There are '+str(len(submitted))+' jobs to be polled.\n')
    jlist=fns.jobstatus(uv.sc_path,output_base,uv.outex,submitted,uv.failchar)
    if len(submitted[0])>0:
      for s in jlist[0]:
        completed.append(s)
        for s in jlist[1]:
          index.append(s)
    n_completed=n_completed+jlist[2]
    n_failed=n_failed+jlist[3]
    denom=n_completed+n_failed;
    if denom!=0:
      srate=float(n_completed)/float(n_completed+n_failed)
    else:
      srate=0
    crate=float(n_completed+n_total)/float(n_jobs)
    fns.output('There are '+str(len(completed))+' completed jobs for this network.\n')
    fns.output(str(n_failed)+' jobs have failed, success rate = '+str(srate)+'\n')
    fns.output('Overall run progress: '+str(crate)+'\n')
    submitted=fns.listcomp(submitted,jlist[0])
    submitted=fns.listcomp(submitted,jlist[1])
    fns.output('There are '+str(len(submitted))+' queued jobs.\n')
    if uv.compress==True:
     cleared_up=fns.manage_files(completed,cleared_up,[uv.compvar,len(uv.var[uv.compvar]),len(rshape[0])],output_base,uv.sc_path,uv.outex)
    
    jobs_due_this_batch=uv.nodes_to_use-fns.qsize(output_base)
    if jobs_due_this_batch>len(index):
      jobs_due_this_batch=len(index)  
      
