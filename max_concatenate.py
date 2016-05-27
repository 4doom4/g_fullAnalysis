#!/usr/bin/python
import argparse
import os
import sys
import subprocess

# write func to find files

class concatenateTrajectories:
	def __init__(self, folder, trajectoryFileType, checkConcatGroup, systemName, repetition):
		# Check if the correct file type was chosen
		self.trajectoryFileType = self.checkFileType(trajectoryFileType)

		# Check if selected group is correct
		self.concatGroup = self.checkConcatGroup(checkConcatGroup)

		# Get all the trajectory names
		self.trajectories = self.checkCorrectFolder(folder, trajectoryFileType)

		# Get the individual trajectory length
		self.trajectoriesLength = self.findTrajectoryLength()

		# System name
		self.systemName = systemName

		# Repetition
		self.repetition = repetition

		# TPR file for this series
		self.tprFile = ""

	def findFilesOfType(self, path, filetype):
		foundFiles = []

		# If path is necessary check if there is a final /
		if not path == "":
			if path[-1] != "/":
				path = "%s/"%path

		files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

		# Loop over all path
		for file in files:
			# IF path is necessary add it to file name
			if not path == "":
				fileAndPath = path+file
			# only show file of the filetype chosen and which do not start with a .
			if fileAndPath.endswith(".%s"%filetype) and file[0] != '.':
				foundFiles.append(fileAndPath)

		# Return files found
		return foundFiles


	def concatenate(self):
		# To concatenate the trajectories we need to find the timestamps of the trajectories
		# It starts at 0
		timeStamp = [0]
		for currentLength in self.trajectoriesLength:
			timeStamp.append(timeStamp[-1]+currentLength)
		
		# We do not need the last time stamp 
		del timeStamp[-1]

		# Time stamp string for the GROMACS concatenate tool
		timeStampString = '\n'.join(str(e) for e in timeStamp)

		# Trjactory path string for the GROMACS concatenate tool
		trajectoryPath = ' '.join(self.trajectories)

		# Find the tpr file
		tprFiles = self.findFilesOfType(os.path.split(self.trajectories[0])[0], "tpr")
		if len(tprFiles) != 1:
			sys.exit("Found %s tpr files in folder %s. Please make sure only the correct tpr file is present")
		else:
			self.tprFile = tprFiles[0]

		# Generate an index file for the concatenate tool to ask for the group to use in the new trajectory
		makeNDXProgram = self.which("make_ndx_mpi")

		# Generate a logfile
		logFile = open("%s_concatenate_rep%i.log"%(self.systemName, self.repetition), 'a')

		# Run the program
		p = subprocess.Popen("echo \"q\" | %s -f %s -o %s_rep%i_protein.ndx"%(makeNDXProgram, self.tprFile, self.systemName, self.repetition), shell=True, stdin=subprocess.PIPE, stdout=logFile, stderr=subprocess.STDOUT)
		p.communicate() #now wait
		
		# Generate the concatenate trajectory
		gmxProgram = self.which("gmx_mpi")

		# Time stamp string for the GROMACS concatenate tool
		timeStampString = "0\n"
		for length in self.trajectoriesLength:
			timeStampString += "%i\n"%(int(timeStampString.split()[-1])+length)

		# Trjactory path string for the GROMACS concatenate tool
		trajectoryPath = ' '.join(self.trajectories)

		p = subprocess.Popen("echo \"1 %s\" | %s trjcat -f %s -settime -o %s_0-%i_rep%i.xtc -n %s_rep%i_protein.ndx"%(timeStampString, gmxProgram, trajectoryPath, self.systemName, sum(self.trajectoriesLength)/1000, self.repetition, self.systemName, self.repetition), shell=True, stdin=subprocess.PIPE, stdout=logFile, stderr=subprocess.STDOUT)
		p.communicate() #now wait

	def which(self, program):
		def is_exe(fpath):
			return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

		fpath, fname = os.path.split(program)
		if fpath:
			if is_exe(program):
				return program
			elif is_exe("%s_mpi"%program):
				return "%s_mpi"%program
			elif is_exe(program[:len(program)-4]):
				return program[:len(program)-4]
		else:
			for path in os.environ["PATH"].split(os.pathsep):
				path = path.strip('"')
				exe_file = os.path.join(path, program)
				if is_exe(exe_file):
					return exe_file
				elif is_exe("%s_mpi"%exe_file):
					return "%s_mpi"%exe_file
				elif is_exe(exe_file[:len(exe_file)-4]):
					return exe_file[:len(exe_file)-4]
		return False

	def checkConcatGroup(self, group):
		# Define the supported groups
		supportedGroupTypes = {"system" : 0, "protein" : 1, "non-water" : 14}

		if group.lower() in supportedGroupTypes:
			return supportedGroupTypes[group.lower()]
		else:
			sys.exit("The group %s is not supported"%group)

	def checkFileType(self, filetype):
		# Define the supported file types
		supportedFileTypes = ["xtc", "trr"]

		# Check if the file type is supported
		if filetype in supportedFileTypes:
			return filetype
		else:
			sys.exit("The file type %s is not supported"%filetype)

	def checkCorrectFolder(self, folder, filetype):
		# Check if the chosen folder exists
		if not os.path.exists(folder):
			sys.exit("%s does not exist"%folder)

		trj_files = []

		# Look for trajectory files
		for root, dirs, files in os.walk(folder):
			foundTrjFile = self.findFilesOfType(root, filetype)

			# If we find more than one file stop
			if len(foundTrjFile) > 1:
				sys.exit("There are multiple %s files in the folder %s"%(filetype, root))

			# If there is no file in the folder continue
			elif len(foundTrjFile) == 0:
				continue
			# If there is one file add it to the trajectories
			trj_files.append(foundTrjFile[0])
		# Verify if we found some trajectories
		if len(trj_files) == 0:
			sys.exit("No trajectory files of type %s in %s and it's subfolders found"%(filetype, folder))
		return trj_files

	def findTrajectoryLength(self):
		# Find the correcy log file and the length in the log file
		trj_length = []

		# Find all log files in all trajectory folders
		for trajectory in self.trajectories:
			trajectoryPath = os.path.split(trajectory)[0]
			
			logFiles = self.findFilesOfType(trajectoryPath, "log")

			# Search for the correct log file
			trj_logFile = ""
			for logFile in logFiles:
				with open(logFile, 'r') as inF:
					for line in inF:
						# Search for the first line in a standard trajectory output
						if "Log file opened on" in line:
							trj_logFile = logFile
							break
			# if the standard trajectory output was not found no log file for the trajectory
			if trj_logFile == "":
				sys.exit("Could not find the log file for %s"%trajectory)

			# If we found the trajectory extract the length dt*nsteps
			else:
				with open(logFile, 'r') as inF:
					for line in inF:
						if ' dt ' in line:
							sizeOfSteps = float(line.split()[2])
						if 'nsteps' in line:
							numberOfSteps = int(line.split()[2])
							break
					trj_length.append(int(sizeOfSteps*numberOfSteps))
		return trj_length

##### GETTER ######

	# Get the trajectory length and name
	def getTrajLength(self):
		trajLength = []
		for index, value in enumerate(self.trajectories):
			trajLength.append([value, self.trajectoriesLength[index]])
		return trajLength

if __name__ == "__main__":

	#####################################
	#									#
	# The help text						#
	#									#
	#####################################

	parser = argparse.ArgumentParser(description="""
	g_trajAnal
	Maximilian Ebert 2016

	This tool let's you analyse and concatenate GROMACS trajectories based 
	on the data structure described in my GROMACS simulation tutorial. You
	must follow the same folder and file nomenclature so that this script
	works out of the box. Otherwise you have to tinker with the code. 

	""", formatter_class=argparse.RawDescriptionHelpFormatter)

	# Definition of arguments

	# Trajectory file or folder holding sub directories with trajectories
	parser.add_argument("-cf", metavar="[<folder to .xtc/.trr>] (Input)", help="Concatenate trajectories in folder", required=True)
	parser.add_argument("-ct", metavar="(xtc) ", help="Concatenate input file type: xtc, trr", default="xtc")
	parser.add_argument("-cg", metavar="(protein) ", help="Concatenate groupe: System, Protein, non-Water", default="Protein")
	parser.add_argument("-n", metavar="", help="Name of the system (ex. 1XPB)", required=True)
	parser.add_argument("-r", metavar="(1) ", help="Repetition of run", default=1)
	args = parser.parse_args()

	trj = concatenateTrajectories(args.cf, args.ct, args.cg, args.n, args.r)
	trj.concatenate()








