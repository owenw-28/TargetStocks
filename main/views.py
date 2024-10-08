from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Portfolio, PortfolioStock, Stock, PriceHistory, Transaction, Follow, Notification
from .forms import TransactionForm, UserSearchForm
from .utils import update_stock_prices
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.models import User
import simplejson as json
from django.db.models import Q
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


def calculate_current_value(portfolio):

    return sum([
        stock.stock.close_price * stock.quantity
        for stock in portfolio.portfoliostock_set.all()
    ])
    

@login_required
def view_portfolio(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    portfolio, created = Portfolio.objects.get_or_create(user_profile=user_profile)

    update_stock_prices()

    portfolio.current_value = calculate_current_value(portfolio)

    transaction_history = Transaction.objects.filter(user_profile=user_profile).order_by('-date')[:15]

    return render(request, 'main/view_portfolio.html', {'portfolio': portfolio, 'transaction_history': transaction_history})


@login_required
def transaction(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    portfolio, created = Portfolio.objects.get_or_create(user_profile=user_profile)

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            stock_symbol = form.cleaned_data['stock_symbol']
            symbol = stock_symbol.symbol
            quantity = form.cleaned_data['quantity']
            price_per_share = form.cleaned_data['price_per_share']
            transaction_type = form.cleaned_data['transaction_type']
            date = form.cleaned_data['date']

            try:
                if transaction_type == 'buy':
                    PortfolioStock.objects.create(portfolio=portfolio, 
                                                  stock=stock_symbol, 
                                                  quantity=quantity, 
                                                  price_per_share=price_per_share,
                                                  date_bought = date,              
                                                  )
                    
                    portfolio.total_expenditure += quantity * price_per_share
                    portfolio.profit = portfolio.total_income - portfolio.total_expenditure

                    Transaction.objects.create(
                        user_profile=user_profile, stock=stock_symbol,
                        quantity=quantity, price_per_share=price_per_share,
                        transaction_type=transaction_type,
                        date = date
                    )
                    
                    followers = user_profile.followers.all()
                    for follower_profile in followers:
                        Notification.objects.create(
                            follower=follower_profile.follower.user,
                            transaction_user=request.user,
                            transaction_details=f"User {request.user.username} bought {quantity} shares of {stock_symbol.symbol} at {price_per_share} USD per share on {date}."
                        )
                    
                elif transaction_type == 'sell':

                    portfolio_stocks = PortfolioStock.objects.filter(portfolio=portfolio, stock__symbol=symbol).order_by('id')
                    
                    if portfolio_stocks.exists():
                        portfolio_stock = portfolio_stocks.first()

                        if quantity <= portfolio_stock.quantity:
                            portfolio_stock.quantity -= quantity
                            total_sell_amount = quantity * price_per_share
                            portfolio.total_income += total_sell_amount
                            portfolio.profit = portfolio.total_income - portfolio.total_expenditure
                            portfolio_stock.save()

                            Transaction.objects.create(
                                user_profile=user_profile, stock=stock_symbol,
                                quantity=quantity, price_per_share=price_per_share,
                                transaction_type=transaction_type,
                                date = date
                            )       


                            followers = user_profile.followers.all()
                            for follower_profile in followers:
                                Notification.objects.create(
                                    follower=follower_profile.follower.user,
                                    transaction_user=request.user,
                                    transaction_details=f"User {request.user.username} bought {quantity} shares of {stock_symbol.symbol} at {price_per_share} USD per share on {date}."
                                )
                            
                        
                            if portfolio_stock.quantity == 0:
                                portfolio_stock.delete()

                        else:
                            error_message = "Insufficient quantity for sell."
                            form.add_error('stock_symbol', error_message)
                            return render(request, 'main/transaction.html', {'form': form, 'portfolio': portfolio})
                    else:

                        error_message = "Stock not found in the portfolio for sell."
                        form.add_error('stock_symbol', error_message)
                        return render(request, 'main/transaction.html', {'form': form, 'portfolio': portfolio})

                portfolio.save()
                messages.success(request, f"Transaction successful for {quantity} shares of {stock_symbol}.")
                return redirect('view_portfolio')

            except PortfolioStock.DoesNotExist:
                messages.error(request, "Error processing the transaction. Please try again.")
        else:
            messages.error(request, "Invalid form submission. Please check the form inputs.")
    else:
        form = TransactionForm()

    return render(request, 'main/transaction.html', {'form': form, 'portfolio': portfolio})


def candlestick_view(request, stock_symbol):
    user_profile = request.user.userprofile

    try:
        portfolio_stocks = PortfolioStock.objects.filter(portfolio__user_profile__user=request.user, stock__symbol=stock_symbol)
        buy_dates = [str(stock.date_bought) for stock in portfolio_stocks]
        transactions = Transaction.objects.filter(
            Q(stock__symbol=stock_symbol) &
            Q(user_profile=user_profile) &
            Q(transaction_type='sell')
        ).order_by('date')
        sell_dates = [str((transaction.date).date()) for transaction in transactions]


    except PortfolioStock.DoesNotExist:
        buy_dates = None
        sell_dates = None

    price_history_data = get_candlestick_data(stock_symbol)
        
    dataJSON = json.dumps(price_history_data) 
    buy_dates = json.dumps(buy_dates)
    sell_dates = json.dumps(sell_dates)

    return render(request, 'main/candlestick_view.html', {
        'stock_symbol': stock_symbol,
        'candlestick_data': dataJSON,
        'buy_dates': buy_dates,
        'sell_dates': sell_dates
    })


def get_candlestick_data(stock_symbol):

    price_history = PriceHistory.objects.filter(stock__symbol=stock_symbol)

    candlestick_data = []
    for entry in price_history:
        candlestick_data.append({
            'date': entry.date.strftime('%Y-%m-%d'),
            'open': entry.open,
            'close': entry.close,
            'low': entry.low,
            'high': entry.high,
        })

    return candlestick_data


def track_stocks(request):
    
    stocks = Stock.objects.filter(volume__gt=0)

    search_query = request.GET.get('search')

    if search_query:
        stocks = stocks.filter(symbol__icontains=search_query)

    paginator = Paginator(stocks, 25)
    page = request.GET.get('page', 1)
    stocks_page = paginator.get_page(page)

    return render(request, 'main/tracker.html', {'stocks_page': stocks_page})


def home(request):

    buy_stocks = Stock.objects.filter(recommendation='buy').order_by('symbol')
    partial_buy_stocks = Stock.objects.filter(recommendation='partial_buy').order_by('symbol')
    sell_stocks = Stock.objects.filter(recommendation='sell').order_by('symbol')

    user_portfolio_symbols = PortfolioStock.objects.filter(portfolio__user_profile__user=request.user, quantity__gt=0).values_list('stock__symbol', flat=True)

    sell_portfoliostock = []

    for stock in sell_stocks:
        if stock.symbol in user_portfolio_symbols:
            sell_portfoliostock.append(stock)
    

    context = {
        'buy_stocks': buy_stocks,
        'partial_buy_stocks': partial_buy_stocks,
        'sell_stocks': sell_portfoliostock,
    }

    return render(request, "main/home.html", context)


def user_search(request):
    form = UserSearchForm()
    results = None 

    if request.method == 'POST':
        form = UserSearchForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            username_query = cleaned_data.get('username')
            if username_query is not None:  
                results = User.objects.filter(username__icontains=username_query).exclude(username=request.user.username)

    return render(request, 'main/user_search.html', {'form': form, 'results': results})


def user_portfolio(request, username):
    user_profile = UserProfile.objects.get(user__username=username)

    if request.user.is_authenticated:
        is_following = Follow.objects.filter(user_profile=user_profile, follower=request.user.userprofile).exists()
    else:
        is_following = False
            
    portfolio, created = Portfolio.objects.get_or_create(user_profile=user_profile)
    
    transaction_history = Transaction.objects.filter(user_profile=user_profile).order_by('-date')[:15]
    
    if not portfolio:
        return render(request, 'main/no_portfolio.html', {'username': username})
    else:
        context = {
            'username': username,
            'user_profile': user_profile,
            'is_following': is_following,
            'portfolio': portfolio,
            'transaction_history': transaction_history,
        }
        return render(request, 'main/user_portfolio.html', context)
    

@login_required
def follow_user(request, username):
    user_profile = get_object_or_404(UserProfile, user__username=username)
    Follow.objects.get_or_create(user_profile=user_profile, follower=request.user.userprofile)
    return redirect('user_portfolio', username=username)


@login_required
def unfollow_user(request, username):
    user_profile = get_object_or_404(UserProfile, user__username=username)
    Follow.objects.filter(user_profile=user_profile, follower=request.user.userprofile).delete()
    return redirect('user_portfolio', username=username)


def leaderboard(request):
    top_10_portfolios = Portfolio.objects.order_by('-profit')[:10]

    context = {
        'portfolios': top_10_portfolios
    }
    return render(request, 'main/leaderboard.html', context)


@login_required
def notifications(request):
    
    user_notifications = Notification.objects.filter(follower=request.user)

    return render(request, 'main/notifications.html', {'notifications': user_notifications})


@login_required
def account(request):
    user_profile = UserProfile.objects.get(user=request.user)
    followers_count = Follow.objects.filter(user_profile=user_profile).count()
    following_count = Follow.objects.filter(follower=user_profile).count()
    return render(request, 'main/account.html', {'user_profile': user_profile, 'following_count': following_count, 'followers_count': followers_count})


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) 
            messages.success(request, 'Your password was successfully updated!')
            return redirect('account') 
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'main/change_password.html', {'form': form})


@login_required
def following_list(request):
    user_profile = UserProfile.objects.get(user=request.user)
    following = Follow.objects.filter(follower=user_profile)
    return render(request, 'main/followers_list.html', {'followers': following})


@login_required
def followers_list(request):
    user_profile = UserProfile.objects.get(user=request.user)
    followers = Follow.objects.filter(user_profile=user_profile)
    return render(request, 'main/following_list.html', {'following': followers})

