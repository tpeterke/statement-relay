# statement-relay
This development will pull statements from bank(s) and create transactions in Waveapps (only Wise for now).



LICENCE.md extended as following
================================
  16. Limitation of Liability.
  
  ....
  
  IMPORTANT TO REMEMBER THAT THIS SOLUTION USES / INTENDED TO USE
GOOGLE CLOUD PLATFORM (GCP) AND ITS SERVICES. THIS AUTOMATICALLY GENERATES
COSTS PAYABLE TO GOOGLE CLOUD PLATFORM WHICH MAY OR MAY NOT BE WAIVED AS
PART OF AN ONGOING FREE TIER. YOU MAY NOT BE ELIGIBLE OR ALREADY BEYOND
THE LIMITS OF FREE TIER WHICH WILL RESULT AMOUNT PAYABLE TO GOOGLE CLOUD
PLATFORM.

Assumptions
===========
- You already set up a Google Cloud Platform (GCP) account and it is billable.
- You have created a new project, activated Cloud Functions, Secret Management and Cloud Scheduler APIs.

Steps to follow
===============

Step 1
------
Login to your Wise.com account and navigate to API tokens in Settings menu.
Add a new token, give it a name of your choice and set it read only.
If you are an advanced GCP user and have fixed IP, you can provide it here too,
for added security. Although, in that case you don't need my advice.
Important: this is only for temporary use!

Step 2
------
Replacing <xxxxx> with your API key acquired in Step 1, run following command
in your local terminal ("cmd" command in Windows) to learn IDs of your profiles.
  
  curl -X GET https://api.transferwise.com/v1/profiles -H "Authorization: Bearer <xxxxx>"
  
Save the output for later use.

Step 3
------
Similarly, run the following command replacing <xxxxx> with your API key and
<profileID> with the profile IDs that you can find in the output of the
previous step. Run this command for each of your profiles:
  
  curl -X GET https://api.transferwise.com/v1/borderless-accounts?profileId=<profileID> -H "Authorization: Bearer <xxxxx>"

Save the output of each runs for later use.

Step 4
------
Return to Wise.com, in the Settings menu navigate to API tokens and delete
the token you have used in the previous steps. While you are here,
create a new token for the next step.

Step 5
------
In GCP Secret Manager create a new secret with the name "TW_TOKEN" and the value will be the token you generated in Step 4.

Step 6
------
Login to Waveapps and then go to "Wave > Developer Portal > Documentation > Create an App":
  
  https://developer.waveapps.com/hc/en-us/articles/360019762711

Only name is important and the "I agree" at the end of the page.
Create a Full Access token that you will use in the next steps.
  
Step 7
------
While still logged in to your Waveapps account, run Waveapps' first and default example query in very own API playground:
  
  https://developer.waveapps.com/hc/en-us/articles/360018937431-API-Playground

...or run wa_businesses.py from this repository. Don't forget to maintain your API token in the code!
Make a note of the business IDs.

Step 8
------
  BE SURE THAT ALL YOUR ACCOUNTS IN WISE ARE ALREADY CREATED IN WAVEAPPS BEFORE RUNNING THIS!!!
  Using each business IDs obtained in Step 7 run the wa_accounts.py from this repository. Don't forget to edit the API token and the Business ID for each run.
Make note of the output. It will contain Account IDs for your bank accounts and the Uncategorized Income and Uncategorized Expense for each of your businesses. Your personal account is a business too!
  
Step 9
  -------------
  Go back to Manage Application site in Waveapps:
  
  https://developer.waveapps.com/hc/en-us/articles/360019762711
  
  Revoke your Full Access token and create a new one. Copy the new value and go to the Secret Manager in GCP.
  Create a new secret with the name "WA_TOKEN" and value would be the new token that you just created.

  Step 10
  -------------
  Edit tw_config.json file from this repository tailoring it to your specific case using data obtained in steps 2, 3 and 8.
  In Secret Manager create a secret with the name "tw_config_json" and upload this file here.
  
  Step 11
  ----------
  In Cloud Functions of GCP create a new function with default values, but set HTTPS required and the endpoint to "main". Copy content of main.py from this repository to the Cloud function's main.py and the contents of reqquirements.txt from this repository to the requirements.txt in Cloud Functions.
  Once it's deployed, test it. It has to give an error.
  
  Step 12
  -------
  In GCP go to IAM/Service accounts and create a new account with the name "cf-invoker".
  Head over to Cloud functions, the one that you created and under permissions add the new "cf-invoker" user with the role "Cloud Function Invoker".
  Head over to Secrete Manager and for each of your secrets add "cf-invoker" account with the role "Secret Manager Secret Accessor".
  
  Step 13
  -------
Go to Cloud Scheduler and schedule a job. For hourly run use "0 * * * *" frequency. Job target will be the HTTP type URL of your with GET method.
  In header User-Agent Google-Cloud-Scheduler will be default, you just have to set OIDC token and the servcie account will be the new "cf-invoker" account.
  
  In case you find unexpected amounts on your GCP bill
  ====================================================
  Credit to @vir-us https://stackoverflow.com/a/64086856/15115806
  
  Credit to @frank-van-puffelen https://stackoverflow.com/a/63580047/15115806
  
  All the above process alone should not generate any charges beyond the free tier given by Google. Yet, I started seeing $0.02 charges monthly.
  
  If you see an unexpected amount on your GCP bill and you determine it comes from Cloud Storage, that might be because of Cloud Build piling up temporary files in us.artifacts.<YOUR_PROJECT'S_NAME>.appspot.com. The above two articles contradict each other.
    
  I decided to setup a 3 days deletion operation in this folder's lifecycle and hope to remember to delete the "container" folder if something goes wrong.
    
