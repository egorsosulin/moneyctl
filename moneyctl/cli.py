from click.shell_completion import CompletionItem
from datetime import datetime, date
from click import ParamType, echo
from calendar import monthrange
from sys import exit

from moneyctl.journal import Journal, JournalException, AccountStatus
from moneyctl.beancount_wrapper import BeancountWrapper
from moneyctl.report import Report, ReportException

import click


### Constants =================================================================

MIN_YEAR = 2000
MAX_YEAR = 2100
MIN_MONTH = 1
MAX_MONTH = 12
DEFAULT_ERROR_CODE = 1
UNKNOWN_ERROR_CODE = 200


### CLI Entrypoint ------------------------------------------------------------

@click.group()
@click.pass_context
def cli(ctx):
    pass


### CLI Exception -------------------------------------------------------------

class CliException(BaseException):
    def __init__(self, message=None):
        super().__init__(message)


### Autocompletion: Transaction Template --------------------------------------

class TransactionTemplateVarType(ParamType):
    name = "template"
    def shell_complete(self, ctx, param, incomplete):
        journal = Journal()
        templates = journal.get_templates_names()
        return [
            CompletionItem(template)
            for template in templates if template.startswith(incomplete)
        ]


### Autocompletion: Open Accounts ---------------------------------------------

class AccountVarType(ParamType):
    name = "account"
    def shell_complete(self, ctx, param, incomplete):
        journal = Journal()
        accounts = journal.get_accounts_names(status=AccountStatus.OPEN)
        return [
            CompletionItem(account)
            for account in accounts if account.startswith(incomplete)
        ]


### Autocompletion: Report Formats --------------------------------------------

class ReportFormatVarType(ParamType):
    name = "format"
    def shell_complete(self, ctx, param, incomplete):
        report = Report()
        formats = report.get_formats_names()
        return [
            CompletionItem(format)
            for format in formats if format.startswith(incomplete)
        ]

# Subcommand Group: Transaction ===============================================

@cli.group()
@click.pass_context
def transaction(ctx):
    """Transaction subcommands"""
    pass


### Transaction Command: Add --------------------------------------------------

@transaction.command()
@click.option('-T', '--template', 'template', type=TransactionTemplateVarType(), help='Use template for transaction')
@click.option('-f', '--from', 'from_', type=AccountVarType(), help='Set transaction source account')
@click.option('-t', '--to', 'to', type=AccountVarType(), help='Set transaction destination account')
@click.option('-d', '--date', 'date', type=click.DateTime(formats=['%Y-%m-%d']), default=datetime.now(), help='Set transaction date')
@click.option('-a', '--amount', 'amount',  multiple=True, type=click.IntRange(min=0), help='Set transaction amount')
@click.option('-m', '--comment', 'comment', help='Add comment for transaction')
@click.option('-e', '--edit', is_flag=True, default=False, help='Edit journal file after transaction adding')
@click.pass_context
def add(ctx, template, from_, to, date, amount, comment, edit):
    '''Add transaction to journal'''
    try:
        journal = Journal()
        transaction = journal.new_transaction()

        transaction.set(date=date,
                        template=template,
                        comment=comment,
                        account_from=from_,
                        account_to=to)

        if len(amount) == 1:
            transaction.set(amount_from=amount[0], amount_to=amount[0])
        elif len(amount) == 2:
            transaction.set(amount_from=amount[0], amount_to=amount[1])
        elif len(amount) > 2:
            raise CliException('Too many "amount" arguments')

        transaction.close()
        journal.commit()

        if edit:
            f = transaction.get_file()
            click.edit(filename=f)

    except (JournalException, CliException) as e:
        echo(f"Error: {e}", err=True)
        exit(DEFAULT_ERROR_CODE)
    
    except BaseException as e:
        echo(f"Unknown Error: {e}", err=True)
        exit(UNKNOWN_ERROR_CODE)

# TODO Transaction Subcommand: edit
# TODO Transaction Subcommand: print


# Subcommand Group: Report ====================================================

@cli.group()
@click.option('--format', 'format', default=Report().get_default_format_name(), type=ReportFormatVarType(), help="Set report output format")
@click.option('--rounding/--no-rounding', default=True, help='Display numbers without rounding')
@click.pass_context
def report(ctx, format, rounding):
    """Report subcommands"""
    ctx.ensure_object(dict)
    ctx.obj['format'] = format
    ctx.obj['rounding'] = rounding


### Report Command: Assets ----------------------------------------------------

@report.command()
@click.option('--empty-accounts/--no-empty-accounts', default=False, help='Display accounts with low amounts')
@click.pass_context
def assets(ctx, empty_accounts):
    """Print current assets report"""
    try:
        beancount_string = Journal().to_beancount_string()
        beancount_wrapper = BeancountWrapper(beancount_string)
        report = beancount_wrapper.assets_report(empty_accounts=empty_accounts, total=True)
        report.set(format=ctx.obj['format'], rounding=ctx.obj['rounding'])
        report.print()

    except (JournalException, CliException, ReportException) as e:
        echo(f"Error: {e}", err=True)
        exit(1)
    
    except BaseException as e:
        echo(f"Unknown Error: {e}", err=True)
        exit(200)


### Additional Functions ------------------------------------------------------

def args_to_timerange(from_, to, year, month) -> date:
    y = date.today().year
    m = date.today().month

    # Only "from" and "to" arguments are set
    if from_ != None and to != None and year == None and month == None:
        if from_ > to:
            raise CliException('"from" date should be less than "to" date')
        return from_.date(), to.date()

    # Only "year" and "month" arguments are set
    elif from_ == None and to == None and year != None and month != None:
        y = year
        m = month

    # Only "month" argument is set
    elif from_ == None and to == None and year == None and month != None:
        m = month

    # Only "year" arguments is set
    elif from_ == None and to == None and year != None and month == None:
        y = year

    # No arguments are set -- use current month begin-end as timerange
    elif from_ == None and to == None and year == None and month == None:
        pass

    # Incorrect arguments combination
    else:
        raise CliException('Incorrect time range arguments combination')

    _, last_month_day = monthrange(y, m)
    return date(y, m, 1), date(y, m, last_month_day)


### Report Command: Expenses --------------------------------------------------

@report.command()
@click.option('-f', '--from', 'from_', type=click.DateTime(formats=['%Y-%m-%d']), help='Set time range beginning')
@click.option('-t', '--to', 'to', type=click.DateTime(formats=['%Y-%m-%d']), help='Set time range ending')
@click.option('-y', '--year', 'year', type=click.IntRange(min=MIN_YEAR, max=MAX_YEAR), help='Set yearly time range')
@click.option('-m', '--month', 'month', type=click.IntRange(min=MIN_MONTH, max=MAX_MONTH), help='Set monthly time range')
@click.pass_context
def expenses(ctx, from_, to, year, month):
    '''Print expenses report'''
    try:
        f, t = args_to_timerange(from_, to, year, month)

        beancount_string = Journal().to_beancount_string()
        beancount_wrapper = BeancountWrapper(beancount_string)
        report = beancount_wrapper.expenses_report(from_=f, to=t, total=True)
        report.set(format=ctx.obj['format'], rounding=ctx.obj['rounding'])
        report.print()

    except (JournalException, CliException, ReportException) as e:
        echo(f"Error: {e}", err=True)
        exit(DEFAULT_ERROR_CODE)
    
    except BaseException as e:
        echo(f"Unknown Error: {e}", err=True)
        exit(UNKNOWN_ERROR_CODE)


### Report Command: Income ----------------------------------------------------

@report.command()
@click.option('-f', '--from', 'from_', type=click.DateTime(formats=['%Y-%m-%d']), help='Set time range beginning')
@click.option('-t', '--to', 'to', type=click.DateTime(formats=['%Y-%m-%d']), help='Set time range ending')
@click.option('-y', '--year', 'year', type=click.IntRange(min=MIN_YEAR, max=MAX_YEAR), help='Set yearly time range')
@click.option('-m', '--month', 'month', type=click.IntRange(min=MIN_MONTH, max=MAX_MONTH), help='Set monthly time range')
@click.pass_context
def income(ctx, from_, to, year, month):
    '''Print income report'''
    try:
        f, t = args_to_timerange(from_, to, year, month)

        beancount_string = Journal().to_beancount_string()
        beancount_wrapper = BeancountWrapper(beancount_string)
        report = beancount_wrapper.income_report(from_=f, to=t, total=True)
        report.set(format=ctx.obj['format'], rounding=ctx.obj['rounding'])
        report.print()

    except (JournalException, CliException, ReportException) as e:
        echo(f"Error: {e}", err=True)
        exit(DEFAULT_ERROR_CODE)
    
    except BaseException as e:
        echo(f"Unknown Error: {e}", err=True)
        exit(UNKNOWN_ERROR_CODE)


### Report Command: Investments Cash ------------------------------------------

@report.command()
@click.pass_context
def invest_cash(ctx):
    '''Print investments cash assets report'''
    try:
        beancount_string = Journal().to_beancount_string()
        beancount_wrapper = BeancountWrapper(beancount_string)
        report = beancount_wrapper.invest_cash_report(total=True)
        report.set(format=ctx.obj['format'], rounding=ctx.obj['rounding'])
        report.print()

    except (JournalException, CliException, ReportException) as e:
        echo(f"Error: {e}", err=True)
        exit(DEFAULT_ERROR_CODE)
    
    except BaseException as e:
        echo(f"Unknown Error: {e}", err=True)
        exit(UNKNOWN_ERROR_CODE)

### Report Command: Investments Part ------------------------------------------

@report.command()
@click.pass_context
def invest_parts(ctx):
    '''Print investments assets distribution report'''
    try:
        beancount_string = Journal().to_beancount_string()
        beancount_wrapper = BeancountWrapper(beancount_string)
        report = beancount_wrapper.invest_parts_report(total=True)
        report.set(format=ctx.obj['format'], rounding=ctx.obj['rounding'])
        report.print()

    except (JournalException, CliException, ReportException) as e:
        echo(f"Error: {e}", err=True)
        exit(DEFAULT_ERROR_CODE)
    
    except BaseException as e:
        echo(f"Unknown Error: {e}", err=True)
        exit(UNKNOWN_ERROR_CODE)

### TODO download-prices
