# Daybreak Agent 🌅

An event-driven, serverless AI agent deployed on AWS that autonomously aggregates external API data and generates daily briefings using Amazon Bedrock.

## 🏗️ Architecture & Tech Stack
*   **Compute:** AWS Lambda (Python 3.x)
*   **AI/LLM:** Amazon Bedrock (Nova Micro) via `boto3`
*   **Orchestration:** Amazon EventBridge (Cron Scheduling)
*   **Integrations:** Open-Meteo API, RSS Feeds
*   **Security:** AWS IAM (Least Privilege Execution Roles)

## ⚙️ Core Workflow
1.  **Trigger:** Amazon EventBridge wakes the Lambda function on a defined schedule.
2.  **Ingestion:** Python scripts fetch live data from external weather and news APIs.
3.  **Processing:** Amazon Bedrock processes the raw payloads to synthesize a natural-language daily briefing.
4.  **Delivery:** The final briefing is routed to the end user.

## 🧪 Quality & Testing Strategy (In Progress)
*As part of an ongoing SDET initiative, this repository is being retrofitted with automated quality gates:*
*   **API Mocking:** Pytest fixtures to simulate external API responses.
*   **Unit Tests:** Validating Bedrock payload generation without triggering live AWS billing.
*   **CI/CD:** GitHub Actions pipeline to run tests automatically on every push.
