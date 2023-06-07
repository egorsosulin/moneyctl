import tomllib
import datetime
from enum import Enum
from pathlib import Path

# Classes =====================================================================

### Journal Class -------------------------------------------------------------

class JournalException(BaseException):
    def __init__(self, message=None):
        super().__init__(message)


class Journal:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._init()
        return cls._instance


    def _init(self):
        self.beancount_files_extension = 'bean'
        self.templates_files_extension = 'toml'

        self.templates_files_glob = '**/*.' + self.templates_files_extension
        self.beancount_files_glob = "**/*." + self.beancount_files_extension

        self.root_dir = Path('.')
        self.transactions_dir = self.root_dir / 'transactions'
        self.templates_dir = self.root_dir / 'templates'
        self.accounts_dir = self.root_dir / 'accounts'

        self.accounts = {}
        self.templates = {}
        self.transaction = None

        self.validate()


    def validate(self):
        if not self.templates_dir.is_dir():
            path = self.templates_dir.absolute()
            message = f'Templates dir "{path}" does not exist'
            raise JournalException(message)

        if not self.accounts_dir.is_dir():
            path = self.accounts_dir.absolute()
            message = f'Accounts dir "{path}" does not exist'
            raise JournalException(message)


    def _read_templates(self):
        for path_object in self.templates_dir.glob(self.templates_files_glob):
            template_name = path_object.stem
            template_object = Template(self, path_object)
            self.templates[template_name] = template_object


    def _gen_transaction_filepath(self, date):
        date_str = date.strftime("%Y-%m-%d")
        year_str = date.strftime("%Y")
        filepath = self.transactions_dir / year_str / f"{date_str}.{self.beancount_files_extension}"
        return filepath


    def _read_accounts(self):
        for path_object in self.accounts_dir.glob(self.beancount_files_glob):
            with open(path_object.absolute(), 'r') as file_object:
                lines = file_object.readlines()
                for line in lines:
                    words = line.split()
                    if len(words) >= 4:

                        date = words[0]
                        status = words[1]
                        account = words[2]
                        ticker = words[3]

                        if account not in self.accounts:
                            self.accounts[account] = Account(self, account)

                        if status == 'open':
                            self.accounts[account].set(
                                open_date=date,
                                status=AccountStatus.OPEN,
                                commodity=Commodity(ticker)) # TODO читать все Commodity по аналогии с Accounts
                        elif status == 'close':
                            self.accounts[account].set(
                                close_date=date,
                                status=AccountStatus.CLOSED)
                        else:
                            message = f'Unknown status "{status}" for account "{account}" in file "{path_object.absolute()}"'
                            raise JournalException(message)


    def get_template(self, template_name):
        if not self.templates:
            self._read_templates()

        if template_name not in self.templates:
            message = f'Template "{template_name}" does not exist'
            raise JournalException(message)

        return self.templates[template_name]


    def get_account(self, account_name):
        if not self.accounts:
            self._read_accounts()
        if account_name not in self.accounts:
            message = f'Account "{account_name}" does not exist'
            raise JournalException(message)
        return self.accounts[account_name]


    def get_templates_names(self):
        if not self.templates:
            self._read_templates()
        return list(self.templates.keys())


    def get_accounts_names(self, status=None):
        if not self.accounts:
            self._read_accounts()
        if status is None:
            return list(self.accounts.keys())
        else:
            names = []
            for account_name in self.accounts:
                account_status = self.accounts[account_name].get_status()
                if status == account_status:
                    names.append(account_name)
            return names


    def new_transaction(self):
        self.transaction = Transaction(self)
        return self.transaction


    def commit(self):
        text = self.transaction.gen_text()
        date = self.transaction.get_date()
        transaction_file = self._gen_transaction_filepath(date)
        transaction_file.parent.mkdir(parents=True, exist_ok=True)
        with open(transaction_file, "a") as f:
            f.write("\n" + text)
        self.transaction.set(file=transaction_file)


    def to_beancount_string(self):
        beancount_string = 'option "operating_currency" "RUB"\n'
        beancount_string += 'option "inferred_tolerance_default" "*:0.01"\n'
        for path_object in self.root_dir.glob(self.beancount_files_glob):
            with open(path_object.absolute(), 'r') as file_object:
                beancount_string += file_object.read()
        return beancount_string


### Account Classes -----------------------------------------------------------

class AccountStatus(Enum):
    OPEN = 1
    CLOSED = 2


class Account:

    def __init__(self, journal, name):
        self.journal = journal
        self.name = name
        self.open_date = None
        self.close_date = None
        self.status = None
        self.commodity = None
        
    def set(self, name=None, open_date=None, close_date=None,
            status=None, commodity=None):
        if name:
           self.name = name
        if open_date:
            self.open_date = open_date
        if close_date:
            self.close_date = close_date
        if status:
            self.status = status
        if commodity:
            self.commodity = commodity

    def get_status(self):
        return self.status

    def get_name(self):
        return self.name

    def get_commodity(self):
        return self.commodity

    def validate(self):
        # проверить что commodity существует
        # проверить что существует open_date
        # проверить что close_date старее open_date
        pass


### Commodity Classes ---------------------------------------------------------

class Commodity:

    def __init__(self, ticker):
        self.open_date = None
        self.ticker = ticker

    def set(self, open_date=None, ticker=None):
        if ticker:
            self.ticker = ticker
        if open_date:
            self.open_date = open_date

    def get_ticker(self):
        return self.ticker


### Transaction Classes -------------------------------------------------------

class TransactionException(JournalException):
    def __init__(self, message=None):
        super().__init__(message)

class TransactionStatus(Enum): # понять а зачем мне вообще статус транзакции (достаточно validate)
    OPEN = 1
    CLOSED = 2
    COMMITED = 3

class Transaction:

    def __init__(self, journal):
        self.status = TransactionStatus.OPEN
        self.journal = journal
        self.file = None

        self.account_from = None
        self.account_to = None
        self.amount_from = None
        self.amount_to = None
        self.comment = None
        self.date = None


    def _merge_transaction(self, transaction):
        if not self.account_from:
            self.account_from = transaction.account_from
        if not self.account_to:
            self.account_to = transaction.account_to
        if not self.amount_from:
            self.amount_from = transaction.amount_from
        if not self.amount_to:
            self.amount_to = transaction.amount_to
        if not self.comment:
            self.comment = transaction.comment
        if not self.date:
            self.date = transaction.date


    def set(self, template=None, file=None, account_from=None, account_to=None,
            amount_from=None, amount_to=None, comment=None, date=None):

        if template:
            t = self.journal.get_template(template)
            self._merge_transaction(t)

        if amount_from:
            self.amount_from = amount_from
        if amount_to:
            self.amount_to = amount_to
        if comment:
            self.comment = comment
        if date:
            self.date = date
        if file:
            self.file = file

        if account_from:
            a = self.journal.get_account(account_from)
            self.account_from = a

        if account_to:
            a = self.journal.get_account(account_to)
            self.account_to = a


    def _validate_non_empty_fields(self):
        if not self.account_from:
            message = 'Transaction field "account_from" not set'
            raise TransactionException(message)
        if not self.account_to:
            message = 'Transaction field "account_to" not set'
            raise TransactionException(message)
        if not self.amount_from:
            message = 'Transaction field "amount_from" not set'
            raise TransactionException(message)
        if not self.amount_to:
            message = 'Transaction field "amount_to" not set'
            raise TransactionException(message)
        if not self.date:
            message = 'Transaction field "date" not set'
            raise TransactionException(message)
        if not self.comment:
            message = 'Transaction field "comment" not set'
            raise TransactionException(message)


    def _validate_accounts(self):
        self.account_to.validate()
        self.account_from.validate()
        if self.account_from.get_name() == self.account_to.get_name():
            message = 'Transaction "account_from" and "account_to" should not be equal'
            raise TransactionException(message)


    def _validate_amounts(self):
        if self.amount_from <= 0:
            message = 'Transaction "amount_from" should be greater then zero'
            raise TransactionException(message)
        if self.amount_to <= 0:
            message = 'Transaction "amount_to" should be greater then zero'
            raise TransactionException(message)


    def _validate_date(self):
        min_year = 2000
        max_year = 2100
        year = self.date.year
        if year < min_year or year > max_year:
            message = f'Transaction "date" not in year range {min_year}-{max_year}'
            raise TransactionException(message)


    def validate(self):
        self._validate_non_empty_fields()
        self._validate_accounts()
        self._validate_amounts()
        self._validate_date()

    
    def get_file(self):
        if self.file is None:
            message = 'File not found for transaction'
            raise TransactionException(message)
        else:
            return self.file


    def get_date(self):
        return self.date


    def gen_text(self):
        date_str = self.date.strftime("%Y-%m-%d")

        account_from_str = self.account_from.get_name()
        account_to_str = self.account_to.get_name()

        commodity_from_str = self.account_from.get_commodity().get_ticker()
        commodity_to_str = self.account_to.get_commodity().get_ticker()

        header_text = f'{date_str} * "{self.comment}"'
        from_text = f'    {account_from_str}    -{self.amount_from} {commodity_from_str}'

        to_text = f'    {account_to_str}    {self.amount_to} {commodity_to_str}'
        if commodity_from_str != commodity_to_str:
            to_text += f' @@ {self.amount_from} {commodity_from_str}'
        # TODO красиво выравнивать суммы по правому краю

        return header_text + '\n' + from_text + '\n' + to_text + '\n'


    def close(self):
        self.validate()
        self.status = TransactionStatus.CLOSED


### Template Classes ----------------------------------------------------------

class Template(Transaction):
    def __init__(self, journal, filepath):
        super().__init__(journal)
        with open(filepath, 'rb') as f:
            data = tomllib.load(f)
            if "amount_from" in data:
                self.amount_from = data["amount_from"]
            if "amount_to" in data:
                self.amount_to = data["amount_to"]
            if "comment" in data:
                self.comment = data["comment"]
            if "date" in data:
                self.date = datetime.strptime(data["date"], "%Y-%m-%d")
            if "account_from" in data:
                self.account_from = self.journal.get_account(data["account_from"])
            if "account_to" in data:
                self.account_to = self.journal.get_account(data["account_to"])
