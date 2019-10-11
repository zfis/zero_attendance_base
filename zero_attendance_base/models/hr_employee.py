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

from datetime import datetime, time
from dateutil import rrule
from odoo import models, fields, _, exceptions, api
from pprint import pformat
import logging

LOGGER = logging.getLogger(__name__)


class Employee(models.Model):
    """ Inherited Employee Model """
    _inherit = 'hr.employee'

    # fixme: move these methods to attendance model, I think it is the right place to manipulate attendance
    @api.multi
    def count_uncovered_missing_attendance_hours(self, work_schedule, date_from_str, date_to_str):
        """
        Counts the missing/un-attended workday hours that the employee took in a workday he/she actually was present on,
        but he/she took no permission/leave for those hours
        :param resource.calendar work_schedule: work schedule of employee
        :param str date_from_str: start of period of calculation
        :param str date_to_str: end of period of calculation
        :return float number_of_hours:
        """
        self.ensure_one()
        attendance_model = self.env['hr.attendance']
        absent_workdays = self.get_absent_workdays(work_schedule, date_from_str, date_to_str)
        uncovered_missing_intervals = attendance_model.filter_uncovered_missing_intervals(self, work_schedule,
                                                                                          date_from_str, date_to_str)
        uncovered_absent_workdays = attendance_model.filter_uncovered_absent_workdays(uncovered_missing_intervals,
                                                                                      absent_workdays)
        missing_intervals = attendance_model. \
            filter_uncovered_missing_intervals_of_attended_workday(uncovered_missing_intervals,
                                                                   uncovered_absent_workdays)
        # extracts the duration by subtracting interval boundaries
        durations = [(_interval.interval[1] - _interval.interval[0]).total_seconds() for _interval in missing_intervals]
        total_duration = sum(durations)
        total_duration_in_hours = round(total_duration / 60.0 / 60.0, 2)

        LOGGER.debug('Total Uncovered Missing Attendance Hours: %s', total_duration_in_hours)
        return total_duration_in_hours

    @api.multi
    def get_absent_workdays(self, work_schedule, date_from_str, date_to_str):
        """
        Gets Workday dates where employee has no check in/out
        :param hr.calendar work_schedule:
        :param str date_from_str:
        :param str date_to_str:
        :return [datetime.datetime, ] list_of_absent_workdays:
        """
        self.ensure_one()
        attendance_model = self.env['hr.attendance']
        _weekdays = work_schedule._get_weekdays()

        if _weekdays:
            weekdays = _weekdays
            LOGGER.debug('Weekdays: %s', weekdays)
        else:
            raise exceptions.ValidationError(_('No valid Work Schedule found.'))

        date_from = fields.Date.from_string(date_from_str)
        date_to = fields.Date.from_string(date_to_str)

        # An iterable that represents the days an employee has to attend from date_from to date_to
        # based on work schedule
        scheduled_workdays = rrule.rrule(rrule.DAILY, dtstart=date_from, wkst=rrule.SU,
                                         until=date_to, byweekday=weekdays)
        LOGGER.debug('Scheduled Workdays Count: %s', scheduled_workdays.count())

        absent_workdays = []

        for day in scheduled_workdays:
            datetime_start_str = fields.Datetime.to_string(datetime.combine(day, time(0, 0)))
            datetime_stop_str = fields.Datetime.to_string(datetime.combine(day, time(23, 59)))

            workday = attendance_model.search([('employee_id', '=', self.id),
                                               ('check_in', '>=', datetime_start_str),
                                               ('check_in', '<=', datetime_stop_str)])
            LOGGER.debug('Actual Attendance: %s', workday)

            if len(workday) == 0:
                absent_workdays.append(day)

        LOGGER.debug('Total Absent Workdays Count: %s', len(absent_workdays))
        LOGGER.debug('Total Absent Workdays: \n%s', pprint.pformat(absent_workdays))

        return absent_workdays
