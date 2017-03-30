class Project:

    def __init__(self, address, title, description, alive=False):
        self.address = address
        self.title = title
        self.description = description
        self.alive = alive

    def serialize(self):
        return {
            'address': self.address,
            'title': self.title,
            'description': self.description
        }
