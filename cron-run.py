#!/usr/bin/env python2

import sys, os, datetime, hashlib, subprocess, shutil



def sha256_checksum(filename, block_size=65536):
	sha256 = hashlib.sha256()
	with open(filename, 'rb') as f:
		for block in iter(lambda: f.read(block_size), b''):
			sha256.update(block)
	return sha256.hexdigest()



def daily_job_updated():
	if os.path.exists('daily-job.py') and os.path.exists('repo/daily-job.py'):
		ex_checksum = sha256_checksum('daily-job.py') 
		new_checksum = sha256_checksum('repo/daily-job.py')
		if ex_checksum != new_checksum:
			shutil.copy('repo/daily-job.py', 'daily-job.py')
			return True
	elif os.path.exists('repo/daily-job.py'):
		shutil.copy('repo/daily-job.py', 'daily-job.py')
		return True

	return False



def trigger_daily_job():
	subprocess.call(["python", "daily-job.py"])



if __name__== "__main__":
	print "cron-run.py @", datetime.datetime.now()
	if daily_job_updated():
		print "Daily midnight job will be triggered"
		trigger_daily_job()
		sys.exit()
	else:
		sys.exit()

#this job is run at midnight every day
#main purpose of this script is to compare local daily-job.py and one found in repo/ folder (which is latest version, from github); if those are different, local file is overwritten and then executed
