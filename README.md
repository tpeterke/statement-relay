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
