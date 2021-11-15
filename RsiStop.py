# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
import logging
from pandas import DataFrame

from freqtrade.strategy import IStrategy
# from freqtrade.strategy import CategoricalParameter, DecimalParameter, IntParameter

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from datetime import datetime, timedelta
from freqtrade.persistence import Trade
# from technical.util import resample_to_interval, resampled_merge

logger = logging.getLogger(__name__)
class RsiStop(IStrategy):

    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 2

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
    "0" : 0.015,
    "15": 0.018,
    "29": 0.0295,
    "70": 0.0145,
    "320": 0
    }
        # ROI table:
    # minimal_roi = {
    #     "0": 0.15631,
    #     "12": 0.09574,
    #     "24": 0.03097,
    #     "87": 0
    # }


    #eniyisi
    #     minimal_roi = {
        # "360":0,
        # "70": 0.0145,
        # "29": 0.0295,
        # "15": 0.018,
        # "0": 0.015
    # }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".

        # Optimal timeframe for the strategy.
    timeframe = '1m'
    stoploss = -0.04
    trailing_stop = True
    trailing_stop_positive = 0.24513
    trailing_stop_positive_offset = 0.28508
    trailing_only_offset_is_reached = True



    # use_custom_stoploss = True

    # def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
    #                     current_rate: float, current_profit: float, **kwargs) -> float:

    #     # Make sure you have the longest interval first - these conditions are evaluated from top to bottom.
    #     if current_time - timedelta(minutes=60) > trade.open_date_utc:
    #         return -0.055
    #     elif current_time - timedelta(minutes=180) > trade.open_date_utc:
    #         return -0.08
    #     return 1  
    
    # def get_ticker_indicator(self):
    #     return int(self.ticker_interval[:-1])

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        :param dataframe: Dataframe with data from the exchange
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """


        # # Resample our dataframes
        # # dataframe_five = resample_to_interval(dataframe, self.get_ticker_indicator())
        # dataframe_ten = resample_to_interval(dataframe, self.get_ticker_indicator() * 2)
        # dataframe_fifteen = resample_to_interval(dataframe, self.get_ticker_indicator() * 3)


        # # RSI
        # # dataframe_five['rsi'] = ta.RSI(dataframe_five, timeperiod=30)
        # dataframe_ten['rsi'] = ta.RSI(dataframe_ten, timeperiod=30)
        # dataframe_fifteen['rsi'] = ta.RSI(dataframe_fifteen, timeperiod=30)
        # # merge dataframe back together
        # # dataframe = resampled_merge(dataframe, dataframe_five, fill_na=True)
        # dataframe = resampled_merge(dataframe, dataframe_ten, fill_na=True)
        # dataframe = resampled_merge(dataframe, dataframe_fifteen, fill_na=True)

        dataframe['angle'] = ta.LINEARREG_ANGLE(dataframe['close'], timeperiod=5)
            # RSI
        dataframe['rsi'] = ta.RSI(dataframe,timeperiod=30)


        # Inverse Fisher transform on RSI: values [-1.0, 1.0] (https://goo.gl/2JGGoy)
        rsi = 0.1 * (dataframe['rsi'] - 50)
        dataframe['fisher_rsi'] = (np.exp(2 * rsi) - 1) / (np.exp(2 * rsi) + 1)

            # # Inverse Fisher transform on RSI normaSlized: values [0.0, 100.0] (https://goo.gl/2JGGoy)
            # dataframe['fisher_rsi_norma'] = 50 * (dataframe['fisher_rsi'] + 1)

        # print(dataframe.columns.values)
        dataframe['ema9'] = ta.EMA(dataframe, timeperiod=9)
        dataframe['ema21'] = ta.EMA(dataframe, timeperiod=21)
        dataframe['ema200'] = ta.EMA(dataframe, timeperiod=200)
        dataframe['ma99'] = ta.MA(dataframe, timeperiod=99)

        

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                # (qtpylib.crossed_above(dataframe['rsi'], 34))&
                # (dataframe['fisher_rsi'] > 0.01) &
                # (dataframe['fisher_rsi'] < -0.5) &
                # (dataframe['angle'] > 0.1) &
                # (dataframe['angle'] < -0.1) &
                (dataframe['rsi'] < 46)&
                # (dataframe['rsi'] > dataframe['rsi'].shift(1))&
                # (qtpylib.crossed_above(dataframe['ema9'], dataframe['ema21'])) &
                # (dataframe['low'] > dataframe['ema200']) &  # Candle low is above EMA
                # Ensure this candle had volume (important for backtesting)
                (dataframe['ma99'] / dataframe['high'] > 1.03) 
                # (dataframe['volume'] > 0) # Make sure Volume is not 0

            ),
            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                # (dataframe['resample_10_rsi'] < dataframe['resample_15_rsi'])&
                (dataframe['rsi'] > 73) # Make sure Volume is not 0
            ),
            'sell'] = 1
        return dataframe
    