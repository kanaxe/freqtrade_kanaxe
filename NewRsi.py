from math import cos, exp, pi, sqrt

import numpy as np
import pandas as pd
from pandas import Series
from pandas import DataFrame

# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
# from freqtrade.strategy.interface import CategoricalParameter, DecimalParameter, IntParameter


import talib.abstract as ta
from finta import TA
import freqtrade.vendor.qtpylib.indicators as qtpylib
from datetime import datetime, timedelta

from freqtrade.persistence import Trade
from functools import reduce

from pandas.core.base import PandasObject

# from technical.indicators import cci
from technical.util import resample_to_interval, resampled_merge


from ta.volume import VolumeWeightedAveragePrice


# --------------------------------


class NewRsiap(IStrategy):
    """

    author@: Gert Wohlgemuth

    converted from:

    https://github.com/sthewissen/Mynt/blob/master/src/Mynt.Core/Strategies/BbandRsi.cs

    """

    # Minimal ROI designed for the strategy.
    # adjust based on market conditions. We would recommend to keep it low for quick turn arounds
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.014,
        "15":0.018,
        "29":0.0295,
        "70":0.0145,
        "720":0
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.12
    

    # Optimal timeframe for the strategy
    timeframe = '1m'
    def informative_pairs(self):

        # get access to all pairs available in whitelist. 
        pairs = self.dp.current_whitelist()
        # Assign tf to each pair so they can be downloaded and cached for strategy.
        informative_pairs = [(pair, '1d') for pair in pairs]
        return informative_pairs

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
                # Assuming 1h dataframe -resampling to 4h:
        # dataframe_long = resample_to_interval(dataframe, 60)  # 240 = 4 * 60 = 4h

        # # dataframe_long['vwap1'] = Series.vwap(dataframe_long, timeperiod=5)
        # # Combine the 2 dataframes
        # dataframe['r_vwap'] = Series.rolling_vwap(dataframe_long,  window=14, min_periods=None)


        # dataframe = resampled_merge(dataframe, dataframe_long, fill_na=True)
        
        
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=30)
        dataframe['ma99'] = ta.MA(dataframe, timeperiod=99)
        dataframe['ma2'] = ta.MA(dataframe, timeperiod=2)
        dataframe['ma7'] = ta.MA(dataframe, timeperiod=7)
        dataframe['ma14'] = ta.MA(dataframe, timeperiod=14)
        dataframe['ma99/close'] = dataframe['ma99'] / dataframe['close']
        dataframe['close/ma99'] = dataframe['close'] / dataframe['ma99']
        dataframe['mean-volume'] = dataframe['volume'].rolling(15).mean() 

        
        # print(Series)
        # dataframe['vwap'] = ta.VOLUME.VolumeWeightedAveragePrice(dataframe, window=3, fillna=True)
        # if self.dp:
        #     if self.dp.runmode.value in ('live', 'dry_run'):
        #         ticker = self.dp.ticker(metadata['pair'])
        #         dataframe['last_price'] = ticker['last']
        #         dataframe['volume24h'] = ticker['quoteVolume']
        #         dataframe['vwap'] = ticker['vwap']


        
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (   
                # (dataframe['ma2'] < dataframe['ma99'])&
                # (dataframe['ma99/high'] > 1.03) &
                # (dataframe['ma99/high'] < 1.05) &
                # (dataframe['ma2'] > dataframe['ma14']) &
                # (dataframe['ma2'] > dataframe['ma7']) &
                # (dataframe['volume'] > 0) &
                # (dataframe['mean-volume'] > 0.75) &
                # (dataframe['volume'].shift(1) > dataframe['volume'])&
                # |
                # (dataframe['ma2'] > dataframe['ma99'])&
                # (dataframe['high/ma99'] > 1.03) &
                # (dataframe['high/ma99'] < 1.05) &
                # (dataframe['ma2'] > dataframe['ma14']) &
                # (dataframe['ma2'] > dataframe['ma7']) &
                # (dataframe['rsi'] < 30)
                # |
                # (dataframe['ma2'] > dataframe['ma99'])&
                # (dataframe['high/ma99'] > 1.08) &
                # (dataframe['ma2'] > dataframe['ma14']) &
                # (dataframe['ma2'] > dataframe['ma7']) &
                # (dataframe['rsi'] < 30)
                # |
                # (dataframe['ma2'] < dataframe['ma99'] )&
                (dataframe['ma99/close'] > 1.5) &
                # (dataframe['ma2'] > dataframe['ma7']) &
                # (dataframe['ma2'] > dataframe['ma14']) &
                (qtpylib.crossed_above(dataframe['rsi'], 30)) 
                # (dataframe['rsi'] < 14)
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (        
                # (dataframe['ma99/close'] > 1.5) &
                (dataframe['ma2'] < dataframe['ma99'] )&      
                (dataframe['rsi'] > 49)
            ),
            'sell'] = 1
        return dataframe
