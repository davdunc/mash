# Copyright (c) 2018 SUSE Linux GmbH.  All rights reserved.
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


class Defaults(object):
    """
    Default values
    """
    @classmethod
    def get_config(self):
        return '/etc/mash/mash_config.yaml'

    @classmethod
    def get_encryption_keys_file(self):
        return '/var/lib/mash/encryption_keys'

    @classmethod
    def get_base_job_directory(self):
        return '/var/lib/mash/'

    @classmethod
    def get_job_directory(self, service_name):
        return '{0}_jobs/'.format(service_name)

    @classmethod
    def get_jwt_algorithm(self):
        return 'HS256'

    @classmethod
    def get_log_directory(self):
        return '/var/log/mash/'

    @classmethod
    def get_service_names(self):
        return [
            'obs', 'upload', 'create', 'test', 'raw_image_upload',
            'replicate', 'publish', 'deprecate'
        ]

    @staticmethod
    def get_amqp_host():
        return 'localhost'

    @staticmethod
    def get_amqp_user():
        return 'guest'

    @staticmethod
    def get_amqp_pass():
        return 'guest'

    @classmethod
    def get_non_credential_service_names(self):
        return ['obs']

    @classmethod
    def get_azure_max_retry_attempts(self):
        return 5

    @staticmethod
    def get_azure_max_workers():
        return 5

    @staticmethod
    def get_smtp_host():
        return 'localhost'

    @staticmethod
    def get_smtp_port():
        return 25

    @staticmethod
    def get_smtp_ssl():
        return False

    @staticmethod
    def get_notification_subject():
        return '[MASH] Job Status Update'

    @staticmethod
    def get_credentials_url():
        return 'http://localhost:8080/'

    @staticmethod
    def get_email_allowlist():
        return []

    @staticmethod
    def get_domain_allowlist():
        return []

    @staticmethod
    def get_max_oci_attempts():
        return 100

    @staticmethod
    def get_max_oci_wait_seconds():
        return 2400

    @staticmethod
    def get_oci_upload_process_count():
        return 3

    @staticmethod
    def get_base_thread_pool_count():
        return 10

    @staticmethod
    def get_publish_thread_pool_count():
        return 50

    @staticmethod
    def get_auth_methods():
        return ['password']

    @staticmethod
    def get_download_dir():
        return '/var/lib/mash/images/'

    @staticmethod
    def get_database_api_url():
        return 'http://localhost:5007/'
