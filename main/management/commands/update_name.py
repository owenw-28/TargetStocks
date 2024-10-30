from django.core.management.base import BaseCommand
from main.models import Stock
import finnhub


class Command(BaseCommand):
    help = 'Update company names for all stocks'

    def handle(self, *args, **options):

        finnhub_client = finnhub.Client(api_key="")

        list_of_companydata = finnhub_client.stock_symbols('US')

        stock_data = []

        keys = ['symbol', 'name']

        for company in list_of_companydata:
            company['symbol'] = company['displaySymbol']
            company['name'] = company['description']
            newdict = {x:company[x] for x in keys}
            stock_data.append(newdict)
                
        tickers = []
        names = []

        for company in stock_data:
            tickers.append(company['symbol'])
            names.append(company['name'])

        result = zip(tickers, names)

        companies = list(result)

        stocks = Stock.objects.all()

        for stock in stocks:
            for symbol, company_name in companies:
                if symbol == stock.symbol:
                    stock.name = company_name
                    stock.save()
                    self.stdout.write(self.style.SUCCESS(f'Successfully updated company name for {stock.symbol}'))
                    break
            else:
                # If the symbol is not found in the local data
                self.stdout.write(self.style.WARNING(f"Company name not found for symbol {stock.symbol}"))
