# 使用说明



# 发布
## 安装依赖
python3 -m pip install --upgrade build

## 打包
python3 -m build

## 上传
twine upload dist/a_trade_calendar-xxxx.whl
如果这一步提示版本不对，那就去dist/目录，把内容全部删除再打包build，如果还有问题，升级一下twine，或者参考这个文档https://packaging.python.org/en/latest/tutorials/packaging-projects/#uploading-your-project-to-pypi

参考：
https://cloud.tencent.com/developer/article/2219745
