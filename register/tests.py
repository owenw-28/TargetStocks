from django.test import TestCase
from django.utils import timezone
from main.forms import TransactionForm
from main.models import Stock  # Import the Stock model

# Create your tests here.

class TransactionFormTest(TestCase):
    def setUp(self):
        # Initialize a stock object with symbol 'AAPL'
        Stock.objects.create(symbol='AAPL', name='Apple Inc.')

    def test_valid_form(self):
        form_data = {
            'stock_symbol': 'AAPL',
            'quantity': 10,
            'price_per_share': 150.50,
            'transaction_type': 'buy',
            'date': timezone.now().date(),
        }
        form = TransactionForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_stock(self):
        form_data = {
            'stock_symbol': 'AAPL',
            'quantity': 10,
            'price_per_share': 150.50,
            'transaction_type': 'buy',
            'date': timezone.now().date(),
        }
        form = TransactionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_quantity(self):
        form_data = {
            'stock_symbol': '123',   # Invalid symbol
            'quantity': 0,  
            'price_per_share': 150.50,
            'transaction_type': 'buy',
            'date': timezone.now().date(),
        }
        form = TransactionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('stock_symbol', form.errors)

    def test_invalid_price_per_share(self):
        form_data = {
            'stock_symbol': 'AAPL',
            'quantity': 10,
            'price_per_share': 0,  # Invalid price_per_share
            'transaction_type': 'buy',
            'date': timezone.now().date(),
        }
        form = TransactionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('price_per_share', form.errors)
