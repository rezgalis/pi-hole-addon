#!/usr/bin/env python2

import sys, os, datetime, hashlib, subprocess, shutil



if __name__== "__main__":
	subprocess.call(["touch", "hello-new.txt"])
	subprocess.call(["cp", "repo/repo-refresh.py", "repo-refresh.py"])

	
# this job is triggered via cron-run.py only if local daily-job.py is different from daily-job.py in repo (and, if so, cron-run.py copies new contents and then executes this script)
#this script is intended to trigger any extra updates needed (e.g. apt-get update && apt-get upgrade) 
