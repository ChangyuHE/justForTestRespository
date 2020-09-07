from types import SimpleNamespace

from django.test import TestCase

from api.collate.business_entities import OutcomeBuilder


class OutcomeBuilderTest(TestCase):
    def assertOutcomeContains(self, error_subset, result):
        self.assertFalse(result['success'], 'Expected failure status.')
        self.assertEqual(len(result['errors']), 1, 'Expected single error_subset.')
        self.assertDictContainsSubset(error_subset, result['errors'][0], 'Expected error_subset not found in result.')

    def test_invalid_validation(self):
        code = 'ERR_INVALID_VALIDATION_ID'
        message = 'Sample invalid validation error'

        outcome = OutcomeBuilder()
        outcome.add_invalid_validation_error(message)
        outcome.add_invalid_validation_error(message)
        outcome.add_invalid_validation_error(message)

        result = outcome.build()
        expected = dict(success=False, errors=[dict(code=code, message=message)])

        self.assertDictContainsSubset(expected, result, 'Expected subset not found in result.')

    def test_existing_validation(self):
        actual_fields_data = dict(foo=1, bar=2).items()
        expected_fields = dict(foo='1', bar='2')
        code = 'ERR_EXISTING_VALIDATION'
        message = 'Sample existing validation error'

        outcome = OutcomeBuilder()
        outcome.add_existing_validation_error(message, actual_fields_data)
        outcome.add_existing_validation_error(message, actual_fields_data)
        outcome.add_existing_validation_error(message, actual_fields_data)

        result = outcome.build()
        expected = dict(success=False, errors=[
            dict(
                code=code,
                message=message,
                entity=dict(model='Validation', fields=expected_fields),
            )
        ])

        self.assertDictContainsSubset(expected, result, 'Expected subset not found in result.')

    def test_missing_field(self):
        model_name = 'Sample model'
        fields = dict(name='foo')
        code = 'ERR_MISSING_ENTITY'

        outcome = OutcomeBuilder()
        outcome.add_missing_field_error((model_name, fields))
        outcome.add_missing_field_error((model_name, fields))
        outcome.add_missing_field_error((model_name, fields))

        result = outcome.build()
        expected = dict(code=code, entity=dict(model=model_name, fields=fields))

        self.assertOutcomeContains(expected, result)

    def test_missing_field_alias(self):
        model_name = 'Sample model'
        fields = dict(name='foo')
        code = 'ERR_MISSING_ENTITY'

        outcome = OutcomeBuilder()
        outcome.add_missing_field_error((model_name, fields), True)
        outcome.add_missing_field_error((model_name, fields), True)
        outcome.add_missing_field_error((model_name, fields), True)

        result = outcome.build()
        expected = dict(code=code, entity=dict(model=model_name, fields=fields))

        self.assertOutcomeContains(expected, result)

    def test_missing_column(self):
        columns = ['column1', 'column2']
        code = 'ERR_MISSING_COLUMNS'

        outcome = OutcomeBuilder()
        outcome.add_missing_columns_error(columns)
        outcome.add_missing_columns_error(columns)
        outcome.add_missing_columns_error(columns)

        result = outcome.build()
        expected = dict(code=code, values=columns)

        self.assertOutcomeContains(expected, result)

    def test_workbook(self):
        code = 'ERR_WORKBOOK_EXCEPTION'
        message = 'Sample workbook error'

        outcome = OutcomeBuilder()
        outcome.add_workbook_error(message)
        outcome.add_workbook_error(message)
        outcome.add_workbook_error(message)

        result = outcome.build()
        expected = dict(success=False, errors=[dict(code=code, message=message)])

        self.assertDictContainsSubset(expected, result, 'Expected subset not found in result.')

    def test_ambigous_column(self):
        code = 'ERR_AMBIGUOUS_COLUMN'
        column = 'Sample column'
        values = ['value1', 'value2']

        outcome = OutcomeBuilder()
        outcome.add_ambiguous_column_error(column, values)
        outcome.add_ambiguous_column_error(column, values)
        outcome.add_ambiguous_column_error(column, values)

        result = outcome.build()
        expected = dict(code=code, column=column, values=values)

        self.assertOutcomeContains(expected, result)

    def test_existing_run(self):
        code = 'ERR_EXISTING_RUN'
        run = SimpleNamespace(name='Run name', session='Run session')

        outcome = OutcomeBuilder()
        outcome.add_existing_run_error(run)
        outcome.add_existing_run_error(run)
        outcome.add_existing_run_error(run)

        result = outcome.build()
        expected = dict(code=code)

        self.assertOutcomeContains(expected, result)

    def test_date_format(self):
        code = 'ERR_DATE_FORMAT'
        date = 'current date'

        outcome = OutcomeBuilder()
        outcome.add_date_format_error(date)
        outcome.add_date_format_error(date)
        outcome.add_date_format_error(date)

        result = outcome.build()
        expected = dict(code=code)

        self.assertOutcomeContains(expected, result)
