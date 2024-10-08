from .models import Stock, PortfolioStock
from django.core.management import call_command

def run_append_price_history():
    call_command('append_price_history')


def update_stock_prices():
    stocks = Stock.objects.all()

    for stock in stocks:

        current_price = stock.close_price

        portfolio_stocks = PortfolioStock.objects.filter(stock=stock)

        for portfolio_stock in portfolio_stocks:
            portfolio_stock.current_price = current_price
            portfolio_stock.save()


def get_stock_data(mydb, symbol):

    mycursor = mydb.cursor()

    headers = ('open_price', 'high_price', 'low_price', 'close_price', 'volume')
                
    mycursor.execute(f"SELECT Open, High, Low, Close, Volume FROM prices WHERE symbol = '{symbol}' ORDER BY Date")

    result = mycursor.fetchall()

    try:
        current = result[-1]
        prices = dict(zip(headers, current))
        return prices
    except:
        return None

