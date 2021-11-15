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


class hmadown(IStrategy):
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

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    # ROI table:
    minimal_roi = {
        "0": 0.02,
        "25": 0.03,
        "47": 0.02,
        "145": 0
    }

    # Stoploss:
    stoploss = -0.03

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.03
    trailing_stop_positive_offset = 0.06
    trailing_only_offset_is_reached = False


    #     # ROI table:
    # minimal_roi = {
    #     "0": 0.091,
    #     "36": 0.069,
    #     "52": 0.038,
    #     "75": 0
    # }

    # # Stoploss:
    # # stoploss = -0.345
    # stoploss = -0.345

    # # Trailing stop:
    # trailing_stop = True
    # trailing_stop_positive = 0.162
    # trailing_stop_positive_offset = 0.232
    # trailing_only_offset_is_reached = True



    # Optimal timeframe for the strategy.
    timeframe = '5m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the "ask_strategy" section in the config.
    # use_sell_signal = True
    # sell_profit_only = True
    # ignore_roi_if_buy_signal = False

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

    # use_custom_sell = True
    # use_custom_stoploss = True


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
        """
        This method can also be loaded from the strategy, if it doesn't exist in the hyperopt class.
        """
        dataframe['adx'] = ta.ADX(dataframe)
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['mfi'] = ta.MFI(dataframe)
        stoch_fast = ta.STOCHF(dataframe)
        dataframe['fastd'] = stoch_fast['fastd']
        dataframe['fastk'] = stoch_fast['fastk']
        stoch_rfast = ta.STOCHRSI(dataframe, timeperiod=7)
        dataframe['rfastd'] = stoch_rfast['fastd']
        dataframe['rfastk'] = stoch_rfast['fastk']
        dataframe['plus_di'] = ta.PLUS_DI(dataframe, timeperiod=5)
        dataframe['minus_di'] = ta.MINUS_DI(dataframe)
        # Bollinger bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe['sar'] = ta.SAR(dataframe)
        dataframe['ohlc4']=(dataframe['open'] + dataframe['high'] + dataframe['low'] + dataframe['close']) / 4
        dataframe['hlc3']=(dataframe['high'] + dataframe['low'] + dataframe['close']) / 3
        dataframe['hl2']=(dataframe['high'] + dataframe['low'] ) / 2
        dataframe['ho']=dataframe['high'] / dataframe['open']
        dataframe['hl']=dataframe['high'] / dataframe['low']
        dataframe['ol']=dataframe['open'] / dataframe['low']
        dataframe['oc']=dataframe['open'] / dataframe['close']
        dataframe['hma310'] = qtpylib.hma(dataframe['close'], 310)
        dataframe['hma120'] = qtpylib.hma(dataframe['close'], 120)
        dataframe['hma61'] = qtpylib.hma(dataframe['close'], 61)
        dataframe['hma19'] = qtpylib.hma(dataframe['close'], 19)
        dataframe['hma8'] = qtpylib.hma(dataframe['hl2'], 8)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=7)
        dataframe['cci'] = (ta.CCI(dataframe, timeperiod=7)/2)
        dataframe['sma71'] = ta.SMA(dataframe, timeperiod=71)
        dataframe['tema230'] = ta.TEMA(dataframe, timeperiod=230)
        dataframe['hma81'] = qtpylib.hma(dataframe['close'], 81)

        Percent = 1
        # changeLONGSHORT = 1

        dataframe['upsignal']=dataframe['close']+(dataframe['close']*Percent/100)
        dataframe['downsignal']=dataframe['close']-(dataframe['close']*Percent/100)
        return dataframe
    
    # def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
    #                     current_rate: float, current_profit: float, **kwargs) -> float:

    #     # evaluate highest to lowest, so that highest possible stop is used
    #     if current_profit > 0.091:
    #         return stoploss_from_open(0.01, current_profit)
    #     elif current_profit > 0.071:
    #         return stoploss_from_open(0.01, current_profit)
    #     elif current_profit > 0.05:
    #         return stoploss_from_open(0.01, current_profit)
    #     elif current_profit > 0.02:
    #         return stoploss_from_open(0.01, current_profit)

        # # return maximum stoploss value, keeping current stoploss price unchanged
        # return 1


    # def custom_sell(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
    #   current_profit: float, **kwargs):
    #   dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
    #   last_candle = dataframe.iloc[-1].squeeze()
    #   candlem = dataframe.iloc[0].squeeze()


    #   # # Above 20% profit, sell when rsi < 80
    #   # if current_profit > 0.2:
    #   #     if last_candle['rsi'] < 60:
    #   #         return 'rsi_below_60'

    #   # Between 2% and 10%, sell if EMA-long above EMA-short
    #   # if candlem['close'] < candlem['open']:
    #   if current_profit > 0.031:
    #     return 1
    #   elif current_profit > 0.021:
    #     return 1  
    #   elif current_profit > 0.015:
    #     return 1        
    #   elif current_profit > 0.011:
    #     return 1      
    #   elif current_profit > 0.003:
    #     return 1      
    #   # if candlem['hma8'] < candlem['hma16']:
    #   #   if current_profit < 0.001:
    #   #     return 1


    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe.loc[
            (
            # (  
                # ((dataframe['ol'] > 1.016 ) | (dataframe['ol'] > 1.00843)) &
                (dataframe['adx'] > 13)&
                (dataframe['rsi'] < 23)&
                # (dataframe['upsignal'].shift(2) < dataframe['bb_lowerband'].shift(2))&
                (qtpylib.crossed_above(
                        dataframe['downsignal'], dataframe['bb_lowerband']
                    ))
                    # )

            #     |
                # (
                #     (qtpylib.crossed_above(
                #         dataframe['sma71'], dataframe['hma61']
                #     ))
                # )
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
            #    ( 
                (dataframe['rfastd'] > 93)&
                (dataframe['adx'] < 81)&
                (dataframe['rsi'] > 98)&
                (qtpylib.crossed_above(
                        dataframe['macdsignal'], dataframe['macd']
                    ))
                    # )
            #         |
                # (
                #     (qtpylib.crossed_above(
                #         dataframe['hma120'], dataframe['hma61']
                #     ))
                # )
             ),
            'sell'] =0
        return dataframe

    