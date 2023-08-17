"""
 
:Author:  逍遥游
:Create:  2023/8/13$ 19:27$
"""
import os
import time

import pandas as pd

_current_directory = os.path.dirname(__file__)
print("当前文件的目录：", _current_directory)

_a_trade_cal_df = pd.read_csv(f'{_current_directory}/a_trade_calendar.csv')
print(len(_a_trade_cal_df))


def _get_curr_date():
    """ 返回当前日期（固定格式）"""
    return time.strftime("%Y-%m-%d", time.localtime())


def _fmt_dtime2str(trade_date):
    """ 将日期变量转为可用字符串，如'2021-12-30' """
    return str(trade_date)[:10]


def is_trade_date(dtime):
    """ 判断dtime是否是交易日 """
    days = _a_trade_cal_df[_a_trade_cal_df['dt'] == dtime]
    return len(days) >= 1


def get_latest_trade_date():
    dtime = _get_curr_date()
    days_df = _a_trade_cal_df[_a_trade_cal_df['dt'] <= dtime]

    latest_trade_date = days_df.iloc[-1]['dt']
    return _fmt_dtime2str(latest_trade_date)


def get_pre_trade_date(dtime, cnt=1):
    """ 获取前面cnt个交易日的日期 """
    if cnt <= 0:
        print(f"非法的参数 cnt: {cnt}, 必须大于0")
        return None

    days_df = _a_trade_cal_df[_a_trade_cal_df['dt'] < dtime]

    latest_trade_date = days_df.iloc[-cnt]['dt']
    return _fmt_dtime2str(latest_trade_date)


def get_next_trade_date(dtime, cnt=1):
    """ 获取后面cnt个交易日的日期 """
    if cnt <= 0:
        print(f"非法的参数 cnt: {cnt}, 必须大于0")
        return None
    days_df = _a_trade_cal_df[_a_trade_cal_df['dt'] > dtime]

    if len(days_df) >= cnt:
        return _fmt_dtime2str(days_df.iloc[cnt - 1]['dt'])
    else:
        return None


def get_trade_days_interval(from_dt, to_dt) -> int:
    """ 获取两个日期相隔的交易日天数 """
    days_df = _a_trade_cal_df[(_a_trade_cal_df['dt'] > from_dt) & (_a_trade_cal_df['dt'] < to_dt)]

    cnt = len(days_df)
    if cnt > 0:
        return cnt
    else:
        return 0
