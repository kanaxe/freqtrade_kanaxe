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


class Hma(IStrategy):
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
        "0": 0.0015,
        "10": 0.0018,
        "15": 0.0015,
        "45": 0.002,
        "65": 0
    }

    # Stoploss:
    stoploss = -0.01

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.021
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True

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
     # Hyperoptable parameters
    buy_rsi = IntParameter(low=1, high=30, default=30, space='buy', optimize=True, load=True)
    sell_rsi = IntParameter(low=35, high=100, default=40, space='sell', optimize=True, load=True)

    use_custom_sell = True
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


        # Cycle Indicator
        # ------------------------------------
        # Hilbert Transform Indicator - SineWave
        hilbert = ta.HT_SINE(dataframe)
        dataframe['htsine'] = hilbert['sine']
        dataframe['htleadsine'] = hilbert['leadsine']

        # Pattern Recognition - Bullish candlestick patterns
        # ------------------------------------
        # # Hammer: values [0, 100]
        # dataframe['CDLHAMMER'] = ta.CDLHAMMER(dataframe)
        # # Inverted Hammer: values [0, 100]
        # dataframe['CDLINVERTEDHAMMER'] = ta.CDLINVERTEDHAMMER(dataframe)
        # # Dragonfly Doji: values [0, 100]
        # dataframe['CDLDRAGONFLYDOJI'] = ta.CDLDRAGONFLYDOJI(dataframe)
        # # Piercing Line: values [0, 100]
        # dataframe['CDLPIERCING'] = ta.CDLPIERCING(dataframe) # values [0, 100]
        # # Morningstar: values [0, 100]
        # dataframe['CDLMORNINGSTAR'] = ta.CDLMORNINGSTAR(dataframe) # values [0, 100]
        # # Three White Soldiers: values [0, 100]
        # dataframe['CDL3WHITESOLDIERS'] = ta.CDL3WHITESOLDIERS(dataframe) # values [0, 100]

        # Pattern Recognition - Bearish candlestick patterns
        # ------------------------------------
        # # Hanging Man: values [0, 100]
        # dataframe['CDLHANGINGMAN'] = ta.CDLHANGINGMAN(dataframe)
        # # Shooting Star: values [0, 100]
        # dataframe['CDLSHOOTINGSTAR'] = ta.CDLSHOOTINGSTAR(dataframe)
        # # Gravestone Doji: values [0, 100]
        # dataframe['CDLGRAVESTONEDOJI'] = ta.CDLGRAVESTONEDOJI(dataframe)
        # # Dark Cloud Cover: values [0, 100]
        # dataframe['CDLDARKCLOUDCOVER'] = ta.CDLDARKCLOUDCOVER(dataframe)
        # # Evening Doji Star: values [0, 100]
        # dataframe['CDLEVENINGDOJISTAR'] = ta.CDLEVENINGDOJISTAR(dataframe)
        # # Evening Star: values [0, 100]
        # dataframe['CDLEVENINGSTAR'] = ta.CDLEVENINGSTAR(dataframe)

        # Pattern Recognition - Bullish/Bearish candlestick patterns
        # ------------------------------------
        # # Three Line Strike: values [0, -100, 100]
        # dataframe['CDL3LINESTRIKE'] = ta.CDL3LINESTRIKE(dataframe)
        # # Spinning Top: values [0, -100, 100]
        # dataframe['CDLSPINNINGTOP'] = ta.CDLSPINNINGTOP(dataframe) # values [0, -100, 100]
        # # Engulfing: values [0, -100, 100]
        # dataframe['CDLENGULFING'] = ta.CDLENGULFING(dataframe) # values [0, -100, 100]
        # # Harami: values [0, -100, 100]
        # dataframe['CDLHARAMI'] = ta.CDLHARAMI(dataframe) # values [0, -100, 100]
        # # Three Outside Up/Down: values [0, -100, 100]
        # dataframe['CDL3OUTSIDE'] = ta.CDL3OUTSIDE(dataframe) # values [0, -100, 100]
        # # Three Inside Up/Down: values [0, -100, 100]
        # dataframe['CDL3INSIDE'] = ta.CDL3INSIDE(dataframe) # values [0, -100, 100]

        # # Chart type
        # # ------------------------------------
        # # Heikin Ashi Strategy
        # heikinashi = qtpylib.heikinashi(dataframe)
        # dataframe['ha_open'] = heikinashi['open']
        # dataframe['ha_close'] = heikinashi['close']
        # dataframe['ha_high'] = heikinashi['high']
        # dataframe['ha_low'] = heikinashi['low']


        dataframe['ohlc4']=(dataframe['open'] + dataframe['high'] + dataframe['low'] + dataframe['close']) / 4
        dataframe['hlc3']=(dataframe['high'] + dataframe['low'] + dataframe['close']) / 3
        dataframe['hl2']=(dataframe['high'] + dataframe['low'] ) / 2
        dataframe['hma16'] = qtpylib.hma(dataframe['ohlc4'], 20)
        dataframe['hma8'] = qtpylib.hma(dataframe['hl2'], 8)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=30)
        # MACD
        macd = ta.MACD(dataframe, timeperod=9)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        dataframe['cci'] = ta.CCI(dataframe, timeperiod=10)
        # dataframe['h-low']= dataframe['hma20'] / dataframe['low']
        dataframe['sar'] = ta.SAR(dataframe)


        dataframe['vwap'] = Series.vwap(dataframe)
        devUD = [1.28, 2.01, 2.51, 3.09, 4.01]

        # my std dev calculation = an incrementing std dev of df.VWAP
        dataframe['DEV'] = dataframe['vwap'].expanding().std()
        # dataframe['vwup1']= dataframe['vwap'] + devUD[0] * dataframe['DEV']
        # dataframe['vwdow1']= dataframe['vwap'] - devUD[0] * dataframe['DEV']
        # dataframe['vwup2']= dataframe['vwap'] + devUD[1] * dataframe['DEV']
        # dataframe['vwdow2']= dataframe['vwap'] - devUD[1] * dataframe['DEV']

        for dev in devUD:
            up = 'vwup{}'.format(dev)
            dow = 'vwdow{}'.format(dev)
            dataframe[up]=dataframe['vwap'] + dev * dataframe['DEV']
            dataframe[dow]= dataframe['vwap'] - dev * dataframe['DEV']

        # Retrieve best bid and best ask from the orderbook
        # ------------------------------------
        """
        # first check if dataprovider is available
        if self.dp:
            if self.dp.runmode in ('live', 'dry_run'):
                ob = self.dp.orderbook(metadata['pair'], 1)
                dataframe['best_bid'] = ob['bids'][0][0]
                dataframe['best_ask'] = ob['asks'][0][0]
        """

        return dataframe
    
    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:

        # evaluate highest to lowest, so that highest possible stop is used
        if current_profit > 0.021:
            return stoploss_from_open(0.02, current_profit)
        elif current_profit > 0.011:
            return stoploss_from_open(0.01, current_profit)
        elif current_profit > 0.003:
            return stoploss_from_open(0.002, current_profit)

        # return maximum stoploss value, keeping current stoploss price unchanged
        return 1


    def custom_sell(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
      current_profit: float, **kwargs):
      dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
      last_candle = dataframe.iloc[-1].squeeze()
      candlem = dataframe.iloc[0].squeeze()


      # Above 20% profit, sell when rsi < 80
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
      elif current_profit > 0.002:
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
                # (dataframe['close'].shift(2) > dataframe['close'])&
              # (dataframe['rsi'] < 45)&
              (qtpylib.crossed_above(dataframe['close'], dataframe['hma16']))
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
                # (dataframe['open'] < dataframe['close'] ) &
                (dataframe['open'] < dataframe['close'])
                # (dataframe['rsi'] > 37 )
                
                # (qtpylib.crossed_below(dataframe['hma16'], dataframe['close']))
             ),
            'sell'] =0
        return dataframe

    