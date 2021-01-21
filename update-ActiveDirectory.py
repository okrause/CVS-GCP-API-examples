#!/usr/bin/env python3
# Update CVS Active Directory entries in GCP

import google.auth
import google.auth.transport.requests
import requests
import json
from os import getenv, path
from sys import exit
from google.auth import jwt
from google.oauth2 import service_account
from google.oauth2 import id_token

# Set this variables for your environment
service_account_file = getenv('SERVICE_ACCOUNT_CREDENTIAL_FILE', None)
project_number = getenv('DEVSHELL_PROJECT_NUMBER', None)
region = "europe-west4"

# Internal variables
audience = 'https://cloudvolumesgcp-api.netapp.com'
server = 'https://cloudvolumesgcp-api.netapp.com'

# check if DEVSHELL_PROJECT_NUMBER is set
if project_number == None:
    print('ERROR: Project number not set.')
    exit(1)
else:
    print("INFO: Project number: ", project_number)

# check if file with service account credentials exists
if not path.isfile(service_account_file):
    print('ERROR: Service account credential file "' + service_account_file + '" cannot be found.')
    exit(1)

# Get all volumes from all regions
get_url = server + "/v2/projects/" + str(project_number) + "/locations/-/Storage/ActiveDirectory"

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

print("Active Directories:")
updated=False
for ad in r.json():
    if ad["region"] == region:
        
        print("Found AD data:")
        print(json.dumps(ad, indent=4, sort_keys=False))
        keys_to_keep = ['DNS', 'domain', 'ldapSigning', 'netBIOS', 'organizationalUnit', 'region', 'username']
        uuid = ad["UUID"]
        newad = dict()
        # only keep relevant keys
        for key in keys_to_keep:
            newad[key] = ad[key]
        # add new keys we want to set
        newad["site"] = "Default-First-Site-Name"
        newad["backupOperators"] = [""]
        newad["password"] = "xxx"
        # print(newad)

        # update AD
        put_url = server + "/v2/projects/" + str(project_number) + "/locations/" + region + "/Storage/ActiveDirectory/" + uuid
        #r2 = requests.put(put_url, data=json.dumps(newad), headers=headers)
        #print(json.dumps(r2.json(), indent=4))
        updated=True

if not updated:
    print("No AD entry for region " + region + " found.")
