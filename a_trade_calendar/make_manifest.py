# -*- coding: utf-8 -*-
"""
make_manifest.py —— 发布数据时用的辅助脚本(给你自己用,不需要打包进库)

每次你更新了 a_trade_calendar.csv 后,在放着 a_trade_calendar.csv 的目录里运行:

    python make_manifest.py a_trade_calendar.csv

它会:
  1. 读取 a_trade_calendar.csv,算出它的 md5(用来判断内容有没有变)
  2. 生成/覆盖同目录下的 manifest.json

然后你把 a_trade_calendar.csv 和 manifest.json 一起 commit + push 到 Gitee 和 GitHub 即可。
用户端的库下次检查更新时,会读到新的 manifest.json,发现 md5 变了,就自动下载新 csv。
"""

import sys
import json
import hashlib
import datetime


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "a_trade_calendar.csv"

    with open(path, "rb") as f:
        data = f.read()

    manifest = {
        # version 只是给人看的,这里用当天日期,你也可以改成自增数字
        "version": datetime.date.today().strftime("%Y.%m.%d"),
        # md5 是机器用来判断"内容有没有变"的关键字段
        "md5": hashlib.md5(data).hexdigest(),
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "size": len(data),
    }

    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("已生成 manifest.json:")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print("\n下一步:把 %s 和 manifest.json 一起提交推送到 Gitee 和 GitHub。" % path)


if __name__ == "__main__":
    main()
