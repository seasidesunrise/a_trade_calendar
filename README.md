# a_trade_calendar

适用于A股，一款简单、纯粹的交易日历工具包。来自[西海岸量化工作室]。

# 安装

## 全新安装

```
pip install a-trade-calendar
```

## 升级安装

```
pip install --upgrade a-trade-calendar
```

# 使用

声明：日期范围从2005.1.1期 到2025-08-15 日止。
将来日期后续会保持更新。

## 1、获取A股最新交易日日期

```
import a_trade_calendar
latest_trade_dt = a_trade_calendar.get_latest_trade_date()

print(latest_trade_dt)
```

## 2、判断某个日期是否是A股交易日

```
import a_trade_calendar
dt = '2023-09-01'
is_trade_date = a_trade_calendar.is_trade_date(dt)

print(is_trade_date)
```

## 3、获取A股前面n个交易日对应的日期

```
import a_trade_calendar
dt = '2023-09-01'
trade_date = a_trade_calendar.get_pre_trade_date(dt, 3)

print(trade_date)
```

## 4、获取A股后面n个交易日对应的日期

```
import a_trade_calendar
dt = '2023-09-01'
trade_date = a_trade_calendar.get_next_trade_date(dt, 3)

print(trade_date)
```

## 5、获取A股两个日期相隔的交易日天数

```
import a_trade_calendar

from_dt = '2023-08-21'
to_dt = '2023-09-01'

trade_days = a_trade_calendar.get_trade_days_interval(from_dt, to_dt)

print(trade_days)
```

