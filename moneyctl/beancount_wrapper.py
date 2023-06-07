import sys
import beancount
import beancount.loader
import beancount.query.query
import pandas as pd
from datetime import date

from moneyctl.report import Report

class BeancountWrapper():

    ASSETS_PREFIX = "Assets:"
    EXPENSES_PREFIX = "Expenses:"
    INCOME_PREFIX = "Income:"
    INVESTMENTS_PREFIX = "Assets:Инвестиции:"

    def __init__(self, beancount_string):
        self.entries, self.errors, self.options = beancount.loader.load_string(beancount_string, log_errors=sys.stderr)

    def _rows_to_dict(self, rows):
        result_dict = {}
        for row in rows:
            fields = row._asdict()
            for field_name in fields:
                field_value = fields[field_name]
                if field_name not in result_dict:
                    result_dict[field_name] = []
                result_dict[field_name].append(field_value)
        return result_dict

    def _rows_to_dataframe(self, rows):
        return pd.DataFrame(self._rows_to_dict(rows))

    def _query(self, query_text):
        _, result_rows = beancount.query.query.run_query(self.entries, self.options, query_text)
        if result_rows:
            return self._rows_to_dataframe(result_rows)
        else:
            return None

    def _gen_total(self, dataframe):
        total = dataframe.sum()
        total[total.index[0]] = 'total'
        return total

    def _exclude_empty_accounts(self, dataframe, by_column):
        MIN_ACCOUNT_POSITION = 99
        return dataframe.loc[(dataframe[by_column] < 0) | (dataframe[by_column] > MIN_ACCOUNT_POSITION)]


    def assets_report(self, empty_accounts=True, total=True):
        today = date.today().strftime('%Y-%m-%d')
        request = f'''
            SELECT
                account,
                sum(number(convert(position, "RUB", TODAY()))) as position
            FROM OPEN ON {today}
            WHERE
                account ~ "{self.ASSETS_PREFIX}"
                AND not account ~ "{self.INVESTMENTS_PREFIX}"
        '''
        response_dataframe = self._query(request)
        if not isinstance(response_dataframe, pd.DataFrame):
            return Report(None, None)
        if not empty_accounts:
            response_dataframe = self._exclude_empty_accounts(response_dataframe, by_column='position')
        response_dataframe['account'] = response_dataframe['account'].str.replace(self.ASSETS_PREFIX, '')
        total_series = self._gen_total(response_dataframe) if total else None
        return Report(response_dataframe, total_series)


    def expenses_report(self, from_, to, total=True):
        from_str = from_.strftime('%Y-%m-%d')
        to_str = to.strftime('%Y-%m-%d')
        request = f'''
            SELECT
                account,
                sum(number(convert(position, "RUB", date))) as position
            WHERE
                account ~ "{self.EXPENSES_PREFIX}"
                AND date >= {from_str}
                AND date <= {to_str}
            ORDER BY position, account DESC
        '''
        response_dataframe = self._query(request)
        if not isinstance(response_dataframe, pd.DataFrame):
            return Report(None, None)
        response_dataframe['account'] = response_dataframe['account'].str.replace(self.EXPENSES_PREFIX, '')
        total_series = self._gen_total(response_dataframe) if total else None
        return Report(response_dataframe, total_series)


    def income_report(self, from_, to, total=True):
        from_str = from_.strftime('%Y-%m-%d')
        to_str = to.strftime('%Y-%m-%d')
        request = f'''
            SELECT
                account,
                neg(sum(number(convert(position, "RUB", date)))) as position
            WHERE
                account ~ "{self.INCOME_PREFIX}"
                AND date >= {from_str}
                AND date <= {to_str}
            ORDER BY position, account DESC
        '''
        response_dataframe = self._query(request)
        if not isinstance(response_dataframe, pd.DataFrame):
            return Report(None, None)
        response_dataframe['account'] = response_dataframe['account'].str.replace(self.INCOME_PREFIX, '')
        total_series = self._gen_total(response_dataframe) if total else None
        return Report(response_dataframe, total_series)

    
    def invest_cash_report(self, total=True):
        request = f'''
            SELECT
                account,
                SUM(number) as position
            WHERE
                account ~ "{self.INVESTMENTS_PREFIX}" AND currency = "RUB"
        '''
        response_dataframe = self._query(request)
        if not isinstance(response_dataframe, pd.DataFrame):
            return Report(None, None)
        response_dataframe['account'] = response_dataframe['account'].str.replace(self.INVESTMENTS_PREFIX, '')
        total_series = self._gen_total(response_dataframe) if total else None
        return Report(response_dataframe, total_series)

    
    def invest_parts_report(self, total=True):
        request = f'''
            SELECT
    	    currency,
            SUM(number) * FIRST(GETPRICE(currency, "RUB", TODAY())) as position
    	WHERE
    	    account ~ "{self.INVESTMENTS_PREFIX}"
    	    AND currency != "RUB"
    	    AND currency != "FXUS"
    	    AND currency != "FXIT"
    	    AND currency != "FXIM"
            ORDER BY position, currency DESC
        '''
        response_dataframe = self._query(request)
        if not isinstance(response_dataframe, pd.DataFrame):
            return Report(None, None)
        response_dataframe = self._exclude_empty_accounts(response_dataframe, by_column='position')
        total = response_dataframe['position'].sum()
        response_dataframe['part'] = response_dataframe['position'] / total * 100
        total_series = self._gen_total(response_dataframe) if total else None

        # TODO посчитать total и извлечь сумму в рублях
        # TODO посчитать процент для каждого currency

        #response_dataframe['account'] = response_dataframe['account'].str.replace(self.INVESTMENTS_PREFIX, '')
        total_series = self._gen_total(response_dataframe) if total else None
        return Report(response_dataframe, total_series)

# TODO !!! Перейти на стандартный для pandas способ добавления total в таблицу
# https://stackoverflow.com/questions/41286569/get-total-of-pandas-column
