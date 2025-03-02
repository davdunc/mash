import pytest

from unittest.mock import call, Mock, patch

from mash.services.test.azure_job import AzureTestJob
from mash.mash_exceptions import MashTestException


class TestAzureTestJob(object):
    def setup(self):
        self.job_config = {
            'id': '1',
            'last_service': 'test',
            'cloud': 'azure',
            'requesting_user': 'user1',
            'ssh_private_key_file': 'private_ssh_key.file',
            'account': 'test-azure',
            'resource_group': 'srg',
            'container': 'sc',
            'storage_account': 'ssa',
            'region': 'East US',
            'tests': ['test_stuff'],
            'utctime': 'now',
        }
        self.config = Mock()
        self.config.get_ssh_private_key_file.return_value = \
            'private_ssh_key.file'
        self.config.get_img_proof_timeout.return_value = 600

    def test_test_azure_missing_key(self):
        del self.job_config['account']

        with pytest.raises(MashTestException):
            AzureTestJob(self.job_config, self.config)

    @patch('mash.services.test.azure_job.AzureImage')
    @patch('mash.services.test.azure_job.os')
    @patch('mash.services.test.azure_job.create_ssh_key_pair')
    @patch('mash.services.test.azure_job.random')
    @patch('mash.utils.mash_utils.NamedTemporaryFile')
    @patch('mash.services.test.azure_job.test_image')
    def test_test_run_azure_test(
        self, mock_test_image, mock_temp_file, mock_random,
        mock_create_ssh_key_pair, mock_os, mock_azure_image
    ):
        tmp_file = Mock()
        tmp_file.name = '/tmp/acnt.file'
        mock_temp_file.return_value = tmp_file
        mock_test_image.return_value = (
            0,
            {
                'tests': [
                    {
                        "outcome": "passed",
                        "test_index": 0,
                        "name": "test_sles_azure_metadata.py::test_sles_azure_metadata[paramiko://10.0.0.10]"
                    }
                ],
                'summary': {
                    "duration": 2.839970827102661,
                    "passed": 1,
                    "num_tests": 1
                },
                'info': {
                    'log_file': 'test.log',
                    'results_file': 'test.results',
                    'instance': 'instance-abc'
                }
            }
        )
        mock_random.choice.return_value = 'Standard_A0'
        mock_os.path.exists.return_value = False

        azure_image = Mock()
        mock_azure_image.return_value = azure_image

        job = AzureTestJob(self.job_config, self.config)
        mock_create_ssh_key_pair.assert_called_once_with('private_ssh_key.file')
        job.credentials = {
            'test-azure': {
                'fake': '123',
                'credentials': '321'
            }
        }
        job.status_msg['cloud_image_name'] = 'name'
        job.status_msg['blob_name'] = 'name.vhd'
        job.cloud_image_name = 'test_image'
        job._log_callback = Mock()
        job.status_msg['images'] = {'bios': 'name'}
        job.run_job()

        mock_test_image.assert_called_once_with(
            'azure',
            cleanup=True,
            description=job.description,
            distro='sles',
            image_id='name',
            instance_type='Standard_A0',
            img_proof_timeout=600,
            log_level=10,
            region='East US',
            service_account_file='/tmp/acnt.file',
            ssh_private_key_file='private_ssh_key.file',
            ssh_user='azureuser',
            tests=['test_stuff'],
            log_callback=job._log_callback,
            prefix_name='mash'
        )
        job._log_callback.info.reset_mock()

        # Failed job test
        mock_test_image.side_effect = Exception('Tests broken!')
        azure_image.delete_storage_blob.side_effect = Exception(
            'Cleanup blob failed!'
        )

        job.run_job()

        assert 'Tests broken!' in job._log_callback.error.mock_calls[0][1][0]
        assert azure_image.delete_compute_image.call_count == 1
        assert azure_image.delete_storage_blob.call_count == 1

        # Failed cleanup image
        azure_image.delete_compute_image.side_effect = Exception(
            'Cleanup image failed!'
        )
        azure_image.delete_storage_blob.side_effect = None

        job.run_job()

        job._log_callback.warning.assert_has_calls([
            call('Image tests failed in region: East US.'),
            call('Failed to cleanup image page blob: Cleanup blob failed!'),
            call('Image tests failed in region: East US.'),
            call('Failed to cleanup image: Cleanup image failed!')
        ])
