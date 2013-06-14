# User variables for job management script

# Simulation setup
localmachine=0						#If 1, then sets up for local machine (no SGE or queue management)
nodes_to_use=250					#Determines number of submissions to split those jobs over	
output_path='~/jobs' 				#Directory into which qsub places its output files (must exist)
working_dir='/home/ucgbgbi/data/BPN_v0.5/Cnet/theory_compare/' 	#Directory in which this file and all companion files are located	
sc_path='/home/ucgbgbi/data/BPN_v0.5/Cnet/theory_compare/'      #Simulation data output directory
output_base='correlations_'				#Base names for simulation output files
seconds=40000							#Execution timelimit per job
mem=3					 				#Memory requested to run job (Gb)
payload='theory_compare.pay'			#File holding application specific procedure
appfile='theory_compare.m'				#File holding application commands

#List loop varaibles, var[1], var[2], ..., var[N]. Increasing index indicates deeper loop
#Each loop variable is set to the list of values over which it should loop
var=[]
#loop for variable 1:
var.append([40])
#loop for variable 2:
var.append([0.005+x*0.005 for x in range(199)])
#var.append([0.1,0.2])
#var.append([(x+1) for x in range(2)])
#loop for variable 3:
var.append([(x+1) for x in range(20)])
#loop for variable 4:
var.append([2])
#var.append([1,2])

#Command to apply to payload on each compute node
failchar=['I','$']
command='/share/apps/Mathematica/Executables/math -noprompt -nodisplay -run \"<<\"'
cmdterminator='\"\"\n'
varstr='*@*@VAR'				#Placeholder for variable insertion to payload
							    #should be CHOSEN SENSIBLY
outstr='*@*@OUTPUTFILE'			#Placeholder for output filename
									
scriptex='.sh' 					#Script file extension
outex='.dat'					#Output file extension
appex='.m'						#Application file extension

compress=True					#Clear up simulation files and compress data
compvar=1						#Variable over which to compress

reconstruct_name='correlations_2013-05-02.16-08-59'			#If string is supplied it is treated as the basename 
								#from which to attempt reconsruction of a halted set of jobs

print 'User specified variables imported'
