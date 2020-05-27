# Copyright (c) 2017 SUSE Linux GmbH.  All rights reserved.
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
import logging
import sys
import traceback

# project
from mash.mash_exceptions import MashException
from mash.services.uploader.config import UploaderConfig
from mash.services.listener_service import ListenerService
from mash.services.job_factory import BaseJobFactory

from mash.services.uploader.azure_job import AzureUploaderJob
from mash.services.uploader.azure_raw_job import AzureRawUploaderJob
from mash.services.uploader.azure_sas_job import AzureSASUploaderJob
from mash.services.uploader.gce_job import GCEUploaderJob
from mash.services.no_op_job import NoOpJob
from mash.services.uploader.s3bucket_job import S3BucketUploaderJob
from mash.services.uploader.oci_job import OCIUploaderJob


def main():
    """
    mash - uploader service application entry point
    """
    try:
        logging.basicConfig()
        log = logging.getLogger('MashService')
        log.setLevel(logging.DEBUG)

        service_name = 'uploader'

        # Create job factory
        job_factory = BaseJobFactory(
            service_name=service_name,
            job_types={
                'azure': AzureUploaderJob,
                'azure_raw': AzureRawUploaderJob,
                'azure_sas': AzureSASUploaderJob,
                'ec2': NoOpJob,
                's3bucket': S3BucketUploaderJob,
                'gce': GCEUploaderJob,
                'oci': OCIUploaderJob
            }
        )

        # run service, enter main loop
        ListenerService(
            service_exchange=service_name,
            config=UploaderConfig(),
            custom_args={
                'listener_msg_args': ['image_file'],
                'status_msg_args': ['image_file', 'source_regions'],
                'job_factory': job_factory
            }
        )
    except MashException as e:
        # known exception
        log.error('{0}: {1}'.format(type(e).__name__, format(e)))
        traceback.print_exc()
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
    except SystemExit:
        # user exception, program aborted by user
        sys.exit(0)
    except Exception as e:
        # exception we did no expect, show python backtrace
        log.error('Unexpected error: {0}'.format(e))
        traceback.print_exc()
        sys.exit(1)
