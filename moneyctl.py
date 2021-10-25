#!/usr/bin/env python3

"""MoneyCTL.

Usage:
  moneyctl.py add <template> [options]
  moneyctl.py expenses [options]
  moneyctl.py income [options]
  moneyctl.py assets [options]
  moneyctl.py invest <report> [options]
  moneyctl.py download-prices [options]
  moneyctl.py split <currency> <rate>

Invest Reports:
  assets
  cash
  part
  profit

Options:
  -e, --edit                  Edit file after add
  -d, --date DATE             Set date for add option
  -c, --cost NUMBER           Set cost for add option
  -Y, --year YEAR             Set year for report
  -M, --month MONTH           Set month for report
  -B, --begin BEGIN_DATE      Set begin of range for report (example: 2021-12-31)
  -E, --end END_DATE          Set end of range for report
  -j, --journal JOURNAL_FILE  Set journal file to load

Examples:
  moneyctl.py split FXUS 100

"""


import os
import re
import sys
import queue
import investpy
import datetime
from docopt import docopt
from datetime import date
from beancount import loader
from termcolor import colored
from calendar import monthrange
from beautifultable import BeautifulTable
from beancount.query.query import run_query


DEFAULT_JOURNAL_DIR = '/home/user/git/money'
DEFAULT_JOURNAL_FILE = DEFAULT_JOURNAL_DIR + '/main.bean'
DEFAULT_TEMPLATE_DIR = DEFAULT_JOURNAL_DIR + '/templates'
DEFAULT_PRICES_DIR = DEFAULT_JOURNAL_DIR + '/prices'


class BeancountWrapper():
    def __init__(self, beancount_file):
        self.entries, self.errors, self.options = loader.load_file(beancount_file, log_errors=sys.stderr)

    def query(self, query_text):
        output = run_query(self.entries, self.options, query_text)
        return output[1]


def get_date(date_str):
    if date_str == None:
        return date.today()
    else:
        return date.fromisoformat(date_str)


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
        position_number = 0

        for i in range(accounts[account].qsize()):
            bond = accounts[account].get()
            rub_diff = bond['price_rub_today'] - bond['price_rub_date']
            position_number += 1
           
            # считаем профит в рублях
            rub_profit = rub_diff
            if rub_diff > 0:
                rub_profit = rub_diff * 0.87

            account_rub_put += bond['price_rub_date']
            account_rub_get += bond['price_rub_date'] + rub_profit

            account_usd_put += bond['price_rub_date'] / bond['usd_date']
            account_usd_get += (bond['price_rub_date'] + rub_profit) / bond['usd_today']

        
        if position_number != 0:
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
	    SUM(number) as num,
            SUM(number) * FIRST(GETPRICE(currency, "RUB", TODAY())) as sum
	WHERE
	    account ~ "Assets:Инвестиции" AND currency != "RUB"
        ORDER BY sum, currency DESC
    '''

    total = 0
    currencies = {}
    currencies_num = {}

    rows = bean.query(q)
    for row in rows:
        currency = str(row.currency)
        sum = float(row.sum)
        number = int(row.num)

        total += sum
        currencies[currency] = sum
        currencies_num[currency] = number

    table = BeautifulTable(maxwidth=1000)

    currency_header = colored("CURRENCY", attrs=['bold'])
    assets_header = colored("ASSETS", attrs=['bold'])
    position_header = colored("TOTAL RUB", attrs=['bold'])
    percent_header = colored("PART", attrs=['bold'])

    table.columns.header = [currency_header, assets_header ,position_header, percent_header]
    table.columns.alignment[currency_header] = BeautifulTable.ALIGN_LEFT
    table.columns.alignment[assets_header] = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment[position_header] = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment[percent_header] = BeautifulTable.ALIGN_RIGHT
    table.set_style(BeautifulTable.STYLE_MARKDOWN)

    for currency in currencies:
        if currencies_num[currency] != 0:
            position = int(currencies[currency])
            percent = position / total * 100

            position_str = colored(f'{position:_} RUB', attrs=['dark'])
            percent_str = f'{percent:.2f} %'

            table.rows.append([currency, currencies_num[currency], position_str, percent_str])

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
    assets_header = colored("ASSETS", attrs=['bold'])
    position_rub_header = colored("POSITION RUB", attrs=['bold'])
    position_usd_header = colored("POSITION USD", attrs=['bold'])

    table.columns.header = [account_header, assets_header, position_rub_header, position_usd_header]
    table.columns.alignment[account_header] = BeautifulTable.ALIGN_LEFT
    table.columns.alignment[assets_header] = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment[position_rub_header] = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment[position_usd_header] = BeautifulTable.ALIGN_RIGHT
    table.set_style(BeautifulTable.STYLE_MARKDOWN)

    total_rub_get = 0
    total_usd_get = 0

    for account in accounts:
        account_rub_get = 0
        account_usd_get = 0
        position_number = 0

        for i in range(accounts[account].qsize()):
            bond = accounts[account].get()
            rub_diff = bond['price_rub_today'] - bond['price_rub_date']

            position_number += 1

            # считаем профит в рублях
            rub_profit = rub_diff
            if rub_diff > 0:
                rub_profit = rub_diff * 0.87

            account_rub_get += bond['price_rub_date'] + rub_profit
            account_usd_get += (bond['price_rub_date'] + rub_profit) / bond['usd_today']

        if position_number != 0:

            total_rub_get += account_rub_get
            total_usd_get += account_usd_get

            account_rub_get_str = f'{int(account_rub_get):_} RUB'
            account_usd_get_str = f'{int(account_usd_get):_} USD'

            table.rows.append([account, position_number, account_rub_get_str,account_usd_get_str])

    total_rub_get_str = colored(f'{int(total_rub_get):_} RUB', attrs=['bold'])
    total_usd_get_str = colored(f'{int(total_usd_get):_} USD', attrs=['bold'])

    total_str = colored('TOTAL', attrs=['bold'])

    table.rows.append(['', '', '', ''])
    table.rows.append([total_str, '', total_rub_get_str, total_usd_get_str])

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


def add_transaction(template_name, date, cost):

    date_str = date.strftime('%Y-%m-%d')
    date_year = str(date.year)

    template_data = ''
    template_file = DEFAULT_TEMPLATE_DIR + '/' + template_name + '.bean'

    if os.path.exists(template_file):
        with open(template_file, 'r') as file_object:
            template_data = file_object.read().format(DATE=date_str, COST=cost)
    else:
        print('Error: Template does not exist: ' + template_name)
        exit(1)

    journal_date_data = ''
    journal_date_dir  = DEFAULT_JOURNAL_DIR + '/journals/' + date_year
    journal_date_file = journal_date_dir + '/' + date_str + '.bean'

    if os.path.exists(journal_date_file):
        with open(journal_date_file, 'r') as file_object:
            journal_date_data = file_object.read()


    new_journal_date_data = journal_date_data + '\n' + template_data

    if not os.path.exists(journal_date_dir):
        os.makedirs(journal_date_dir)

    with open(journal_date_file, 'w') as file_object:
        file_object.write(new_journal_date_data)

    return journal_date_file


def download_prices(date):

    previous_date = date - datetime.timedelta(days=1)
    date_year = str(date.year)
    date_str = date.strftime('%Y-%m-%d')

    prices = {}

    etfs = ['FXUS', 'FXIM', 'FXIT']
    currency_crosses = ['USD/RUB']

    for etf in etfs:
        ticker = investpy.search_quotes(text=etf, products=['etfs'], countries=['russia'], n_results=5)
        data = ticker[-1].retrieve_historical_data(from_date=previous_date.strftime('%d/%m/%Y'), to_date=date.strftime('%d/%m/%Y'))
        prices[etf] = data.loc[date_str, 'Close']

    for cross in currency_crosses:
        data  = investpy.get_currency_cross_historical_data(cross, from_date=previous_date.strftime('%d/%m/%Y'), to_date=date.strftime('%d/%m/%Y'))
        prices[cross.replace('/RUB', '')] = data.loc[date_str, 'Close']

    data = ''
    for ticker in prices:
        data += f'{date_str} price {ticker} {prices[ticker]} RUB\n'


    prices_file_dir = DEFAULT_PRICES_DIR + '/' + date_year
    prices_file = prices_file_dir + '/' + date_str + '.bean'

    if not os.path.exists(prices_file_dir):
        os.makedirs(prices_file_dir)

    with open(prices_file, 'w') as file_object:
        file_object.write(data)


def split_currency(currency, rate):

    def rate_price(old_price):
        new_price = float(old_price) / rate
        return f'{new_price:.8}'

    def rate_num(old_num):
        new_num = int(old_num) * rate
        return f'{new_num}'

    price_regex = re.compile(f'^[-0-9]+ +price +{currency} +([-\.0-9]+) +')
    num_regex = re.compile(f'.* +([-\.0-9]+) +{currency} +@@')

    files = []
    for dirpath, dnames, fnames in os.walk(DEFAULT_JOURNAL_DIR):
        for f in fnames:
            if (
                    f.endswith('.bean')
                    and not 'template' in dirpath
                    and not 'accounts' in dirpath
                    and not 'commodities' in dirpath
                ):
                files.append(os.path.join(dirpath, f))

    for file in files:
        content = ''
        changes = False
        lines = []

        with open(file, 'r') as file_object:
            lines = file_object.readlines()

        for line in lines:

            updated_line = line

            price_match = price_regex.match(line)
            if price_match:
                old_price = price_match.group(1)
                new_price = rate_price(old_price)
                updated_line = line.replace(old_price, new_price)

            num_match = num_regex.match(line)
            if num_match:
                old_num = num_match.group(1)
                new_num = rate_num(old_num)
                updated_line = line.replace(old_num, new_num, 1)

            if updated_line != line:
                changes = True

            content += updated_line

        if changes:
            with open(file, 'w') as file_object:
                file_object.write(content)


def git_crypt_unlocked():
    status_file = DEFAULT_JOURNAL_DIR + "/.git-crypt.status"

    if os.path.isfile(status_file):

        status = ''
        with open(status_file, 'rb') as file:
            status = file.readline()

        if status.startswith(b'unlocked'):
            return True
        else:
            return False

    else:
        return True


if __name__ == "__main__":
    args = docopt(__doc__)
    # print(args)

    if not git_crypt_unlocked():
        print('Error: Repo is locked')
        exit(1)

    if args['split']:
        split_currency(args['<currency>'], int(args['<rate>']))
        exit(0)

    if args['download-prices']:
        date = get_date(args['--date'])
        download_prices(date)
        exit(0)

    if args['add']:
        date = get_date(args['--date'])

        if args['--cost'] is None:
            print('Error: Cost does not specify')
            exit(1)

        journal_date_file = add_transaction(args['<template>'], date, args['--cost'])

        if args['--edit']:
            editor = os.environ['EDITOR']
            os.execvp(editor, [editor, journal_date_file])

        exit(0)

    journal = DEFAULT_JOURNAL_FILE
    if args['--journal']:
        journal = args['--journal']

    begin, end = date_range(args)
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
