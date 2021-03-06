#!/usr/bin/python
#!/usr/bin/env python

"""Parse files generated by piped output from Invoke-Mimikatz.ps1"""

import logging
import argparse
import sys
import os
import readline

#################################################
#                    Variables                  #
#################################################
__author__ = "Russel Van Tuyl"
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Russel Van Tuyl"
__email__ = "Russel.VanTuyl@gmail.com"
__status__ = "Development"
logging.basicConfig(stream=sys.stdout, format='%(asctime)s\t%(levelname)s\t%(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S %p', level=logging.DEBUG)  # Log to STDOUT
script_root = os.path.dirname(os.path.realpath(__file__))
readline.parse_and_bind('tab: complete')
readline.set_completer_delims('\t')

#################################################
#                   COLORS                      #
#################################################
note = "\033[0;0;33m-\033[0m"
warn = "\033[0;0;31m!\033[0m"
info = "\033[0;0;36mi\033[0m"
question = "\033[0;0;37m?\033[0m"

parser = argparse.ArgumentParser()
parser.add_argument('-F', '--file', type=argparse.FileType('r'), help="Mimikatz output file")
parser.add_argument('-D', '--directory', help="Directory containing Mimikatz output files")
# parser.add_argument('-O', '--output', help="File to save username and password list")
parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Verbose Output")
args = parser.parse_args()


def parse_file(f):
    """Parse a text file for hashes"""

    users = {}
    # users = {SID{username: <username>, domain: <domain>, LM: <LM>, NTLM:<NTLM>}}
    username = None
    domain = None
    SID = None
    print "["+note+"]Parsing " + f
    mimikatz_file = open(f, "r")
    mimikatz_file_data = mimikatz_file.readlines()
    for line in mimikatz_file_data:
        # print line
        if line.startswith('User Name         : '):
            # print "["+info+"]Found User: " + line[20:]
            if line.endswith("$\r\n") or line.endswith('LOCAL SERVICE\r\n') or line.endswith('(null)\r\n'):  # Filter out Machine accounts
                username = None
                domain = None
                SID = None
            else:
                username = line[20:].rstrip('\r\n')
        if line.startswith('Domain            : ') and username is not None:
            # print "["+info+"]Found Domain: " + line[20:]
            if line.endswith('NT AUTHORITY\r\n'):
                username = None
                domain = None
                SID = None
            else:
                domain = line[20:].rstrip('\r\n')
        if line.startswith('SID               : ') and username is not None:
            # print "["+info+"]Found SID: " + line[20:]
            SID = line[20:].rstrip('\r\n')
            if SID not in users:
                if args.verbose:
                    print "["+info+"]Found User: " + domain + "\\" + username
                users[SID] = {'username': username, 'domain': domain}
        if line.startswith('	 * LM       : ') and username is not None:
            if args.verbose and 'LM' not in users[SID].keys():
                print "\t["+info+"]LM HASH: " + line[15:]
            users[SID]['LM'] = line[15:].rstrip('\r\n')
        if line.startswith('	 * NTLM     : ') and username is not None:
            if args.verbose and 'NTLM' not in users[SID].keys():
                print "\t["+info+"]NTLM Hash: " + line[15:]
            users[SID]['NTLM'] = line[15:].rstrip('\r\n')
        if line.startswith('	 * Password : ') and username is not None:
            if 'password' not in users[SID].keys():
                if args.verbose and 'password' not in users[SID].keys():
                    print "\t["+info+"]Password: " + line[15:]
                # print "\t["+note+"]Creds: " + domain + "\\" + username + ":" + line[15:]
                users[SID]['password'] = line[15:].rstrip('\r\n')
        # raw_input("Press Enter")

    if args.file:
        print_user_pass(users)
    elif args.directory:
        return users


def parse_directory():

    users = {}
    files = None
    if os.path.isdir(os.path.expanduser(args.directory)):
        files = os.listdir(args.directory)

    if files is not None:
        for f in files:
            temp = parse_file(os.path.join(os.path.expanduser(args.directory), f))
            users.update(temp)

    print_user_pass(users)


def print_user_pass(users):
    """Print recovered user accounts and credentials to the screen"""

    for u in users:
        if 'password' in users[u].keys():
            if len(users[u]['password']) < 100:  # Use this to exclude Kerberos data
                print "["+warn+"]" + users[u]['domain'] + "\\" + users[u]['username'] + ":" + users[u]['password']


if __name__ == '__main__':
    try:
        if args.file:
            creds = parse_file(args.file.name)
        elif args.directory:
            parse_directory()
        else:
            print "["+warn+"]No arguments provided!"
            print "["+warn+"]Try: python " + __file__ + " --help"
    except KeyboardInterrupt:
        print "\n["+warn+"]User Interrupt! Quitting...."
    except:
        print "\n["+warn+"]Please report this error to " + __maintainer__ + " by email at: " + __email__
        raise