import click
from invoice_handler import InvoiceSet, InvoiceSetValidationError, InvoiceSession, InvoiceRecord
import csv
from dataclasses import fields, asdict
import os


@click.group()
def cli():
    pass


@click.command()
@click.argument('name')
@click.option('--debug', is_flag=True)
@click.option('--download', is_flag=True)
def vytvor(name, debug, download):
    invoice_set = InvoiceSet.from_files(name)
    print(debug)
    api_session = InvoiceSession(debug=debug)

    output = []
    try:
        invoice_set.validate()
    except InvoiceSetValidationError as error:
        click.echo(click.style(str(error), fg='red'), err=True)
        return
    click.echo(click.style('Zakladám faktúry ...', fg='green'))
    for customer in invoice_set.customers:
        invoice_record = api_session.create_invoice(
            customer=customer, invoice_set=invoice_set)
        click.echo(click.style(
            f'Založená faktúra pod číslom {invoice_record.cislo_faktury}', fg='green'))
        output.append(invoice_record)
        if download:
            api_session.download_invoice(invoice_record.kod_faktury)

    with open(os.path.join('output', f'{name}.csv'), 'w', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=InvoiceRecord.__dataclass_fields__.keys(), delimiter=';')
        writer.writeheader()
        for customer in output:
            writer.writerow(asdict(customer))
    click.echo(click.style('V outputs je vystup', fg='green'))


@click.command()
@click.argument('name')
def skontroluj(name):
    invoice_set = InvoiceSet.from_files(name)
    try:
        invoice_set.validate()
        click.echo(click.style('Všetko vyzerá byť v poriadku', fg='green'))
    except InvoiceSetValidationError as error:
        click.echo(click.style(str(error), fg='red'), err=True)


@click.command()
@click.argument('from_date')
@click.argument('to_date')
def dennik(from_date, to_date):
    session = InvoiceSession()
    session.list_invoices(from_date, to_date)


cli.add_command(vytvor)
cli.add_command(skontroluj)
cli.add_command(dennik)
if __name__ == '__main__':
    cli()
