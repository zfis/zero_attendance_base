import logging
import pprint
from datetime import datetime

from dateutil import rrule
from odoo import models, fields, _, exceptions, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from ..analyzed_period import P_VE, LEAVE_COVERED, N_VE
from ..analyzed_interval import AnalyzedInterval
from functools import reduce

LOGGER = logging.getLogger(__name__)


class Attendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def get_attendance_dates(self, employee, date_from, date_to):
        """Get Attendance Days of an employee in a selected period.

        :param date_from: start date of selected period (can be str or datetime object).
        :param date_to: end date of selected period (can be str or datetime object).

        :return list of tuples, each has the following structure contains datetime object of attendance
                date (days) and float object number of hours logged in.
        :rtype [(<datetime.date> attendance_date, <float> interval_length,
                 <datetime.datetime> interval_start, <datetime.datetime> interval_stop),]


        :example 1: get attendance dates with total hours of each day:
        >>> attendance_model.get_attendance_dates('2015-07-01', '2015-07-31')
        [(datetime.date(2015, 7, 1), 3.5, datetime.datetime(2015, 7, 1, 8, 21, 53),
          datetime.datetime(2015, 7, 1, 11, 51, 53)),
         (datetime.date(2015, 7, 2), 7.1, datetime.datetime(2015, 7, 2, 12, 47, 53),
          datetime.datetime(2015, 7, 2, 19, 53, 53)),
         (datetime.date(2015, 7, 16), 5.4, datetime.datetime(2015, 7, 16, 7, 10, 53),
          datetime.datetime(2015, 7, 16, 12, 34, 53)),
         (datetime.date(2015, 7, 16), 6.4, datetime.datetime(2015, 7, 16, 14, 10, 53),
          datetime.datetime(2015, 7, 16, 20, 34, 53))]

        :example 2: get total worked intervals (shifts):
        >>> days = len(attendance_model.get_attendance_dates('2015-07-01', '2015-07-31'))

        :example 3: get total worked hours:
        >>> hours = sum([x[1] for x in attendance_model.get_attendance_dates('2015-07-01', '2015-07-31')])
        """
        if isinstance(date_from, str):
            date_from_str = date_from
            date_from = fields.Date.from_string(date_from)
        else:
            date_from_str = fields.Date.to_string(date_from)

        if isinstance(date_to, str):
            date_to_str = date_to
            date_to = fields.Date.from_string(date_to)
        else:
            date_to_str = fields.Date.to_string(date_to)

        # Get all recorded check-(in/out)s in the selected period of that employee.
        # NOTE: Odoo by default doesn't accept Missing/Misdated checks.
        checks = self.search([('check_in', '>=', date_from_str),
                              ('check_in', '<=', date_to_str),
                              ('employee_id', '=', employee.id)], order='check_in')
        LOGGER.debug('Selected Period: %s - %s', date_from, date_to)
        LOGGER.debug('Checks of the selected period: %s', checks)
        result = []
        # Check-In Record of Previous check in the loop, default is None for the first time.
        in_record = None
        # Loop over the checks and record periods
        for check in checks:
            if check.check_out:
                in_date = fields.Datetime.from_string(check.check_in)
                out_date = fields.Datetime.from_string(check.check_out)

                period_in_hours = round(check.worked_hours, 2)
                period_in_days = round(period_in_hours / 24.0, 2)
                if (0 < period_in_days < 1) and in_date.day == out_date.day:
                    # Normal Check-in and Check-out on the same day
                    result.append((out_date.date(), period_in_hours, in_date, out_date))
                elif (0 < period_in_days < 1) and out_date.day != in_date.day:
                    # Calculate multi-days check-ins
                    # in-record period: is the period of the first day after the check-in
                    in_record_period = (datetime(in_date.year, in_date.month, in_date.day,
                                                 23, 59, 59) - in_date).total_seconds() / 60 / 60
                    in_record_period = round(in_record_period, 2)
                    result.append((in_date.date(), in_record_period, in_date,
                                   datetime(in_date.year, in_date.month, in_date.day, 23, 59, 59)))
                    # out-record period: is the period of the last day before the check-out
                    out_record_period = out_date.hour + out_date.minute / 60.0 + out_date.second / 3600.0
                    out_record_period = round(out_record_period, 2)
                    result.append((out_date.date(), out_record_period,
                                   datetime(out_date.year, out_date.month, out_date.day, 0, 0, 0),
                                   out_date))
                elif period_in_days >= 1.0:
                    # No one works more than 24 hours consecutively
                    in_date_str = fields.Datetime.to_string(in_date)
                    out_date_str = fields.Datetime.to_string(out_date)
                    raise exceptions.ValidationError(_("There's missing check-in/out between the date: %s and the "
                                                       "date: %s. please check the attendance records before "
                                                       "calculating the attendance." % (in_date_str, out_date_str)))
                else:
                    # We should not get here at all except if the checks are not ordered correctly.
                    raise exceptions.ValidationError(_("Check-in record is not prior to the Check-out record."))

        # Return Result
        LOGGER.debug("Count of Attendance Days: %s", len(result))
        LOGGER.debug("Attendance Days: \n%s", pprint.pformat(result))
        return result

    @api.model
    def generate_scheduled_workdays(self, work_schedule, date_from_str, date_to_str):
        _weekdays = work_schedule._get_weekdays()
        if _weekdays:
            weekdays = _weekdays
            LOGGER.debug('Weekdays: %s', weekdays)
        else:
            raise exceptions.ValidationError(_('No valid Work Schedule found.'))

        date_from = datetime.strptime(date_from_str, DEFAULT_SERVER_DATE_FORMAT)
        date_to = datetime.strptime(date_to_str, DEFAULT_SERVER_DATE_FORMAT)
        scheduled_workdays = rrule.rrule(rrule.DAILY, dtstart=date_from, wkst=rrule.SU, until=date_to,
                                         byweekday=weekdays)
        LOGGER.debug('Scheduled Workdays count: %s', scheduled_workdays.count())
        return scheduled_workdays

    @api.model
    def analyze_attendance(self, employee, work_schedule, date_from_str, date_to_str, include_leave_types=None,
                           exclude_leave_types=None):
        """
        Analyzes employee attendance based on :param work_schedule: and extracts extra/missing work intervals

        Note: there could be a value in either include_leave_types or exclude_leave_types, if include_leave_types
        has value, then exclude_leave_types is ignored. If both are none, then all leave types are considered.

        :param hr.employee employee:
        :param resource.calendar work_schedule:
        :param str date_from_str:
        :param str date_to_str:
        :param [<hr.holidays.status>, ] include_leave_types: leave types to only include, so that only fetch
                                                             leaves of such types when comparing with attendance
                                                             intervals

        :param [<hr.holidays.status>, ] exclude_leave_types: leave types to exclude, so that don't fetch
                                                             leaves of such types in the given interval from
                                                             :param date_from: to :param date_to:
        :return [AnalyzedInterval, ]:
        """
        scheduled_workdays = self.generate_scheduled_workdays(work_schedule, date_from_str, date_to_str)
        intervals_difference = []

        for day in scheduled_workdays:
            day_date_str = fields.Date.to_string(day)
            # workday_intervals comes in the form of [[(start_datetime_obj, end_datetime_obj),]]
            # Outer list is added due to conversion from old_api to new_api
            workday_intervals = work_schedule._get_day_work_intervals(day)
            LOGGER.debug("Scheduled Workday Intervals of day {}: \n{}".format(day, pprint.pformat(workday_intervals)))

            _attendance_intervals = self.get_attendance_dates(employee, day_date_str, day_date_str)

            actual_attendance_intervals = [(_interval[2], _interval[3]) for _interval in _attendance_intervals]
            employee_leaves = work_schedule.get_leave_intervals_including_public_vacations(employee.resource_id.id,
                                                                                           day_date_str, day_date_str,
                                                                                           include_leave_types,
                                                                                           exclude_leave_types)

            LOGGER.debug('Actual Attendance Intervals of Day (%s): \n%s', day,
                         pprint.pformat(actual_attendance_intervals))

            intervals_difference += self.compute_diff_intervals(actual_attendance_intervals, workday_intervals,
                                                                employee_leaves)

        LOGGER.debug('Total Intervals Difference Count: %s', len(intervals_difference))
        LOGGER.debug('Total Intervals Difference: \n%s', pprint.pformat(intervals_difference))
        return intervals_difference

    @api.model
    def validate_interval(self, interval):
        # if len(interval) != 2:
        #     raise ValueError(_('Interval "%s" must be a tuple of two elements.' % interval))
        if filter(lambda obj: not isinstance(obj, datetime), interval):
            raise ValueError(_('Boundaries of interval "%s" must be of type datetime.datetime' % interval))
        return True

    @api.model
    def compute_diff_intervals(self, actual_intervals, scheduled_intervals, employee_leaves):
        """
        Breaks down work/attendance/leave intervals into smaller intervals and categorizes each one
        with respect to employee attendance into 3 categories:
        +ve: It is an extra work interval over scheduled work hours.
        -ve: It is a missed work interval employee didn't attend.
        l: It is missing interval an employee took permission for.
        :param [(datetime.datetime, datetime.datetime), ] actual_intervals:
        :param [(datetime.datetime, datetime.datetime), ] scheduled_intervals:
        :param [(datetime.datetime, datetime.datetime), ] employee_leaves:
        :return:
        """
        _employee_leave_intervals = [leave[:2] for leave in employee_leaves]
        _scheduled_intervals = [interval[:2] for interval in scheduled_intervals]
        _all_intervals = actual_intervals + _scheduled_intervals + _employee_leave_intervals
        datetime_objects = sorted(reduce(lambda tup1, tup2: tup1 + tup2, _all_intervals, tuple()))
        # datetime_objects = sorted(_all_intervals)

        sub_intervals = []
        diff_intervals = []
        for idx in range(0, len(datetime_objects) - 1):
            sub_intervals.append((datetime_objects[idx], datetime_objects[idx + 1]))

        LOGGER.debug('Sub-intervals: \n%s', pprint.pformat(sub_intervals))

        for sub_interval in sub_intervals:
            nesting_actual_interval = self._get_nesting_intervals(sub_interval, actual_intervals)
            nesting_scheduled_interval = self._get_nesting_intervals(sub_interval, scheduled_intervals)
            nesting_leave_interval = self._get_nesting_intervals(sub_interval, employee_leaves)

            if nesting_actual_interval and not nesting_scheduled_interval and not nesting_leave_interval:
                diff_intervals.append(AnalyzedInterval(P_VE, sub_interval))
            elif not nesting_actual_interval and nesting_scheduled_interval and not nesting_leave_interval:
                diff_intervals.append(AnalyzedInterval(N_VE, sub_interval))
            elif not nesting_actual_interval and nesting_scheduled_interval and nesting_leave_interval:
                diff_intervals.append(AnalyzedInterval(LEAVE_COVERED, sub_interval, nesting_leave_interval[0]))

        LOGGER.debug('Difference Intervals: \n%s', pprint.pformat(diff_intervals))
        return diff_intervals

    @api.model
    def is_nested_interval(self, nested_interval, nesting_intervals):
        """
        It checks whether :param nested_interval: is subset of ANY OF :param nesting_intervals:
        :return bool:
        """

        [self.validate_interval(interval) for interval in [nested_interval] + nesting_intervals]
        if self._get_nesting_intervals(nested_interval, nesting_intervals):
            return True
        else:
            return False

    @api.model
    def _get_nesting_intervals(self, nested_interval, nesting_intervals):
        """
        It gets all intervals in :param nesting_intervals: that contains :param nested_interval:
        :return [(datetime.datetime, datetime.datetime), ]:
        """
        return [interval for interval in nesting_intervals if self._is_nested_interval(nested_interval, interval)]

    @api.model
    def _is_nested_interval(self, nested_interval, nesting_interval):
        """
        It checks whether :param nested_interval: is subset of this ONE :param nesting_interval:
        :return bool:
        """
        if nested_interval[0] >= nesting_interval[0] and nested_interval[1] <= nesting_interval[1]:
            LOGGER.debug('Interval %s is nested in interval %s' % (nested_interval, nesting_interval))
            return True
        else:
            return False

    @api.model
    def filter_uncovered_absent_workdays(self, uncovered_missing_intervals, absent_workdays):
        """
        Filters out the :param absent_workdays: based on :param uncovered_missing_intervals: to
        get Absent Workdays that an employee took without permission/leave
        :param [AnalyzedInterval, ]uncovered_missing_intervals:
        :param [datetime.datetime, ]absent_workdays:
        :return: [datetime.datetime, ]
        """

        def _is_uncovered_absent_workday(absent_workday):
            for _interval in uncovered_missing_intervals:
                if absent_workday.date() == _interval.date_of_interval:
                    return True
            return False

        uncovered_days = list(filter(_is_uncovered_absent_workday, absent_workdays))

        LOGGER.debug('Uncovered Absent Workdays Count: %s', len(uncovered_days))
        LOGGER.debug('Uncovered Absent Workdays: \n%s', pprint.pformat(uncovered_days))
        return uncovered_days

    @api.model
    def filter_uncovered_missing_intervals(self, employee, work_schedule, date_from_str, date_to_str):
        """
        Filters out the missing attendance intervals that are NOT covered with approved leaves
        :param [AnalyzedInterval, ] total_missing_intervals:
        :param [(datetime.datetime, datetime.datetime, float), ] employee_leaves:
        :return: [AnalyzedInterval, ]
        """
        LOGGER.debug('employee: %s', employee)
        analyzed_intervals = self.analyze_attendance(employee, work_schedule, date_from_str, date_to_str)
        uncovered_missing_intervals = list(filter(lambda obj: obj.state == N_VE, analyzed_intervals))

        LOGGER.debug('Uncovered Missing Intervals Count: %s', len(uncovered_missing_intervals))
        LOGGER.debug('Uncovered Missing Intervals: \n%s', pprint.pformat(uncovered_missing_intervals))
        return uncovered_missing_intervals

    @api.model
    def filter_uncovered_missing_intervals_of_attended_workday(self, uncovered_missing_intervals,
                                                               uncovered_absent_workdays):
        """
        Filters out uncovered missing intervals that employee missed on a day he/she actually attended
        :param [AnalyzedInterval, ] uncovered_missing_intervals:
        :param [datetime.datetime, ] uncovered_absent_workdays:
        :return [AnalyzedInterval, ]:
        """

        def _is_uncovered_missing_interval_of_attended_workday(_interval):
            for absent_workday in uncovered_absent_workdays:
                if _interval.date_of_interval == absent_workday.date():
                    return False
            return True

        diff = filter(_is_uncovered_missing_interval_of_attended_workday, uncovered_missing_intervals)

        LOGGER.debug('Total Uncovered Missing Intervals of Attended Workday: %s', pprint.pformat(diff))
        return diff

    @api.model
    def filter_covered_missing_intervals(self, employee, work_schedule, date_from_str, date_to_str,
                                         include_leave_types=None, exclude_leave_types=None):
        """
        Extract the missing attendance intervals that are covered with approved leave requests

        Note: there could be a value in either include_leave_types or exclude_leave_types, if include_leave_types
        has value, then exclude_leave_types is ignored. If both are none, then all leave types are considered.

        :param [<hr.holidays.status>, ] include_leave_types: leave types to only include, so that don't  only fetch
                                                             leaves of such types in the given interval from
                                                             :param date_from: to :param date_to:

        :param [<hr.holidays.status>, ] include_leave_types: leave types to exclude, so that don't fetch
                                                             leaves of such types in the given interval from
                                                             :param date_from: to :param date_to:

        :return: [[<covered_missing_interval>, (<covering_leave>)], ]
        """

        analyzed_intervals = self.analyze_attendance(employee, work_schedule, date_from_str, date_to_str,
                                                     include_leave_types, exclude_leave_types)
        covered_missing_intervals = filter(lambda obj: obj.state == LEAVE_COVERED, analyzed_intervals)
        LOGGER.debug('Covered Missing Intervals: \n%s', pprint.pformat(covered_missing_intervals))
        return covered_missing_intervals

    # @api.model
    # def filter_covered_missing_intervals_of_specific_leave(self, all_covered_intervals, covering_leave):
    #     """
    #     Extract the missing attendance intervals that are covered with approved leave requests
    #     :return: [[<covered_missing_interval>, (<covering_leave>)], ]
    #     """
    #
    #     covered_missing_intervals = filter(lambda obj: obj.state == LEAVE_COVERED, analyzed_intervals)
    #     LOGGER.debug('Covered Missing Intervals: \n%s', pprint.pformat(covered_missing_intervals))
    #     return covered_missing_intervals

    @api.model
    def filter_covered_absent_workdays(self, covered_missing_intervals, absent_workdays):
        """
        Filters absent workdays that are covered with approved leaves.

        :param [<AnalyzedInterval>, ] covered_missing_intervals:
        :param [<datetime.datetime>, ] absent_workdays:
        :return ([<datetime.datetime> CoveredAbsentWorkday, ],
                 [(<datetime.datetime> leave_start_time,
                   <datetime.datetime> leave_end_time,
                   <float> leave_paid_percent), ]
                ):
        """
        covering_leaves = []

        def _is_covered_absent_workday_interval(absent_workday):
            for covered_missing_interval in covered_missing_intervals:
                if absent_workday.date() == covered_missing_interval.date_of_interval:
                    covering_leaves.append(covered_missing_interval.covering_leave)
                    return True
            return False

        covered_absent_workdays = filter(_is_covered_absent_workday_interval, absent_workdays)
        return covered_absent_workdays, covering_leaves

    @api.model
    def filter_covered_missing_intervals_of_attended_workdays(self, covered_missing_intervals,
                                                              covered_absent_workdays):
        """
        Filters missing intervals that the employee missed on a workday he/she actually attended,
        but he/she took a permission/leave for those intervals
        :param [AnalyzedInterval, ] covered_missing_intervals:
        :param [datetime.datetime, ] covered_absent_workdays:
        :return [AnalyzedInterval, ]:
        """

        def _is_covered_missing_interval_of_attended_workday(covered_missing_interval):
            for absent_workday in covered_absent_workdays:
                if covered_missing_interval.date_of_interval == absent_workday.date():
                    return False
            return True

        diff = filter(_is_covered_missing_interval_of_attended_workday, covered_missing_intervals)

        LOGGER.debug('Total Covered Missing Intervals of Attended Workday: \n%s', pprint.pformat(diff))
        return diff
