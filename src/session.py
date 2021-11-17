class Session:
    def __init__(self):
        self.externail_id = None
        self.name = None
        self.second_name = None
        self.third_name = None
        self.password = None
        self.phone = None
        self.email = None

    @property
    def is_active(self):
        return False
