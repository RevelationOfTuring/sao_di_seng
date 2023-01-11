from datetime import datetime
import backtrader as bt
import pandas as pd
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

    # 想了解在策略执行过程中订单的状态变化，重写notify_order方法
    # 在next方法中，通过self.buy()或self.sell()创建出订单后，每次订单状态有改变时，都会触发notify_order方法。
    def notify_order(self, order):
        # 处于Submitted和Accepted状态的订单，就是未决订单
        if order.status in [order.Submitted, order.Accepted]:
            # 订单状态 submitted/accepted，处于未决订单状态(pending order)。
            # submitted为订单需求已提交给经纪行，accepted为经纪行已接收该订单
            return
        # order还有一个Created状态，即当日收盘后要创建订单，此时的状态就是Created。等第二天开盘后，才向经纪行提交订单信息，改为Submitted

        # 订单已决，执行如下语句
        if order.status in [order.Completed]:
            if order.isbuy():  # 如果该订单是买单
                self.log(
                    f'买单执行, price {round(order.executed.price, 2)}, size {order.executed.size}, cost {round(order.executed.value, 2)}')

            elif order.issell():  # 如果该订单是卖单
                self.log(
                    f'卖单执行, price {round(order.executed.price, 2)}, size {order.executed.size}, cost {round(order.executed.value, 2)}')

        # 如果当前库存现金不足等，买单无法执行，会处于以下四种状态（此时也是已决订单）
        # 现金不足而无法挂单的状态Margin
        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            self.log('订单 Canceled/Margin/Rejected')

    # 记录交易收益情况（可省略，默认不输出结果）
    # 每当交易 trade 打开或关闭（即开仓后仓位被平掉），触发 notify_trade 方法
    def notify_trade(self, trade):

        status_names = ['Created', 'Open', 'Closed']
        self.log('trade status %s' % status_names[trade.status])
        if trade.isclosed:
            print('毛收益 %0.2f, 扣佣后收益 % 0.2f, 佣金 %.2f' %
                  (trade.pnl, trade.pnlcomm, trade.commission))

    def next(self):

        if not self.position:  # 还没有仓位
            # 当日收盘价上穿5日均线，创建买单，买入100股
            if self.data.close[
                -1] < self.move_average[-1] and self.data > self.move_average:
                self.log('创建买单')
                self.buy(size=100)  # 市价单，默认以下一根bar的开盘价成交
        # 有仓位，并且当日收盘价下破5日均线，创建卖单，卖出100股
        elif self.data.close[
            -1] > self.move_average[-1] and self.data < self.move_average:
            self.log('创建卖单')
            self.sell(size=100)  # 市价单，默认以下一根bar的开盘价成交


##########################
# 主程序开始
#########################

# 创建大脑引擎对象
cerebro = bt.Cerebro()

# 获取本脚本文件所在路径
modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
# 拼接得到数据文件全路径
datapath = os.path.join(modpath, 'data/600000qfq.csv')

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
cerebro.broker.setcommission(0.001)  # 佣金费率，千分之一
# 固定滑点，也可用cerebro.broker.set_slippage_perc()设置百分比滑点
cerebro.broker.set_slippage_fixed(0.05)  # 固定滑点，以高出目标价格0.05元买入，或低于目标价格0.05元卖出

print('初始市值: %.2f' % cerebro.broker.getvalue())
cerebro.run()  # 运行
print('最终市值: %.2f' % cerebro.broker.getvalue())
cerebro.plot()
