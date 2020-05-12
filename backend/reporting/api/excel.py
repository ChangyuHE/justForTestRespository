from utils import intel_calendar

from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.styles import Font, Alignment
from openpyxl.styles.colors import WHITE
from openpyxl.utils import get_column_letter as to_letter

from .models import *

BOLD_FONT = Font(bold=True)


def do_best_report(data=None, extra=None):
    validations = extra or []
    ct = data

    wb = Workbook()
    ws = wb.active

    rdate = 'Best status report: {0} ww{1}.{2}'.format(*intel_calendar.ww_date())
    ws['A2'] = rdate
    ws['A2'].font = Font(bold=True, size=14)
    ws.merge_cells('A2:G2')

    ws['A3'] = 'Report generated basing on validations:'
    ws.merge_cells('A3:G3')

    # List of selected validations
    c_row = 4
    formatted_validations = []
    for v in validations:
        formatted_validations.append(f'{v.name} ({v.platform.name}, {v.env.name}, {v.os.name})')

    for v in formatted_validations:
        c = ws.cell(row=c_row, column=1)
        c.value = v
        c.font = BOLD_FONT
        ws.merge_cells(start_row=c_row, start_column=1, end_row=c_row, end_column=7)
        c_row += 1
    c_row += 1

    # Starting table creation
    table_row_start, table_columns = c_row + 1, 1
    table_row_end = c_row + 1

    # DataFrame to cells
    rows = dataframe_to_rows(ct, index=True, header=True)
    for r_id, row in enumerate(rows, 1):
        table_columns = len(row)
        c_row += 1
        table_row_end = c_row
        for c_id, value in enumerate(row, 1):
            ws.cell(row=c_row, column=c_id, value=value)

    # Insert first column header name
    ws.cell(row=table_row_start, column=1, value='Group name')

    # First column
    max_groups_len = max(map(len, list(ct.index)))

    # Format first and last row in "table"
    column_names = list(ct.columns)  # not run, error, failed passed total, pass-rate
    for c_id in range(1, table_columns + 1):
        ws.cell(row=table_row_start, column=c_id).font = Font(color=WHITE)
        ws.cell(row=table_row_end, column=c_id).font = BOLD_FONT

        # Set columns default width by text len
        if c_id != 1:
            ws.column_dimensions[to_letter(c_id)].width = len(column_names[c_id - 2]) + 4   # padding for filter button
        else:
            ws.column_dimensions[to_letter(c_id)].width = max_groups_len

    # Apply table style (zebra + color + header sort/filters)
    medium_style = TableStyleInfo(name='TableStyleMedium6', showRowStripes=True)

    table = Table(
        ref=f'{to_letter(1)}{table_row_start}:{to_letter(table_columns)}{table_row_end - 1}',
        displayName='Results', tableStyleInfo=medium_style)
    ws.add_table(table)

    # Remove empty row where DataFrame index name should be located
    ws.delete_rows(table_row_start + 1, 1)

    return wb


def do_comparison_report(data=None):
    ct = data
    statuses = Status.objects.all().values_list('test_status', flat=True)

    wb = Workbook()
    ws = wb.active

    rdate = 'Validations comparison report: {0} ww{1}.{2}'.format(*intel_calendar.ww_date())
    ws['A2'] = rdate
    ws['A2'].font = Font(bold=True, size=14)
    ws.merge_cells('A2:G2')

    c_row = 3

    # Starting table creation
    table_row_start, table_columns = c_row + 1, 1
    table_row_end = c_row + 1

    # DataFrame to cells
    rows = dataframe_to_rows(ct, index=True, header=True)
    for r_id, row in enumerate(rows, 1):
        table_columns = len(row)
        c_row += 1
        table_row_end = c_row
        for c_id, value in enumerate(row, 1):
            ws.cell(row=c_row, column=c_id, value=value)
            if r_id == table_row_start:
                ws.cell(row=c_row, column=c_id).alignment = Alignment(wrap_text=True)


            font = Font()
            # coloring statuses
            if value in statuses:
                if value == 'Passed':
                    font = Font(color='2E7D32')
                elif value == 'Failed':
                    font = Font(color='B71C1C')
                elif value == 'Error':
                    font = Font(color='D84315')
                elif value == 'Blocked':
                    font = Font(color='616161')
                elif value == 'Skipped':
                    font = Font(color='00838F')
                elif value == 'Canceled':
                    font = Font(color='3E2723')
                font.bold = True
                ws.cell(row=c_row, column=c_id).alignment = Alignment(horizontal='center')
            ws.cell(row=c_row, column=c_id).font = font

    # Insert first column header name
    ws.cell(row=table_row_start, column=1, value='Case name')

    # First column
    max_first_column_len = max(map(len, list(ct.index)))

    # Format first and last row in "table"
    for c_id in range(1, table_columns + 1):
        ws.cell(row=table_row_start, column=c_id).font = Font(color=WHITE)
        ws.column_dimensions[to_letter(c_id)].width = max_first_column_len

    # Apply table style (zebra + color + header sort/filters)
    medium_style = TableStyleInfo(name='TableStyleMedium6', showRowStripes=True)

    table = Table(
        ref=f'{to_letter(1)}{table_row_start}:{to_letter(table_columns)}{table_row_end - 1}',
        displayName='Results', tableStyleInfo=medium_style)
    ws.add_table(table)

    # Remove empty row where DataFrame index name should be located
    ws.delete_rows(table_row_start + 1, 1)

    return wb
