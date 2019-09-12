# CVS-GCP-API-examples
Some code to do API calls for Cloud Volumes Services for GCP

## How to use
Run from GCP Cloud Shell in your project.

1) Create an service account and a keyfile. You can use create-api-service-account.sh to do this.
2) run "python3 get-volumes.py" from Cloud Shell. In the first run, it will ask you to run a gcloud command to put project number into a environment variable. If variable is populated, it will print existing volumes and offer to delete volumes in state "error".
