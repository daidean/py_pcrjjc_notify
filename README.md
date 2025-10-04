# 公主连结 竞技场排名通知 2.0

> 简体字服 属性版本 重构项目

## 0、安装依赖
```bash
# 克隆项目
https://github.com/daidean/py_pcrjjc_notify.git
cd py_pcrjjc_notify

# 安装UV创建环境
pip install uv
uv sync
```

## 1、配置参数
```bash
# 编辑配置文件
cp .env.example .env
vim .env
```

```python
# 将WORKWX_WEBHOOK参数替换为实际链接
WORKWX_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# 根据需要填写设备ID和类型
PCR_Device_ID=00ABCD123456ABCD123456ABCD123456
PCR_Device_Type='Huawei Meta X'

# 填写PCR账号和密码
PCR_USERNAME=email
PCR_USERPASS=password

# 填写需要监听的用户ID，以英文逗号分隔
PCR_WATCH_LIST=1234567890000,1234567890001,1234567890002,...
```

## 2、运行脚本

```bash
uv run main.py
```