import logging
import pprint

from odoo import models, fields, api

LOGGER = logging.getLogger(__name__)


class ResourceCalendar(models.Model):
    """Resource Inherited Model"""
    _inherit = 'resource.calendar'

    @staticmethod
    def _extract_interval(leave):
        """
        Extract interval from leave object along with any other needed data
        :param <hr.holidays> leave:
        :return: tuple of leave interval
        :rtype: (<datetime.datetime> date_from, <datetime.datetime> date_to)
        """
        _date_from = fields.Datetime.from_string(leave.date_from)
        _date_to = fields.Datetime.from_string(leave.date_to)
        return _date_from, _date_to

    # TODO: I think this method should be in resource.calendar.leave model
    @api.model
    def get_leave_intervals(self, resource_id, date_from, date_to, include_leave_types=None, exclude_leave_types=None):
        """
        Return leave intervals for selected resource (employee).
        Get all intervals that intersect with interval starting at :param: date_from
        and ending at :param: date_to.

        Note: there could be a value in either include_leave_types or exclude_leave_types, if include_leave_types
        has value, then exclude_leave_types is ignored. If both are none, then all leave types are considered.

        :param [<hr.holidays.status>, ] include_leave_types: leave types to only include, so that don't only fetch
                                                             leaves of such types in the given interval from
                                                             :param date_from: to :param date_to:

        :param [<hr.holidays.status>, ] exclude_leave_types: leave types to exclude, so that don't fetch
                                                             leaves of such types in the given interval from
                                                             :param date_from: to :param date_to:
        :return: list of leave intervals
        """
        calendar_leaves_model = self.env['resource.calendar.leaves']
        domain = [('resource_id', '=', resource_id),
                  '|',
                  '&', ('date_from', '<', date_from),
                  ('date_to', '>', date_to),
                  '|',
                  '&', ('date_from', '>=', date_from),
                  ('date_from', '<=', date_to),
                  '&', ('date_to', '>=', date_from),
                  ('date_to', '<=', date_to),
                  ]

        if include_leave_types:
            LOGGER.debug('Leaves Included: %s', include_leave_types)
            include_leave_type_ids = [_leave.id for _leave in include_leave_types]
            domain.insert(0, ('leave_type', 'in', include_leave_type_ids))
        elif exclude_leave_types:
            LOGGER.debug('Leaves Excluded: %s', exclude_leave_types)
            exclude_leave_type_ids = [_leave.id for _leave in exclude_leave_types]
            domain.insert(0, ('leave_type', 'not in', exclude_leave_type_ids))

        approved_leaves = calendar_leaves_model.search(domain)

        return map(self._extract_interval, approved_leaves)

    # TODO: I think this method should be in resource.calendar.leave model
    @api.model
    def get_leave_intervals_including_public_vacations(self, resource_id, date_from, date_to, include_leave_types=None,
                                                       exclude_leave_types=None):
        """
        Includes public vacations, as intervals, to normal leaves.

        Note: there could be a value in either include_leave_types or exclude_leave_types, if include_leave_types
        has value, then exclude_leave_types is ignored. If both are none, then all leave types are considered.

        :param resource.resource resource_id:
        :param str date_from:
        :param str date_to:
        :param [<hr.holidays.status>, ] include_leave_types: leave types to only include, so that don't  only fetch
                                                             leaves of such types in the given interval from
                                                             :param date_from: to :param date_to:

        :param [<hr.holidays.status>, ] exclude_leave_types: leave types to exclude, so that don't fetch
                                                             leaves of such types in the given interval from
                                                             :param date_from: to :param date_to:
        :rtype: [(<datetime.datetime> date_from, <datetime.datetime> date_to), ]
        """
        public_holidays_model = self.env['hr.holidays.public']
        public_holidays = public_holidays_model.get_public_holidays(date_from, date_to)
        leaves = self.get_leave_intervals(resource_id, date_from, date_to)

        LOGGER.debug('Normal holiday intervals from %s to %s: \n%s', date_from, date_to,
                     pprint.pformat(leaves))
        return list(leaves) + public_holidays

