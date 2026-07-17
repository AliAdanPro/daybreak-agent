# Deploying DayBreak from scratch

Everything below happens once. Total hands-on time: ~30–40 minutes, most of it
AWS account signup.

## 1. Create an AWS account (~15 min)

1. Go to <https://aws.amazon.com/free> and click **Create a free account**.
2. Sign up with your email. You'll need a **credit/debit card** (identity check —
   the Free Tier terms state the account will not be converted to billable or
   charged without your consent) and a **phone number** for an SMS code.
3. Choose the **Basic (free) support plan** when asked.

## 2. Create an access key for the AWS CLI (~10 min)

Best practice is to avoid using the root account day-to-day, so create an
admin user:

1. Sign in to the AWS Console → search **IAM** → **Users** → **Create user**.
2. Name: `daybreak-admin`. Do **not** tick console access. → **Next**.
3. Choose **Attach policies directly** → tick **AdministratorAccess** → **Next** → **Create user**.
4. Open the user → **Security credentials** tab → **Create access key** →
   choose **Command Line Interface (CLI)** → tick the confirmation → **Create**.
5. Keep the page open — you'll copy the two values into `aws configure` next.
   (Delete this key from the same page once the challenge is over.)

## 3. Install and configure the AWS CLI (~5 min)

```powershell
winget install Amazon.AWSCLI
```

Open a **new** terminal, then:

```powershell
aws configure
# AWS Access Key ID:      (paste from step 2)
# AWS Secret Access Key:  (paste from step 2)
# Default region name:    us-east-1
# Default output format:  json
```

## 4. Enable Bedrock model access (~2 min)

1. In the AWS Console (region **N. Virginia / us-east-1**), search **Bedrock**.
2. Left menu → **Model access** → **Modify model access**.
3. Tick **Amazon Nova Micro** → **Next** → **Submit**. Amazon's own models are
   granted instantly.

## 5. Deploy (~2 min)

From the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1 -Email you@example.com
```

Then **check your inbox and click "Confirm subscription"** in the email from
AWS — SNS will not deliver anything until you do.

## 6. Verify

```powershell
aws lambda invoke --function-name daybreak --payload '{}' out.json
Get-Content out.json   # expect {"ok": true, "ai_used": true, ...}
```

A Morning Brief email should arrive within seconds. From then on the
EventBridge schedule fires every day at 6:00 AM Asia/Karachi with no human
involved.

## Cleanup (after the challenge)

```powershell
aws scheduler delete-schedule --name daybreak-6am-brief
aws cloudwatch delete-alarms --alarm-names daybreak-run-failed
aws lambda delete-function --function-name daybreak
aws logs delete-log-group --log-group-name /aws/lambda/daybreak
aws sns delete-topic --topic-arn <topic-arn>
aws budgets delete-budget --account-id <account-id> --budget-name daybreak-zero-spend-alarm
aws iam delete-role-policy --role-name daybreak-lambda-role --policy-name daybreak-lambda-permissions
aws iam delete-role --role-name daybreak-lambda-role
aws iam delete-role-policy --role-name daybreak-scheduler-role --policy-name daybreak-scheduler-invoke
aws iam delete-role --role-name daybreak-scheduler-role
```

Finally, delete the `daybreak-admin` access key in the IAM console
(IAM → Users → daybreak-admin → Security credentials → deactivate/delete the key).
