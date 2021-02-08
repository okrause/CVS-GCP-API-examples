# CVS-GCP-API-examples
Some code to do API calls for Cloud Volumes Services for GCP

## How to use
Run from *GCP Cloud Shell*:

1) Create an service account and a keyfile. You can use a script to do this. It create a keyfile named "cvs-api-sa.json'
```bash
source create-api-service-account.sh
```
2) Run
```bash
export DEVSHELL_PROJECT_NUMBER=$(gcloud projects list --filter="$DEVSHELL_PROJECT_ID" --format="value(PROJECT_NUMBER)")
```
3) Recommended: Use virtual python environment
```bash
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
```
4) Run get-volumes.py. It will print existing volumes and offer to delete volumes in state "error"
```bash
python3 get-volumes.py
```
