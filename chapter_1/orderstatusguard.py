# 当交易中存在pending order时，如何编写策略

from datetime import datetime
from datetime import timedelta
import backtrader as bt
import os.path  # 管理路径
import sys  # 发现脚本名字(in argv[0])


# 创建策略类
class SmaCross(bt.Strategy):
    # 定义参数
    params = dict(period=5  # 移动平均期数
                  )

    # 日志函数
    def log(self, txt, dt=None):
        '''日志函数'''
        dt = dt or self.datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 移动平均线指标
        self.move_average = bt.ind.MovingAverageSimple(
            self.data, period=self.params.period)

        # 用来引用未决订单（即尚未执行的订单）。这是一个标志位，如果不为None，则认为目前存在pending order
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 订单状态 submitted/accepted，处于未决订单状态。不重置
            return

        # 订单已决，执行如下语句
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('买单执行, %.2f' % order.executed.price)

            elif order.issell():
                self.log('卖单执行, %.2f' % order.executed.price)

        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            self.log('订单 Canceled/Margin/Rejected/order.Expired: %s' % order.getstatusname())

        # 重置未决订单为空，表示无未决订单了
        self.order = None

    # 记录交易收益情况（可省略，默认不输出结果）
    def notify_trade(self, trade):
        print('trade')
        if trade.isclosed:
            print('毛收益 %0.2f, 扣佣后收益 % 0.2f, 佣金 %.2f' %
                  (trade.pnl, trade.pnlcomm, trade.commission))

    def next(self):
        # 如果有未决订单，则无动作，不再生成新订单
        if self.order:
            return

        if not self.position:  # 还没有仓位
            # 当日收盘价上穿5日均线，创建买单，买入100股
            if self.data.close[-1] < self.move_average[-1] and self.data > self.move_average:
                self.log('创建买单')
                # 记录订单引用
                # 有效期7天（当前时间+7天）
                validday = self.data.datetime.datetime(0) + timedelta(days=7)
                # 创建一个限价买单（带有限期的）
                self.order = self.buy(
                    size=100,
                    exectype=bt.Order.Limit,
                    price=0.99 * self.data,  # 限价（当前bar的收盘价）
                    valid=validday  # 有效期
                )
        # 有仓位，并且当日收盘价下破5日均线，创建卖单，卖出100股
        elif self.data.close[
            -1] > self.move_average[-1] and self.data < self.move_average:
            self.log('创建卖单')
            # 记录订单引用
            self.order = self.sell(size=100)


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
    openinterest=-1,  # 无未平仓量列
    dtformat=('%Y%m%d'),  # 日期格式
    fromdate=datetime(2019, 1, 1),  # 起始日
    todate=datetime(2020, 7, 8))  # 结束日

cerebro.adddata(data)  # 将行情数据对象注入引擎
cerebro.addstrategy(SmaCross)  # 将策略注入引擎

cerebro.broker.setcash(10000.0)  # 设置初始资金
cerebro.broker.setcommission(0.001)  # 佣金费率
# 固定滑点，也可用cerebro.broker.set_slippage_perc()设置百分比滑点
cerebro.broker.set_slippage_fixed(0.05)

print('初始市值: %.2f' % cerebro.broker.getvalue())
cerebro.run()  # 运行
print('最终市值: %.2f' % cerebro.broker.getvalue())
cerebro.plot()
