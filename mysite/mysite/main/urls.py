from django.urls import path
from . import views

urlpatterns = [
    path('tracker/', views.track_stocks, name='tracker'),
    path('view-portfolio/', views.view_portfolio, name='view_portfolio'),
    path('transaction/', views.transaction, name='transaction'),
    path('home/', views.home, name='home'),
    path('candlestick_view/<str:stock_symbol>/', views.candlestick_view, name='candlestick_view'),
    path('user_search/', views.user_search, name='user_search'),
    path('user/<str:username>/', views.user_portfolio, name='user_portfolio'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    path('unfollow/<str:username>/', views.unfollow_user, name='unfollow_user'),
    path('notifications/', views.notifications, name='notifications'),
    path('account/', views.account, name='account_page'),
    path('change_password/', views.change_password, name='change_password'),
    path('followers/', views.followers_list, name='followers_list'),
    path('following/', views.following_list, name='following_list'),
    
]