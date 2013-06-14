#Support functions for script management
import sys
import os
import time
import subprocess

def qsize(jobstr):
  # Returns number of queued jobs  
  os.system('qstat -r  | grep '+jobstr+' | wc -l > queued_jobs')
  time.sleep(1)
  f=open('queued_jobs','r')
  numq=f.read()
  f.close()
  #os.system('rm queued_jobs')
  if int(numq) != 0:
    numq=str(int(numq)-2)
  return int(numq)
  
def output(message):
  sys.stdout.write(message)
  sys.stdout.flush()
  
def indexstr(variables):
  indexstring=''
  for var in variables:
    indexstring=indexstring+'_'+str(var)
  return indexstring

def jobstatus(path,base,ext,checkindex,failchar):
  out=[[],[],[],[]]
  failedlist=[]
  completedlist=[]
  completed=0
  failed=0
  if len(checkindex[0])>0:
    for file in checkindex:
      fname=path+base+indexstr(file)+ext
      if os.access(fname,os.R_OK):
        fcnt=0
        ecnt=0
        while fcnt<100:
          try:
            f=open(fname,'r')
            firstline=f.readline()
            if len(firstline)>0:  
              break
            else:
              time.sleep(1)     
          except IOError:
            time.sleep(0.2)        
            fcnt=fcnt+1
        if fcnt==100:
          output('File error on '+fname+'\n')
        
        fchar=False
        for c in failchar:
          if firstline[0]==c:
            fchar=True

        if fchar:
          output('Job '+fname+' failed!'+'\n')
          failedlist.append(file)
          failed=failed+1
        else:
          completedlist.append(file)
          completed=completed+1
    out[0]=completedlist
    out[1]=failedlist
    out[2]=completed
    out[3]=failed
  else:
    out[2]=0
    out[3]=0
  return out

def listcomp(l1,l2): 
  # returns the complement of list l2 in l1
  out=[]
  tcnt=0
  for x1 in l1:
    tv=True
    for x2 in l2:
      tv=tv&(x1!=x2)
    if tv==True:  
      out.append(x1)
  return out    
  
def flatten(x):
    """flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, MyVector(8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]
    From: http://kogs-www.informatik.uni-hamburg.de/~meine/python_tricks
    02/02/2012
    """
    result = []
    for el in x:
        #if isinstance(el, (list, tuple)):
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result   
    
def generate_file(variables,varstr,payfile,appfile,path):
  output=''
  nvars=len(variables)
  #Open file
  payload=open(path+payfile)
  #Readline of file
  for thisline in payload:
    for var in range(nvars):
      thisline=thisline.replace(varstr+str(var),str(variables[var]))
      #Catch end of line case
      thisline=thisline.replace(varstr+str(var)+'\n',str(variables[var])+'\n')
    #Write line to return data structure  
    output=output+thisline  
  appendstr='<<\"'+path+appfile+'\"\n'  
  if thisline!=appendstr:
    output=output+appendstr
  payload.close()  
  return output 
  
def remove_dups(s):
# remove duplicate entries in a list of lists
  u = []
  for x in s:
    if x not in u:
      u.append(x)
  return u

def complete_list(query_list, varls):
# split list of items into a list of lists of complete sets
# complete set shows full range of the variable index in question
  var_index=varls[0]
  complete_number=varls[1] 
  nvars=varls[2]
  testlist=[]
  dexlist=[]
  outlist=[]
  for dex in range(nvars):
    if dex!=var_index:
      dexlist.append(dex)
  for val in query_list:
    testlist.append([val[i] for i in dexlist])
  uniqueitems=remove_dups(testlist)
  for ui in uniqueitems:
    count=testlist.count(ui)
    if count==complete_number: 
      outlist.append([query_list[j] for j in [i for i,x in enumerate(testlist) if x == ui]])
  return outlist
  
def zipdex(variables,vardex):
# create a string that has wildcards for the fixed variables (i.e. those not having index vardex)
  out=""
  for i in range(len(variables)):
    if i!=vardex:
      out=out+'_'+str(variables[i])
    else:
      out=out+'_*'
  return out
  
def manage_files(completed_jobs,cleared_up,varls,filebase,path,extension):
# function to look for completed runs of variables and compress them, deleting the 
# original files
# varls is a list containing specification of criteria for completion of a 
# variable: [index of variable to be compressed over, number of files in a complete set for this variable,
# number of variables in the job index] 
  to_check=listcomp(completed_jobs,cleared_up)
  # detemine if there are any completed data sets
  completed_sets=complete_list(to_check,varls)
  c_sets=len(completed_sets)
  dexlist=[]
  for dex in range(varls[2]):
    if dex!=varls[0]:
      dexlist.append(dex)
  if c_sets>0:
    dirid=""
    for c_set in completed_sets:
      rmstr=zipdex(c_set[0],varls[0])
      zipstr=path+filebase+rmstr+extension
      dirid=indexstr([c_set[0][i] for i in dexlist])
      dirid=dirid[1:]
      dirstr=path+dirid
      outstr=dirid
      output('Compressing data for '+outstr+'\n')
      subprocess.call('tar -czf '+dirstr+'.tar.bz2'+' '+zipstr,shell=True)
      #output('tar -czf '+dirstr+'.tar.bz2'+' '+zipstr+'\n')
      time.sleep(10)
      subprocess.call('mkdir '+dirstr,shell=True)
      #output('mkdir '+dirstr+'\n')
      time.sleep(1)
      subprocess.call('mv '+zipstr+' '+dirstr,shell=True)
      #output('mv '+zipstr+' '+dirstr+'\n')
      subprocess.call('rm '+filebase+rmstr+'.sh',shell=True)
      #output('rm '+filebase+rmstr+'.sh'+'\n')
      subprocess.call('rm '+filebase+rmstr+'.m',shell=True)
      #output('rm '+filebase+rmstr+'.m'+'\n')
      output(outstr+' done.\n')
      for cj in c_set:
        cleared_up.append(cj)
  return cleared_up    

def product(*args, **kwds):
#      uncomment for version < 2.6 
#      product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
#      product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
#      from http://docs.python.org/library/itertools.html#itertools.product
  pools = map(tuple, args) * kwds.get('repeat', 1)
  result = [[]]
  for pool in pools:
    result = [x+[y] for x in result for y in pool]
  for prod in result:
    yield tuple(prod)

  
  
