import polars as pl
import talib as ta
from .models import Stock, PriceHistory


class Recommender:

    def __init__(self):
        self.buy_symbols = []
        self.partial_buy = []
        self.sell_symbols = []


    def get_symbols(self):
        stock_symbols = Stock.objects.values_list('symbol', flat=True).distinct()

        return stock_symbols


    def get_prices(self, ticker):

        price_history_entries = PriceHistory.objects.select_related('stock').filter(stock__symbol=ticker)

        if price_history_entries.exists():

            data = list(price_history_entries.values('date', 'open', 'high', 'low', 'close', 'volume'))
            df = pl.DataFrame(data)

            df = df.select(
                pl.col('date'),
                pl.col("open").cast(pl.Float64).alias("open"),
                pl.col("high").cast(pl.Float64).alias("high"),
                pl.col("low").cast(pl.Float64).alias("low"),
                pl.col("close").cast(pl.Float64).alias("close"),
                pl.col("volume")
            )


        return df

    def MACD(self, df, close):
        ewma_26 = (close.ewm_mean(span=26, min_periods=26, adjust=False))
        ewma_12 = (close.ewm_mean(span=12, min_periods=12, adjust=False))

        df = df.with_columns(
            MACD = (ewma_12 - ewma_26).round(2),
            MACDs = (ewma_12 - ewma_26).ewm_mean(span=9, min_periods=9, adjust=False).round(2)
        )

        return df


    def RSI(self, df, close):
        rsi = ta.RSI(close, timeperiod=14)
        rsi = rsi.to_frame('rsi')
        df = pl.concat([df, rsi], how='horizontal')
        df = self.StochRSI(df)
        df = df.with_columns(
            pl.col('rsi').round(2)
        )
        
        return df

        
    def StochRSI(self, df, smoothK = 3, smoothD = 3):
        rsi = df.to_series(7)
        
        rolling_min = rsi.rolling_min(window_size=14)
        rolling_max = rsi.rolling_max(window_size=14)

        stochrsi  = ((rsi - rolling_min)/(rolling_max - rolling_min)) * 100
        
        stochrsi_K = stochrsi.rolling_mean(smoothK).round(2)
        stochrsi_D = stochrsi_K.rolling_mean(smoothD).round(2)

        stochrsi_K = stochrsi_K.to_frame('stochrsi_K')
        stochrsi_D = stochrsi_D.to_frame('stochrsi_D')
        
        df = pl.concat([df, stochrsi_K, stochrsi_D], how='horizontal')

        return df

        
    def BBands(self, df, close):
        u_bband, m_bband, l_bband = ta.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
        df = df.with_columns(u_bband.round(2).alias('u_bband'),
                            m_bband.round(2).alias('m_bband'), 
                            l_bband.round(2).alias('l_bband'))

        return df


    def EOM(self, df):
        high = df.to_series(2)
        low = df.to_series(3)
        volume = df.to_series(5)
        distance = ((high + low)/2) - ((high.shift(1) + low.shift(1))/2).alias('distance')
        box_ratio = (volume/100000000) / (high - low)
        period1_eom = distance/box_ratio
        eom = ta.SMA(period1_eom, timeperiod=14)
        df = df.with_columns(eom.round().alias('eom'))

        return df


    def ichimoku_cloud(self, df, close):
        high, low = df.to_series(2), df.to_series(3)
        period9_high = high.rolling_max(window_size=9)
        period9_low = low.rolling_min(window_size=9)
        period26_high = high.rolling_max(window_size=26)
        period26_low = low.rolling_min(window_size=26)
        period52_high = high.rolling_max(window_size=52)
        period52_low = low.rolling_min(window_size=52)

        conversion_line = (period9_high + period9_low) / 2
        base_line = (period26_high + period26_low) / 2
        leading_spanA = ((conversion_line + base_line) / 2).shift(26)
        leading_spanB = ((period52_high + period52_low) / 2).shift(26)
        lagging_span = close.shift(-26)

        df = df.with_columns(
            conversion_line.round(2).alias('conversion line'),
            base_line.round(2).alias('base line'),
            leading_spanA.round(2).alias('leading span A'),
            leading_spanB.round(2).alias('leading span B'),
            lagging_span.round(2).alias('lagging span')
        )

        return df

    def apply_technicals(self, df):
        close = df.to_series(4)
        df = self.MACD(df, close)
        df = self.RSI(df, close)
        df = self.BBands(df, close)
        df = self.EOM(df)
        df = self.ichimoku_cloud(df, close)

        return df


    def get_signals(self, df):

        MACD_sign = (pl.col('MACD') - pl.col('MACDs')).sign()

        ichimoku_sign = (pl.col('conversion line') - pl.col('base line')).sign()

        df = df.with_columns(    
            signal_MACD = (
            pl.when(MACD_sign.is_first_distinct().over(MACD_sign.rle_id()))
            .then(MACD_sign)
            .otherwise(0)),

            signal_rsi = (pl.when(pl.col('rsi') > 70).then(-1)
                            .when(pl.col('rsi') < 30).then(1)
                            .otherwise(0)),
        
            signal_stochrsi = (pl.when(pl.col('stochrsi_K') > 80).then(-1)
                            .when(pl.col('stochrsi_K') < 20).then(1)
                            .otherwise(0)),

            signal_bbands = (pl.when(pl.col('close') > pl.col('u_bband')).then(-1)
                            .when(pl.col('close') < pl.col('l_bband')).then(1)
                            .otherwise(0)),

            signal_eom = (pl.when(pl.col('eom') > 10).then(1)
                        .when(pl.col('eom') < 0).then(-1)
                        .otherwise(0)),
            
            signal1_ichimoku = (
                pl.when((pl.col('close') > pl.col('leading span A')) 
                        & (pl.col('close') > pl.col('leading span B'))).then(1)
                        .when((pl.col('close') < pl.col('leading span A')) 
                            & (pl.col('close') < pl.col('leading span B'))).then(-1)
                            .otherwise(0)),
            
            signal2_ichimoku = (
            pl.when(ichimoku_sign.is_first_distinct().over(ichimoku_sign.rle_id()))
            .then(ichimoku_sign)
            .otherwise(0))
        )

        signals = df.select(['date', 'signal_MACD', 'signal_rsi', 'signal_stochrsi', 'signal_bbands', 'signal_eom', 'signal1_ichimoku', 'signal2_ichimoku'])

        return signals

    def recommender(self):
        tickerlist = self.get_symbols()

        for symbol in tickerlist:
            try:
                df = self.get_prices(symbol)
                df = self.apply_technicals(df)
                signals = self.get_signals(df)

                last_row = signals.row(by_predicate=(pl.col('date') == df.select(pl.last('date')).item()))
                count_1 = last_row.count(1)
                count_minus_1 = last_row.count(-1)

                if count_minus_1 == 0: 
                    if count_1 >= 4:
                        self.buy_symbols.append(symbol)
                    elif count_1 == 3:
                        self.partial_buy.append(symbol)
                else:
                    if count_minus_1 >= 2:
                        self.sell_symbols.append(symbol)

            except:
                pass
        
        Stock.objects.update(recommendation=None)


        for symbol in self.buy_symbols:
            stock = Stock.objects.get(symbol=symbol)
            stock.recommendation = 'buy'
            stock.save()

        for symbol in self.partial_buy:
            stock = Stock.objects.get(symbol=symbol)
            stock.recommendation = 'partial_buy'
            stock.save()

        for symbol in self.sell_symbols:
            stock = Stock.objects.get(symbol=symbol)
            stock.recommendation = 'sell'
            stock.save()