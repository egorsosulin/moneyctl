#!/usr/bin/env python3

from moneyctl.cli import cli

if __name__ == '__main__':
    cli(obj={})

# import click

# @click.group()
# @click.option('-j', '--journal', 'journal')
# @click.pass_context
# def cli(ctx, journal):
#      ctx.ensure_object(dict)
#      ctx.obj['journal'] = journal


# @cli.command()
# @click.option('-f', '--from', 'from_') # TODO автокомплит из доступных счетов
# @click.option('-t', '--to', 'to')  # TODO автокомплит из доступных счетов
# @click.option('-d', '--date', 'date') # TODO проверка что это дата TODO возможность не указывать
# @click.option('-a', '--amount', 'amount') # TODO проверка что число TODO возможность ввода двух значений
# @click.option('-c', '--comment', 'comment') # TODO опциональный параметр
# @click.pass_context
# def add(ctx, from_, to, date, amount, comment):
#     click.echo('debug add')

# if __name__ == '__main__':
#     cli(obj={})
# if __name__ == '__main__':
#     hello()


#moneyctl -j cash  add -f raiffeisen-card -t food-shop -c 1000 -d 2022-01-30
#moneyctl -j cash  add -f tinkoff-deposit -t investments -c 70000 -C "Отложил деньги на подарок"
#
## Покупка ценных бумаг
#moneyctl -j invest  add -f tinkoff-investments-rub -c 35000 -t tinkoff-broker-SBER -c 10
## Получение дивидентов по бумаге
#moneyctl -j invest  add -f tinkoff-sber-profit -c 5000 -t tinkoff-investmants-rub
#
#moneyctl -j cash   report expenses -M 3
#moneyctl -j invest report income -Y 2021
#
#moneyctl -j invest tools download-currencies
