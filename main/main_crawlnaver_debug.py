import sys
import common.connector_db as db
from crawl.jazzstock_core_realtime import JazzstockCoreRealtimeNaver

# 실행부, 자세한 로직은 JazzstockCrawlCoreSlaveNaver를 참조

if __name__=='__main__':

    if len(sys.argv) > 1:
        stockcode_list = sys.argv[1:]

    else:
        stockcode_list = ['093320']
        # stockcode_list = db.selectSingleColumn("SELECT STOCKCODE "
        #                                 "FROM jazzdb.T_STOCK_SND_ANALYSIS_RESULT_TEMP "
        #                                 "JOIN jazzdb.T_DATE_INDEXED USING (DATE) "
        #                                 "JOIN jazzdb.T_STOCK_MC USING(STOCKCODE, DATE) "
        #                                 "WHERE 1=1 "
        #                                 "AND CNT=0 "
        #                                 "AND MC > 1 "
        #                                 "ORDER BY YG5 "
        #                                 "LIMIT 100 ")
        # stockcode_list = db.selectSingleColumn('SELECT STOCKCODE FROM jazzdb.T_UNIVERSE_LIST WHERE DATE = "2020-04-28" LIMIT 40')



    the_date_index = 0
    the_date = db.selectSingleValue('SELECT CAST(DATE AS CHAR) AS DATE FROM jazzdb.T_DATE_INDEXED WHERE CNT = %s'%(the_date_index)).replace('-','')

    print(the_date)

    m = JazzstockCoreRealtimeNaver(stockcode_list = stockcode_list, the_date=the_date, the_date_index=the_date_index)
    m.debug()
