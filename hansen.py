# --- Do not remove these libs ---
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy as np
# --------------------------------
import talib.abstract as ta
from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy import (merge_informative_pair, CategoricalParameter, DecimalParameter, IntParameter)
from freqtrade.exchange import timeframe_to_prev_date
from freqtrade.persistence import Trade
from datetime import datetime
from pandas import DataFrame


def bollinger_bands(stock_price, window_size, num_of_std):
    rolling_mean = stock_price.rolling(window=window_size).mean()
    rolling_std = stock_price.rolling(window=window_size).std()
    lower_band = rolling_mean - (rolling_std * num_of_std)
    return np.nan_to_num(rolling_mean), np.nan_to_num(lower_band)


class CombinedBinHAndCluc(IStrategy):
    # Based on a backtesting:
    # - the best perfomance is reached with "max_open_trades" = 2 (in average for any market),
    #   so it is better to increase "stake_amount" value rather then "max_open_trades" to get more profit
    # - if the market is constantly green(like in JAN 2018) the best performance is reached with
    #   "max_open_trades" = 2 and minimal_roi = 0.01
    minimal_roi = {
        "0": 0.01
    }
    stoploss = -0.03
    timeframe = '5m'
    inf_1h = '1h'  # informative tf

    use_sell_signal = False
    sell_profit_only = True
    ignore_roi_if_buy_signal = True

    trailing_stop = True
    trailing_stop_positive = 0.00628
    trailing_stop_positive_offset = 0.02999
    trailing_only_offset_is_reached = True

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, self.inf_1h) for pair in pairs]
        return informative_pairs

    def informative_1h_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        assert self.dp, "DataProvider is required for multiple timeframes."
        # Get the informative pair
        informative_1h = self.dp.get_pair_dataframe(
            pair=metadata['pair'], timeframe=self.inf_1h)

        stoch_rfast = ta.STOCHRSI(informative_1h, timeperiod=7)
        informative_1h['rfastd'] = stoch_rfast['fastd']
        informative_1h['rfastk'] = stoch_rfast['fastk']
        informative_1h['angle'] = ta.LINEARREG_ANGLE(informative_1h['close'], timeperiod=5)
        informative_1h['lr_middle'] = ta.LINEARREG(informative_1h['close'], timeperiod=25)
        informative_1h['atr'] = ta.ATR(informative_1h,timeperiod=7)
        informative_1h['lr_lower1.0'] = informative_1h['lr_middle'] - informative_1h['atr']

        informative_1h['angle']=ta.LINEARREG_ANGLE(informative_1h['close'], timeperiod=5)
        
        return informative_1h

    def normal_tf_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # strategy BinHV45
        mid, lower = bollinger_bands(dataframe['close'], window_size=40, num_of_std=2)
        dataframe['lower'] = lower
        dataframe['bbdelta'] = (mid - dataframe['lower']).abs()
        dataframe['closedelta'] = (dataframe['close'] - dataframe['close'].shift()).abs()
        dataframe['tail'] = (dataframe['close'] - dataframe['low']).abs()
        # strategy ClucMay72018
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=50)
        dataframe['volume_mean_slow'] = dataframe['volume'].rolling(window=30).mean()
        dataframe['angle'] = ta.LINEARREG_ANGLE(dataframe['close'], timeperiod=21)
        stoch_rfast = ta.STOCHRSI(dataframe, timeperiod=30)
        dataframe['rfastd'] = stoch_rfast['fastd']
        dataframe['rfastk'] = stoch_rfast['fastk']

        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # The indicators for the 1h informative timeframe
        informative_1h = self.informative_1h_indicators(dataframe, metadata)
        dataframe = merge_informative_pair(
            dataframe, informative_1h, self.timeframe, self.inf_1h, ffill=True)

        # The indicators for the normal (5m) timeframe
        dataframe = self.normal_tf_indicators(dataframe, metadata)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (  # strategy BinHV45
                    dataframe['lower'].shift().gt(0) &
                    dataframe['bbdelta'].gt(dataframe['close'] * 0.008) &
                    dataframe['closedelta'].gt(dataframe['close'] * 0.0175) &
                    dataframe['tail'].lt(dataframe['bbdelta'] * 0.25) &
                    dataframe['close'].lt(dataframe['lower'].shift()) &
                    dataframe['close'].le(dataframe['close'].shift())
            ) |
            (  # strategy ClucMay72018
                    (dataframe['close'] < dataframe['ema_slow']) &
                    (dataframe['close'] < 0.985 * dataframe['bb_lowerband']) &
                    (dataframe['volume'] < (dataframe['volume_mean_slow'].shift(1) * 20))
            ),
            'buy'
        ] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        """
        dataframe.loc[
                (dataframe['angle_1h'] > 75)&
                (dataframe['angle'] > 85)&
                (dataframe['rfastd'].shift(1) > 85)&

                (qtpylib.crossed_below(dataframe['rfastd'], dataframe['angle_1h'])),
            'sell'
        ] = 1
        return dataframe