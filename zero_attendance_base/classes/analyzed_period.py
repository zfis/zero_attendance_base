from abc import ABCMeta

from odoo import exceptions

# Missing Hours
N_VE = '-ve'
# Extra Hours
P_VE = '+ve'
# Missing Hours but covered with leave
LEAVE_COVERED = 'l'


# This is an abstract class to be sub-classed by classes that get processed in attendance calculations
class BaseAnalyzedPeriod(object):
    ___metaclass__ = ABCMeta

    def __init__(self, day, state, period_in_minutes, covering_leave=None):
        self.day = day
        self.period_in_minutes = period_in_minutes
        # set the value of @covering_leave before @state because the latter depends on it
        self.covering_leave = covering_leave
        self._state = state

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        accepted_values = (N_VE, P_VE, LEAVE_COVERED)
        # checking value
        if value in accepted_values:
            # Make sure the leave-covered hours type has a covering leave with it
            if value == LEAVE_COVERED and self.covering_leave is None:
                raise exceptions.ValidationError('Leave-covered period must have a covering leave attached')
            self._state = value
        else:
            raise exceptions.ValidationError('State must be any of "{}" not "{}"'.format(accepted_values, value))
