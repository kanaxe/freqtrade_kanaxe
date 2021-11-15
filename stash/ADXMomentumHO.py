# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy import IntParameter, DecimalParameter
from pandas import DataFrame
import talib.abstract as ta


# --------------------------------


class ADXMomentumHO(IStrategy):
    """
    author@: Gert Wohlgemuth
    converted from:
        https://github.com/sthewissen/Mynt/blob/master/src/Mynt.Core/Strategies/AdxMomentum.cs
    """

    # Minimal ROI designed for the strategy.
    # adjust based on market conditions. We would recommend to keep it low for quick turn arounds
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.592,
        "162": 0.184,
        "324": 0.052,
        "1757": 0
    }

    buy_params = {
        "buy_adx_limit": 35.697,
        "buy_mom_limit": 1.718,
        "buy_plus_di_limit": 44.925,
    }

    sell_params = {
        "sell_adx_limit": 25,
        "sell_minus_di_limit": 31,
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.25

    # Optimal timeframe for the strategy
    timeframe = '1h'

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 20

    buy_adx_limit = DecimalParameter(0, 40, default=25, space='buy', optimize=True, load=True)
    buy_plus_di_limit = DecimalParameter(10, 50, default=25, space='buy', optimize=True, load=True)
    buy_mom_limit = DecimalParameter(-10, 5, default=0, space='buy', optimize=True, load=True)
    sell_adx_limit = DecimalParameter(10, 40, default=25, space='sell', optimize=True, load=True)
    sell_minus_di_limit = DecimalParameter(10, 40, default=25, space='sell', optimize=True, load=True)
    sell_mom_limit = DecimalParameter(-10, 15, default=0, space='sell', optimize=True, load=True)
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['plus_di'] = ta.PLUS_DI(dataframe, timeperiod=25)
        dataframe['minus_di'] = ta.MINUS_DI(dataframe, timeperiod=25)
        dataframe['sar'] = ta.SAR(dataframe)
        dataframe['mom'] = ta.MOM(dataframe, timeperiod=14)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe['adx'] > self.buy_adx_limit.value) &
                    (dataframe['mom'] > self.buy_mom_limit.value) &
                    (dataframe['plus_di'] > self.buy_plus_di_limit.value) &
                    (dataframe['plus_di'] > dataframe['minus_di'])

            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe['adx'] > self.sell_adx_limit.value) &
                    (dataframe['mom'] < self.sell_mom_limit.value) &
                    (dataframe['minus_di'] > self.sell_minus_di_limit.value) &
                    (dataframe['plus_di'] < dataframe['minus_di'])

            ),
            'sell'] = 1
        return dataframe