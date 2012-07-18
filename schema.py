from tests import mocks


class Field():

    @staticmethod
    def validate(field):
        error = False
        if 'name' not in field:
            error = True
        if field['class'] == 'text':
            return not error
        elif field['class'] == 'ref':
            return (Field._validate_ref(field) and not error)
        elif field['class'] == 'image':
            return Field._validate_image(field)

    @staticmethod
    def _validate_image(field):
        return True

    @staticmethod
    def _validate_ref(field):
        error = False
        # Ref needs an atributte called ref
        if 'ref' not in field:
            error = True
        else:
            # ref must be composed as $collection.$table
            ref = field['ref'].split('.')
            if len(ref) != 2:
                error = True
            else:
                for token in ref:
                    if token == '':
                        error = True
        return not error


class Schema():
    """
        Schema class
    """

    def __init__(self):
        self.name = None
        self.fields = {}

    def loadFromDict(self, config):
        """Loads schema from a dict"""
        self.name = config['name']
        fields = config['fields']
        for field in fields:
            if Field.validate(fields[field]):
                self.fields[field] = fields[field]
            else:
                raise Exception('Field ' + field + ' not valid')


if __name__ == '__main__':
    Schema().loadFromDict(mocks.schemas['boardgames'])
