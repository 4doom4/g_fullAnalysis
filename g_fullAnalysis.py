#!/usr/bin/python
import argparse

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

parser.parse_args()