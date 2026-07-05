# -*- coding: utf-8 -*-
"""
a_trade_calendar 远程更新模块
==============================

作用:让已经安装了你这个库的用户,在运行时自动从远程拉取最新的 a_trade_calendar.csv,
而不用重新 pip install 升级。

设计原则(对应你看到的那张流程图):
1. 主用 Gitee,失败自动切换到 jsDelivr(GitHub) 备份。
2. 先下载很小的 manifest.json,用里面的 md5 判断"到底有没有更新",
   有更新才下载完整的 a_trade_calendar.csv,省流量。
3. 下载的新文件写到"用户缓存目录"(比如 ~/.cache/a_trade_calendar/),
   绝不写 site-packages —— 那里通常没有写权限,而且 pip 升级会被覆盖。
4. 任何一步失败(断网、超时、校验不过)都不会抛异常搞崩用户程序,
   而是安静地回退到"缓存里的旧文件"或"随包发布的 a_trade_calendar.csv"。
5. 有节流:默认 24 小时内最多检查一次,避免每次 import/调用都联网。

你只需要做两件事:
  A) 把下面【需要你修改】区域的 URL 换成你自己的仓库地址。
  B) 把你原来"读取 a_trade_calendar.csv 的那行路径"换成 get_calendar_path() 的返回值。
"""

import os
import sys
import json
import time
import hashlib
import tempfile
import urllib.request
from pathlib import Path

try:
    # Python 3.9+ 推荐用这个方式定位包内数据文件
    from importlib.resources import files as _res_files
except Exception:
    _res_files = None


# ========================================================================
# 【需要你修改】把下面三处换成你自己的仓库信息
# ========================================================================
PACKAGE_NAME = "a_trade_calendar"     # 你的库名(用于定位缓存目录和包内文件)
DATA_FILENAME = "a_trade_calendar.csv"             # 静态数据文件名

# Gitee raw 地址格式:https://gitee.com/<用户名>/<仓库名>/raw/<分支>/<文件>
# 注意 Gitee 默认分支通常是 master,不是 main,请按实际填写。
GITEE_BASE = "https://raw.giteeusercontent.com/alex2028/a_trade_calendar_data/raw/master"

# jsDelivr(读取 GitHub 仓库)地址格式:
# https://cdn.jsdelivr.net/gh/<GitHub用户名>/<仓库名>@<分支或tag>/<文件>
JSDELIVR_BASE = "https://cdn.jsdelivr.net/gh/seasidesunrise/a_trade_calendar_data@main"
# ========================================================================


# 下载顺序:先主(Gitee),失败再备(jsDelivr)
MANIFEST_URLS = [
    GITEE_BASE + "/manifest.json",
    JSDELIVR_BASE + "/manifest.json",
]
CSV_URLS = [
    GITEE_BASE + "/" + DATA_FILENAME,
    JSDELIVR_BASE + "/" + DATA_FILENAME,
]

CHECK_INTERVAL_SECONDS = 24 * 3600   # 节流窗口:24 小时内不重复检查
HTTP_TIMEOUT = 8                     # 单次网络请求超时(秒),必须设,否则会卡死


# ------------------------------------------------------------------------
# 缓存目录相关:决定"下载的新文件存到哪儿"
# ------------------------------------------------------------------------
def _cache_dir() -> Path:
    """返回一个跨平台、可写的用户缓存目录,并确保它存在。"""
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Caches")
    else:  # Linux 及其他
        base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    d = Path(base) / PACKAGE_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cached_csv_path() -> Path:
    return _cache_dir() / DATA_FILENAME


def _local_manifest_path() -> Path:
    # 记录"我本地缓存的这份 csv 对应的是哪个 manifest"
    return _cache_dir() / "manifest.local.json"


def _stamp_path() -> Path:
    # 记录"上次检查更新的时间",用于节流
    return _cache_dir() / "last_check.txt"


# ------------------------------------------------------------------------
# 网络下载相关
# ------------------------------------------------------------------------
def _http_get(url: str, timeout: int = HTTP_TIMEOUT) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": PACKAGE_NAME + "-updater"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _http_get_with_fallback(urls):
    """按顺序尝试多个 URL,第一个成功就返回。全失败则抛出最后一个异常。"""
    last_err = None
    for url in urls:
        try:
            return _http_get(url), url
        except Exception as e:
            last_err = e
    raise last_err if last_err else RuntimeError("no url to try")


def _md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _atomic_write(path: Path, data: bytes):
    """先写临时文件再原子替换,避免下载中途断掉导致文件损坏。"""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)  # os.replace 是原子操作
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


# ------------------------------------------------------------------------
# 兜底:随包发布的 a_trade_calendar.csv(最后的保险)
# ------------------------------------------------------------------------
def _bundled_csv_path() -> Path:
    if _res_files is not None:
        try:
            return Path(str(_res_files(PACKAGE_NAME).joinpath(DATA_FILENAME)))
        except Exception:
            pass
    # 退路:相对本文件定位(updater.py 与 a_trade_calendar.csv 在同一个包目录下)
    return Path(__file__).resolve().parent / DATA_FILENAME


# ------------------------------------------------------------------------
# 节流 & 本地 manifest 读写
# ------------------------------------------------------------------------
def _should_check() -> bool:
    stamp = _stamp_path()
    if not stamp.exists():
        return True
    try:
        last = float(stamp.read_text().strip())
    except Exception:
        return True
    return (time.time() - last) >= CHECK_INTERVAL_SECONDS


def _touch_stamp():
    try:
        _stamp_path().write_text(str(time.time()))
    except Exception:
        pass


def _read_local_manifest() -> dict:
    p = _local_manifest_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _write_local_manifest(m: dict):
    try:
        _local_manifest_path().write_text(
            json.dumps(m, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass


# ------------------------------------------------------------------------
# 对外的两个主函数
# ------------------------------------------------------------------------
def update(force: bool = False, verbose: bool = False) -> bool:
    """
    检查远程是否有新版数据,有就下载到缓存目录。

    参数:
      force   : True 则忽略 24h 节流,强制检查。
      verbose : True 则打印过程日志(排错时用)。

    返回:
      True  = 本次确实下载并更新了文件
      False = 无需更新 / 已是最新 / 更新失败(都属于正常情况)
    """
    if not force and not _should_check():
        return False

    # 第 1 步:下载小小的 manifest
    try:
        raw, _ = _http_get_with_fallback(MANIFEST_URLS)
        remote = json.loads(raw.decode("utf-8"))
    except Exception as e:
        if verbose:
            print("[%s] 检查更新失败(忽略,用本地数据):%s" % (PACKAGE_NAME, e))
        _touch_stamp()
        return False

    remote_md5 = remote.get("md5", "")
    local_md5 = _read_local_manifest().get("md5", "")
    cached = _cached_csv_path()

    # 第 2 步:已是最新且缓存文件在,就不下载
    if remote_md5 and remote_md5 == local_md5 and cached.exists():
        _touch_stamp()
        if verbose:
            print("[%s] 已是最新:%s" % (PACKAGE_NAME, remote.get("version")))
        return False

    # 第 3 步:下载完整 CSV
    try:
        data, used = _http_get_with_fallback(CSV_URLS)
    except Exception as e:
        if verbose:
            print("[%s] 下载数据失败(忽略,用本地数据):%s" % (PACKAGE_NAME, e))
        _touch_stamp()
        return False

    # 第 4 步:校验完整性(manifest 里有 md5 才校验)
    if remote_md5 and _md5_bytes(data) != remote_md5:
        if verbose:
            print("[%s] md5 校验不通过,丢弃本次下载" % PACKAGE_NAME)
        _touch_stamp()
        return False

    # 第 5 步:原子写入缓存 + 记录本地 manifest
    _atomic_write(cached, data)
    _write_local_manifest(remote)
    _touch_stamp()
    if verbose:
        print("[%s] 已更新到:%s(来自 %s)" % (PACKAGE_NAME, remote.get("version"), used))
    return True


def get_calendar_path(auto_update: bool = True) -> str:
    """
    返回当前应该使用的 a_trade_calendar.csv 的绝对路径。
    优先级:缓存里的最新文件 > 随包发布的兜底文件。

    你原来读 a_trade_calendar.csv 的代码,只要把"文件路径"换成这个函数的返回值即可,例如:
        import pandas as pd
        from a_trade_calendar.updater import get_calendar_path
        df = pd.read_csv(get_calendar_path())

    用户可以用环境变量彻底关闭自动更新:
        Linux/Mac:  export A_TRADE_CALENDAR_NO_UPDATE=1
        Windows:    set A_TRADE_CALENDAR_NO_UPDATE=1
    """
    if os.environ.get("A_TRADE_CALENDAR_NO_UPDATE") == "1":
        auto_update = False

    if auto_update:
        try:
            update()  # 带节流,失败也不会抛异常
        except Exception:
            pass

    cached = _cached_csv_path()
    if cached.exists():
        return str(cached)
    return str(_bundled_csv_path())


if __name__ == "__main__":
    # 直接运行本文件可手动测试:python updater.py
    changed = update(force=True, verbose=True)
    print("本次是否更新了文件:", changed)
    print("当前使用的文件路径:", get_calendar_path(auto_update=False))
