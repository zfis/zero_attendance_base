# -*- coding: utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 - now Bytebrand Outsourcing AG (<http://www.bytebrand.net>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from pprint import pformat
from odoo import fields
from datetime import datetime, time
from odoo import models, fields, _, exceptions, api
from odoo import models
import logging

LOGGER = logging.getLogger(__name__)


class PublicHoliday(models.Model):
    _inherit = 'hr.holidays.public'

    @api.model
    def get_public_holidays(self, date_from_str, date_to_str):
        """
        Get public holidays that fall between :param date_from_str and :param date_to_str
        
        :param <str> date_from_str: a date-formatted string
        :param <str> date_to_str:a date-formatted string
        :return: [(<datetime.datetime> date_from, <datetime.datetime> date_to), ] Public Holiday Intervals
        """
        public_holidays = []

        date_from = fields.Datetime.from_string(date_from_str)
        date_to = fields.Datetime.from_string(date_to_str)
        years = range(date_from.year, date_to.year + 1)
        LOGGER.info("Getting Public Holidays in from {} to {}".format(date_from_str, date_to_str))

        for year in years:
            holidays = self.get_holidays_list(year)
            for holiday in holidays:
                if date_from_str <= holiday.date <= date_to_str:
                    LOGGER.debug("Public holiday matched: {}".format(holiday))
                    _date_form = (datetime.combine(date_from, time(0, 0, 0)))
                    _date_to = (datetime.combine(date_to, time(23, 59, 59)))
                    public_holidays.append((_date_form, _date_to))

        LOGGER.debug("All matching public holidays: \n{}".format(pformat(public_holidays)))
        return public_holidays
