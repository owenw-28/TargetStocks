from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class Follow(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='followers')
    follower = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='following')

    class Meta:
        unique_together = ('user_profile', 'follower')  


class Notification(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_received')
    transaction_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_sent')
    transaction_details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)   
        

class Stock(models.Model):
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default = 0.0)
    open_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    high_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    low_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    close_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume = models.PositiveIntegerField(null=True, blank=True)
    recommendation = models.CharField(max_length=20, null=True, blank=True)
            

    def __str__(self):
        return f"{self.symbol}"
    
class PriceHistory(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    date = models.DateField()
    open = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.PositiveIntegerField(null=True, blank=True)


    def __str__(self):
        return f"{self.stock.symbol} - {self.date}"
    

class Portfolio(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_expenditure = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def calculate_current_value(self):
        total_value = Decimal('0.0')

        portfolio_stocks = PortfolioStock.objects.filter(portfolio=self)
        for portfolio_stock in portfolio_stocks:
            stock = portfolio_stock.stock
            quantity = Decimal(str(portfolio_stock.quantity))

            if stock.close_price is not None:
                close_price = Decimal(str(stock.close_price))  
                total_value += quantity * close_price

        self.current_value = total_value
        self.save()


    def __str__(self):
        return f"Stock Portfolio for {self.user_profile.user.username}"


class Transaction(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10) 
    date = models.DateTimeField(default=timezone.now().date())

    def __str__(self):
        return f"{self.transaction_type} - {self.quantity} shares of {self.stock.symbol} on {self.date}"
    

class PortfolioStock(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    date_bought = models.DateField(null=True, blank=True)
    date_sold = models.DateField(null=True, blank=True)
    transaction_history = models.ManyToManyField(Transaction, blank=True)

    