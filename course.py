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

    def __init__(self, code, name):
        self.code = code
        self.name = name


class Year:

    def __init__(self, code, number, name):
        self.code = code
        self.number = number
        self.name = name


class Lecture:

    def __init__(self, name, time, teacher, day, room):
        self.name = name
        self.time = time
        self.teacher = teacher
        self.day = day
        self.room = room

        self.format_name()

    def format_name(self):
        if '>' in self.name:
            last_html_char = self.name.rfind('>')
            self.name = self.name[last_html_char + 2:]

    def __str__(self):
        return self.name + ' - ' + self.time + ' - ' + self.day
