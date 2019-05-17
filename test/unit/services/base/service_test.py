import io

from unittest.mock import patch
from unittest.mock import call
from unittest.mock import MagicMock, Mock
from pytest import raises

from mash.services.mash_service import MashService

from mash.mash_exceptions import (
    MashRabbitConnectionException,
    MashLogSetupException
)
from mash.utils.json_format import JsonFormat

open_name = "builtins.open"


class TestBaseService(object):
    @patch('mash.services.mash_service.get_configuration')
    @patch('mash.services.mash_service.Connection')
    def setup(
        self, mock_connection, mock_get_configuration
    ):
        self.connection = Mock()
        self.channel = Mock()
        self.msg_properties = {
            'content_type': 'application/json',
            'delivery_mode': 2
        }
        queue = Mock()
        queue.method.queue = 'queue'
        self.channel.queue.declare.return_value = queue
        self.channel.exchange.declare.return_value = queue

        self.connection.channel.return_value = self.channel
        self.connection.is_closed = True
        mock_connection.return_value = self.connection

        config = Mock()
        config.get_service_names.return_value = [
            'obs', 'uploader', 'testing', 'replication', 'publisher',
            'deprecation'
        ]
        mock_get_configuration.return_value = config

        self.service = MashService('obs')

        mock_get_configuration.assert_called_once_with('obs')
        self.service.log = Mock()
        mock_connection.side_effect = Exception
        with raises(MashRabbitConnectionException):
            MashService('obs')
        self.channel.reset_mock()

    def test_post_init(self):
        self.service.post_init()

    @patch('mash.services.mash_service.os')
    @patch('logging.FileHandler')
    def test_set_logfile(self, mock_logging_FileHandler, mock_os):
        logfile_handler = Mock()
        mock_logging_FileHandler.return_value = logfile_handler

        mock_os.path.dirname.return_value = '/some'
        mock_os.path.isdir.return_value = False

        self.service.set_logfile('/some/log')

        mock_os.path.dirname.assert_called_with('/some/log')
        mock_os.path.isdir.assert_called_with('/some')
        mock_os.makedirs.assert_called_with('/some')

        mock_logging_FileHandler.assert_called_once_with(
            encoding='utf-8', filename='/some/log'
        )
        self.service.log.addHandler.assert_has_calls(
            [call(logfile_handler)]
        )

    @patch('mash.services.mash_service.os')
    @patch('logging.FileHandler')
    def test_set_logfile_raises(self, mock_logging_FileHandler, mock_os):
        mock_logging_FileHandler.side_effect = Exception
        with raises(MashLogSetupException):
            self.service.set_logfile('/some/log')

    def test_consume_queue(self):
        callback = Mock()
        self.service.consume_queue(callback, queue_name='service')
        self.channel.basic.consume.assert_called_once_with(
            callback=callback, queue='obs.service'
        )

    def test_close_connection(self):
        self.connection.close.return_value = None
        self.channel.close.return_value = None
        self.service.close_connection()
        self.connection.close.assert_called_once_with()
        self.channel.close.assert_called_once_with()

    def test_persist_job_config(self):
        self.service.job_directory = 'tmp-dir/'

        with patch(open_name, create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            self.service.persist_job_config({'id': '1'})
            file_handle = mock_open.return_value.__enter__.return_value
            # Dict is mutable, mock compares the final value of Dict
            # not the initial value that was passed in.
            file_handle.write.assert_called_with(
                JsonFormat.json_message({
                    "id": "1",
                    "job_file": "tmp-dir/job-1.json"
                })
            )

    @patch('mash.services.mash_service.json.load')
    @patch('mash.services.mash_service.os.listdir')
    def test_restart_jobs(self, mock_os_listdir, mock_json_load):
        self.service.job_directory = 'tmp-dir'
        mock_os_listdir.return_value = ['job-123.json']
        mock_json_load.return_value = {'id': '1'}

        with patch(open_name, create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            mock_callback = Mock()
            self.service.restart_jobs(mock_callback)

            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.call_count == 1

        mock_callback.assert_called_once_with({'id': '1'})

    def test_unbind_queue(self):
        self.service.unbind_queue(
            'service', 'testing', '1'
        )
        self.service.channel.queue.unbind.assert_called_once_with(
            queue='testing.service', exchange='testing', routing_key='1'
        )

    def test_should_notify(self):
        result = self.service._should_notify(
            None, 'single', 'always', 'success', 'publisher'
        )
        assert result is False

        result = self.service._should_notify(
            'test@fake.com', 'single', 'always', 'success', 'publisher'
        )
        assert result is False

    def test_create_notification_content(self):
        msg = self.service._create_notification_content(
            '1', 'failed', 'always', 'deprecation', 3,
            'Invalid publish permissions!'
        )

        assert msg

    @patch('mash.services.mash_service.smtplib')
    def test_send_email_notification(self, mock_smtp):
        job_id = '12345678-1234-1234-1234-123456789012'
        to = 'test@fake.com'

        self.service.smtp_ssl = False
        self.service.smtp_host = 'localhost'
        self.service.smtp_port = 25
        self.service.smtp_user = to
        self.service.smtp_pass = None
        self.service.notification_subject = '[MASH] Job Status Update'

        smtp_server = MagicMock()
        mock_smtp.SMTP_SSL.return_value = smtp_server
        mock_smtp.SMTP.return_value = smtp_server

        # Send email without SSL
        self.service.send_email_notification(
            job_id, to, 'periodic', 'success', 'now', 'replication', 1
        )
        assert smtp_server.send_message.call_count == 1

        self.service.smtp_ssl = True
        self.service.smtp_pass = 'super.secret'

        # Send email with SSL
        self.service.send_email_notification(
            job_id, to, 'periodic', 'failed', 'now', 'replication', 1
        )
        assert smtp_server.send_message.call_count == 2

        # Send error
        self.service.service_exchange = 'testing'
        smtp_server.send_message.side_effect = Exception('Broke!')
        self.service.send_email_notification(
            job_id, to, 'single', 'success', 'now', 'testing', 1
        )
        self.service.log.warning.assert_called_once_with(
            'Unable to send notification email: Broke!'
        )
