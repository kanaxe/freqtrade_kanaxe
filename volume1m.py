# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

# --- Do not remove these libs ---
from logging import NullHandler, fatal
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame, Series

from freqtrade.strategy import IStrategy
from freqtrade.strategy import (merge_informative_pair, CategoricalParameter, DecimalParameter, IntParameter)
from freqtrade.exchange import timeframe_to_prev_date
from datetime import datetime
from freqtrade.persistence import Trade
from freqtrade.strategy import stoploss_from_open

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from technical.indicators import indicators
from freqtrade.persistence import Trade
from datetime import datetime

class volume1m(IStrategy):
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
    # minimal_roi = {
    #     "0": 0.02106,
    #     "74": 0.01537,
    #     "123": 0.01027,
    #     "137": 0
    # }

    # # Stoploss:
    # stoploss = -0.03574

    minimal_roi = {"25": 0.011}

    stoploss = -0.015

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.006
    trailing_only_offset_is_reached = True


    
    # trailing_stop = True
    # trailing_stop_positive = 0.004




    # Optimal timeframe for the strategy.
    timeframe = '1m'
    inf_15m = '15m'  # informative tf

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the "ask_strategy" section in the config.
    # use_sell_signal = True
    # sell_profit_only = True
    # ignore_roi_if_buy_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 240

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
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, self.inf_15m) for pair in pairs]
        return informative_pairs

    def informative_15m_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        assert self.dp, "DataProvider is required for multiple timeframes."
        # Get the informative pair
        informative_15m = self.dp.get_pair_dataframe(
            pair=metadata['pair'], timeframe=self.inf_15m)

        stoch_rfast = ta.STOCHRSI(informative_15m, timeperiod=14)
        informative_15m['rfastd'] = stoch_rfast['fastd']
        informative_15m['rfastk'] = stoch_rfast['fastk']
        informative_15m['angle'] = ta.LINEARREG_ANGLE(informative_15m['close'], timeperiod=21)
        informative_15m['lr_middle'] = ta.LINEARREG(informative_15m['close'], timeperiod=25)
        informative_15m['atr'] = ta.ATR(informative_15m,timeperiod=7)
        informative_15m['lr_lower1.0'] = informative_15m['lr_middle'] - informative_15m['atr']

        informative_15m['angle']=ta.LINEARREG_ANGLE(informative_15m['close'], timeperiod=5)
        informative_15m['volumeM'] = informative_15m['volume'].rolling(40).mean()

        
        return informative_15m

    def normal_tf_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        This method can also be loaded from the strategy, if it doesn't exist in the hyperopt class.
        """
        dataframe['adx'] = ta.ADX(dataframe)
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=21)
        dataframe['mfi'] = ta.MFI(dataframe)
        stoch_fast = ta.STOCHF(dataframe,  timeperiod=31)
        dataframe['fastd'] = stoch_fast['fastd']
        dataframe['fastk'] = stoch_fast['fastk']
        stoch_rfast = ta.STOCHRSI(dataframe, timeperiod=30)
        dataframe['rfastd'] = stoch_rfast['fastd']
        dataframe['rfastk'] = stoch_rfast['fastk']
        dataframe['minus_di'] = ta.MINUS_DI(dataframe, timeperiod=5)
        dataframe['plus_di'] = ta.PLUS_DI(dataframe, timeperiod=5)
        # Bollinger bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe['sar'] = ta.SAR(dataframe)
        dataframe['ohlc4']=(dataframe['open'] + dataframe['high'] + dataframe['low'] + dataframe['close']) / 4
        dataframe['hlc3']=(dataframe['high'] + dataframe['low'] + dataframe['close']) / 3
        dataframe['hl2']=(dataframe['high'] + dataframe['low'] ) / 2
        dataframe['ol']=(dataframe['open'] / dataframe['low']) - 1
        dataframe['cl']=dataframe['close'] / dataframe['low']
        dataframe['ho']=(dataframe['high'] / dataframe['open']) - 1
        dataframe['hma19'] = qtpylib.hma(dataframe['close'], 19)
        dataframe['hma8'] = qtpylib.hma(dataframe['hl2'], 8)
        dataframe['cci'] = (ta.CCI(dataframe, timeperiod=21)/2)
        dataframe['sma60']=ta.SMA(dataframe['close'], timeperiod=60)
        dataframe['vema']=ta.EMA(dataframe['volume'], timeperiod=34)
        dataframe['vwma'] = (ta.SMA(dataframe['close']*dataframe['volume'], timeperiod=9)/ta.SMA(dataframe['volume'], timeperiod=9))
        dataframe['evwma'] = (ta.EMA(dataframe['close']*dataframe['volume'], timeperiod=9)/ta.EMA(dataframe['volume'], timeperiod=9))
        dataframe['angle'] = ta.LINEARREG_ANGLE(dataframe['close'], timeperiod=9)
        dataframe['lr_middle'] = ta.LINEARREG(dataframe['close'], timeperiod=25)
        dataframe['atr'] = ta.ATR(dataframe,timeperiod=7)
        dataframe['lr_lower1.0'] = dataframe['lr_middle'] - dataframe['atr']
        dataframe['var'] = ta.VAR(dataframe['ho'], timeperiod=7)
        dataframe['tsf'] = ta.TSF(dataframe['ho'], timeperiod=7)
        dataframe['stddev'] = ta.STDDEV(dataframe['ho'], timeperiod=7)


        dataframe['shom']= ta.SMA(dataframe['ho'], timeperiod=14)
        dataframe['vshom']=(ta.SMA(dataframe['ho']*dataframe['volume']*dataframe['lr_middle'], timeperiod=14)/ta.SMA(dataframe['volume']*dataframe['lr_middle'], timeperiod=14))
        dataframe['solm']= ta.SMA(dataframe['ol'], timeperiod=14)
        dataframe['vsolm']= (ta.SMA(dataframe['ol']*dataframe['volume'], timeperiod=14)/ta.SMA(dataframe['volume'], timeperiod=14))
        dataframe['eshom']= ta.EMA(dataframe['ho'], timeperiod=14)
        dataframe['evshom']=(ta.EMA(dataframe['ho']*(dataframe['tsf'])*dataframe['volume'], timeperiod=14)/ta.SMA(dataframe['volume']*(dataframe['tsf']), timeperiod=14))
        dataframe['esolm']= ta.EMA(dataframe['ol'], timeperiod=14)
        dataframe['evsolm']= (ta.EMA(dataframe['ol']*dataframe['volume'], timeperiod=14)/ta.EMA(dataframe['volume'], timeperiod=14))
        dataframe['volumeM'] = dataframe['volume'].rolling(20).mean()

        


        Percent = 0.4
        # changeLONGSHORT = 1

        dataframe['upsignal']=(ta.EMA(dataframe['close'],timeperiod=7))+((ta.EMA(dataframe['close'],timeperiod=7))*Percent/100)
        dataframe['downsignal']=(ta.EMA(dataframe['close'],timeperiod=7))-(ta.EMA(dataframe['close'],timeperiod=7)*Percent/100)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # The indicators for the 1h informative timeframe
        informative_15m = self.informative_15m_indicators(dataframe, metadata)
        dataframe = merge_informative_pair(
            dataframe, informative_15m, self.timeframe, self.inf_15m, ffill=True)

        # The indicators for the normal (5m) timeframe
        dataframe = self.normal_tf_indicators(dataframe, metadata)

        return dataframe




    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # print(" {}  -- {}".format(dataframe['volume'], dataframe['volume'].rolling(21).mean()))
        dataframe.loc[
            (
                # (dataframe['upsignal'].shift(3) < dataframe['hma19'])&
                # (qtpylib.crossed_above(dataframe['close'] , dataframe['vwma'])) &
                # (qtpylib.crossed_below(dataframe['sar'] , dataframe['hma19']))&
                # (dataframe['ol'] > 1.015) 
                # (dataframe['ol'] > 1.0312) &
                # ((dataframe['ol'] - dataframe['cl']) > 0.0512) &
                # (dataframe['mfi'] < 20)
                # (dataframe['rfastk'] < 1)&
                # (dataframe['plus_di'] < 2.5)
                # (dataframe['adx'] < 23)&
                # (dataframe['downsignal'] < dataframe['hma19'])
                # (dataframe['minus_di'] > dataframe['mfi'])&
                # (dataframe['minus_di'] >40)&
                # (dataframe['minus_di'] <49)
                #((dataframe['adx'] - dataframe['mfi']) < 3)
                # (qtpylib.crossed_above(dataframe['minus_di'], dataframe['plus_di']))
                #  (dataframe['angle'] < -50)&
                # (qtpylib.crossed_above(dataframe['vshom'], dataframe['vsolm']))
                # ((dataframe['angle'] < -50) &
                # (qtpylib.crossed_above(dataframe['angle'], -70)))
                # |
                # ((dataframe['angle'] > 0 ) &
                # (qtpylib.crossed_above(dataframe['angle'], 15)))
                # (qtpylib.crossed_above(dataframe['close'], dataframe['lr_lower1.0']))
                # (dataframe['rfastd'] < 10)&
                # (dataframe['lr_lower1.0'] < dataframe['downsignal'])&
                # (dataframe['angle'] < -80)&
                # (qtpylib.crossed_above(dataframe['rfastd'], dataframe['atr']))
                # (dataframe['angle_1h'] < -80)&
                # (dataframe['angle'] < -80)&
                # (dataframe['macd'] <dataframe['angle'])&
                # (dataframe['rfastd'].shift(1) < 1)&
                # (qtpylib.crossed_above(dataframe['rfastd'], 1))
                # (dataframe['rfastd_1h'] < 10)&
                # (qtpylib.crossed_above(dataframe['rfastd'], dataframe['rfastd_1h']))
                # (dataframe['close'] < dataframe['bb_lowerband'])&
                # (dataframe['angle_15m'] > 0) &
                (dataframe['volume'] > 0) &
                (dataframe['close'] > dataframe['close'].shift(1)) &

                (dataframe['volumeM_15m'] <= dataframe['volume'])
                                
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
                # (dataframe['downsignal'] > dataframe['hma19'])&
                # (qtpylib.crossed_above(dataframe['close'], dataframe['hma19']))
                # (qtpylib.crossed_above(dataframe['rfastd'], 89))
                # (
                    # (dataframe['mfi'] > 70) 
                    # | 
                    # (dataframe['angle'] > 87)&
                    # (qtpylib.crossed_below(dataframe['fastd'], 95))
                    # | 
                    # (dataframe['cci'] > 130)
                    # | 
                    # ((dataframe['rfastk'] > 98) & (dataframe['minus_di'] < 25))           
                # )
                
                # (((qtpylib.crossed_above(dataframe['close'], dataframe['bb_upperband']))&
                # (dataframe['rfastd'] > 97)) 
                # | 
                # ((qtpylib.crossed_above(dataframe['rfastk'], dataframe['rfastd']))&
                # (dataframe['rfastd'] > 97))
                
                # )
                # (dataframe['angle_15m'] > 75)&
                # (dataframe['angle'] > 85)&
                (dataframe['bb_upperband'] < dataframe['close'])&
                (dataframe['rfastd_15m'].shift(1) > 99)&

                (qtpylib.crossed_below(dataframe['rfastd'], dataframe['rfastd_15m']))  



             ),
            'sell'] =1
        return dataframe

    
