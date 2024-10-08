from django import forms
from .models import Stock
from django.core.validators import MinValueValidator
from django.utils import timezone
from .models import Transaction
import pandas_market_calendars as mcal
from django.utils import timezone


class TransactionForm(forms.Form):
    stock_symbol = forms.CharField(label='Stock Symbol', max_length=10)
    quantity = forms.IntegerField(validators=[MinValueValidator(1, message="Quantity must be at least 1.")])
    price_per_share = forms.DecimalField(label='Price per Share (USD)', max_digits=10, decimal_places=2, 
                                         validators=[MinValueValidator(0.005, message="Price per share has to be greater than 0.")])
    transaction_type = forms.ChoiceField(choices=[('buy', 'Buy'), ('sell', 'Sell')])
    date = forms.DateField(label='Date', initial=timezone.now().date())

    class Meta:
        model = Transaction
        fields = ['stock_symbol', 'quantity', 'price_per_share', 'transaction_type', 'date']
    

    
    def clean_date(self):
        date = self.cleaned_data['date']        

        nyse = mcal.get_calendar('NYSE')
        valid_dates = nyse.valid_days(start_date=date, end_date=date)
        valid = False
        for valid_date in valid_dates:
            if date > timezone.now().date():
                raise forms.ValidationError("Selected date is after today")
            date = str(date)
            valid_date = valid_date.to_pydatetime()
            valid_date = valid_date.strftime("%Y-%m-%d")
            print(valid_date, type(valid_date)) 
            print(date, type(date))
            if valid_date == date:
                valid = True

        if not valid:
            raise forms.ValidationError("Selected date is not a valid trading day.")
        
        return date
    

    def clean_stock_symbol(self):
        stock_symbol = self.cleaned_data['stock_symbol']
        try:
            stock = Stock.objects.get(symbol=stock_symbol)
        except Stock.DoesNotExist:

            raise forms.ValidationError('Invalid stock symbol.')
        return stock
    
class StockSearchForm(forms.Form):
    search_query = forms.CharField(
        label='Search by symbol',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search by symbol'})
    )

class UserSearchForm(forms.Form):
    username = forms.CharField(max_length=150, required=False, label='Search by Username')
