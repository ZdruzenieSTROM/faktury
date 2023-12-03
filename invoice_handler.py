import csv
import json
from datetime import date
import requests
from dataclasses import dataclass
from typing import List, Dict
from decimal import Decimal
import os
import yaml
import tqdm
from multiprocessing import Pool

from settings import API_KEY, STROM_ID


@dataclass(frozen=True)
class InvoiceItem:
    nazov_polozky: str
    jednotka: str
    cena: Decimal


@dataclass(frozen=True)
class InvoiceRecord:
    cislo_faktury: str
    odberatel: str
    datum_vystavenia: str
    datum_dodania: str
    datum_splatnosti: str
    predmet: str
    suma: Decimal
    datum_uhrady: str
    kod_faktury: str


class InvoiceSetValidationError(Exception):
    """Invalid invoice set"""


@dataclass(frozen=True)
class InvoiceSet:
    issuer: str
    date_delivery: str
    date_issue: str
    date_due: str
    invoice_items: Dict[str, InvoiceItem]
    customers: List[dict]

    def validate_customer(self, customer: dict):
        if 'o_name' not in customer:
            raise InvoiceSetValidationError('Zákazník nemá vyplnené meno')
        name = customer['o_name']
        if 'f_paid' in customer and ('i_date_paid' not in customer or customer['i_date_paid'] is None):
            raise InvoiceSetValidationError(
                f'Faktúra pre {name} bola označená ako uhradená ale nemá vyplnený dátum zaplatenia v stĺpci i_date_paid')
        if 'i_date_paid' in customer and customer['i_date_paid'] is not None and customer['i_date_paid'] > self.date_issue:
            raise InvoiceSetValidationError(
                f'Faktúra pre {name} má dátum úhrady i_date_paid neskorší ako dátum vystavenia')

    def validate(self):
        if self.date_due is None:
            raise InvoiceSetValidationError('Dátum splatnosti nebol vyplnený')
        if self.date_delivery is None:
            raise InvoiceSetValidationError('Dátum dodania nebol vyplnený')
        if self.date_issue <= self.date_due:
            raise InvoiceSetValidationError(
                'Dátum vystavenia je neskorší ako dátum splatnosti')
        for customer in self.customers:
            self.validate_customer(customer)

    @staticmethod
    def load_customers(file_name):
        customers = []
        with open(file_name, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                customers.append(
                    {key: value for key, value in row.items() if value})
        return customers

    @staticmethod
    def from_files(event_name: str):
        customer_file = os.path.join('input', f'{event_name}.csv')
        settings_file = os.path.join('input', f'{event_name}.yaml')
        if not os.path.exists(customer_file):
            raise InvoiceSetValidationError(
                f'Súbor so zoznamom zákazníkov ({customer_file}) neexistuje')
        if not os.path.exists(settings_file):
            raise InvoiceSetValidationError(
                f'Súbor s nastaveniami ({settings_file}) neexistuje')
        customers = InvoiceSet.load_customers(customer_file)
        with open(settings_file, encoding='utf-8') as settings_stream:
            settings_dict = yaml.load(settings_stream, yaml.Loader)

        return InvoiceSet(
            issuer=settings_dict.get('vystavil'),
            date_delivery=settings_dict.get('datum_dodania'),
            date_issue=settings_dict.get('datum_vystavenia', date.today()),
            date_due=settings_dict.get('datum_splatnosti'),
            invoice_items={item_name: InvoiceItem(
                **item_specs) for item_name, item_specs in settings_dict.get('polozky', {}).items()},
            customers=customers

        )


class InvoiceSession:

    def __init__(self, debug=False):
        self.session = requests.Session()
        self.debug = debug
        self.__send_request('init', {})

    def __send_request(self, method: str, data: dict):
        """Request to Faktury"""
        return self.session.get(
            f'https://www.faktury-online.com/api/{method}',
            params={
                'data': json.dumps(
                    dict(
                        key=API_KEY,
                        email='info@strom.sk',
                        apitest=1 if self.debug else 0,
                        **data
                    )
                )
            },
            verify=True
        )

    def download_invoice(self, code):
        return self.__send_request(
            'detail-subor',
            data={'f': code}
        ).content

    def get_invoice(self, code):
        invoice_url = self.__send_request('zf', {'code': code}).json()['url']
        response = self.session.get(invoice_url)
        return response.content

    def create_invoice(self, customer: Dict[str, str], invoice_set: InvoiceSet) -> InvoiceRecord:
        # Sort customer properties
        info = {key: value for key, value in customer.items()
                if key.startswith('i_')}
        faktura = {key: value for key,
                   value in customer.items() if key.startswith('f_')}
        items = [(invoice_set.invoice_items[key], value)
                 for key, value in customer.items()
                 if key in invoice_set.invoice_items]

        # Compile items
        items_compiled = []
        total_price = 0

        for item, quantity in items:
            if quantity == 0 or quantity == '0':
                continue

            items_compiled.append(
                {
                    'p_text': item.nazov_polozky.format(**info),
                    'p_unit': item.jednotka,
                    'p_price': str(item.cena),
                    'p_quantity': quantity
                }
            )
            total_price += Decimal(quantity)*Decimal(item.cena)

        # Send request
        response = self.__send_request(
            'nf',
            {
                'd': {'d_id': STROM_ID},
                'o': {key: value for key, value in customer.items()
                      if key.startswith('o_')},
                'f': {
                    'f_date_issue': invoice_set.date_issue,
                    'f_date_delivery': invoice_set.date_delivery,
                    'f_date_due': invoice_set.date_due,
                    'f_issued_by': invoice_set.issuer,
                    **faktura
                },
                'p': items_compiled
            }

        )
        code = response.json()['code']
        number = response.json()['number']

        return InvoiceRecord(
            cislo_faktury=number,
            odberatel=f'{customer.get("o_name","")}, {customer.get("o_street","")}, {customer.get("o_zip","")} {customer.get("o_city","")}',
            datum_dodania=invoice_set.date_delivery,
            datum_vystavenia=invoice_set.date_issue,
            datum_splatnosti=invoice_set.date_due,
            predmet=items.keys()[0].nazov_polozky.format(
                **info) if len(items) == 0 else '',
            suma=total_price,
            kod_faktury=code,
            datum_uhrady=customer.get('i_date_paid', '')
        )

    def get_invoice_detail(self, code: str):
        response = self.__send_request(
            method='status',
            data={
                'code': code
            }
        )
        return response.json()

    def list_invoices(self, from_date, to_date):
        def get_file_name(from_date, to_date):
            return f'output/export_dennik_{from_date}_{to_date}.csv'

        def invoice_to_dict(invoice):
            invoice_detail = self.get_invoice_detail(invoice['code'])
            subject = ','.join(item['item_name']
                               for item in invoice_detail['items'])
            return {
                'Poradové číslo': int(invoice['invoice_number'][:3]),
                'Číslo faktúry': invoice['invoice_number'],
                'Odberateľ': f"{invoice['customer']}, {invoice_detail['customer_street']}, {invoice_detail['customer_zip']} {invoice_detail['customer_city']}",
                'Dátum vystavenia': invoice['invoice_date_issue'],
                'Dátum dodania': invoice['invoice_date_delivery'],
                'Dátum splatnosti': invoice['invoice_date_due'],
                'Predmet': subject,
                'Suma': invoice['invoice_amount'],
                'Dátum úhrady': ''
            }

        response = self.__send_request(
            method='list/issued',
            data={
                'from': from_date,
                'to': to_date
            }
        )
        invoices = response.json()['invoices']
        invoices_with_detail = map(invoice_to_dict, invoices)
        print(invoices_with_detail)
        with open(get_file_name(from_date, to_date), 'w', newline='', encoding='utf-8') as export_file:
            writer = csv.DictWriter(export_file,
                                    fieldnames=['Poradové číslo', 'Číslo faktúry', 'Odberateľ', 'Dátum vystavenia', 'Dátum dodania', 'Dátum splatnosti', 'Predmet', 'Suma', 'Dátum úhrady'])

            writer.writerows(invoices_with_detail)
