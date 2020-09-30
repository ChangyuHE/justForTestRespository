class CommaSeparatedOptionalPathConverter:

    regex = '(v?\d*(,v?\d*)*)?'

    def to_python(self, value):
        return [v for v in value.split(',')]

    def to_url(self, value):
        return ','.join(map(str, value))


class CommaSeparatedIntegersPathConverter:

    regex = '(?<=/)\d*(?:,\d+)*(?=/?)'

    def to_python(self, value):
        return [int(v) for v in value.split(',')]

    def to_url(self, value):
        return ','.join(map(str, value))