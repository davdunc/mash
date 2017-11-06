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
from mash.mash_exceptions import MashLogSetupException


class MashLog(object):
    @classmethod
    def set_logfile(self, log, logfile):
        try:
            logfile_handler = logging.FileHandler(
                filename=logfile, encoding='utf-8'
            )
            logfile_handler.setFormatter(
                logging.Formatter(
                    '%(levelname)-6s: %(asctime)-8s | %(message)s', '%H:%M:%S'
                )
            )
            log.addHandler(logfile_handler)
        except Exception as e:
            raise MashLogSetupException(
                'Log setup failed: {0}'.format(e)
            )
