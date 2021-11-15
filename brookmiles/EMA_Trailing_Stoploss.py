from freqtrade.strategy import IStrategy
from typing import Dict, List
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class EMA_Trailing_Stoploss(IStrategy):

    minimal_roi = { "0": 0.01 }

    stoploss = -0.01
    
    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.00628
    trailing_stop_positive_offset = 0.02999
    trailing_only_offset_is_reached = True

    timeframe = '1h'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe['ema3'] = ta.EMA(dataframe, timeperiod=3)
        dataframe['ema5'] = ta.EMA(dataframe, timeperiod=5)
        dataframe['go_long'] = qtpylib.crossed_above(dataframe['ema3'], dataframe['ema5']).astype('int')

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            qtpylib.crossed_above(dataframe['go_long'], 0)
        ,
        'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['sell'] = 0
        return dataframe