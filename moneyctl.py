#!/usr/bin/env python3

"""MoneyCTL.

Usage:
  moneyctl.py expenses [options]
  moneyctl.py income [options]
  moneyctl.py assets [options]
  moneyctl.py invest <report> [options]

Invest Reports:
  assets
  cash
  part
  profit

Options:
  -y, --year YEAR             Set year for report
  -m, --month MONTH           Set month for report
  -b, --begin BEGIN_DATE      Set begin of range for report (example: 2021-12-31)
  -e, --end END_DATE          Set end of range for report
  -j, --journal JOURNAL_FILE  Set journal file to load

"""



import sys
import queue
from docopt import docopt
from datetime import date
from beancount import loader
from termcolor import colored
from calendar import monthrange
from beautifultable import BeautifulTable
from beancount.query.query import run_query


DEFAULT_JOURNAL_FILE = '/home/user/documents/beancount/main.bean'


class BeancountWrapper():
    def __init__(self, beancount_file):
        self.entries, self.errors, self.options = loader.load_file(beancount_file, log_errors=sys.stderr)

    def query(self, query_text):
        output = run_query(self.entries, self.options, query_text)
        return output[1]



def date_range(args):

    begin, end = None, None

    if args['--begin'] and args['--end']:
        begin = date.fromisoformat(args['--begin'])
        end = date.fromisoformat(args['--end'])

    elif args['--year'] and args['--month']:
        year_n = int(args['--year'])
        month_n = int(args['--month'])
        _, lastday_month = monthrange(year_n, month_n)

        begin = date(year_n, month_n, 1)
        end = date(year_n, month_n, lastday_month)

    elif args['--year']:
        year_n = int(args['--year'])
        _, lastday_year = monthrange(year_n, 12)

        begin = date(year_n, 1, 1)
        end = date(year_n, 12, lastday_year)

    elif args['--month']:
        year_n = date.today().year
        month_n = int(args['--month'])
        _, lastday_month = monthrange(year_n, month_n)

        begin = date(year_n, month_n, 1)
        end = date(year_n, month_n, lastday_month)

    else: # current month by default
        year_n = date.today().year
        month_n = date.today().month
        _, lastday_month = monthrange(year_n, month_n)

        begin = date(year_n, month_n, 1)
        end = date(year_n, month_n, lastday_month)

    return begin, end


def expenses_report(bean, begin, end):
    begin_str = begin.strftime('%Y-%m-%d')
    end_str = end.strftime('%Y-%m-%d')

    q = f'''
        SELECT 
            account,
            currency,
            sum(number(convert(position, "RUB", date))) as position_rub,
            sum(number(convert(position, "USD", date))) as position_usd
        WHERE
            account ~ "Expenses" and date >= {begin_str} and date <= {end_str}
        ORDER BY position_usd, account DESC
    '''

    table = BeautifulTable()

    account_header = colored("ACCOUNT", attrs=['bold'])
    position_rub_header = colored("POSITION RUB", attrs=['bold'])
    position_usd_header = colored("POSITION USD", attrs=['bold'])
    
    table.columns.header = [account_header, position_rub_header, position_usd_header]
    table.columns.alignment[account_header] = BeautifulTable.ALIGN_LEFT
    table.columns.alignment[position_rub_header] = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment[position_usd_header] = BeautifulTable.ALIGN_RIGHT
    table.set_style(BeautifulTable.STYLE_MARKDOWN)


    total_rub = 0
    total_usd = 0
    rows = bean.query(q)
    for row in rows:
        currency = str(row.currency)
        account = str(row.account).replace('Expenses:', '')
        position_rub = float(row.position_rub)
        position_usd = float(row.position_usd)

        total_rub += position_rub
        total_usd += position_usd

        position_rub_str = f'{int(position_rub):_}' + " RUB"
        position_usd_str = f'{int(position_usd):_}' + " USD"

        if currency == 'RUB':
            position_usd_str = colored(position_usd_str, attrs=['dark'])

        if currency == 'USD':
            position_rub_str = colored(position_rub_str, attrs=['dark'])

        table.rows.append([account, position_rub_str, position_usd_str])


    total_rub_str = f'{int(total_rub):_}' + " RUB"
    total_usd_str = f'{int(total_usd):_}' + " USD"
    table.rows.append(["","", ""])
    table.rows.append([colored("TOTAL", attrs=['bold']), colored(total_rub_str,attrs=['bold']), colored(total_usd_str,attrs=['bold'])])
    print("")
    print(table)



def income_report(bean, begin, end):
    begin_str = begin.strftime('%Y-%m-%d')
    end_str = end.strftime('%Y-%m-%d')

    q = f'''
        SELECT
            account,
            currency,
            neg(sum(number(convert(position, "RUB", date)))) as position_rub,
            neg(sum(number(convert(position, "USD", date)))) as position_usd
        WHERE
            account ~ "Income" and date >= {begin_str} and date <= {end_str}
        ORDER BY position_usd, account DESC
    '''

    table = BeautifulTable()

    account_header = colored("ACCOUNT", attrs=['bold'])
    position_rub_header = colored("POSITION RUB", attrs=['bold'])
    position_usd_header = colored("POSITION USD", attrs=['bold'])

    table.columns.header = [account_header, position_rub_header, position_usd_header]
    table.columns.alignment[account_header] = BeautifulTable.ALIGN_LEFT
    table.columns.alignment[position_rub_header] = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment[position_usd_header] = BeautifulTable.ALIGN_RIGHT
    table.set_style(BeautifulTable.STYLE_MARKDOWN)


    total_rub = 0
    total_usd = 0
    rows = bean.query(q)
    for row in rows:
        currency = str(row.currency)
        account = str(row.account).replace('Income:', '')
        position_rub = float(row.position_rub)
        position_usd = float(row.position_usd)

        total_rub += position_rub
        total_usd += position_usd

        position_rub_str = f'{int(position_rub):_}' + " RUB"
        position_usd_str = f'{int(position_usd):_}' + " USD"

        if currency == 'RUB':
            position_usd_str = colored(position_usd_str, attrs=['dark'])

        if currency == 'USD':
            position_rub_str = colored(position_rub_str, attrs=['dark'])

        table.rows.append([account, position_rub_str, position_usd_str])


    total_rub_str = f'{int(total_rub):_}' + " RUB"
    total_usd_str = f'{int(total_usd):_}' + " USD"
    table.rows.append(["","",""])
    table.rows.append([colored("TOTAL", attrs=['bold']), colored(total_rub_str,attrs=['bold']), colored(total_usd_str,attrs=['bold'])])
    print("")
    print(table)


def assets_report(bean):
    today = date.today().strftime('%Y-%m-%d')
    q = f'''
        SELECT 
            account,
            currency,
            sum(number(convert(position, "RUB", TODAY()))) as position_rub,
            sum(number(convert(position, "USD", TODAY()))) as position_usd
        FROM OPEN ON {today}
        WHERE
            account ~ "Assets" AND not account ~ "Инвестиции"
    '''
    table = BeautifulTable()

    account_header = colored("ACCOUNT", attrs=['bold'])
    position_rub_header = colored("POSITION RUB", attrs=['bold'])
    position_usd_header = colored("POSITION USD", attrs=['bold'])

    table.columns.header = [account_header, position_rub_header, position_usd_header]
    table.columns.alignment[account_header] = BeautifulTable.ALIGN_LEFT
    table.columns.alignment[position_rub_header] = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment[position_usd_header] = BeautifulTable.ALIGN_RIGHT
    table.set_style(BeautifulTable.STYLE_MARKDOWN)


    total_rub = 0
    total_usd = 0
    rows = bean.query(q)
    for row in rows:
        currency = str(row.currency)
        account = str(row.account).replace('Assets:', '')
        position_rub = float(row.position_rub)
        position_usd = float(row.position_usd)

        total_rub += position_rub
        total_usd += position_usd

        position_rub_str = f'{int(position_rub):_}' + " RUB"
        position_usd_str = f'{int(position_usd):_}' + " USD"

        if currency == 'RUB':
            position_usd_str = colored(position_usd_str, attrs=['dark'])

        if currency == 'USD':
            position_rub_str = colored(position_rub_str, attrs=['dark'])

        table.rows.append([account, position_rub_str, position_usd_str])


    total_rub_str = f'{int(total_rub):_}' + " RUB"
    total_usd_str = f'{int(total_usd):_}' + " USD"
    table.rows.append(["","",""])
    table.rows.append([colored("TOTAL", attrs=['bold']), colored(total_rub_str,attrs=['bold']), colored(total_usd_str,attrs=['bold'])])
    print("")
    print(table)


def invest_profit_report(bean):
    q = '''
    SELECT
        account,
        number,
        GETPRICE(currency, "RUB", date) as price_rub_date,
        GETPRICE(currency, "RUB", TODAY()) as price_rub_today,
        GETPRICE("USD", "RUB", date) as usd_date,
        GETPRICE("USD", "RUB", TODAY()) as usd_today
    WHERE
        account ~ "Инвестиции" AND currency != "RUB" AND currency != "USD";
    '''

    accounts = {}

    rows = bean.query(q)
    for row in rows:
        account = str(row.account).replace('Assets:Инвестиции:', '')
        number = int(row.number)

        bond = {
            'price_rub_date': float(row.price_rub_date),
            'price_rub_today': float(row.price_rub_today),
            'usd_date': float(row.usd_date),
            'usd_today': float(row.usd_today)
        }

        if account not in accounts:
            accounts[account] = queue.Queue()
        
        for i in range(abs(number)):
            if number > 0:
                accounts[account].put(bond)
            else:
                accounts[account].get()


    table = BeautifulTable(maxwidth=1000)

    account_header = colored("ACCOUNT", attrs=['bold'])
    position_rub_header = colored("PROFIT RUB", attrs=['bold'])
    position_usd_header = colored("PROFIT USD", attrs=['bold'])
    persent_rub_header = colored("PERCENT RUB", attrs=['bold'])
    persent_usd_header = colored("PERCENT USD", attrs=['bold'])

    table.columns.header = [account_header, position_rub_header, persent_rub_header, position_usd_header, persent_usd_header]
    table.columns.alignment[account_header] = BeautifulTable.ALIGN_LEFT
    table.columns.alignment[position_rub_header] = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment[position_usd_header] = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment[persent_rub_header] = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment[persent_usd_header] = BeautifulTable.ALIGN_RIGHT
    table.set_style(BeautifulTable.STYLE_MARKDOWN)

    total_rub_put = 0
    total_rub_get = 0
    total_usd_put = 0
    total_usd_get = 0

    for account in accounts:
        account_rub_put = 0
        account_rub_get = 0
        account_usd_put = 0
        account_usd_get = 0

        for i in range(accounts[account].qsize()):
            bond = accounts[account].get()
            rub_diff = bond['price_rub_today'] - bond['price_rub_date']
           
            # считаем профит в рублях
            rub_profit = rub_diff
            if rub_diff > 0:
                rub_profit = rub_diff * 0.87

            account_rub_put += bond['price_rub_date']
            account_rub_get += bond['price_rub_date'] + rub_profit

            account_usd_put += bond['price_rub_date'] / bond['usd_date']
            account_usd_get += (bond['price_rub_date'] + rub_profit) / bond['usd_today']

        
        total_rub_put += account_rub_put
        total_rub_get += account_rub_get
        total_usd_put += account_usd_put
        total_usd_get += account_usd_get

        account_rub_profit = account_rub_get - account_rub_put
        account_usd_profit = account_usd_get - account_usd_put

        account_rub_profit_persent = (account_rub_get / account_rub_put - 1) * 100
        account_usd_profit_persent = (account_usd_get / account_usd_put - 1) * 100


        account_rub_profit_str = colored(f'{int(account_rub_profit):_}' + " RUB", attrs=['dark'])
        account_usd_profit_str = f'{int(account_usd_profit):_}' + " USD"

        account_rub_profit_persent_str = colored(f'{account_rub_profit_persent:.2f} % RUB', attrs=['dark'])
        account_usd_profit_persent_str = f'{account_usd_profit_persent:.2f} % USD'

        table.rows.append([account, account_rub_profit_str, account_rub_profit_persent_str, account_usd_profit_str, account_usd_profit_persent_str])

    total_rub_profit = total_rub_get - total_rub_put
    total_usd_profit = total_usd_get - total_usd_put

    total_rub_profit_persent = (total_rub_get / total_rub_put - 1) * 100
    total_usd_profit_persent = (total_usd_get / total_usd_put - 1) * 100

    total_rub_profit_str = colored(f'{int(total_rub_profit):_}' + " RUB", attrs=['dark'])
    total_usd_profit_str = colored(f'{int(total_usd_profit):_}' + " USD", attrs=['bold'])

    total_rub_profit_persent_str = colored(f'{total_rub_profit_persent:.2f} % RUB', attrs=['dark'])
    total_usd_profit_persent_str = colored(f'{total_usd_profit_persent:.2f} % USD', attrs=['bold'])

    total_str = colored('TOTAL', attrs=['bold'])

    table.rows.append(['', '', '', '', ''])
    table.rows.append([total_str, total_rub_profit_str, total_rub_profit_persent_str, total_usd_profit_str, total_usd_profit_persent_str])

    print('')
    print(table)


def invest_part_report(bean):
    q = '''
        SELECT
	    currency,
            SUM(number) * FIRST(GETPRICE(currency, "RUB", TODAY())) as sum
	WHERE
	    account ~ "Assets:Инвестиции" AND currency != "RUB"
        ORDER BY sum, currency DESC
    '''

    total = 0
    currencies = {}

    rows = bean.query(q)
    for row in rows:
        currency = str(row.currency)
        sum = float(row.sum)

        total += sum
        currencies[currency] = sum

    table = BeautifulTable(maxwidth=1000)

    currency_header = colored("CURRENCY", attrs=['bold'])
    position_header = colored("TOTAL RUB", attrs=['bold'])
    percent_header = colored("PART", attrs=['bold'])

    table.columns.header = [currency_header,position_header, percent_header]
    table.columns.alignment[currency_header] = BeautifulTable.ALIGN_LEFT
    table.columns.alignment[position_header] = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment[percent_header] = BeautifulTable.ALIGN_RIGHT
    table.set_style(BeautifulTable.STYLE_MARKDOWN)

    for currency in currencies:
        position = int(currencies[currency])
        percent = position / total * 100

        position_str = colored(f'{position:_} RUB', attrs=['dark'])
        percent_str = f'{percent:.2f} %'

        table.rows.append([currency, position_str, percent_str])

    print('')
    print(table)


def invest_assets_report(bean):
    q = '''
    SELECT
        account,
        number,
        GETPRICE(currency, "RUB", date) as price_rub_date,
        GETPRICE(currency, "RUB", TODAY()) as price_rub_today,
        GETPRICE("USD", "RUB", TODAY()) as usd_today
    WHERE
        account ~ "Инвестиции" AND currency != "RUB" AND currency != "USD";
    '''

    accounts = {}

    rows = bean.query(q)
    for row in rows:
        account = str(row.account).replace('Assets:Инвестиции:', '')
        number = int(row.number)

        bond = {
            'price_rub_date': float(row.price_rub_date),
            'price_rub_today': float(row.price_rub_today),
            'usd_today': float(row.usd_today)
        }

        if account not in accounts:
            accounts[account] = queue.Queue()

        for i in range(abs(number)):
            if number > 0:
                accounts[account].put(bond)
            else:
                accounts[account].get()


    table = BeautifulTable(maxwidth=1000)

    account_header = colored("ACCOUNT", attrs=['bold'])
    position_rub_header = colored("POSITION RUB", attrs=['bold'])
    position_usd_header = colored("POSITION USD", attrs=['bold'])

    table.columns.header = [account_header, position_rub_header, position_usd_header]
    table.columns.alignment[account_header] = BeautifulTable.ALIGN_LEFT
    table.columns.alignment[position_rub_header] = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment[position_usd_header] = BeautifulTable.ALIGN_RIGHT
    table.set_style(BeautifulTable.STYLE_MARKDOWN)

    total_rub_get = 0
    total_usd_get = 0

    for account in accounts:
        account_rub_get = 0
        account_usd_get = 0

        for i in range(accounts[account].qsize()):
            bond = accounts[account].get()
            rub_diff = bond['price_rub_today'] - bond['price_rub_date']

            # считаем профит в рублях
            rub_profit = rub_diff
            if rub_diff > 0:
                rub_profit = rub_diff * 0.87

            account_rub_get += bond['price_rub_date'] + rub_profit
            account_usd_get += (bond['price_rub_date'] + rub_profit) / bond['usd_today']

        total_rub_get += account_rub_get
        total_usd_get += account_usd_get

        account_rub_get_str = f'{int(account_rub_get):_} RUB'
        account_usd_get_str = f'{int(account_usd_get):_} USD'

        table.rows.append([account, account_rub_get_str,account_usd_get_str])

    total_rub_get_str = colored(f'{int(total_rub_get):_} RUB', attrs=['bold'])
    total_usd_get_str = colored(f'{int(total_usd_get):_} USD', attrs=['bold'])

    total_str = colored('TOTAL', attrs=['bold'])

    table.rows.append(['', '', ''])
    table.rows.append([total_str, total_rub_get_str, total_usd_get_str])

    print('')
    print(table)


def invest_cash_report(bean):
    q = '''
        SELECT
            account,
            SUM(number) as sum
        WHERE
            account ~ "Assets:Инвестиции" AND currency = "RUB"
    '''

    table = BeautifulTable(maxwidth=1000)

    currency_header = colored("ACCOUNT", attrs=['bold'])
    position_header = colored("POSITION RUB", attrs=['bold'])

    table.columns.header = [currency_header,position_header]
    table.columns.alignment[currency_header] = BeautifulTable.ALIGN_LEFT
    table.columns.alignment[position_header] = BeautifulTable.ALIGN_RIGHT
    table.set_style(BeautifulTable.STYLE_MARKDOWN)


    total = 0

    rows = bean.query(q)
    for row in rows:
        account = str(row.account).replace('Assets:Инвестиции:', '').replace(':RUB', '')
        position = float(row.sum)

        position_str = colored(f'{int(position):_} RUB')
        table.rows.append([account, position_str])

        total += position

    total_str = colored('TOTAL', attrs=['bold'])
    total_position_str = colored(f'{int(total):_} RUB', attrs=['bold'])

    table.rows.append(['', ''])
    table.rows.append([total_str, total_position_str])

    print('')
    print(table)


if __name__ == "__main__":
    args = docopt(__doc__)
    # print(args)

    begin, end = date_range(args)

    journal = DEFAULT_JOURNAL_FILE
    if args['--journal']:
        journal = args['--journal']
    
    bean = BeancountWrapper(journal)

    if args['expenses']:
        expenses_report(bean, begin, end)

    elif args['income']:
        income_report(bean, begin, end)

    elif args['assets']:
        assets_report(bean)

    elif args['invest'] and args['<report>'] == 'profit':
        invest_profit_report(bean)

    elif args['invest'] and args['<report>'] == 'part':
        invest_part_report(bean)

    elif args['invest'] and args['<report>'] == 'assets':
        invest_assets_report(bean)

    elif args['invest'] and args['<report>'] == 'cash':
        invest_cash_report(bean)
