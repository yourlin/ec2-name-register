import pytest

from ec2_change_name import app

TESTED_INSTANCE_ID = 'i-0a2000ae62afe9250'


@pytest.fixture()
def name_change_to_d():
    """ tag修改事件 """

    return {
        "version": "0",
        "id": "ffd8a6fe-32f8-ef66-c85c-111111111111",
        "detail-type": "Tag Change on Resource",
        "source": "aws.tag",
        "account": "123456789012",
        "time": "2018-09-18T20:41:06Z",
        "region": "us-west-2",
        "resources": [
            "arn:aws:ec2:us-east-1:123456789012:instance/" + TESTED_INSTANCE_ID
        ],
        "detail": {
            "changed-tag-keys": [
                "Name"
            ],
            "service": "ec2",
            "resource-type": "instance",
            "version": 5,
            "tags": {
                "Name": "test-d",
                "key1": "value1",
                "key2": "value2"
            }
        }
    }


@pytest.fixture()
def name_change_to_e():
    """ tag修改事件 """

    return {
        "version": "0",
        "id": "ffd8a6fe-32f8-ef66-c85c-111111111111",
        "detail-type": "Tag Change on Resource",
        "source": "aws.tag",
        "account": "123456789012",
        "time": "2018-09-18T20:41:06Z",
        "region": "us-west-2",
        "resources": [
            "arn:aws:ec2:us-east-1:123456789012:instance/" + TESTED_INSTANCE_ID
        ],
        "detail": {
            "changed-tag-keys": [
                "Name"
            ],
            "service": "ec2",
            "resource-type": "instance",
            "version": 5,
            "tags": {
                "Name": "test-e",
                "key1": "value1",
                "key2": "value2"
            }
        }
    }


def test_lambda_handler(name_change_to_d, mocker):
    ret = app.lambda_handler(name_change_to_d, "")


def test_lambda_handler2(name_change_to_e, mocker):
    ret = app.lambda_handler(name_change_to_e, "")
