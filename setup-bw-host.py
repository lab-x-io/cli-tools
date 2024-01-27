import os
import subprocess
import sys
import re
import shutil

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command '{command}': {e.stderr.decode().strip()}")
        sys.exit(1)

def check_bw_installation():
    if not shutil.which('bw'):
        print("Bitwarden CLI 'bw' is not installed.")
        print("Attempting to download and install Bitwarden CLI...")

        BW_CLI_URL = "https://vault.bitwarden.com/download/?app=cli&platform=linux"
        run_command(f"wget '{BW_CLI_URL}' -O bw.zip")
        run_command("unzip bw.zip -d bw-cli")
        run_command("sudo mv bw-cli/bw /usr/local/bin/bw")
        run_command("rm -rf bw.zip bw-cli")

        if not shutil.which('bw'):
            print("Failed to install Bitwarden CLI. Please install it manually.")
            sys.exit(1)

def create_setup_script():
    with open('.lab-x/.sh', 'w') as file:
        file.write("#!/bin/sh\n")
        file.write("echo 'Log in to Bitwarden'\n")
        file.write("bw login\n")
        file.write("echo 'After logging in, run: export BW_SESSION=...'\n")
    print("Created sh .lab-x/setup.sh. Please run it to log in to Bitwarden.")

def check_bw_login_status():
    status_output = run_command('bw status')
    if not status_output or '"status":"unlocked"' not in status_output:
        create_setup_script()
        sys.exit(0)

def bw_ensure_login():
    status_output = run_command('bw status')
    if '"status":"unlocked"' not in status_output:
        print("Your session is locked or in an unknown state. Please unlock your vault.")
        sys.exit(1)

def get_hostname():
    return run_command('hostname')

def folder_exists(folder_name):
    folders = run_command(f'bw list folders')
    return f'"name":"{folder_name}"' in folders

def create_folder_if_not_exists(folder_name):
    if not folder_exists(folder_name):
        folder_object = run_command(f'bw get template folder | jq -r --arg name "{folder_name}" \'.name = $name\' | bw encode')
        run_command(f'bw create folder "{folder_object}"')
        print(f"Folder '{folder_name}' created.")

def determine_host_folder():
    host_name = get_hostname()
    if re.search('codespaces-', host_name):
        # Assuming the current directory is the git repository for codespaces hosts
        git_repo_name = os.path.basename(os.getcwd())
        return f"github/{git_repo_name}"
    else:
        return f"hosts/{host_name}"

def create_subfolders(base_folder):
    subfolders = ["codespaces", "workflow", "environment"]
    for subfolder in subfolders:
        full_folder_name = f"{base_folder}/{subfolder}"
        create_folder_if_not_exists(full_folder_name)

# Main Execution
check_bw_installation()
check_bw_login_status()
bw_ensure_login()
host_folder = determine_host_folder()
create_folder_if_not_exists(host_folder)
create_subfolders(host_folder)

print(f"Setup completed for {host_folder}")
