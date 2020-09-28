import execjs
from urllib import parse

url2 = 'http://www.95598.cn/95598/outageNotice/queryOutageNoticeListInit'
with open("crack.js", encoding="utf-8") as f:
    ctx = execjs.get(execjs.runtime_names.Node).compile(f.read())

mm = ctx.call("get_MmEwMD", parse.urlparse(url2).path)
params = {"MmEwMD": mm}
print(mm)