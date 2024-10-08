from django.core.management.base import BaseCommand
from main.recommender import Recommender


class Command(BaseCommand):
    help = 'Update the recommendations'

    def handle(self, *args, **kwargs):
        
        obj = Recommender()
        obj.recommender()

        self.stdout.write(self.style.SUCCESS('Stock recommendation process completed.'))