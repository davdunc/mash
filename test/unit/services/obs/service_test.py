from pytest import raises
from unittest.mock import patch
from unittest.mock import call
from unittest.mock import Mock

from test.unit.test_helper import (
    patch_open
)

from mash.services.obs.service import OBSImageBuildResultService
from mash.services.mash_service import MashService


class TestOBSImageBuildResultService(object):

    @patch('mash.services.obs.service.os.makedirs')
    @patch('mash.services.obs.service.setup_logfile')
    @patch.object(OBSImageBuildResultService, '_process_message')
    @patch.object(OBSImageBuildResultService, '_send_job_result_for_upload')
    @patch('mash.services.obs.service.restart_jobs')
    @patch.object(MashService, '__init__')
    @patch('os.listdir')
    @patch('logging.getLogger')
    @patch('atexit.register')
    def setup_method(
        self, method, mock_register, mock_log, mock_listdir, mock_MashService,
        mock_restart_jobs, mock_send_job_result_for_upload,
        mock_process_message,
        mock_setup_logfile, mock_makedirs
    ):
        config = Mock()
        config.get_log_file.return_value = 'logfile'
        config.get_job_directory.return_value = '/var/lib/mash/obs_jobs/'
        self.log = Mock()
        mock_listdir.return_value = ['job']
        mock_MashService.return_value = None

        self.obs_result = OBSImageBuildResultService()

        self.obs_result.log = self.log
        self.obs_result.config = config
        self.obs_result.consume_queue = Mock()
        self.obs_result.bind_service_queue = Mock()
        self.obs_result.channel = Mock()
        self.obs_result.channel.is_open = True
        self.obs_result.close_connection = Mock()
        self.obs_result.service_exchange = 'obs'
        self.obs_result.service_queue = 'service'
        self.obs_result.next_service = 'upload'
        self.obs_result.job_document_key = 'job_document'
        self.obs_result.listener_msg_key = 'listener_msg'

        self.obs_result.post_init()

        config.get_job_directory.assert_called_once_with('obs')
        mock_makedirs.assert_called_once_with(
            '/var/lib/mash/obs_jobs/', exist_ok=True
        )

        mock_setup_logfile.assert_called_once_with('logfile')
        mock_restart_jobs.assert_called_once_with(
            '/var/lib/mash/obs_jobs/',
            self.obs_result._start_job
        )

        self.obs_result.consume_queue.assert_called_once_with(
            mock_process_message, 'service', 'obs'
        )
        self.obs_result.channel.start_consuming.assert_called_once_with()

        self.obs_result.channel.start_consuming.side_effect = Exception
        with raises(Exception):
            self.obs_result.post_init()
            self.obs_result.close_connection.assert_called_once_with()

        self.obs_result.channel.start_consuming.side_effect = KeyboardInterrupt()
        self.obs_result.post_init()

    @patch.object(MashService, '_publish')
    @patch.object(OBSImageBuildResultService, '_delete_job')
    def test_send_job_result_for_upload(
        self, mock_delete_job, mock_publish
    ):
        self.obs_result.jobs['815'] = Mock()
        self.obs_result.jobs['815'].job_nonstop = False
        self.obs_result._send_job_result_for_upload('815', {})
        mock_delete_job.assert_called_once_with('815')
        mock_publish.assert_called_once_with(
            'obs', 'listener_msg', '{}'
        )

    def test_send_control_response_local(self):
        result = {
            'message': 'message',
            'ok': False
        }
        self.obs_result._send_control_response(result, '4711')
        self.obs_result.log.error.assert_called_once_with(
            'message',
            extra={'job_id': '4711'}
        )

    def test_send_control_response_public(self):
        result = {
            'message': 'message',
            'ok': True
        }
        self.obs_result._send_control_response(result)
        self.obs_result.log.info.assert_called_once_with(
            'message',
            extra={}
        )

    @patch.object(OBSImageBuildResultService, '_publish')
    @patch.object(OBSImageBuildResultService, '_delete_job')
    @patch.object(OBSImageBuildResultService, '_add_job')
    @patch.object(OBSImageBuildResultService, '_send_control_response')
    def test_process_message(
        self, mock_send_control_response, mock_add_job, mock_delete_job,
        mock_publish
    ):
        message = Mock()
        message.method = {'routing_key': 'job_document'}
        message.body = '{"obs_job":{"id": "4711","download_url": ' + \
            '"http://download.suse.de/ibs/Devel:/PubCloud:/Stable:/' + \
            'Images12/images","image": ' + \
            '"test-image-docker","utctime": ' + \
            '"always"}}'
        self.obs_result._process_message(message)
        message.ack.assert_called_once_with()
        mock_add_job.assert_called_once_with(
            {
                'obs_job': {
                    "download_url": "http://download.suse.de/ibs/Devel:/"
                                    "PubCloud:/Stable:/Images12/images",
                    'image': 'test-image-docker',
                    'id': '4711',
                    'utctime': 'always'
                }
            }
        )

        message.body = '{"job_delete": "4711"}'
        self.obs_result._process_message(message)

        message.body = 'foo'
        self.obs_result._process_message(message)
        assert mock_send_control_response.call_args_list == [
            call(mock_add_job.return_value, '4711'),
            call(
                {
                    'message':
                        "No idea what to do with: {'job_delete': '4711'}",
                    'ok': False
                },
                None
            ),
            call(
                {
                    'message':
                        'JSON:deserialize error: foo : '
                        'Expecting value: line 1 column 1 (char 0)',
                    'ok': False
                }
            )
        ]

    @patch('mash.services.obs.service.persist_json')
    @patch.object(OBSImageBuildResultService, '_start_job')
    @patch_open
    def test_add_job(self, mock_open, mock_start_job, mock_persist_json):
        self.obs_result.job_directory = 'tmp/'
        job_data = {
            "obs_job": {
                "id": "123",
                "download_url": "http://download.suse.de/ibs/Devel:/"
                                "PubCloud:/Stable:/Images12/images",
                "image": "test-image-oem",
                "last_service": "publish",
                "utctime": "now",
                "conditions": [
                    {
                        "package_name": "openssl",
                        "version": "4.13.1",
                        "release": "1.1",
                        "condition": ">="
                    },
                    {"version": "1.42.1"}
                ]
            }
        }
        self.obs_result._add_job(job_data)
        mock_persist_json.assert_called_once_with(
            'tmp/job-123.json',
            job_data['obs_job']
        )
        mock_start_job.assert_called_once_with(job_data['obs_job'])

    @patch('os.remove')
    def test_delete_job(self, mock_os_remove):
        assert self.obs_result._delete_job('815') == {
            'message': 'Job does not exist, can not delete it', 'ok': False
        }
        job_worker = Mock()
        job_worker.job_file = 'job_file'
        self.obs_result.jobs = {'815': job_worker}
        assert self.obs_result._delete_job('815') == {
            'message': 'Job Deleted', 'ok': True
        }
        mock_os_remove.assert_called_once_with('job_file')
        job_worker.stop_watchdog.assert_called_once_with()
        assert '815' not in self.obs_result.jobs
        self.obs_result.jobs = {'815': job_worker}
        mock_os_remove.side_effect = Exception('remove_error')
        assert self.obs_result._delete_job('815') == {
            'message': 'Job deletion failed: remove_error', 'ok': False
        }

    @patch('mash.services.obs.service.OBSImageBuildResult')
    def test_start_job_with_conditions(self, mock_OBSImageBuildResult):
        job_worker = Mock()
        mock_OBSImageBuildResult.return_value = job_worker
        self.obs_result._send_job_response = Mock()
        self.obs_result._send_job_result_for_upload = Mock()
        data = {
            "id": "123",
            "job_file": "tempfile",
            "download_url": "http://download.suse.de/ibs/Devel:/"
                            "PubCloud:/Stable:/Images12/images",
            "image": "test-image-oem",
            "last_service": "publish",
            "utctime": "now",
            "log_callback": Mock(),
            "conditions": [
                {
                    "package_name": "openssl",
                    "version": "4.13.1",
                    "release": "1.1",
                    "condition": ">="
                },
                {"version": "1.42.1"}
            ],
            "cloud_architecture": "aarch64",
            "notification_email": "test@fake.com",
            "notify": True,
            "profile": "Proxy",
            "conditions_wait_time": 500,
            "disallow_licenses": ["MIT"],
            "disallow_packages": ["*-mini"]
        }
        self.obs_result._start_job(data)
        job_worker.set_result_handler.assert_called_once_with(
            self.obs_result._send_job_result_for_upload
        )
        job_worker.start_watchdog.assert_called_once_with(
            isotime=None
        )

    @patch('mash.services.obs.service.OBSImageBuildResult')
    def test_start_job_without_conditions(self, mock_OBSImageBuildResult):
        job_worker = Mock()
        mock_OBSImageBuildResult.return_value = job_worker
        data = {
            "id": "123",
            "job_file": "tempfile",
            "download_url": "http://download.suse.de/ibs/Devel:/"
                            "PubCloud:/Stable:/Images12/images",
            "image": "test-image-oem",
            "last_service": "publish",
            "utctime": "now"
        }
        self.obs_result._start_job(data)
        job_worker.start_watchdog.assert_called_once_with(
            isotime=None
        )

    @patch('mash.services.obs.service.OBSImageBuildResult')
    def test_start_job_at_utctime(self, mock_OBSImageBuildResult):
        job_worker = Mock()
        mock_OBSImageBuildResult.return_value = job_worker
        data = {
            "id": "123",
            "job_file": "tempfile",
            "download_url": "http://download.suse.de/ibs/Devel:/"
                            "PubCloud:/Stable:/Images12/images",
            "image": "test-image-oem",
            "last_service": "publish",
            "utctime": "Wed Oct 11 17:50:26 UTC 2017"
        }
        self.obs_result._start_job(data)
        job_worker.start_watchdog.assert_called_once_with(
            isotime='2017-10-11T17:50:26+00:00'
        )
