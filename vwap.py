from math import cos, exp, pi, sqrt

import numpy as np
import pandas as pd
from pandas import DataFrame, Series, merge, DatetimeIndex

# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
# from freqtrade.strategy.interface import CategoricalParameter, DecimalParameter, IntParameter


import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
import datetime

from freqtrade.persistence import Trade
from functools import reduce

from pandas.core.base import PandasObject

# from technical.indicators import cci
from technical.util import resample_to_interval, resampled_merge
from freqtrade.strategy import timeframe_to_minutes



# --------------------------------


class mvwap(IStrategy):
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
    # def informative_pairs(self):

    #     # get access to all pairs available in whitelist. 
    #     pairs = self.dp.current_whitelist()
    #     # Assign tf to each pair so they can be downloaded and cached for strategy.
    #     informative_pairs = [(pair, '1d') for pair in pairs]
    #     return informative_pairs

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
                # Assuming 1h dataframe -resampling to 4h:
        now = datetime.datetime.now()
        minutes=(now.hour * 60) + now.minute
        df_res = resample_to_interval(dataframe.resample(f'{minutes}min'))
        df_res['vwapday'] = Series.vwap(df_res)
        dataframe = resampled_merge(dataframe, df_res, fill_na=True)

        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=30)

        dataframe['vwap'] = Series.vwap(dataframe)
        devUD = [1.28, 2.01, 2.51, 3.09, 4.01]
                # similar to above vwapsum
        dataframe['Typical_Price'] = (dataframe['volume'] * (dataframe['high'] + dataframe['low']) / 2).cumsum()  

        # similar to above volumesum
        dataframe['Typical_Volume'] = dataframe['volume'].cumsum()  
        dataframe['r_vwap'] = Series.rolling_vwap(dataframe,  window=200, min_periods=1)
        # similar to above myvwap
        dataframe['vwap'] = dataframe['Typical_Price'] / dataframe['Typical_Volume']   

        # my std dev calculation = an incrementing std dev of df.VWAP
        dataframe['DEV'] = dataframe['vwap'].expanding().std()
        # dataframe['vwup1']= dataframe['vwap'] + devUD[0] * dataframe['DEV']
        # dataframe['vwdow1']= dataframe['vwap'] - devUD[0] * dataframe['DEV']
        # dataframe['vwup2']= dataframe['vwap'] + devUD[1] * dataframe['DEV']
        # dataframe['vwdow2']= dataframe['vwap'] - devUD[1] * dataframe['DEV']

        for dev in devUD:
            up = 'vwup{}'.format(dev)
            dow = 'vwdow{}'.format(dev)
            dataframe[up]= df_res['vwapday'] + dev * dataframe['DEV']
            dataframe[dow]= df_res['vwapday'] - dev * dataframe['DEV']
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
                # (dataframe['ma99/close'] > 1.5) &
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
                # (dataframe['ma2'] < dataframe['ma99'] )&      
                (dataframe['rsi'] > 49)
            ),
            'sell'] = 1
        return dataframe
