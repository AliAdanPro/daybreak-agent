# Article material — collected as we build

Target article: **"Weekend Agent Challenge: DayBreak"** — tag `agents`, ≥500 words,
published on AWS Builder Center before **July 20, 2026, 1:00 PM PT** (July 21, 1:00 AM PKT).

## Required sections checklist
- [ ] Title contains "Weekend Agent Challenge: [Name of Your Agent]"
- [ ] Tag `agents` added
- [ ] Vision & What the Agent Does
- [ ] How You Built It (decisions, challenges, fixes)
- [ ] AWS Services Used / Architecture Overview (+ diagram)
- [ ] What You Learned
- [ ] Public GitHub repo link (must stay public!)
- [ ] ≥500 words

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
- (pending)

## Evidence to capture for the article 📸
- [ ] Screenshot: EventBridge schedule in the console (cron + timezone visible)
- [ ] Screenshot: the brief email in the inbox, timestamped ~6:00 AM
- [ ] Screenshot: CloudWatch log of an unattended run
- [ ] Architecture diagram (mermaid in README, export image for article)
