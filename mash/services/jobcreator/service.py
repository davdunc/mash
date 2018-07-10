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

import json
import uuid

from jsonschema import FormatChecker, validate

from mash.csp import CSP
from mash.mash_exceptions import (
    MashJobCreatorException,
    MashValidationException
)
from mash.services.base_service import BaseService
from mash.services.jobcreator import create_job
from mash.services.jobcreator import schema


class JobCreatorService(BaseService):
    """
    Implementation of job creator service.

    Handles the orchestration of jobs for mash.
    """

    def post_init(self):
        """
        Initialize job creator service class.
        """
        self.set_logfile(self.config.get_log_file(self.service_exchange))
        self.provider_data = self.config.get_provider_data()
        self.services = self.config.get_service_names()

        self.bind_queue(
            self.service_exchange, self.add_account_key, self.listener_queue
        )
        self.bind_queue(
            self.service_exchange, self.delete_account_key, self.listener_queue
        )

        self.jobs = {}

        self.start()

    def _handle_listener_message(self, message):
        """
        Process add and delete account messages.
        """
        try:
            account_message = json.loads(message.body)
        except Exception:
            self.log.warning(
                'Invalid message received: {0}.'.format(message.body)
            )
        else:
            if message.method['routing_key'] == 'add_account':
                self.add_account(account_message)
            elif message.method['routing_key'] == 'delete_account':
                self.delete_account(account_message)
            else:
                self.log.warning(
                    'Received unknown message type: {0}. Message: {1}'.format(
                        message.method['routing_key'],
                        message.body
                    )
                )

        message.ack()

    def _handle_service_message(self, message):
        """
        Handle new and delete job messages.
        """
        try:
            job_doc = json.loads(message.body)
            if 'job_delete' in job_doc:
                self.publish_delete_job_message(job_doc['job_delete'])
            elif 'invalid_job' in job_doc:
                self.log.warning(
                    'Job failed, accounts do not exist.',
                    extra={'job_id': job_doc['invalid_job']}
                )
            elif 'start_job' in job_doc:
                self.send_job(job_doc['start_job'])
            else:
                self.process_new_job(job_doc)
        except Exception as error:
            self.log.error(
                'Invalid message received: {0}.'.format(error)
            )

        message.ack()

    def add_account(self, message):
        """
        Validate add account message and relay to credentials service.
        """
        csp_name = message.get('provider')

        if csp_name == CSP.ec2:
            message_schema = schema.add_account_ec2
        elif csp_name == CSP.azure:
            message_schema = schema.add_account_azure
        else:
            self.log.warning(
                'Support for {csp} Cloud Service not implemented.'.format(
                    csp=csp_name
                )
            )
            return

        try:
            validate(message, message_schema, format_checker=FormatChecker())
        except Exception as error:
            self.log.error(
                'Add account message is invalid: {0}'.format(error)
            )
            return
        else:
            self._publish(
                'credentials', self.add_account_key,
                json.dumps(message, sort_keys=True)
            )

    def delete_account(self, message):
        """
        Validate delete account message and relay to credentials service.
        """
        try:
            validate(
                message, schema.delete_account, format_checker=FormatChecker()
            )
        except Exception as error:
            self.log.error(
                'Delete account message is invalid: {0}'.format(error)
            )
            return
        else:
            self._publish(
                'credentials', self.delete_account_key,
                json.dumps(message, sort_keys=True)
            )

    def process_new_job(self, job_doc):
        """
        Validate job and send account check message to credentials service.
        """
        csp_name = job_doc.get('provider')

        if csp_name == CSP.ec2:
            message_schema = schema.ec2_job_message
        elif csp_name == CSP.azure:
            message_schema = schema.azure_job_message
        else:
            raise MashJobCreatorException(
                'Support for {csp} Cloud Service not implemented.'.format(
                    csp=csp_name
                )
            )

        try:
            validate(job_doc, message_schema, format_checker=FormatChecker())
        except Exception as error:
            raise MashValidationException(error)
        else:
            job_id = str(uuid.uuid4())
            self.jobs[job_id] = job_doc

            account_check_message = {
                'credentials_job_check': {
                    'id': job_id,
                    'provider': job_doc['provider'],
                    'provider_accounts': job_doc['provider_accounts'],
                    'provider_groups': job_doc['provider_groups'],
                    'requesting_user': job_doc['requesting_user']
                }
            }

            self.publish_job_doc(
                'credentials',
                json.dumps(account_check_message, sort_keys=True)
            )

    def publish_delete_job_message(self, job_id):
        """
        Publish delete job message to obs and credentials services.

        This will flush the job with the given id out of the pipeline.
        """
        self.log.info(
            'Deleting job with ID: {0}.'.format(job_id),
            extra={'job_id': job_id}
        )

        delete_message = {
            "obs_job_delete": job_id
        }
        self._publish(
            'obs', self.job_document_key, json.dumps(delete_message)
        )

        delete_message = {
            "credentials_job_delete": job_id
        }
        self._publish(
            'credentials', self.job_document_key, json.dumps(delete_message)
        )

    def publish_job_doc(self, service, job_doc):
        """
        Publish the job_doc message to the given service exchange.
        """
        self._publish(service, self.job_document_key, job_doc)

    def send_job(self, message):
        """
        Create instance of job and send to all services to initiate job.

        Message from credentials service contains account info for the
        provider.
        """
        job_id = message['id']
        job_doc = self.jobs[job_id]
        accounts_info = message['accounts_info']
        job = create_job(job_id, job_doc, accounts_info, self.provider_data)

        self.log.info(
            'Started a new job: {0}'.format(json.dumps(job_doc, indent=2)),
            extra={'job_id': job.id}
        )

        # Credentials job always sent for all jobs.
        self.publish_job_doc('credentials', job.get_credentials_message())

        for service in self.services:
            if service == 'deprecation':
                self.publish_job_doc(
                    'deprecation', job.get_deprecation_message()
                )
            elif service == 'obs':
                self.publish_job_doc(
                    'obs', job.get_obs_message()
                )
            elif service == 'pint':
                self.publish_job_doc(
                    'pint', job.get_pint_message()
                )
            elif service == 'publisher':
                self.publish_job_doc(
                    'publisher', job.get_publisher_message()
                )
            elif service == 'replication':
                self.publish_job_doc(
                    'replication', job.get_replication_message()
                )
            elif service == 'testing':
                self.publish_job_doc(
                    'testing', job.get_testing_message()
                )
            elif service == 'uploader':
                self.publish_job_doc(
                    'uploader', job.get_uploader_message()
                )

            if service == job.last_service:
                break

        del self.jobs[job_id]

    def start(self):
        """
        Start job creator service.
        """
        self.consume_queue(self._handle_service_message)
        self.consume_queue(
            self._handle_listener_message, queue_name=self.listener_queue
        )
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            pass
        except Exception:
            raise
        finally:
            self.stop()

    def stop(self):
        """
        Stop job creator service.

        Stop consuming queues and close pika connections.
        """
        self.channel.stop_consuming()
        self.close_connection()
