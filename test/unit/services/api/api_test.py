import json

from unittest.mock import MagicMock, patch


@patch('mash.services.api.utils.amqp.Connection')
def test_api_add_account_azure(mock_connection, test_client):
    channel = MagicMock()
    connection = MagicMock()
    connection.channel.return_value = channel
    mock_connection.return_value = connection

    request = {
        'account_name': 'test',
        'region': 'us-east-1',
        'requesting_user': 'user1',
        "source_container": "string",
        "source_resource_group": "string",
        "source_storage_account": "string",
        "destination_container": "string",
        "destination_resource_group": "string",
        "destination_storage_account": "string",
        "credentials": {
            "clientId": "string",
            "clientSecret": "string",
            "subscriptionId": "string",
            "tenantId": "string",
            "activeDirectoryEndpointUrl": "string",
            "resourceManagerEndpointUrl": "string",
            "activeDirectoryGraphResourceId": "string",
            "sqlManagementEndpointUrl": "string",
            "galleryEndpointUrl": "string",
            "managementEndpointUrl": "string"
        }
    }
    response = test_client.post(
        '/accounts/azure/',
        content_type='application/json',
        data=json.dumps(request, sort_keys=True)
    )

    request['cloud'] = 'azure'
    channel.basic.publish.assert_called_once_with(
        body=json.dumps(request, sort_keys=True),
        routing_key='add_account',
        exchange='jobcreator',
        properties={
            'content_type': 'application/json',
            'delivery_mode': 2
        },
        mandatory=True
    )
    assert response.status_code == 201
    assert response.data == b'{"name":"test"}\n'


@patch('mash.services.api.utils.amqp.Connection')
def test_api_delete_account_azure(mock_connection, test_client):
    channel = MagicMock()
    connection = MagicMock()
    connection.channel.return_value = channel
    mock_connection.return_value = connection

    data = {
        'requesting_user': 'user1'
    }
    response = test_client.delete(
        '/accounts/azure/test',
        content_type='application/json',
        data=json.dumps(data, sort_keys=True)
    )

    data['cloud'] = 'azure'
    data['account_name'] = 'test'
    channel.basic.publish.assert_called_once_with(
        body=json.dumps(data, sort_keys=True),
        routing_key='delete_account',
        exchange='jobcreator',
        properties={
            'content_type': 'application/json',
            'delivery_mode': 2
        },
        mandatory=True
    )
    assert response.status_code == 200
    assert response.data == b'{"name":"test"}\n'


@patch('mash.services.api.routes.jobs.uuid')
@patch('mash.services.api.utils.amqp.Connection')
def test_api_add_job_gce(mock_connection, mock_uuid, test_client):
    channel = MagicMock()
    connection = MagicMock()
    connection.channel.return_value = channel
    mock_connection.return_value = connection

    uuid = '12345678-1234-1234-1234-123456789012'
    mock_uuid.uuid4.return_value = uuid

    with open('../data/gce_job.json', 'r') as job_doc:
        data = json.load(job_doc)

    del data['job_id']
    del data['cloud']
    response = test_client.post(
        '/jobs/gce/',
        content_type='application/json',
        data=json.dumps(data, sort_keys=True)
    )

    data['job_id'] = uuid
    data['cloud'] = 'gce'
    channel.basic.publish.assert_called_once_with(
        body=json.dumps(data, sort_keys=True),
        routing_key='job_document',
        exchange='jobcreator',
        properties={
            'content_type': 'application/json',
            'delivery_mode': 2
        },
        mandatory=True
    )
    assert response.status_code == 201
    assert response.data == \
        b'{"job_id": "12345678-1234-1234-1234-123456789012"}'


@patch('mash.services.api.routes.jobs.uuid')
@patch('mash.services.api.utils.amqp.Connection')
def test_api_add_job_azure(mock_connection, mock_uuid, test_client):
    channel = MagicMock()
    connection = MagicMock()
    connection.channel.return_value = channel
    mock_connection.return_value = connection

    uuid = '12345678-1234-1234-1234-123456789012'
    mock_uuid.uuid4.return_value = uuid

    with open('../data/azure_job.json', 'r') as job_doc:
        data = json.load(job_doc)

    del data['job_id']
    del data['cloud']
    response = test_client.post(
        '/jobs/azure/',
        content_type='application/json',
        data=json.dumps(data, sort_keys=True)
    )

    data['job_id'] = uuid
    data['cloud'] = 'azure'
    channel.basic.publish.assert_called_once_with(
        body=json.dumps(data, sort_keys=True),
        routing_key='job_document',
        exchange='jobcreator',
        properties={
            'content_type': 'application/json',
            'delivery_mode': 2
        },
        mandatory=True
    )
    assert response.status_code == 201
    assert response.data == \
        b'{"job_id": "12345678-1234-1234-1234-123456789012"}'


@patch('mash.services.api.utils.amqp.Connection')
def test_api_delete_job(mock_connection, test_client):
    channel = MagicMock()
    connection = MagicMock()
    connection.channel.return_value = channel
    mock_connection.return_value = connection

    response = test_client.delete(
        '/jobs/12345678-1234-1234-1234-123456789012'
    )

    channel.basic.publish.assert_called_once_with(
        body='{"job_delete": "12345678-1234-1234-1234-123456789012"}',
        routing_key='job_document',
        exchange='jobcreator',
        properties={
            'content_type': 'application/json',
            'delivery_mode': 2
        },
        mandatory=True
    )
    assert response.status_code == 200
    assert response.data == \
        b'{"job_id":"12345678-1234-1234-1234-123456789012"}\n'
