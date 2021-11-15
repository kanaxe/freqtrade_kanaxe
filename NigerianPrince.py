# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame

from freqtrade.strategy import IStrategy
from freqtrade.strategy import CategoricalParameter, DecimalParameter, IntParameter

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

from ta.trend import ADXIndicator
from tapy import Indicators

# This class is a sample. Feel free to customize it.
class NigerianPrince(IStrategy):
    """
    This is a sample strategy to inspire you.
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

    # ROI table:
    minimal_roi = {
        "0": 0.0483,
        "34": 0.02444,
        "75": 0.01393,
        "110": 0
    }

    # Stoploss:
    stoploss = -0.9

    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.01531
    trailing_stop_positive_offset = 0.04512
    trailing_only_offset_is_reached = False


    # Trailing stoploss
    # trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured



    # Hyperoptable parameters
    # buy_rsi = IntParameter(low=1, high=50, default=30, space='buy', optimize=True, load=True)
    # sell_rsi = IntParameter(low=50, high=100, default=70, space='sell', optimize=True, load=True)

    # Optimal timeframe for the strategy.
    timeframe = '5m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the "ask_strategy" section in the config.
    # use_sell_signal = True
    # sell_profit_only = False
    # ignore_roi_if_buy_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 20

    # Optional order type mapping.
    order_types = {
        'buy': 'market',
        'sell': 'market',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc'
    }

    plot_config = {
        'main_plot': {
            'tema': {},
            'sar': {'color': 'white'},
        },
        'subplots': {
            "MACD": {
                'macd': {'color': 'blue'},
                'macdsignal': {'color': 'orange'},
            },
            "RSI": {
                'rsi': {'color': 'red'},
            }
        }
    }

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
      
        #positive directional indicator
        dataframe['DI'] = ADXIndicator(dataframe['high'], dataframe['low'], dataframe['close'], 14, False).adx_pos()

        #Accelerator Oscillator
        i = Indicators(dataframe.rename(columns={"open": "Open", "high": "High", "low": "Low", "close":"Close"}))
        i.accelerator_oscillator(column_name='AC')
        dataframe['AC'] = i.df['AC']

        return dataframe


    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['DI'] <= 10) & 
                (dataframe['AC'] < 0)
            ),
            'buy'] = 1

        return dataframe


    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe.loc[
            (
                (dataframe['DI'] >= 20) 
                                
            ),
            'sell'] = 0
        return dataframe
