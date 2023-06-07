from rich.console import Console
from rich.table import Table
from rich import box
import pandas as pd
import decimal


# Classes =====================================================================

class ReportException(BaseException):
    def __init__(self, message=None):
        super().__init__(message)

### Report Class --------------------------------------------------------------

class Report:

    FORMAT_TABLE = 'table'
    FORMAT_MD_TABLE = 'md-table'
    FORMAT_JSON = 'json'
    FORMAT_CSV = 'csv'

    FORMAT_DEFAULT = FORMAT_TABLE

    FORMATS = [FORMAT_TABLE, FORMAT_MD_TABLE, FORMAT_JSON, FORMAT_CSV]

    def get_formats_names(self):
        return self.FORMATS

    def get_default_format_name(self):
        return self.FORMAT_DEFAULT

    def __init__(self, report_dataframe=None, total_dataframe=None):
        self.report_dataframe = report_dataframe
        self.total_dataframe = total_dataframe
        self.rounding = True
        self.format = self.get_default_format_name()
        # TODO раскрашивать вывод или нет
        # TODO раскрашивать accounts


    def set(self, report_dataframe=None, total_dataframe=None, format=None, rounding=None):
        if report_dataframe is not None:
            self.report_dataframe = report_dataframe
        if total_dataframe is not None:
            self.total_dataframe = total_dataframe
        if rounding is not None:
            self.rounding = rounding
        if format is not None:
            self.format = format

    def _validate_format(self):
        if self.format not in self.FORMATS:
            message = f'Report does not support "{self.format}" format type'
            raise ReportException(message)

    def is_empty(self):
        if isinstance(self.report_dataframe, pd.DataFrame):
            return False
        else:
            return True

    def validate(self):
        self._validate_format()

    def _print_csv(self):
        if self.is_empty():
            print('')
        else:
            print(self.report_dataframe.to_csv())

    def _print_json(self): # TODO реализовать метод
        # { 
        #   "report": {
        #     "Sberbank": {
        #        "position_rub": 4500.50,
        #        "position_usd": 100.00,
        #     },
        #   },
        #   "total": {
        #     "position_rub": 4500.50,
        #     "position_usd": 100.00,
        #   },
        # }
        pass

    def _format_decimal(self, decimal_):
        if self.rounding:
            quant = decimal.Decimal('1.')
            decimal_ = decimal_.quantize(quant, rounding=decimal.ROUND_DOWN)
            return f"{int(decimal_):_}" # "123_456"
        else:
            quant = decimal.Decimal('0.01')
            decimal_ = decimal_.quantize(quant, rounding=decimal.ROUND_DOWN)
            return f"{float(decimal_):_.2f}" # "123_456.78"

    def _format_header(self, header):
        return header.upper().replace('-', ' ').replace('_', ' ')

    def _format_footer(self, footer):
        return self._format_header(footer)

    def _format_field(self, field, as_header=False, as_footer=False):
        if isinstance(field, decimal.Decimal):
            return self._format_decimal(field)
        if as_header:
            return self._format_header(field)
        if as_footer:
            return self._format_footer(field)
        else:
            return field


    def _select_justify(self, field):
        # TODO переделать логику -- нужно идти в датафрейм и смотреть тип
        if 'position' in field:
            return 'right'
        elif 'part' in field:
            return 'right'
        else:
            return 'left'


    def _gen_columns(self):
        columns = []
        report_dict = self.report_dataframe.to_dict()
        total_dict = {}
        if self.total_dataframe is not None:
             total_dict = self.total_dataframe.to_dict()
        for field in report_dict:
            column = {}
            column['header'] = self._format_field(field, as_header=True)
            column['justify'] = self._select_justify(field)
            column['footer'] = ''
            if self.total_dataframe is not None:
                column['footer'] = self._format_field(total_dict[field], as_footer=True)
            columns.append(column)
        return columns


    def _gen_rows(self):
        rows = []
        report_dict = self.report_dataframe.to_dict()
        for i in list(report_dict.values())[0].keys(): # TODO переписать более понятно
            row = []
            for column in report_dict:
                row.append(self._format_field(report_dict[column][i]))
            rows.append(row)
        return rows


    def _print_table(self, style=box.SIMPLE):
        console = Console()

        if self.is_empty():
            console.print('no data')
            return

        show_footer= True if self.total_dataframe is not None else False
        table = Table(show_footer=show_footer, box=style)

        for column in self._gen_columns():
            table.add_column(header=column['header'], footer=column['footer'], justify=column['justify'])

        for row in self._gen_rows():
            table.add_row(*row)

        console.print(table)


    def print(self):
        self.validate()

        if self.format == self.FORMAT_CSV:
            self._print_csv()
            return

        if self.format == self.FORMAT_JSON:
            self._print_json()
            return
    
        if self.format == self.FORMAT_TABLE:
            self._print_table()
            return

        if self.format == self.FORMAT_MD_TABLE:
            self._print_table(style=box.MARKDOWN)
            return


