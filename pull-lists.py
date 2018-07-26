#!/usr/bin/env python2

import os, hashlib, urllib, subprocess

pihole_adlists_path = '/etc/pihole/adlists.list'
pihole_addon_lists = 'https://raw.githubusercontent.com/rezgalis/pi-hole-addon/master/blacklists/lists'
pihole_addon_local_blacklist = 'blacklist.list'
custom_adlists_comment = '# pi-hole-addon blacklist'

newlines = []


def sha256_checksum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha256.update(block)
    return sha256.hexdigest()


def check_updates_exist():
        urllib.urlretrieve(pihole_addon_lists, pihole_addon_local_blacklist+'__temp')
        if os.path.exists(pihole_addon_local_blacklist):
                ex_hash = sha256_checksum(pihole_addon_local_blacklist)
                new_hash = sha256_checksum(pihole_addon_local_blacklist+'__temp')
                if ex_hash==new_hash:
                        os.remove(pihole_addon_local_blacklist+'__temp')
                        return False
                else:
                        os.rename(pihole_addon_local_blacklist+'__temp', pihole_addon_local_blacklist)
                        return True
        else:
                os.rename(pihole_addon_local_blacklist+'__temp', pihole_addon_local_blacklist)
                return True


def remove_prev_custom_lists():
        f = open(pihole_adlists_path,"r")
        lines = f.readlines()
        f.close()

        i = 0
        while i < len(lines):
                thisline = lines[i]
                if thisline.startswith(custom_adlists_comment):
                        i = i+1
                else:
                        newlines.append(thisline)
                i = i+1


def write_new_custom_lists():
        f = open(pihole_addon_local_blacklist,"r")
        lines = f.readlines()
        f.close()

        for line in lines:
                if line.startswith('#')==False and len(line)>1:
                        newlines.append(custom_adlists_comment + '\n')
                        newlines.append(line)

        f = open(pihole_adlists_path, 'wb')
        f.writelines(newlines)
        f.close()

def trigger_pihole_retrieve_lists():
        subprocess.call(["pihole", "-g"])


if check_updates_exist():
        print "Updates found, pulling & refreshing adlists"
        remove_prev_custom_lists()
        write_new_custom_lists()
        trigger_pihole_retrieve_lists()
