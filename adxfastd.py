# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

# --- Do not remove these libs ---
from logging import fatal
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame, Series

from freqtrade.strategy import IStrategy
from freqtrade.strategy import CategoricalParameter, DecimalParameter, IntParameter
from freqtrade.exchange import timeframe_to_prev_date
from datetime import datetime
from freqtrade.persistence import Trade
from freqtrade.strategy import stoploss_from_open

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from technical.indicators import indicators


class AdxFd(IStrategy):
    """
    This is a strategy template to get you started.
    More information in https://www.freqtrade.io/en/latest/strategy-customization/

    You can:
        :return: a Dataframe with all mandatory indicators for the strategies
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the methods: populate_indicators, populate_buy_trend, populate_sell_trend
    You should keep:
    - timeframe, minimal_roi, stoploss, trailing_*
    """
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 2



    # ROI table: 1.01659
    minimal_roi = {
        "0": 0.018,
        "20": 0.013,
        "40": 0.008,
        "60": 0
    }

    # Stoploss:
    stoploss = -0.015

    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.006
    trailing_only_offset_is_reached = False


    # Optimal timeframe for the strategy.
    timeframe = '5m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

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


     # Hyperoptable parameters
    # buy_rsi = IntParameter(low=1, high=30, default=30, space='buy', optimize=True, load=True)
    # sell_rsi = IntParameter(low=35, high=100, default=40, space='sell', optimize=True, load=True)

    use_custom_sell = True
    use_custom_stoploss = False


    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe['adx'] = ta.ADX(dataframe)
        stoch_fast = ta.STOCHF(dataframe)
        dataframe['fastd'] = stoch_fast['fastd']
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=20)
        dataframe['sar'] = ta.SAR(dataframe)
        dataframe['mfi'] = ta.MFI(dataframe)


        return dataframe
    
    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:

        # evaluate highest to lowest, so that highest possible stop is used
        if current_profit > 0.021:
            return stoploss_from_open(0.02, current_profit)
        elif current_profit > 0.011:
            return stoploss_from_open(0.01, current_profit)
        elif current_profit > 0.005:
            return stoploss_from_open(0.004, current_profit)

        # return maximum stoploss value, keeping current stoploss price unchanged
        return 1


    def custom_sell(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
      current_profit: float, **kwargs):
      dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
      last_candle = dataframe.iloc[-1].squeeze()
      candlem = dataframe.iloc[0].squeeze()


      # # Above 20% profit, sell when rsi < 80
      # if current_profit > 0.2:
      #     if last_candle['rsi'] < 60:
      #         return 'rsi_below_60'

      # Between 2% and 10%, sell if EMA-long above EMA-short
      # if candlem['close'] < candlem['open']:
      if current_profit > 0.031:
        return 1
      elif current_profit > 0.021:
        return 1  
      elif current_profit > 0.015:
        return 1        
      elif current_profit > 0.011:
        return 1   
      elif current_profit > 0.003:
        return 1      
      # if candlem['hma8'] < candlem['hma16']:
      #   if current_profit < 0.001:
      #     return 1


    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                (
                    (dataframe['adx'] < 19.6)&
                    (dataframe['mfi'] < 40)&
                    (dataframe['mfi'] > dataframe['adx'])&
                    (dataframe['fastd'] < dataframe['adx']) 
                ) 
                |
                (
                    (dataframe['adx'] > 54)&
                    (dataframe['mfi'] < 20)&
                    (dataframe['mfi'] < dataframe['fastd'])&
                    (dataframe['fastd'] < dataframe['adx'])
                )
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
                (
                (dataframe['mfi'] > 75)&
                (dataframe['fastd'] > dataframe['mfi'])&
                ((dataframe['fastd'] - dataframe['mfi']) < 12) 
                )
                |
                (
                (dataframe['mfi'] > 70)&
                (dataframe['fastd'] > dataframe['mfi'])&
                ((dataframe['fastd'] - dataframe['mfi']) > 20)
                )
                
            ),
            'sell'] =1
        return dataframe

    