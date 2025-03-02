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

import copy

from mash.services.api.v1.schema import string_with_example
from mash.services.api.v1.schema.jobs import base_job_message

gce_job_message = copy.deepcopy(base_job_message)
gce_job_message['properties']['family'] = string_with_example(
    'opensuse-leap',
    description='Family to add the image to. Image families help group '
                'related images together and provide versioning of images.'
)
gce_job_message['properties']['months_to_deletion'] = {
    'type': 'integer',
    'minimum': 0,
    'example': 6,
    'description': 'When an image is deprecated it can be marked for '
                   'deletion. The image is deleted after a certain number'
                   'of months has passed. This is 6 months by default.'
}
gce_job_message['properties']['guest_os_features'] = {
    'type': 'array',
    'items': string_with_example('UEFI_COMPATIBLE'),
    'uniqueItems': True,
    'minItems': 1,
    'example': ['UEFI_COMPATIBLE'],
    'description': 'A list of guest os features to add when creating the '
                   'image.'
}
gce_job_message['properties']['test_fallback_regions'] = {
    'type': 'array',
    'items': string_with_example('us-west1-a'),
    'minItems': 0,
    'example': ['us-west1-a'],
    'description': 'A list of fallback regions to use if the instance test '
                   'fails on a recoverable error. This allows mash to test '
                   'the image multiple times for certain expected issues.'
}
gce_job_message['properties']['testing_account'] = string_with_example(
    'testaccount1',
    description='The account to use for launching and test an instance '
                'of the image. This is required if the cloud_account is a '
                'publishing account which cannot launch instances.'
)
gce_job_message['properties']['cloud_account'] = string_with_example(
    'account1',
    description='The name of the cloud account to use for image '
                'publishing.'
)
gce_job_message['properties']['bucket'] = string_with_example(
    'images',
    description='The name of the storage bucket to use for uploading the '
                'image tarball.'
)
gce_job_message['properties']['region'] = string_with_example(
    'us-east1-a',
    description='The zone to use for launching and test an instance '
                'of the image. This should be in zone format such as the '
                'example.'
)
gce_job_message['properties']['image_project'] = string_with_example(
    'suse-cloud',
    description='The image project for the image that will be tested. '
                'If using a test project for test the public image '
                'project where the image is published is required.'
)
gce_job_message['required'].append('cloud_account')
gce_job_message['properties']['image']['example'] = 'openSUSE-Leap-15.0-GCE'
gce_job_message['properties']['cloud_image_name']['example'] = \
    'opensuse-leap-15-v{date}'
gce_job_message['properties']['old_cloud_image_name']['example'] = \
    'opensuse-leap-15-v20190520'
gce_job_message['properties']['image_description']['example'] = \
    'openSUSE Leap 15'
gce_job_message['properties']['instance_type']['example'] = 'n1-standard-1'
