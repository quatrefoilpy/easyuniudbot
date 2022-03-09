class Course:

    def __init__(self, name, code, course_type):
        self.name = name
        self.code = code
        self.course_type = course_type
        self.periods = []
        self.years = []

    def add_year(self, year):
        self.years.append(year)

    def add_period(self, period):
        self.periods.append(period)

    def periods_as_string(self):
        result = ''
        for period in self.periods:
            result += period.as_string() + '.'
        return result


class Period:

    def __init__(self, code, name):
        self.code = code
        self.name = name

    def as_string(self):
        return self.name + ';' + self.code


class Year:

    def __init__(self, code, number, name):
        self.code = code
        self.number = number
        self.name = name
