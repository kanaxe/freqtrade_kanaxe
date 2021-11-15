# --- Do not remove these libs --- freqtrade backtesting --strategy SmoothScalp --timerange 20210110-20210410
from pandas.core.dtypes.missing import notna, notnull
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
# --------------------------------
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from typing import Dict, List
from functools import reduce
from pandas import DataFrame, DatetimeIndex, merge
# --------------------------------
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy

#V1
class heikin(IStrategy):
    #do not use this strategy in live mod. It is not good enough yet and can only be use to find trends.
    timeframe = '5m'
    #I haven't found the best roi and stoplost, so feel free to explore.
    minimal_roi = {
        "5": 0.004,
        "15": 0.008,
        "25": 0.013,
        "31": 0
    }
    stoploss = -0.031

        # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.01
    trailing_only_offset_is_reached = True

        # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 500

    # Optional order type mapping.
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc'
    }
    
#     plot_config = {
#   "main_plot": {
#     "hma20": {
#       "color": "#811125",
#       "type": "line"
#     }
#   },
#   "subplots": {
#     "RSI": {
#       "rsi": {
#         "color": "red"
#       }
#     },
#     "hlow": {
#       "h-low": {
#         "color": "#2de7cc",
#         "type": "line"
#       }
#     },
#     "htsine": {
#       "htsine": {
#         "color": "#688669",
#         "type": "line"
#       }
#     }
#   }
# }
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:   
        #     /study("Heikin Ashi Smoothed Buy Sell v4 ", overlay=true)
        # EMAlength=input(55,"EMA LENGTH?")

        # src = ohlc4
        dataframe['ohlc4']=(dataframe['open'] + dataframe['high'] + dataframe['low'] + dataframe['close']) / 4
        dataframe['ohlc4-1']=(dataframe['open'].shift(1) + dataframe['high'].shift(1) + dataframe['low'].shift(1) + dataframe['close'].shift(1)) / 4
        dataframe['hlc3']=(dataframe['high'] + dataframe['low'] + dataframe['close']) / 3
        # haOpen = 0.0
        # haOpen := (src + nz(haOpen[1])) / 2
        dataframe['ohlc4-1']=dataframe['ohlc4-1'].fillna(dataframe['ohlc4'])
        dataframe['haOpen'] = (dataframe['ohlc4'] + dataframe['ohlc4-1']) / 2
        # haC = (ohlc4 + nz(haOpen) + max(high, nz(haOpen)) + min(low, nz(haOpen))) / 4
        # print(dataframe)
       
        dataframe['haC']= (dataframe['ohlc4'] + dataframe['haOpen'] + dataframe[['high', 'haOpen']].max(axis=1) + dataframe[['low', 'haOpen']].min(axis=1) ) / 4
        # EMA1 = ema(haC, EMAlength)
        dataframe['ema1'] = ta.EMA(dataframe['haC'], timeperiod=15)
        # EMA2 = ema(EMA1, EMAlength)
        dataframe['ema2'] = ta.EMA(dataframe['ema1'], timeperiod=15)
        # EMA3 = ema(EMA2, EMAlength)
        dataframe['ema3'] = ta.EMA(dataframe['ema2'], timeperiod=15)
        # TMA1 = 3 * EMA1 - 3 * EMA2 + EMA3
        dataframe['TMA1'] = 3 * dataframe['ema1'] - 3 * dataframe['ema2'] + dataframe['ema3']
        # EMA4 = ema(TMA1, EMAlength)
        dataframe['ema4'] = ta.EMA(dataframe['TMA1'], timeperiod=15)
        # EMA5 = ema(EMA4, EMAlength)
        dataframe['ema5'] = ta.EMA(dataframe['ema4'], timeperiod=15)
        # EMA6 = ema(EMA5, EMAlength)
        dataframe['ema6'] = ta.EMA(dataframe['ema5'], timeperiod=15)
        # TMA2 = 3 * EMA4 - 3 * EMA5 + EMA6
        dataframe['TMA2'] = 3 * dataframe['ema4'] - 3 * dataframe['ema5'] + dataframe['ema6']
        # IPEK = TMA1 - TMA2
        dataframe['ipek'] = dataframe['TMA1'] - dataframe['TMA2']
        # YASIN = TMA1 + IPEK
        dataframe['yasin'] = dataframe['TMA1'] - dataframe['ipek']
        # EMA7 = ema(hlc3, EMAlength)
        dataframe['ema7'] = ta.EMA(dataframe['hlc3'], timeperiod=15)
        # EMA8 = ema(EMA7, EMAlength)
        dataframe['ema8'] = ta.EMA(dataframe['ema7'], timeperiod=15)
        # EMA9 = ema(EMA8, EMAlength)
        dataframe['ema9'] = ta.EMA(dataframe['ema8'], timeperiod=15)
        # TMA3 = 3 * EMA7 - 3 * EMA8 + EMA9
        dataframe['TMA3'] = 3 * dataframe['ema7'] - 3 * dataframe['ema8'] + dataframe['ema9']
        # EMA10 = ema(TMA3, EMAlength)
        dataframe['ema10'] = ta.EMA(dataframe['TMA3'], timeperiod=15)
        # EMA11 = ema(EMA10, EMAlength)
        dataframe['ema11'] = ta.EMA(dataframe['ema10'], timeperiod=15)
        # EMA12 = ema(EMA11, EMAlength)
        dataframe['ema12'] = ta.EMA(dataframe['ema11'], timeperiod=15)
        # TMA4 = 3 * EMA10 - 3 * EMA11 + EMA12
        dataframe['TMA4'] = 3 * dataframe['ema10'] - 3 * dataframe['ema11'] + dataframe['ema12']
        # IPEK1 = TMA3 - TMA4
        dataframe['ipek1'] = dataframe['TMA3'] - dataframe['TMA4']
        # YASIN1 = TMA3 + IPEK1
        dataframe['yasin1'] = dataframe['TMA3'] - dataframe['ipek1']

        # mavi = YASIN1
        # kirmizi = YASIN


        # longCond=mavi>kirmizi and mavi[1]<=kirmizi[1]
        # shortCond=mavi<kirmizi and mavi[1]>=kirmizi[1]


        dataframe['ohlc4']=(dataframe['open'] + dataframe['high'] + dataframe['low'] + dataframe['close']) / 4
        dataframe['hlc3']=(dataframe['high'] + dataframe['low'] + dataframe['close']) / 3
        dataframe['hl2']=(dataframe['high'] + dataframe['low'] ) / 2
        dataframe['hma16'] = qtpylib.hma(dataframe['ohlc4'], 20)
        dataframe['hma8'] = qtpylib.hma(dataframe['hl2'], 8)
        return dataframe
        

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (qtpylib.crossed_above(dataframe['close'], dataframe['hma16']))&
                (dataframe['yasin1'] > dataframe['yasin']) &
                (dataframe['yasin1'].shift(1) <= dataframe['yasin'].shift(1))
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['yasin1'] < dataframe['yasin']) &
                (dataframe['yasin1'].shift(1) >= dataframe['yasin'].shift(1))
            ),
            'sell'] = 0
        return dataframe
