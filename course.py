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


class Period:

    def __init__(self, code, label):
        self.code = code
        self.label = label


class Year:

    def __init__(self, code, number, label):
        self.code = code
        self.number = number
        self.label = label