from analyzed_period import BaseAnalyzedPeriod


class AnalyzedInterval(BaseAnalyzedPeriod):
    def __init__(self, state, interval, covering_leave=None):
        self.interval = interval
        self.date_of_interval = interval[0].date()
        period_in_minutes = round(self.duration / 60.0, 2)
        super(AnalyzedInterval, self).__init__(self.date_of_interval, state, period_in_minutes, covering_leave)

    def __repr__(self):
        return self.state + ' -- ' + str(self.interval)

    def __eq__(self, other):
        if self.interval[0] == other.interval[0] and self.interval[1] == other.interval[1]:
            return True
        else:
            return False

    @property
    def duration(self):
        """
        Duration in sec
        :return:
        """
        return (self.interval[1] - self.interval[0]).total_seconds()
