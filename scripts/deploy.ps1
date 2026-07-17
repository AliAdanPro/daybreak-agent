# DayBreak — one-shot deployment script (AWS CLI, PowerShell 5.1 compatible)
#
# Creates everything the agent needs in your AWS account:
#   SNS topic + email subscription -> IAM roles -> Lambda function -> EventBridge schedule
#
# Usage (from the repo root, after `aws configure`):
#   powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1 -Email you@example.com
#
# Safe to re-run: each step skips or updates resources that already exist.

param(
    [Parameter(Mandatory = $true)][string]$Email,
    [string]$Region = "us-east-1",
    [string]$ScheduleCron = "cron(0 6 * * ? *)",
    [string]$ScheduleTimezone = "Asia/Karachi"
)

$ErrorActionPreference = "Stop"
$env:AWS_DEFAULT_REGION = $Region

$FunctionName = "daybreak"
$TopicName = "daybreak-brief"
$LambdaRoleName = "daybreak-lambda-role"
$SchedulerRoleName = "daybreak-scheduler-role"
$ScheduleName = "daybreak-6am-brief"
$RepoRoot = Split-Path -Parent $PSScriptRoot

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

Step "Verifying AWS credentials"
$AccountId = aws sts get-caller-identity --query Account --output text
if (-not $AccountId) { throw "AWS CLI is not configured. Run 'aws configure' first." }
Write-Host "Account: $AccountId  Region: $Region"

Step "Creating SNS topic + email subscription"
$TopicArn = aws sns create-topic --name $TopicName --query TopicArn --output text
Write-Host "Topic: $TopicArn"
$Subs = aws sns list-subscriptions-by-topic --topic-arn $TopicArn --query "Subscriptions[?Endpoint=='$Email']" --output text
if (-not $Subs) {
    aws sns subscribe --topic-arn $TopicArn --protocol email --notification-endpoint $Email | Out-Null
    Write-Host "Subscription created - CHECK YOUR INBOX and click 'Confirm subscription'." -ForegroundColor Yellow
} else {
    Write-Host "Email already subscribed."
}

Step "Creating Lambda execution role"
$LambdaRoleArn = ""
try {
    $LambdaRoleArn = aws iam get-role --role-name $LambdaRoleName --query Role.Arn --output text 2>$null
} catch {}
if (-not $LambdaRoleArn) {
    $LambdaRoleArn = aws iam create-role --role-name $LambdaRoleName `
        --assume-role-policy-document file://$RepoRoot/infra/lambda-trust-policy.json `
        --query Role.Arn --output text
}
aws iam put-role-policy --role-name $LambdaRoleName --policy-name daybreak-lambda-permissions `
    --policy-document file://$RepoRoot/infra/lambda-permissions-policy.json
Write-Host "Role: $LambdaRoleArn"

Step "Packaging Lambda code"
$BuildDir = Join-Path $RepoRoot "build"
New-Item -ItemType Directory -Force $BuildDir | Out-Null
$ZipPath = Join-Path $BuildDir "daybreak.zip"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path (Join-Path $RepoRoot "src\lambda_function.py") -DestinationPath $ZipPath
Write-Host "Packaged: $ZipPath"

Step "Creating (or updating) the Lambda function"
$FunctionArn = ""
try {
    $FunctionArn = aws lambda get-function --function-name $FunctionName `
        --query Configuration.FunctionArn --output text 2>$null
} catch {}
if ($FunctionArn) {
    aws lambda update-function-code --function-name $FunctionName --zip-file fileb://$ZipPath | Out-Null
    Write-Host "Existing function updated: $FunctionArn"
} else {
    # New IAM roles take a few seconds to become assumable by Lambda; retry.
    $attempt = 0
    while ($true) {
        $attempt++
        try {
            $FunctionArn = aws lambda create-function --function-name $FunctionName `
                --runtime python3.13 --handler lambda_function.lambda_handler `
                --zip-file fileb://$ZipPath --role $LambdaRoleArn `
                --timeout 60 --memory-size 256 `
                --environment "Variables={SNS_TOPIC_ARN=$TopicArn}" `
                --query FunctionArn --output text
            break
        } catch {
            if ($attempt -ge 6) { throw }
            Write-Host "Role not ready yet (attempt $attempt/6), waiting 10s..."
            Start-Sleep -Seconds 10
        }
    }
    Write-Host "Function created: $FunctionArn"
}

Step "Creating scheduler role"
$SchedulerRoleArn = ""
try {
    $SchedulerRoleArn = aws iam get-role --role-name $SchedulerRoleName --query Role.Arn --output text 2>$null
} catch {}
if (-not $SchedulerRoleArn) {
    $SchedulerRoleArn = aws iam create-role --role-name $SchedulerRoleName `
        --assume-role-policy-document file://$RepoRoot/infra/scheduler-trust-policy.json `
        --query Role.Arn --output text
}
aws iam put-role-policy --role-name $SchedulerRoleName --policy-name daybreak-scheduler-invoke `
    --policy-document file://$RepoRoot/infra/scheduler-invoke-policy.json
Write-Host "Role: $SchedulerRoleArn"

Step "Creating (or updating) the EventBridge schedule ($ScheduleCron, $ScheduleTimezone)"
$Target = "{`"Arn`":`"$FunctionArn`",`"RoleArn`":`"$SchedulerRoleArn`"}"
$existing = ""
try {
    $existing = aws scheduler get-schedule --name $ScheduleName --query Name --output text 2>$null
} catch {}
$attempt = 0
while ($true) {
    $attempt++
    try {
        if ($existing) {
            aws scheduler update-schedule --name $ScheduleName `
                --schedule-expression $ScheduleCron --schedule-expression-timezone $ScheduleTimezone `
                --flexible-time-window Mode=OFF --target $Target | Out-Null
        } else {
            aws scheduler create-schedule --name $ScheduleName `
                --schedule-expression $ScheduleCron --schedule-expression-timezone $ScheduleTimezone `
                --flexible-time-window Mode=OFF --target $Target | Out-Null
        }
        break
    } catch {
        if ($attempt -ge 6) { throw }
        Write-Host "Scheduler role not ready yet (attempt $attempt/6), waiting 10s..."
        Start-Sleep -Seconds 10
    }
}
Write-Host "Schedule ready: $ScheduleName"

Step "DONE"
Write-Host "1. Confirm the SNS subscription email in your inbox (required before any brief arrives)."
Write-Host "2. Test now:  aws lambda invoke --function-name $FunctionName --payload '{}' out.json; cat out.json"
Write-Host "3. Tomorrow at 6:00 AM $ScheduleTimezone the brief arrives on its own."
