from pytest import raises
from unittest.mock import MagicMock, patch, Mock

from mash.services.deprecation.gce_job import GCEDeprecationJob
from mash.mash_exceptions import MashDeprecationException


class TestGCEDeprecationJob(object):
    def setup(self):
        self.job_config = {
            'id': '1',
            'last_service': 'deprecation',
            'cloud': 'gce',
            'requesting_user': 'user1',
            'old_cloud_image_name': 'old_image_123',
            'deprecation_accounts': ['test-gce'],
            'utctime': 'now'
        }

        self.config = Mock()
        self.job = GCEDeprecationJob(self.job_config, self.config)
        self.job.credentials = {
            'test-gce': {
                'client_email': 'test@gce.com',
                'project_id': '1234567890'
            }
        }

    def test_deprecation_gce_missing_key(self):
        del self.job_config['deprecation_accounts']

        with raises(MashDeprecationException):
            GCEDeprecationJob(self.job_config, self.config)

    @patch.object(GCEDeprecationJob, 'send_log')
    @patch('mash.services.deprecation.gce_job.Provider')
    @patch('mash.services.deprecation.gce_job.get_driver')
    def test_deprecate(self, mock_get_driver, mock_provider, mock_send_log):
        compute_engine = MagicMock()
        mock_get_driver.return_value = compute_engine

        compute_driver = MagicMock()
        compute_engine.return_value = compute_driver

        self.job.run_job()

        assert compute_driver.ex_deprecate_image.call_count == 1
        assert self.job.status == 'success'
        mock_send_log.assert_called_once_with(
            'Deprecated image old_image_123.'
        )

    def test_deprecate_no_old_image(self):
        self.job.old_cloud_image_name = None
        self.job.run_job()
        assert self.job.status == 'success'

    @patch.object(GCEDeprecationJob, 'send_log')
    @patch('mash.services.deprecation.gce_job.Provider')
    @patch('mash.services.deprecation.gce_job.get_driver')
    def test_deprecate_exception(
        self, mock_get_driver, mock_provider, mock_send_log
    ):
        compute_engine = MagicMock()
        mock_get_driver.return_value = compute_engine

        compute_driver = MagicMock()
        compute_driver.ex_deprecate_image.side_effect = Exception('Failed!')
        compute_engine.return_value = compute_driver

        self.job.run_job()

        mock_send_log.assert_called_once_with(
            'There was an error deprecating image in test-gce: Failed!',
            False
        )
        assert self.job.status == 'failed'
