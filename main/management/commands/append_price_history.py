from django.core.management.base import BaseCommand
from main.models import Stock, PriceHistory
import polars as pl
import yfinance as yf
from datetime import datetime
import pandas_market_calendars as mcal


class Command(BaseCommand):
    help = 'Populate PriceHistory model with historical stock prices'

    def handle(self, *args, **options):
        today = datetime.today().strftime('%Y-%m-%d')
        nyse = mcal.get_calendar('NYSE')
        valid_dates = nyse.valid_days(start_date=today, end_date=today)
        if today in valid_dates:

            stocks = Stock.objects.all()

            for stock in stocks:

                df = yf.download(stock.symbol, period='1d')
                #df = yf.download(stock.symbol, start='2024-04-01', end='2024-04-03')  #Incase I forget to turn on my laptop for the day

                df = df.reset_index()

                last_prices = pl.from_pandas(df)

                last_prices = last_prices.with_columns(
                    pl.col("Open").round(2),
                    pl.col("High").round(2),
                    pl.col("Low").round(2),
                    pl.col("Close").round(2)
                )
                    
                for row in last_prices.rows(named=True):
                    PriceHistory.objects.create(
                        stock=stock,
                        date=row['Date'],
                        open=row['Open'],
                        high=row['High'],
                        low=row['Low'],
                        close=row['Close'],
                        volume=row['Volume']
                    )

                self.stdout.write(self.style.SUCCESS(f'Successfully populated PriceHistory for {stock.symbol}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Stock market is closed today'))
