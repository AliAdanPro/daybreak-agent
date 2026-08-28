# Daybreak Agent 🌅

An event-driven, serverless AI agent deployed on AWS that autonomously aggregates external API data and generates daily briefings using Amazon Bedrock[cite: 1].

## 🏗️ Architecture & Tech Stack
*   **Compute:** AWS Lambda (Python 3.x)[cite: 1]
*   **AI/LLM:** Amazon Bedrock (Nova Micro) via `boto3`[cite: 1]
*   **Orchestration:** Amazon EventBridge (Cron Scheduling)[cite: 1]
*   **Integrations:** Open-Meteo API, RSS Feeds[cite: 1]
*   **Security:** AWS IAM (Least Privilege Execution Roles)[cite: 1]

## ⚙️ Core Workflow
1.  **Trigger:** Amazon EventBridge wakes the Lambda function on a defined schedule[cite: 1].
2.  **Ingestion:** Python scripts fetch live data from external weather and news APIs[cite: 1].
3.  **Processing:** Amazon Bedrock processes the raw payloads to synthesize a natural-language daily briefing[cite: 1].
4.  **Delivery:** The final briefing is routed to the end user.

## 🧪 Quality & Testing Strategy (In Progress)
*As part of an ongoing SDET initiative, this repository is being retrofitted with automated quality gates:*
*   **API Mocking:** Pytest fixtures to simulate external API responses.
*   **Unit Tests:** Validating Bedrock payload generation without triggering live AWS billing[cite: 1].
*   **CI/CD:** GitHub Actions pipeline to run tests automatically on every push.
