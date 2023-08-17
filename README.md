# a_trade_calendar

一款纯粹的交易日历工具包，适用于A股

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
```
# 1、获取最新交易日日期
import a_trade_calendar
latest_trade_dt = a_trade_calendar.get_latest_trade_date()

print(latest_trade_dt)


```