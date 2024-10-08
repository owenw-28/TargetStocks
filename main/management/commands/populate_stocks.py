import finnhub
from django.core.management.base import BaseCommand
from main.models import Stock


class Command(BaseCommand):
    help = 'Populate the Stock model with initial data'

    def handle(self, *args, **kwargs):
        finnhub_client = finnhub.Client(api_key="cmk23m1r01qi6gquk9p0cmk23m1r01qi6gquk9pg")

        list_of_companydata = finnhub_client.stock_symbols('US')

        stock_data = []

        keys = ['symbol', 'name']

        for company in list_of_companydata:
            company['symbol'] = company['displaySymbol']
            company['name'] = company['description']
            newdict = {x:company[x] for x in keys}
            stock_data.append(newdict)

        for data in stock_data:
            Stock.objects.create(**data)

        self.stdout.write(self.style.SUCCESS('Stocks successfully populated.'))
