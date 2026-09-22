import json
import pytest
from unittest.mock import patch, MagicMock
import responses
import boto3
from src.lambda_function import lambda_handler, get_weather, get_headlines

# Sample data
MOCK_WEATHER = {
    "current": {"temperature_2m": 25.0},
    "daily": {
        "weather_code": [0],
        "temperature_2m_max": [30.0],
        "temperature_2m_min": [15.0],
        "precipitation_probability_max": [0],
        "wind_speed_10m_max": [10.0]
    }
}

MOCK_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Mock News</title>
    <item><title>Mock Headline 1</title></item>
    <item><title>Mock Headline 2</title></item>
  </channel>
</rss>
"""

@responses.activate
@patch("src.lambda_function.http_get")
def test_lambda_handler_success(mock_http_get, aws_mock):
    """Test successful run with mocked AWS and HTTP calls."""
    
    # We patch http_get to avoid live calls, since responses doesn't native mock urllib.request
    # We will still use responses if we can, but patching http_get is safest for urllib
    def side_effect(url, timeout=10):
        if "open-meteo.com" in url:
            return json.dumps(MOCK_WEATHER).encode("utf-8")
        elif "feeds" in url:
            return MOCK_RSS.encode("utf-8")
        return b""
    mock_http_get.side_effect = side_effect

    event = {"source": "aws.scheduler", "schedule_arn": "arn:aws:events:us-east-1:123:schedule/test", "scheduled_time": "2026-09-22T00:00:00Z"}
    
    with patch("src.lambda_function.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:daybreak-topic"):
        with patch("boto3.client") as mock_boto3_client:
            mock_sns = boto3.client("sns", region_name="us-east-1")
            mock_bedrock = MagicMock()
            mock_bedrock.converse.return_value = {
                "output": {"message": {"content": [{"text": "Mock AI generated brief"}]}}
            }
            
            def client_side_effect(service, **kwargs):
                if service == "sns":
                    return mock_sns
                if service == "bedrock-runtime":
                    return mock_bedrock
                return MagicMock()
                
            mock_boto3_client.side_effect = client_side_effect

            result = lambda_handler(event, None)
    
    assert result["ok"] is True
    assert result["weather_ok"] is True
    assert result["ai_used"] is True

    assert result["headline_count"] > 0
    assert not result["problems"]


@patch("src.lambda_function.http_get")
def test_lambda_handler_fallback(mock_http_get, aws_mock):
    """Test fallback brief generation if bedrock fails."""
    
    def side_effect(url, timeout=10):
        if "open-meteo.com" in url:
            return json.dumps(MOCK_WEATHER).encode("utf-8")
        elif "feeds" in url:
            return MOCK_RSS.encode("utf-8")
        return b""
    mock_http_get.side_effect = side_effect

    # Mock bedrock to fail
    with patch("boto3.client") as mock_boto3_client:
        mock_sns = MagicMock()
        mock_bedrock = MagicMock()
        mock_bedrock.converse.side_effect = Exception("Bedrock error")
        
        def client_side_effect(service, **kwargs):
            if service == "sns":
                return mock_sns
            if service == "bedrock-runtime":
                return mock_bedrock
            return MagicMock()
            
        mock_boto3_client.side_effect = client_side_effect
        
        with patch("src.lambda_function.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:daybreak-topic"):
            result = lambda_handler({}, None)
        
        assert result["ok"] is True
        assert result["ai_used"] is False
        assert len(result["problems"]) == 1
        assert "bedrock: Bedrock error" in result["problems"][0]
