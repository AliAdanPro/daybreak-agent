# Weekend Agent Challenge: DayBreak — the morning brief that writes itself

> **Publishing checklist (delete this block before publishing):**
> - Tag the article with `agents` (also add `challenge` and `aws-builders`)
> - Replace `[REPO-URL]` with the public GitHub link
> - Insert the four screenshots where marked
> - Publish before July 20, 2026, 1:00 PM PT

## Vision & What the Agent Does

My mornings used to start the same way for a lot of us: pick up the phone,
bounce between a weather app and three news sites, and lose twenty minutes
before the day even begins. For last weekend's challenge people built tools
you open and paste things into. This weekend's brief was to give that idea
legs — so I built an agent that does the morning routine *for* me, before I
wake up.

**DayBreak** is a personal AI agent that runs completely unattended. Every day
at 6:00 AM Pakistan time, Amazon EventBridge Scheduler wakes it up — no button,
no human. It gathers today's weather forecast for Islamabad and the latest
world and tech headlines, asks Amazon Bedrock (Nova Micro) to turn that raw
material into a short, friendly brief with practical advice ("keep an umbrella
handy"), and emails it to me through Amazon SNS. By the time my alarm goes
off, the day's summary is already sitting in my inbox.

It also always reports back, even on a bad day: every data source is wrapped
independently, so if a news feed is down the brief ships without it, and if
the AI call itself ever fails, the agent assembles a plain fallback brief from
the raw data instead of staying silent.

**[SCREENSHOT 1: the 6:00 AM brief email in my inbox, timestamp visible]**

And because the whole point of the challenge is that it happened without me,
each email's footer states exactly how the run was triggered — the
scheduler-fired runs name the schedule and the scheduled time that AWS itself
injected into the event:

> DayBreak, 06:00 PKT: ran unattended on AWS Lambda, fired by Amazon
> EventBridge Scheduler (schedule 'daybreak-6am-brief'). Nobody pressed a button.

## How You Built It

Full honesty up front: this was my **first ever AWS deployment**, and I built
it with Claude Code as my pair programmer, making the decisions together and
learning the platform as we went. The guiding principle was simplicity —
every choice below is the boring, reliable option:

- **A single-file Python Lambda using only the standard library + boto3.**
  Nothing to package, no dependency layers, nothing to break on deploy.
- **Keyless data sources.** Weather comes from the free Open-Meteo API and
  headlines from public RSS feeds (BBC World, Ars Technica) — zero API keys,
  zero accounts, zero secrets to manage.
- **Amazon Nova Micro via the Bedrock Converse API.** The cheapest capable
  model; a full year of daily briefs costs about five cents.
- **EventBridge Scheduler instead of classic cron rules**, because it is
  timezone-aware: `cron(0 6 * * ? *)` in `Asia/Karachi` says exactly what it
  means.
- **SNS for delivery instead of SES** — one topic, one email subscription,
  one confirmation click, no sender-identity verification dance.

The challenges were real and all of them taught me something:

1. **IAM is eventually consistent.** My first `lambda create-function` failed
   with "the role cannot be assumed by Lambda" — a freshly created IAM role
   takes about ten seconds to propagate. The deploy script now retries.
2. **Windows PowerShell 5.1 eats JSON quotes.** Passing the schedule target
   inline turned `{"Arn": ...}` into `{Arn: ...}`. Complex CLI parameters now
   travel as `file://` documents.
3. **Honest evidence needed engineering.** My first test email proudly claimed
   it was "triggered by EventBridge Scheduler" — but I had invoked it by hand.
   The fix: the schedule injects its own context attributes
   (`<aws.scheduler.schedule-arn>`, `<aws.scheduler.scheduled-time>`) into the
   event payload, and the agent describes its trigger truthfully — manual test
   runs are labeled as manual test runs.

## AWS Services Used / Architecture Overview

```
EventBridge Scheduler ──(6:00 AM PKT daily, no human)──> AWS Lambda (Python 3.13)
                                                            │
                                    ┌───────────────────────┼─────────────────┐
                                    ▼                       ▼                 ▼
                             Open-Meteo API           public RSS feeds   Amazon Bedrock
                             (weather, free)          (headlines)        (Nova Micro writes
                                    │                       │             the brief)
                                    └───────────┬───────────┘                 │
                                                ▼                             │
                                          Amazon SNS  <──────────────────────┘
                                                │
                                                ▼
                                          📧 my inbox (before I wake up)
```

**[SCREENSHOT 2: EventBridge schedule in the console — cron + Asia/Karachi timezone visible]**

| Service | Role | Cost |
|---|---|---|
| **Amazon EventBridge Scheduler** | The "always-on" part: timezone-aware daily trigger | Free (14M invocations/month free) |
| **AWS Lambda** | Runs the agent (~10 s/day, 256 MB) | Free (1M requests/month free) |
| **Amazon Bedrock — Nova Micro** | Writes the brief from raw weather + headlines | ~$0.0001 per brief |
| **Amazon SNS** | Email delivery | Free (first 1,000 emails/month) |
| **Amazon CloudWatch Logs** | Evidence of every unattended run | Free (5 GB tier) |
| **AWS IAM** | Two least-privilege roles (Lambda exec, Scheduler invoke) | Always free |

**[SCREENSHOT 3: CloudWatch log of the scheduler-fired run]**

Cost was a hard requirement for me — I'm a student and wanted this at $0. The
account runs on the AWS Free plan ($100 credits, the card cannot be charged),
plus a zero-spend budget alarm that emails me if actual charges ever exceed
$0.01. Measured usage so far rounds to zero.

## What You Learned

- **Serverless really can be free.** A genuinely useful, always-on agent fits
  inside permanent free allowances; the AI is the only metered part and costs
  a hundredth of a cent per day.
- **Model access got simpler.** Bedrock's "Model access" page was retired —
  Nova Micro enabled itself on my first invocation, zero clicks.
- **IAM eventual consistency, exit codes for native CLIs, and `file://` for
  complex parameters** — three deployment lessons I'll reuse forever.
- **Evidence is a design requirement, not an afterthought.** Making the agent
  prove *how* it was triggered shaped the architecture (scheduler context
  attributes) and made the whole submission more trustworthy.
- Most of all: as a complete AWS beginner, I went from "empty account" to "a
  scheduled AI agent emailing me every morning" in one day. The gap between
  wanting an always-on agent and having one is much smaller than I thought.

**[SCREENSHOT 4: the email footer showing the schedule name — proof it ran unattended]**

## Link to App or Repo

Source code, IAM policies, deploy script, and docs: **[REPO-URL]**

*Tags: #agents #challenge #aws-builders*
