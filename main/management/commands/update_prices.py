from django.core.management.base import BaseCommand
from main.models import Stock, PriceHistory
from django.core.exceptions import ObjectDoesNotExist


class Command(BaseCommand):
    help = 'Update the latest stock prices based on historical prices.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Updating latest stock prices...'))

        for stock in Stock.objects.all():
            try:
                latest_price = PriceHistory.objects.filter(stock=stock).latest('date')

                stock.open_price = latest_price.open
                stock.high_price = latest_price.high
                stock.low_price = latest_price.low
                stock.close_price = latest_price.close
                stock.volume = latest_price.volume

                stock.save()

                self.stdout.write(self.style.SUCCESS(f'Latest stock prices updated for {stock.symbol}.'))
            except ObjectDoesNotExist:
                self.stderr.write(self.style.WARNING(f'No price history found for {stock.symbol}. Skipping...'))

        self.stdout.write(self.style.SUCCESS('Latest stock prices updated successfully.'))
