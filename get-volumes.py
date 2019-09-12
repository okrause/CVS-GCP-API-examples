#!/usr/bin/env python3
# Query CVS volumes in GCP
# If volume is in state error, offer to delete it
# Run from GCP Cloud Shell

import google.auth
import google.auth.transport.requests
import requests
import json
from os import getenv, path
from sys import exit
from pprint import pprint
from google.auth import jwt
from google.oauth2 import service_account
from google.oauth2 import id_token

regions = ("us-west2", "europe-west3", "us-east4", "us-central1")

# Small utility function to convert bytes to gibibytes
def convertToGiB(bytes):
    return bytes/1024/1024/1024

def yes_or_no(question):
    print(question)
    answer = None
    while answer not in ("yes", "no"):
        answer = input("Enter yes or no: ")
        if answer == "yes":
            return True
        elif answer == "no":
            return False
        else:
            print("Please enter yes or no.")

# Check if we run from Cloud Shell
if getenv('CLOUD_SHELL', None) == None:
    print("ERROR: Please run this script from GCP Cloud Shell and make sure it is configured to the correct project.")
    exit(1)

# Check if DEVSHELL_PROJECT_ID is set
project_id = getenv('DEVSHELL_PROJECT_ID', None)
if project_id == None:
    print("ERROR: Please run this script from GCP Cloud Shell and make sure it is configured to the correct project.")
    exit(1)
else:
    print("INFO: Running for project: ", project_id)

# Set common variables
audience = 'https://cloudvolumesgcp-api.netapp.com'
server = 'https://cloudvolumesgcp-api.netapp.com'
service_account_file = './cvs-api-sa.json'
project_number = getenv('DEVSHELL_PROJECT_NUMBER', None)
# check if DEVSHELL_PROJECT_NUMBER is set
if project_number == None:
    print('ERROR: Project number not set. Please run')
    print('export DEVSHELL_PROJECT_NUMBER=$(gcloud projects list --filter="$DEVSHELL_PROJECT_ID" --format="value(PROJECT_NUMBER)")')
    print('\nfrom Cloud Shell or manually set')
    print('export DEVSHELL_PROJECT_NUMBER=<projectnumber>')
    print('\nbefore executing the script.')
    exit(1)
else:
    print("INFO: Project number: ", project_number)
# check if file with service account credentials exists
if not path.isfile(service_account_file):
    print('ERROR: Service account credential file "' + service_account_file + '" cannot be found.')
    exit(1)

# Get all volumes from all regions
get_url = server + "/v2/projects/" + str(project_number) + "/locations/-/Volumes"

# Create credential object from private key file
svc_creds = service_account.Credentials.from_service_account_file(service_account_file)

# Create jwt
jwt_creds = jwt.Credentials.from_signing_credentials(svc_creds, audience=audience)

# Issue request to get auth token
request = google.auth.transport.requests.Request()
jwt_creds.refresh(request)

# Extract token
id_token = jwt_creds.token

# Construct GET request
headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + id_token.decode('utf-8')
        }

# Issue the request to the server
r = requests.get(get_url, headers=headers)
r.raise_for_status()

# Print out all vols
# print ("Response to GET request: " + get_url)
print("Volumes:")
for vol in r.json():
    # Get volume attributes
    volname = vol["name"]
    volsizeGiB = convertToGiB(vol["quotaInBytes"])
    region = vol["region"]
    volumeId = vol["volumeId"]
    print ("Name: " + volname + ", size: " + str(volsizeGiB) + "GiB, region: " + region + ", volumeID: " + volumeId)
    # if something is wrong, print more details
    if vol["lifeCycleState"] != "available":
        # pprint(vol)
        print("\tStatus: " + vol["lifeCycleStateDetails"])
    if vol["lifeCycleState"] == "error":
        if region == "":
            print("Region information is missing for Volume", volname, ". Querying ...")
            # Region is missing. Query each region individually to find out who hosts the volume
            for location in regions:
                get_url = server + "/v2/projects/" + str(project_number) + "/locations/" + location + "/Volumes/" + volumeId
                resp = requests.get(get_url, headers=headers)
                data = resp.json()
                # pprint(data)
                if "volumeId" in data:
                    # we found the region containing the volume
                    region = location
                    print("Found region:", region)
                    break
        delete_url = server + "/v2/projects/" + str(project_number) + "/locations/" + region + "/Volumes/" + volumeId
        # print("\t" + delete_url)
        # Issue the request to the server
        if yes_or_no("*** Do you want to delete failed volume: " + volname + " in region: " + region):

            print ("*** Deleting !!! Name: " + volname + ", size: " + str(volsizeGiB) + "GiB, region: " + region + ", volumeID: " + volumeId)            
            r = requests.delete(delete_url, headers=headers)
            if (r.status_code == 200 or r.status_code == 202):
                print("Deleted volume. Status code:", r.status_code) 
            else:
                print("ERROR deleting volume " + volname + ". Status code:", r.status_code)