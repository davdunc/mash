# Copyright (c) 2019 SUSE LLC.  All rights reserved.
#
# This file is part of mash.
#
# mash is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# mash is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with mash.  If not, see <http://www.gnu.org/licenses/>
#

from collections import defaultdict

from mash.mash_exceptions import MashJobCreatorException
from mash.utils.json_format import JsonFormat


class BaseJob(object):
    """
    Base job message class.

    Handles incoming job requests.
    """
    def __init__(self, accounts_info, cloud_data, kwargs):
        self.accounts_info = accounts_info
        self.cloud_data = cloud_data
        self.target_account_info = {}

        try:
            self.id = kwargs['job_id']
            self.cloud = kwargs['cloud']
            self.requesting_user = kwargs['requesting_user']
            self.last_service = kwargs['last_service']
            self.utctime = kwargs['utctime']
            self.image = kwargs['image']
            self.cloud_image_name = kwargs['cloud_image_name']
            self.image_description = kwargs['image_description']
            self.distro = kwargs['distro']
            self.download_url = kwargs['download_url']
        except KeyError as error:
            raise MashJobCreatorException(
                'Jobs require a(n) {0} key in the job doc.'.format(
                    error
                )
            )

        self.tests = kwargs.get('tests', [])
        self.conditions = kwargs.get('conditions')
        self.instance_type = kwargs.get('instance_type')
        self.old_cloud_image_name = kwargs.get('old_cloud_image_name')
        self.cleanup_images = kwargs.get('cleanup_images')
        self.cloud_architecture = kwargs.get('cloud_architecture', 'x86_64')
        self.cloud_accounts = self._get_accounts_data(
            kwargs.get('cloud_accounts')
        )
        self.cloud_groups = kwargs.get('cloud_groups', [])
        self.notification_email = kwargs.get('notification_email')
        self.notification_type = kwargs.get('notification_type', 'single')
        self.profile = kwargs.get('profile')
        self.kwargs = kwargs

        self.base_message = {
            'id': self.id,
            'utctime': self.utctime,
            'last_service': self.last_service
        }

        if self.notification_email:
            self.base_message['notification_email'] = self.notification_email
            self.base_message['notification_type'] = self.notification_type

        self.post_init()
        self.get_account_info()

    def get_account_info(self):
        """
        Parse dictionary of account data from accounts file.

        Implementation in child class.
        """
        raise NotImplementedError(
            'This {0} class does not implement the '
            'get_account_info method.'.format(
                self.__class__.__name__
            )
        )

    def _get_accounts_data(self, cloud_accounts):
        """
        Convert cloud accounts from a list to dictionary.

        This simplifies data lookup.
        """
        account_data = defaultdict(dict)

        if cloud_accounts:
            for account in cloud_accounts:
                account_data[account['name']] = account

        return account_data

    def get_credentials_message(self):
        """
        Build credentials job message.
        """
        accounts = []
        for source_region, value in self.target_account_info.items():
            accounts.append(value['account'])

        credentials_message = {
            'credentials_job': {
                'cloud': self.cloud,
                'cloud_accounts': accounts,
                'requesting_user': self.requesting_user
            }
        }
        credentials_message['credentials_job'].update(self.base_message)

        return JsonFormat.json_message(credentials_message)

    def get_deprecation_message(self):
        """
        Build deprecation job message.

        Implement in child class.
        """
        raise NotImplementedError(
            'This {0} class does not implement the '
            'get_deprecation_message method.'.format(
                self.__class__.__name__
            )
        )

    def get_obs_message(self):
        """
        Build OBS job message.
        """
        obs_message = {
            'obs_job': {
                'download_url': self.download_url,
                'image': self.image
            }
        }
        obs_message['obs_job'].update(self.base_message)

        if self.cloud_architecture:
            obs_message['obs_job']['cloud_architecture'] = \
                self.cloud_architecture

        if self.conditions:
            obs_message['obs_job']['conditions'] = self.conditions

        if self.profile:
            obs_message['obs_job']['profile'] = self.profile

        return JsonFormat.json_message(obs_message)

    def get_publisher_message(self):
        """
        Build publisher job message.

        Implementation in child class.
        """
        raise NotImplementedError(
            'This {0} class does not implement the '
            'get_publisher_message method.'.format(
                self.__class__.__name__
            )
        )

    def get_replication_message(self):
        """
        Build replication job message and publish to replication exchange.
        """
        raise NotImplementedError(
            'This {0} class does not implement the '
            'get_replication_message method.'.format(
                self.__class__.__name__
            )
        )

    def get_replication_source_regions(self):
        """
        Return a dictionary of replication source regions.

        Implementation in child class.
        """
        raise NotImplementedError(
            'This {0} class does not implement the '
            'get_replication_source_regions method.'.format(
                self.__class__.__name__
            )
        )

    def get_testing_message(self):
        """
        Build testing job message.
        """
        testing_message = {
            'testing_job': {
                'cloud': self.cloud,
                'tests': self.tests,
                'test_regions': self.get_testing_regions()
            }
        }

        if self.distro:
            testing_message['testing_job']['distro'] = self.distro

        if self.instance_type:
            testing_message['testing_job']['instance_type'] = \
                self.instance_type

        if self.last_service == 'testing' and \
                self.cleanup_images in [True, None]:
            testing_message['testing_job']['cleanup_images'] = True

        testing_message['testing_job'].update(self.base_message)

        return JsonFormat.json_message(testing_message)

    def get_testing_regions(self):
        """
        Return a dictionary of target test regions.

        Implementation in child class.
        """
        raise NotImplementedError(
            'This {0} class does not implement the '
            'get_testing_regions method.'.format(
                self.__class__.__name__
            )
        )

    def get_uploader_message(self):
        """
        Build uploader job message.
        """
        uploader_message = {
            'uploader_job': {
                'cloud_image_name': self.cloud_image_name,
                'cloud': self.cloud,
                'image_description': self.image_description,
                'target_regions': self.get_uploader_regions()
            }
        }
        uploader_message['uploader_job'].update(self.base_message)

        if self.cloud_architecture:
            uploader_message['uploader_job']['cloud_architecture'] = \
                self.cloud_architecture

        return JsonFormat.json_message(uploader_message)

    def get_uploader_regions(self):
        """
        Return a dictionary of target uploader regions.

        Implementation in child class.
        """
        raise NotImplementedError(
            'This {0} class does not implement the '
            'get_uploader_regions method.'.format(
                self.__class__.__name__
            )
        )

    def post_init(self):
        """
        Post initialization method.

        Implementation in child class.
        """
        pass
