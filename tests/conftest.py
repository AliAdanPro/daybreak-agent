import os
import pytest
import boto3
from moto import mock_aws
import responses

@pytest.fixture(scope="function", autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["SNS_TOPIC_ARN"] = "arn:aws:sns:us-east-1:123456789012:daybreak-topic"

@pytest.fixture(scope="function")
def aws_mock(aws_credentials):
    """Start moto mock for AWS services."""
    with mock_aws():
        # Setup SNS
        sns = boto3.client("sns", region_name="us-east-1")
        topic = sns.create_topic(Name="daybreak-topic")
        os.environ["SNS_TOPIC_ARN"] = topic["TopicArn"]
        yield

@pytest.fixture(scope="function")
def mock_responses():
    """Start responses mock for HTTP calls."""
    with responses.RequestsMock() as rsps:
        yield rsps
