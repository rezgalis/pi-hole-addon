#!/usr/bin/env python2

import sys, os, hashlib, subprocess, shutil
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
        print 'Changes in repo detected'
		repo.config_writer().set_value('user', 'name', 'default.repo').release()
		repo.config_writer().set_value('user', 'email', 'default.repo').release()
		repo.git.stash()
		repo.git.merge()



def sha256_checksum(filename, block_size=65536):
	sha256 = hashlib.sha256()
	with open(filename, 'rb') as f:
		for block in iter(lambda: f.read(block_size), b''):
			sha256.update(block)
	return sha256.hexdigest()



def check_addon_lists_updated():
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



def check_updates_exist():
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



fetch_from_github()

if check_updates_exist():
	print "Updates found for list of lists"
	remove_prev_custom_lists()
	write_new_custom_lists()
	check_addon_lists_updated() #to copy actual lists
	trigger_pihole_retrieve_lists()
	sys.exit()

if check_addon_lists_updated():
	print "Updates found for individual adlists"
	trigger_pihole_retrieve_lists()
	sys.exit()

#this job runs every hour
#it pulls data from github repository and evaluates whether any list data have changes; if so, pi-hole lists refresh is triggered

