#!/usr/bin/env python2

import sys, os, datetime, hashlib, subprocess, shutil
from git import Repo

git_remote = 'https://github.com/rezgalis/pi-hole-addon.git'
pihole_adlists_path = '/etc/pihole/adlists.list'
custom_adlists_comment = '# pi-hole-addon blacklist'

prevlines = []
newlines = []



def fetch_from_github():
	is_new = False
	try:
		repo = Repo('repo')
	except:
		repo = Repo.init('repo')
		remote = repo.create_remote('origin', git_remote)
		remote.fetch() 
		repo.create_head('master', remote.refs.master).set_tracking_branch(remote.refs.master).checkout()
		is_new = True

	origin = repo.remotes.origin
	origin.fetch()

	checksum_remote = origin.refs.master.commit
	checksum_local = repo.head.commit

	if checksum_remote!=checksum_local or is_new:
		print 'Changes in repo detected @', datetime.datetime.now()
		repo.config_writer().set_value('user', 'name', 'default.repo').release()
		repo.config_writer().set_value('user', 'email', 'default.repo').release()
		repo.git.stash()
		repo.git.merge()
		shutil.copy('repo/cron-run.py', 'cron-run.py')



def sha256_checksum(filename, block_size=65536):
	sha256 = hashlib.sha256()
	with open(filename, 'rb') as f:
		for block in iter(lambda: f.read(block_size), b''):
			sha256.update(block)
	return sha256.hexdigest()



def check_wildcards_updated():
	if os.path.exists('/etc/dnsmasq.d/96-custom-wildcard.conf') and os.path.exists('repo/blacklists/96-custom-wildcard.conf'):
		ex_checksum = sha256_checksum('/etc/dnsmasq.d/96-custom-wildcard.conf') 
		new_checksum = sha256_checksum('repo/blacklists/96-custom-wildcard.conf')
		if ex_checksum != new_checksum:
			shutil.copy('repo/blacklists/96-custom-wildcard.conf', '/etc/dnsmasq.d/96-custom-wildcard.conf')
			return True
	elif os.path.exists('repo/blacklists/96-custom-wildcard.conf'):
		shutil.copy('repo/blacklists/96-custom-wildcard.conf', '/etc/dnsmasq.d/96-custom-wildcard.conf')
		return True
		
	return False



def check_restricted_updated():
	if os.path.exists('/etc/dnsmasq.d/95-restrict.conf') and os.path.exists('repo/blacklists/95-restrict.conf'):
		ex_checksum = sha256_checksum('/etc/dnsmasq.d/95-restrict.conf') 
		new_checksum = sha256_checksum('repo/blacklists/95-restrict.conf')
		if ex_checksum != new_checksum:
			shutil.copy('repo/blacklists/95-restrict.conf', '/etc/dnsmasq.d/95-restrict.conf')
			return True
	elif os.path.exists('repo/blacklists/95-restrict.conf'):
		shutil.copy('repo/blacklists/95-restrict.conf', '/etc/dnsmasq.d/95-restrict.conf')
		return True
		
	return False


def check_adlists_contents_updated():
	updates_found = False
	
	if os.path.exists('blacklists/list.txt'):
		f = open('blacklists/list.txt','r')
		lines = f.readlines()
		f.close()

		files_from_lines = []
		for url in lines:
			if url.startswith('https://') and '/pi-hole-addon/' in url:
				files_from_lines.append(url[url.rfind("/")+1:].replace("\n", ""))

		for f in files_from_lines:
			if os.path.exists('blacklists/'+f) and os.path.exists('repo/blacklists/'+f):
				ex_hash = sha256_checksum('blacklists/'+f)
				new_hash = sha256_checksum('repo/blacklists/'+f)
				if ex_hash != new_hash:
					shutil.copy('repo/blacklists/'+f, 'blacklists/'+f)
					updates_found = True
			elif os.path.exists('repo/blacklists/'+f):
				shutil.copy('repo/blacklists/'+f, 'blacklists/'+f)
				updates_found = True
				
	return updates_found



def check_addlists_updated():
	if os.path.exists('blacklists/list.txt') and os.path.exists('repo/blacklists/list.txt'):
		ex_checksum = sha256_checksum('blacklists/list.txt') 
		new_checksum = sha256_checksum('repo/blacklists/list.txt')
		if ex_checksum != new_checksum:
			shutil.copy('repo/blacklists/list.txt', 'blacklists/list.txt')
			return True
	elif os.path.exists('repo/blacklists/list.txt'):
		shutil.copy('repo/blacklists/list.txt', 'blacklists/list.txt')
		return True
		
	return False



def remove_prev_custom_lists():
	f = open(pihole_adlists_path,'r')
	lines = f.readlines()
	f.close()

	i = 0
	while i < len(lines):
		thisline = lines[i]
		if thisline.startswith(custom_adlists_comment):
			i = i+1
		else:
			prevlines.append(thisline)
		i = i+1



def write_new_custom_lists():
	f = open('blacklists/list.txt','r')
	lines = f.readlines()
	f.close()

	for line in lines:
		if line.startswith('#')==False and len(line)>1:
			newlines.append(custom_adlists_comment + '\n')
			newlines.append(line)

	f = open(pihole_adlists_path, 'wb')
	f.writelines(prevlines)
	f.writelines(newlines)
	f.close()



def trigger_pihole_retrieve_lists():
	subprocess.call(["pihole", "-g"])



if __name__== "__main__":
	fetch_from_github()
	
	if check_wildcards_updated() or check_restricted_updated():
		#TO-DO - need to ensure /etc/hosts is also updated if necessary
		#anything betwween tags "# start pi-hole add-on restrictions" and "# end pi-hole add-on restrictions"
		#hosts file - we cannot rely on checksum, so we'll update it any time wildcards or restricted is updated
		#https://discourse.pi-hole.net/t/use-dns-to-force-youtube-into-restricted-mode-and-pi-hole/1996/23
		subprocess.call(["service", "dnsmasq", " restart"])

	if check_addlists_updated():
		print "Updates found for list of lists"
		remove_prev_custom_lists()
		write_new_custom_lists()
		check_adlists_contents_updated() #to copy actual lists
		trigger_pihole_retrieve_lists()
		sys.exit()

	if check_adlists_contents_updated():
		print "Updates found for individual adlists"
		trigger_pihole_retrieve_lists()
		sys.exit()

#this job runs every hour
#it pulls data from github repository and evaluates whether any list data have changes; if so, pi-hole lists refresh is triggered
