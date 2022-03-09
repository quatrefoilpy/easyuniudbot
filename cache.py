class Cache:

    def __init__(self):
        self.storage = {}

    def get_user_session(self, chat_id):
        if self.storage[chat_id] is None:
            self.storage[chat_id] = UserData()
        return self.storage[chat_id]


class UserData:

    def __init__(self):
        self.courses = None
        self.course_code = None
        self.year_code = None
        self.year_name = None
        self.period_code = None

    def reset(self):
        self.courses = None
        self.course = None
        self.year = None
        self.period_code = None
        self.year_name = None
