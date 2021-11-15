# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
import logging
from pandas import DataFrame

from freqtrade.strategy import IStrategy
from freqtrade.strategy import CategoricalParameter, DecimalParameter, IntParameter

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from technical.indicators import ichimoku

logger = logging.getLogger(__name__)
class Ichi(IStrategy):

    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 2

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "0": 0.1
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".

        # Optimal timeframe for the strategy.
    timeframe = '5m'
    stoploss = -0.22

    trailing_stop = True
    trailing_stop_positive = 0.08
    trailing_stop_positive_offset = 0.20
    trailing_only_offset_is_reached = True



    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ichi=ichimoku(dataframe)
        dataframe['tenkan']=ichi['tenkan_sen']
        dataframe['kijun']=ichi['kijun_sen']
        dataframe['senkou_a']=ichi['senkou_span_a']
        dataframe['senkou_b']=ichi['senkou_span_b']
        dataframe['cloud_green']=ichi['cloud_green']
        dataframe['cloud_red']=ichi['cloud_red']
        dataframe['angle'] = ta.LINEARREG_ANGLE(dataframe['close'], timeperiod=5)
            # RSI
        dataframe['rsi'] = ta.RSI(dataframe,timeperiod=30)


            # # Inverse Fisher transform on RSI: values [-1.0, 1.0] (https://goo.gl/2JGGoy)
            # rsi = 0.1 * (dataframe['rsi'] - 50)
            # dataframe['fisher_rsi'] = (np.exp(2 * rsi) - 1) / (np.exp(2 * rsi) + 1)

            # # Inverse Fisher transform on RSI normaSlized: values [0.0, 100.0] (https://goo.gl/2JGGoy)
            # dataframe['fisher_rsi_norma'] = 50 * (dataframe['fisher_rsi'] + 1)

        # print(dataframe.columns.values)
        

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
                (dataframe['tenkan'].shift(1)<dataframe['kijun'].shift(1)) &
                (dataframe['tenkan']>dataframe['kijun']) &
                (dataframe['cloud_red']==True)
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
                # (dataframe['rsi'] > 69) # Make sure Volume is not 0
            ),
            'sell'] = 1
        return dataframe
    