# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

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




class Macddema(IStrategy):

    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 2

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    # ROI table:
    # ROI table:
    minimal_roi = {

        "0": 0.004,
        "22": 0
    }

    # Stoploss:
    stoploss = -0.00854

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.002044
    trailing_stop_positive_offset = 0.05934
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


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # study("MACD DEMA",shorttitle='MACD DEMA')
        # //by ToFFF
        # sma = input(12,title='DEMA Courte')
        sma=12
        # lma = input(26,title='DEMA Longue')
        lma=24
        # tsp = input(9,title='Signal')
        tsp=9
        # dolignes = input(true,title="Lignes")

        # MMEslowa = ema(close,lma)
        dataframe['MMEslowa']=ta.EMA(dataframe['close'], lma)
        # MMEslowb = ema(MMEslowa,lma)
        dataframe['MMEslowb']=ta.EMA(dataframe['MMEslowa'], lma)

        # DEMAslow = ((2 * MMEslowa) - MMEslowb )
        dataframe['DEMAslow']= ((2 * dataframe['MMEslowa']) - dataframe['MMEslowb'] )

        # MMEfasta = ema(close,sma)
        dataframe['MMEfasta']= ta.EMA(dataframe['close'], sma)
        # MMEfastb = ema(MMEfasta,sma)
        dataframe['MMEfastb']= ta.EMA(dataframe['MMEfasta'], sma)

        # DEMAfast = ((2 * MMEfasta) - MMEfastb)
        dataframe['DEMAfast']= ((2 * dataframe['MMEfasta']) - dataframe['MMEfastb'] )

        # LigneMACDZeroLag = (DEMAfast - DEMAslow)
        dataframe['LigneMACDZeroLag'] = (dataframe['DEMAfast'] -dataframe['DEMAslow'])
        # MMEsignala = ema(LigneMACDZeroLag, tsp)
        dataframe['MMEsignala']= ta.EMA(dataframe['LigneMACDZeroLag'], tsp)
        # MMEsignalb = ema(MMEsignala, tsp)
        dataframe['MMEsignalb']= ta.EMA(dataframe['MMEsignala'], tsp)

        # Lignesignal = ((2 * MMEsignala) - MMEsignalb )
        dataframe['Lignesignal']= ((2 * dataframe['MMEsignala']) - dataframe['MMEsignalb'] )
        # MACDZeroLag = (LigneMACDZeroLag - Lignesignal)
        dataframe['MACDZeroLag'] = (dataframe['LigneMACDZeroLag'] - dataframe['Lignesignal'])
        # swap1 = MACDZeroLag>0?green:red
    
        # plot(MACDZeroLag,color=swap1,style=columns,title='Histo',histbase=0)
        # p1 = plot(dolignes?LigneMACDZeroLag:na,color=blue,title='LigneMACD')
        # p2 = plot(dolignes?Lignesignal:na,color=red,title='Signal')
        # fill(p1, p2, color=blue)
        # hline(0)
        dataframe['sma20']=ta.SMA(dataframe['close'], timeperiod=60)
        dataframe['ema20']=ta.EMA(dataframe['close'], timeperiod=60)
        dataframe['tema'] = ta.TEMA(dataframe, timeperiod=80)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
      

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
                # (dataframe['tema'] < dataframe['sma20'])&
                (qtpylib.crossed_above(dataframe['ema20'], dataframe['sma20'])) 
                # (qtpylib.crossed_above(dataframe['LigneMACDZeroLag'],0))#&
                # (dataframe['rsi'] < 34)  # Make sure Volume is not 0
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
                (qtpylib.crossed_below(dataframe['LigneMACDZeroLag'],0)) # Make sure Volume is not 0
            ),
            'sell'] = 0
        return dataframe
    