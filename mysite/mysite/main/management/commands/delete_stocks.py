from django.core.management.base import BaseCommand
from main.models import PriceHistory


class Command(BaseCommand):
    help = 'Deletes records from the Stock model based on a condition'

    def handle(self, *args, **options):

        price_history_to_delete = PriceHistory.objects.filter(date='2024-04-01')

        price_history_to_delete.delete()


