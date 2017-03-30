class Project:

    def __init__(self, address, title, description):
        self.address = address
        self.title = title
        self.description = description

    def serialize(self):
        return {
            'address': self.address,
            'title': self.title,
            'description': self.description
        }
