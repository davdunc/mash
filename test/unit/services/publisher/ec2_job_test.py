from pytest import raises
from unittest.mock import Mock, patch

from mash.mash_exceptions import MashPublisherException
from mash.services.publisher.ec2_job import EC2PublisherJob


class TestEC2PublisherJob(object):
    def setup(self):
        self.job_config = {
            'allow_copy': '123,321',
            'id': '1',
            'last_service': 'publisher',
            'requesting_user': 'user1',
            'cloud': 'ec2',
            'publish_regions': [
                {
                    'account': 'test-aws',
                    'target_regions': ['us-east-2']
                }
            ],
            'share_with': 'all',
            'utctime': 'now'
        }

        self.config = Mock()
        self.job = EC2PublisherJob(self.job_config, self.config)
        self.job._log_callback = Mock()
        self.job.credentials = {
            'test-aws': {
                'access_key_id': '123456',
                'secret_access_key': '654321',
                'ssh_key_name': 'key-123',
                'ssh_private_key': 'key123'
            }
        }
        self.job.source_regions = {
            'cloud_image_name': 'image_name_123',
            'us-east-2': 'image-id'
        }
        self.job._log_callback = Mock()

    def test_publish_ec2_missing_key(self):
        del self.job_config['publish_regions']

        with raises(MashPublisherException):
            EC2PublisherJob(self.job_config, self.config)

    @patch('mash.services.publisher.ec2_job.EC2PublishImage')
    def test_publish(self, mock_ec2_publish_image):
        publisher = Mock()
        mock_ec2_publish_image.return_value = publisher
        self.job.run_job()

        mock_ec2_publish_image.assert_called_once_with(
            access_key='123456', allow_copy='123,321', image_name='image_name_123',
            secret_key='654321', visibility='all', log_callback=self.job._log_callback
        )

        publisher.set_region.assert_called_once_with('us-east-2')

        assert publisher.publish_images.call_count == 1
        assert self.job.status == 'success'

    @patch('mash.services.publisher.ec2_job.EC2PublishImage')
    def test_publish_exception(
        self, mock_ec2_publish_image
    ):
        publisher = Mock()
        publisher.publish_images.side_effect = Exception('Failed to publish.')
        mock_ec2_publish_image.return_value = publisher

        msg = 'An error publishing image image_name_123 in us-east-2.' \
            ' Failed to publish.'
        with raises(MashPublisherException) as e:
            self.job.run_job()
        assert msg == str(e.value)
