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
