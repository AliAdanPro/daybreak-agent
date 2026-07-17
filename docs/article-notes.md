# Article material — collected as we build

Target article: **"Weekend Agent Challenge: DayBreak"** — tag `agents`, ≥500 words,
published on AWS Builder Center before **July 20, 2026, 1:00 PM PT** (July 21, 1:00 AM PKT).

## Required sections checklist — ALL DONE, published Jul 17, 2026 ✅
Article: <https://builder.aws.com/content/3GdZOr6eF0NaewoIWikF0ZpLV6i/weekend-agent-challenge-daybreak-the-morning-brief-that-writes-itself>
- [x] Title contains "Weekend Agent Challenge: [Name of Your Agent]"
- [x] Tag `agents` added
- [x] Vision & What the Agent Does
- [x] How You Built It (decisions, challenges, fixes)
- [x] AWS Services Used / Architecture Overview (+ diagram)
- [x] What You Learned
- [x] Public GitHub repo link (must stay public!)
- [x] ≥500 words (~1,000 published)

## Key decisions (why — for the "How You Built It" section)
- **Morning brief agent** chosen over watcher/digest ideas: it is the challenge's own
  first example, needs no third-party API keys, no stored state, no OAuth — the
  highest-probability path in a first-100-submissions race.
- **Single-file Python Lambda, stdlib only**: no packaging, no dependency layers,
  nothing to break during deployment.
- **Open-Meteo + public RSS** as data sources: free, keyless, reliable.
- **Bedrock Nova Micro via the Converse API**: cheapest capable model; the AI and the
  AWS-service requirements are satisfied by the same component.
- **EventBridge Scheduler (not classic EventBridge rules)**: timezone-aware cron —
  `cron(0 6 * * ? *)` in Asia/Karachi survives any DST nonsense and reads cleanly.
- **SNS for email** instead of SES: no sender-identity verification dance; one topic,
  one email subscription, one confirmation click.
- **Resilience**: each data source independently wrapped; Bedrock failure falls back
  to a plain assembled brief — the agent always reports back.

## Challenges encountered (fill in as they happen)
- **IAM eventual consistency**: the very first `lambda create-function` failed with
  "The role defined for the function cannot be assumed by Lambda" — a brand-new IAM
  role takes ~10s to propagate. Fixed with an exit-code-based retry loop.
- **PowerShell 5.1 vs AWS CLI quoting**: passing the schedule's `--target` JSON inline
  stripped the double quotes (`{Arn:...}` instead of `{"Arn":...}`). Fixed by writing
  the JSON to a file and passing `file://` — a good habit for ANY complex CLI param.
- **Also learned**: the AWS CLI is a native exe, so PowerShell `try/catch` never fires
  on failure; you must check `$LASTEXITCODE` after every call.
- **Bedrock model access page retired (July 2026)**: models now auto-enable on first
  invocation — our first Lambda test call enabled Nova Micro automatically, zero clicks.

## Cost-safety measures taken (article material)
- Account uses the AWS **Free plan** ($100 credits, card cannot be charged; verified
  via `aws freetier get-account-plan-state`).
- Zero-spend budget alarm (`daybreak-zero-spend-alarm`): emails the owner if actual
  spend exceeds $0.01 in any month.
- Whole architecture is pay-per-use: one ~10s Lambda run/day, ~$0.0001 of Nova Micro
  per brief, everything inside permanent free allowances.

## Evidence captured for the article 📸 — all in the published article + docs/screenshots/
- [x] Screenshot: EventBridge schedule in the console (cron + timezone visible)
- [x] Screenshot: the brief email in the inbox (scheduler-fired 20:25 PKT run)
- [x] Screenshot: CloudWatch log of the unattended run
- [x] Architecture diagram (mermaid rendered by GitHub, screenshot in article)
- [x] Footer close-up: the email naming its own schedule + AWS-injected scheduled time
