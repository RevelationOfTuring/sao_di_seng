from datetime import datetime
import backtrader as bt
import os.path  # 管理路径
import sys  # 发现脚本名字(in argv[0])


# 创建策略类
class SmaCross(bt.Strategy):
    # 定义参数
    params = dict(period=5)  # 移动平均期数

    def __init__(self):
        # 移动平均线指标
        self.move_average = bt.ind.MovingAverageSimple(
            self.datas[0].close, period=self.params.period)
        # 注：在init方法中，含线对象中的第一根线是其默认线
        # self.move_average = bt.ind.MovingAverageSimple(
        #     self.datas[0], period=self.params.period)  # 等价于上语句

        # 在定义指标时也可以直接省略self.datas[0].close（线参数），这时bt会默认取self.datas[0]中的第一条线作为输入，即上面等价于
        # self.move_average = bt.ind.MovingAverageSimple(period=self.p.period)

        # self.move_average和self.datas[0]都是一个含线对象
        print(self.move_average.lines.getlinealiases())  # ('sma',)
        print(self.datas[
                  0].lines.getlinealiases())  # ('close', 'low', 'high', 'open', 'volume', 'openinterest', 'datetime')

        self.datas[0].lines.close  # 访问线
        self.datas[0].lines[0]  # 等价于上面，self.datas[0]中有7根线，第一根就是close
        self.datas[0].close  # 等价于上面，最常用的写法

        # 在init方法中，利用圆括号生成错位的线
        self.dataearly = self.data.close(-1)  # 收盘价集体下移一天
        self.datalate = self.data.close(1)  # 收盘价集体上移一天

    def next(self):

        if not self.position.size:  # 还没有仓位
            # 当日收盘价上穿5日均线，创建买单，买入100股
            if self.datas[0].close[-1] < self.move_average.sma[-1] and \
                    self.datas[0].close[0] > self.move_average.sma[0]:
                self.buy(size=100)
        # 有仓位，并且当日收盘价下破5日均线，创建卖单，卖出100股
        elif self.datas[0].close[-1] > self.move_average.sma[-1] and \
                self.datas[0].close[0] < self.move_average.sma[0]:
            self.sell(size=100)

        # 注：在next方法中，self.datas[0].close是self.datas[0].close[0]的简写形式，即next方法中线对象默认为该对象的当前值
        # 在next方法中，含线对象可以当做是其默认线的当前值，即self.datas[0]也是self.datas[0].close[0]的简写形式。

        print(f'该bar是第几根bar：{len(self)}')
        print(f'当前data线长：{len(self.datas[0])}')
        print(f'总data线长：{self.datas[0].buflen()}')

        # 得到线的一个切片
        # 获取上一根bar开始，向前10个的open值
        my_slice = self.datas[0].open.get(ago=-1, size=3)  # 改写法只能在next()中
        print(my_slice)

        # 其他一些简写方法
        print(self.datas[0].close[0])
        print(self.data0_close[0])  # 线对象self.datas[X].name 等价于 self.dataX_name


##########################
# 主程序开始
#########################

# 创建大脑引擎对象
cerebro = bt.Cerebro()

# 获取本脚本文件所在路径
modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
# 拼接得到数据文件全路径
datapath = os.path.join(modpath, '../data/600000qfq.csv')

# 创建行情数据对象，加载数据
data = bt.feeds.GenericCSVData(
    dataname=datapath,
    datetime=2,  # 日期行所在列
    open=3,  # 开盘价所在列
    high=4,  # 最高价所在列
    low=5,  # 最低价所在列
    close=6,  # 收盘价价所在列
    volume=10,  # 成交量所在列
    openinterest=-1,  # 无未平仓量列.(openinterest是期货交易使用的)
    dtformat=('%Y%m%d'),  # 日期格式
    fromdate=datetime(2019, 1, 1),  # 起始日
    todate=datetime(2020, 7, 8))  # 结束日

cerebro.adddata(data)  # 将行情数据对象注入引擎
cerebro.addstrategy(SmaCross)  # 将策略注入引擎
cerebro.broker.setcash(10000.0)  # 设置初始资金

cerebro.run()  # 运行

print('最终市值: %.2f' % cerebro.broker.getvalue())
# 若绘图出错，很可能是matplotlib版本不兼容，要降级到3.2.2，可运行如下命令降级：
# pip uninstall matplotlib
# pip install matplotlib==3.2.2
cerebro.plot(style='bar')
