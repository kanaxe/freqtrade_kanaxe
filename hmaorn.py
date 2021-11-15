# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

# --- Do not remove these libs ---
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


class HmaOrn(IStrategy):
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
    # ROI table:
    minimal_roi = {
        "0": 0.03148,
        "62": 0.02599,
        "121": 0.01904,
        "135": 0
    }

    # Stoploss:
    stoploss = -0.08

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.00249
    trailing_stop_positive_offset = 0.01195
    trailing_only_offset_is_reached = True




    # Optimal timeframe for the strategy.
    timeframe = '5m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = True
    sell_profit_only = True
    ignore_roi_if_buy_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: False

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
    
    plot_config = {
  "main_plot": {

  },
  "subplots": {
    "RSI": {
      "rsi": {
        "color": "red"
      }
    },
    "hlow": {
      "h-low": {
        "color": "#2de7cc",
        "type": "line"
      }
    },
    "htsine": {
      "htsine": {
        "color": "#688669",
        "type": "line"
      }
    }
  }
}
    #  # Hyperoptable parameters
    # buy_rsi = IntParameter(low=1, high=30, default=30, space='buy', optimize=True, load=True)
    # sell_rsi = IntParameter(low=35, high=100, default=40, space='sell', optimize=True, load=True)

    use_custom_sell = False
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
        dataframe['hma19'] = qtpylib.hma(dataframe['close'], 19)
        dataframe['hma8'] = qtpylib.hma(dataframe['hl2'], 8)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=7)
        dataframe['cci'] = (ta.CCI(dataframe, timeperiod=7)/2)
        dataframe['sma90'] = ta.SMA(dataframe, timeperiod=90)
        dataframe['tema80'] = ta.TEMA(dataframe, timeperiod=80)
        dataframe['s_t9080'] = dataframe['sma90'] / dataframe['tema80']


        return dataframe
    
    # def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
    #                     current_rate: float, current_profit: float, **kwargs) -> float:

    #     # evaluate highest to lowest, so that highest possible stop is used
    #     if current_profit > 0.021:
    #         return stoploss_from_open(0.02, current_profit)
    #     elif current_profit > 0.011:
    #         return stoploss_from_open(0.01, current_profit)
    #     elif current_profit > 0.003:
    #         return stoploss_from_open(0.002, current_profit)

    #     # return maximum stoploss value, keeping current stoploss price unchanged
    #     return 1


    # def custom_sell(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
    #   current_profit: float, **kwargs):
    #   dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
    #   last_candle = dataframe.iloc[-1].squeeze()
    #   candlem = dataframe.iloc[0].squeeze()


    #   # Above 20% profit, sell when rsi < 80
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
    #   elif current_profit > 0.002:
    #     return 1      
    #    # if candlem['hma8'] < candlem['hma16']:
    #   #   if current_profit < 0.001:
    #   #     return 1


    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
              # (dataframe['ol'] > 1.016)&
              # (dataframe['mfi'] < 22)&
              # (dataframe['fastd'] < 35)&
              # (dataframe['adx'] > 27)&
              (dataframe['rsi'] < 40)&
              # (qtpylib.crossed_above(
              #            dataframe['close'], dataframe['sar']
              #       ))
              (dataframe['s_t9080'] > 1.02) &
              (qtpylib.crossed_above(
                  dataframe['tema80'], dataframe['tema80'].shift(1)
                    ))
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

              (dataframe['fastd'] > 98)


             ),
            'sell'] =1
        return dataframe

    