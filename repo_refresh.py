#!/usr/bin/env python2

import sys, os, hashlib, urllib, subprocess

pihole_adlists_path = '/etc/pihole/adlists.list'
pihole_addon_lists_folder = 'https://raw.githubusercontent.com/rezgalis/pi-hole-addon/master/blacklists/'
pihole_addon_local_blacklist_folder = 'blacklists/'
custom_adlists_comment = '# pi-hole-addon blacklist'

prevlines = []
newlines = []


def sha256_checksum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha256.update(block)
    return sha256.hexdigest()


def check_addon_lists_updated():
        updates_found = False

        if os.path.exists(pihole_addon_local_blacklist_folder+'blacklist.list'):
                f = open(pihole_addon_local_blacklist_folder+'blacklist.list',"r")
                lines = f.readlines()
                f.close()

                files_from_lines = []
                for url in lines:
                        if url.startswith('https://'):
                                files_from_lines.append(url[url.rfind("/")+1:].replace("\n", ""))


                for file in files_from_lines:
                        urllib.urlretrieve(pihole_addon_lists_folder+file, pihole_addon_local_blacklist_folder+file+'__temp')

                        if os.path.exists(pihole_addon_local_blacklist_folder+file):
                                ex_hash = sha256_checksum(pihole_addon_local_blacklist_folder+file)
                                new_hash = sha256_checksum(pihole_addon_local_blacklist_folder+file+'__temp')
                                if ex_hash==new_hash:
                                        os.remove(pihole_addon_local_blacklist_folder+file+'__temp')
                                else:
                                        os.rename(pihole_addon_local_blacklist_folder+file+'__temp', pihole_addon_local_blacklist_folder+file)
                                        updates_found = True
                        else:
                                os.rename(pihole_addon_local_blacklist_folder+file+'__temp', pihole_addon_local_blacklist_folder+file)
                                updates_found = True
        return updates_found


def check_updates_exist():
        urllib.urlretrieve(pihole_addon_lists_folder+'lists', pihole_addon_local_blacklist_folder+'blacklist.list__temp')
        if os.path.exists(pihole_addon_local_blacklist_folder+'blacklist.list'):
                ex_hash = sha256_checksum(pihole_addon_local_blacklist_folder+'blacklist.list')
                new_hash = sha256_checksum(pihole_addon_local_blacklist_folder+'blacklist.list__temp')
                if ex_hash==new_hash:
                        os.remove(pihole_addon_local_blacklist_folder+'blacklist.list__temp')
                        return False
                else:
                        os.rename(pihole_addon_local_blacklist_folder+'blacklist.list__temp', pihole_addon_local_blacklist_folder+'blacklist.list')
                        return True
        else:
                os.rename(pihole_addon_local_blacklist_folder+'blacklist.list__temp', pihole_addon_local_blacklist_folder+'blacklist.list')
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
                        prevlines.append(thisline)
                i = i+1


def write_new_custom_lists():
        f = open(pihole_addon_local_blacklist_folder+'blacklist.list',"r")
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


if check_updates_exist():
        print "Updates found for list of lists"
        remove_prev_custom_lists()
        write_new_custom_lists()
        trigger_pihole_retrieve_lists()
        sys.exit()

if check_addon_lists_updated():
        print "Updates found for individual adlists"
        trigger_pihole_retrieve_lists()
        sys.exit()

#this job should run every 30 minutes
