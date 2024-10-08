from django.test import TestCase
from main.models import Stock, PriceHistory, Portfolio, PortfolioStock, UserProfile, Transaction
from django.contrib.auth import get_user_model
from decimal import Decimal


class StockTest(TestCase):

    def create_stock(self, symbol='TEST', name='Test Symbol', current_price=10.00, open_price=10.00,
                     high_price=12.00, low_price=8.00, close_price=11.00,volume=10000,
                     recommendation=None):
        return Stock.objects.create(symbol=symbol, name=name, current_price=current_price,
                                    open_price=open_price, high_price=high_price, low_price=low_price,
                                    close_price=close_price, volume=volume, recommendation=recommendation)

    def test_stock_creation(self):
        stock = self.create_stock()
        self.assertTrue(isinstance(stock, Stock))
        self.assertEqual(stock.__str__(), stock.symbol)


class PriceHistoryTest(TestCase):

    def create_stock(self, symbol='TEST', name='Test Symbol', current_price=10.00, open_price=10.00,
                     high_price=12.00, low_price=8.00, close_price=11.00,volume=10000,
                     recommendation=None):
        return Stock.objects.create(symbol=symbol, name=name, current_price=current_price,
                                    open_price=open_price, high_price=high_price, low_price=low_price,
                                    close_price=close_price, volume=volume, recommendation=recommendation)

    def create_pricehistory(self, date='2024-03-28', open=10.00,
                     high=12.00, low=8.00, close=11.00,volume=10000):
        return PriceHistory.objects.create(stock=self.create_stock(), date=date, open=open, high=high,
                                           low=low, close=close, volume=volume)
    
    def test_pricehistory_creation(self):
        candle = self.create_pricehistory()
        self.assertTrue(isinstance(candle, PriceHistory))
        self.assertEqual(candle.__str__(), 'TEST - 2024-03-28')



class PortfolioTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.user_profile = UserProfile.objects.create(user=self.user)
        self.portfolio = Portfolio.objects.create(user_profile=self.user_profile, total_income=1000, total_expenditure=500, profit=500)

        stock1 = Stock.objects.create(symbol='AAPL', close_price=150.0)
        stock2 = Stock.objects.create(symbol='GOOGL', close_price=2000.0)

        PortfolioStock.objects.create(portfolio=self.portfolio, stock=stock1, quantity=10, price_per_share=10.00)
        PortfolioStock.objects.create(portfolio=self.portfolio, stock=stock2, quantity=5, price_per_share=9.00)

    def test_calculate_current_value(self):
        self.portfolio.calculate_current_value()

        expected_current_value = Decimal(10 * 150.0 + 5 * 2000.0)
        self.assertEqual(self.portfolio.current_value, expected_current_value)

    def test_portfolio_creation(self):
        self.assertEqual(self.portfolio.__str__(), 'Stock Portfolio for testuser')


class TransactionTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.user_profile = UserProfile.objects.create(user=self.user)
        self.stock = Stock.objects.create(symbol='TEST', name='Test Symbol', current_price=10.00, open_price=10.00,
                     high_price=12.00, low_price=8.00, close_price=11.00,volume=10000,
                     recommendation=None)
        self.transaction = Transaction.objects.create(user_profile=self.user_profile, stock=self.stock, quantity=2,
                                                      price_per_share=5.00, transaction_type='buy', date='2024-03-28')
    
    def test_transaction_creation(self):
        self.assertEqual(self.transaction.__str__(), 'buy - 2 shares of TEST on 2024-03-28')


