from object.jazzstock_object import JazzstockObject
from datetime import datetime
import copy
class JazzstockObject_Account(JazzstockObject):

    def __init__(self, stockcode, the_date, the_date_index, purchased=0, amount=0):
        super().__init__(stockcode, the_date, the_date_index)
        self.purchased = float(purchased)
        self.amount = amount
        self.profit = 0

    def simul_all_condition_iteration(self, condition_dict, cond_df):
        st = datetime.now()
        ret = []

        for cond_name, cond_ori in sorted(condition_dict.items(), key=lambda key_value: key_value[0]):
            cond = copy.deepcopy(cond_ori)
            flag = True
            for col, cond in cond.items():
                for i, each in enumerate(cond):
                    if i > 0 and isinstance(each, str):
                        cond[i] = self._getter(cond_df, each)

                cond_df = cond_df[self._operation(cond_df, col, cond[0], *cond[1:])]
                if (len(cond_df) == 0):
                    flag = False
                    break
            if ~flag and len(cond_df) > 0:
                ret.append(cond_name)

        return {"result": ret, "elapsed_time": datetime.now() - st}

    def _buy(self, row, amount, open=False):

        self.amount += amount
        if open:
            self.purchased += float(row.OPEN * amount)
        else:
            self.purchased += float(row.CLOSE * amount)
        self._record(action='B',row=row, amount=amount, profit=0)
        return float(row.CLOSE * amount)
    # 매도
    def _sell(self, row, amount):

        # 매도개수가 해당종목 보유수량보다 많으면, 해당종목 보유수량으로 치환함
        if (amount > self.amount):
            amount = self.amount

        # 매도직전 평단:

        # 이번 판매로 인한 수익금 (판매가 - 평단)
        profit = amount * row.CLOSE - (self.purchased / self.amount * amount)
        self.selled = float(row.CLOSE) * amount
        self.profit += float(profit)


        # 이번 판매로 인한 매수금액 조정
        self.purchased = float(self.purchased * (self.amount - amount) / self.amount)


        # 보유수량 조정
        self.amount = self.amount - amount
        self._record(action='S',row=row, amount=amount, profit=profit)

        return {'selled_thistime':float(row.CLOSE * amount),
                'profit_thistime':float(profit)}

    def _record(self, action, row, amount, profit=0):
        print('* ROW ', self.stockname, action, int(row.CLOSE), str(row.DATE.values), str(row.TIME.values), amount, int(profit))
        pass


    def check_status(self, row, condition_buy, should_sell_cutoff=0.05, default_purchase=100000):

        if (self.amount > 0):
            ifsell = self.shouldsell(row, should_sell_cutoff)
            ifbuy = self.shouldbuy(row, condition_buy, default_purchase=default_purchase)

            # 팔아야 한다면
            if ifsell:
                selled_result = self._sell(row, ifsell)
                return {'selled':selled_result['selled_thistime'], 'profit':selled_result['profit_thistime']}

            # 사야 한다면
            elif ifbuy:
                purchased = self._buy(row, ifbuy)
                return {'purchased': purchased}
            # 아니면
            else:
                return {}

            # 미보유시
        else:

            ifbuy = self.shouldbuy(row, condition_buy)
            if (ifbuy):
                purchased = self._buy(row, ifbuy)
                return {'purchased': purchased}
            else:
                return {}



    def shouldbuy(self, row, condition_buy=None, default_purchase=100000):

        # 지표기준 조건부 매수
        res = self.simul_all_condition_iteration(condition_buy, row)['result']
        if res:
            return default_purchase // int(row.CLOSE) + 1
        else:
            return False


    def shouldsell(self, row, cutoff):

        if int(row.CLOSE) > int((self.purchased / self.amount) * (1+cutoff)):

            if self.purchased > 100000:
                return self.amount
            else:

                return self.amount // 2


        else:
            return False
