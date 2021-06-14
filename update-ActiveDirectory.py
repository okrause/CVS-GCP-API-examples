#!/usr/bin/env python3
# Update CVS Active Directory entries in GCP
# Usage: python3 update-ActiveDirectory.py <region>
# set environment variables first: 
# - SERVICE_ACCOUNT_CREDENTIAL_FILE
# - DEVSHELL_PROJECT_NUMBER

import google.auth.transport.requests
import requests
import json
from os import getenv, path
from sys import exit, argv
from google.auth import jwt
from google.oauth2 import service_account, id_token

# Set this variables for your environment
service_account_file = getenv('SERVICE_ACCOUNT_CREDENTIAL_FILE', None)
project_number = getenv('DEVSHELL_PROJECT_NUMBER', None)
if len(argv) == 2:
    region = argv[1]
else:
    region = "europe-west3"

# Internal variables
audience = 'https://cloudvolumesgcp-api.netapp.com'
server = 'https://cloudvolumesgcp-api.netapp.com'

# check if DEVSHELL_PROJECT_NUMBER is set
if project_number == None:
    print('ERROR: Project number not set in DEVSHELL_PROJECT_NUMBER.')
    exit(1)
else:
    print("INFO: Project number: ", project_number)

# check if file with service account credentials exists
if not path.isfile(service_account_file):
    print('ERROR: Service account credential file "' + service_account_file + '" cannot be found.')
    print('Please set environment variable SERVICE_ACCOUNT_CREDENTIAL_FILE')
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
found=False
for ad in r.json():
    if ad["region"] == region:
        
        print("Found AD data:")
        print(json.dumps(ad, indent=4, sort_keys=True))
        keys_to_keep = ['DNS',
                        'domain',
                        'ldapSigning',
                        'netBIOS',
                        'organizationalUnit',
                        'region',
                        'username',
                        'backupOperators',
                        'securityOperators',
                        "aesEncryption",
                        "allowLocalNFSUsersWithLdap"
                        ]
        uuid = ad["UUID"]
 
        newad = dict()
        # only keep relevant keys
        for key in keys_to_keep:
            if key in ad:
                newad[key] = ad[key]

        # add new keys we want to set. Eaxmples:
        # newad["site"] = "Default-First-Site-Name"#
        newad["backupOperators"] = ["svc-GFC"]
        # newad["aesEncryption"] = True

        # password will not be returned by GET call. You have to set it again
        newad["password"] = "xxx"

        # print(json.dumps(newad, indent=4, sort_keys=True))

        # update AD
        inp = input("Do you want to write modifications done to the settings? Enter YES to continue or anything else to stop: ")
        if inp == "YES":
            print("Updating settings:")
            put_url = server + "/v2/projects/" + str(project_number) + "/locations/" + region + "/Storage/ActiveDirectory/" + uuid
            r2 = requests.put(put_url, data=json.dumps(newad), headers=headers)
            print("New AD settings:")
            print(json.dumps(r2.json(), indent=4))
        else:
            print("No updates")

        found=True
        break

if not found:
    print("No AD entry for region " + region + " found.")
