import sys
import common.connector_db as db
import util.index_calculator as ic
import pandas as pd
import config.condition as cd
from datetime import datetime
from object.jazzstock_object_account import JazzstockObject_Account

pd.options.display.max_rows = 1000
pd.options.display.max_columns= 500
# =====================================================================================
# 추가구현시 CLASS, FUNCTION 네이밍 참조:
# =====================================================================================
# CLASS_*    => 클래스는 Camel 케이스를 사용한다 => CamleCase
# FUNC_*     => 함수는 Snake 케이스를           => snake_case
# FUNC_SET   => 객체에 뭔가를 입히는 함수, 아무것도 반환하지 않고, 객체에 입히기만 한다.
# FUNC_GET   => 객체에서 무언가를 꺼내오는 함수, 되도록 GET_FUNC 에서는 아무것도 출력하지 않고
#               CORE 부에서 메세지를 출력한다.
# FUNC_CAL   => 인풋에 대해서 뭔가를 계산하여 반환하는 함수
# _FUNC      => 객체내부에서만 사용되는 함수, 외부에서 호출할일 없는 함수는 _ 을 붙여주도록.
# =====================================================================================


class JazzstockCoreSimulation:
    def __init__(self, stockcode, condition_buy, the_date, the_date_index, purchased=0, amount=0, hist_purchased=0, hist_selled=0):
        '''

        :param stockcode:
        :param stockname:
        :param to:
        :param condition:
        '''

        self.obj = JazzstockObject_Account(stockcode, the_date, the_date_index, purchased, amount)
        self.obj.set_ohlc_day_from_db_include_index(cntto=the_date_index + 1, window=60)       # to + 1, 즉 시뮬레이션 전 거래일 까지의 일봉정보를 가져옴
        self.obj.set_ohlc_min_from_db(cntto=the_date_index, window=1)                          # to 거래일 까지의 5분봉을 가져옴
        self.obj.set_prev_day_index()

        self.obj.df_ohlc_realtime_filled = ic.fillindex(self.obj.df_ohlc_min)     # 5분봉에 지표들을 붙여줌

        # # 의문의 DATE타임 전처리.... 왜인지 어떤건 되고 어떤건 안됨
        # self.obj.df_ohlc_realtime_filled.DATE = self.obj.df_ohlc_realtime_filled.DATE.astype(str)

        self.obj.df_ohlc_realtime_filled = self.obj.df_ohlc_realtime_filled[self.obj.df_ohlc_realtime_filled.DATE==the_date]
        self.COLUMNS_DAY=['DATE', 'TIME', 'CLOSE', 'VSMAR20', 'BBP', 'BBW', 'K', 'D', 'J']
        self.COLUMNS_MIN = ['DATE', 'TIME', 'CLOSE', 'VSMAR20', 'BBP', 'BBW', 'K', 'D', 'J']

        self.condition_buy  = condition_buy

        self.hist_purchased= hist_purchased
        self.hist_selled = hist_selled

        # DEBUGGING ================================================
        # print(stockcode, the_date, the_date_index)
        # print(self.obj.df_ohlc_day.tail(2))
        # print(self.obj.df_ohlc_realtime_filled.tail(10))
        # DEBUGGING ================================================




class JazzstockCoreSimulationCustom(JazzstockCoreSimulation):
    def __init__(self, stockcode,
                 condition_buy,
                 the_date,
                 the_date_index,
                 purchased,
                 amount,
                 hist_purchased,
                 hist_selled,
                 cutoff=0.05,
                 market_open_buy=False,
                 market_close_sell=False,
                 default_purchase_open=1000000,
                 default_purchase=300000):
        super().__init__(stockcode, condition_buy, the_date, the_date_index, purchased, amount, hist_purchased, hist_selled)

        self.market_open_buy = market_open_buy
        self.market_close_sell = market_close_sell
        self.cutoff = cutoff
        self.default_purchase_open = default_purchase_open
        self.default_purchase = default_purchase

    def simulate(self, log_level=5):

        '''
        한바퀴 다돌림
        : param log_level   5 : END_SUMMARY
                            4 : INCLUDE
                            3 : DAILY_SUMMARY
                            3 : EACH_BUY/SELL LOG

        :return:
        '''



        purchased= 0
        selled = 0
        hist_purchased = self.hist_purchased
        hist_selled =  self.hist_selled


        for j, row in enumerate(self.obj.df_ohlc_realtime_filled.values):


            tempdf = pd.DataFrame(data=[row], columns=self.obj.df_ohlc_realtime_filled.columns)

            # 시초가매수의 경우
            if self.market_open_buy and j==0:

                amount = (self.default_purchase_open//tempdf.OPEN.values[0])+1
                res = {'purchased':self.obj._buy(tempdf, amount, open=True)}
                purchased += res['purchased']  # 당일매수

            # 장중5분봉 체크하는경우
            else:
                res = self.obj.check_status(tempdf, self.condition_buy, should_sell_cutoff=self.cutoff, default_purchase= self.default_purchase)
                if 'purchased' in res.keys():
                    purchased += res['purchased']       # 당일매수
                    # hist_purchased += res['purchased']  # 시뮬레이션 시작이후 누적매수

                elif 'selled' in res.keys():
                    selled += res['selled']             # 당일매도
                    hist_selled += res['selled']        # 시뮬레이션 시작이후 누적매도
                    hist_purchased +=  res['selled']-res['profit']

            # 종가매도의 경우
            if self.market_close_sell and j == len(self.obj.df_ohlc_realtime_filled.values)-1 and self.obj.amount !=0:

                selled_result = self.obj._sell(tempdf, self.obj.amount)
                res = {'selled': selled_result['selled_thistime'], 'profit': selled_result['profit_thistime']}
                selled += res['selled']  # 당일매도
                hist_selled += res['selled']  # 시뮬레이션 시작이후 누적매도
                hist_purchased += res['selled'] - res['profit']

        close_day = self.obj.df_ohlc_realtime_filled.CLOSE.tail(1).values[0]
        return self.obj.purchased, \
               self.obj.amount, \
               self.obj.profit, \
               hist_purchased, hist_selled, \
               close_day




        


if __name__=='__main__':
    test = JazzstockCoreSimulationCustom(stockcode = '079940',
                                         amount=0,
                                         purchased=0,
                                         the_date_index=36,
                                         the_date='2020-11-16',
                                         hist_purchased=0,
                                         hist_selled=0,
                                         condition_buy=cd.COND_TEST_A,
                                         market_open_buy=True,
                                         market_close_sell=True)
    r = test.simulate()
    print(r)