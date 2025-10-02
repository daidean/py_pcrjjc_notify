# pcrjjc2-workwx
pcrjjc2封装，用于对接企业微信WebHook机器人

## 食用教程

0. 安装依赖

    ```bash
    # 克隆本仓库
    git clone https://github.com/daidean/py_pcrjjc_notify.git

    # 同步依赖仓库
    cd py_pcrjjc_notify
    git submodule update --init --recursive

    # 新建环境，安装依赖库
    pip install uv
    uv sync
    ```

1. 配置参数

    ```bash
    # 编辑.env文件
    cp .env.example .env
    vim .env
    ```

    ```python
    # 将WORKWX_WEBHOOK参数替换为实际链接
    WORKWX_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

    # 填写PCR账号和密码
    PCR_USERNAME=email
    PCR_USERPASS=password

    # 若有需要，自行改写监听用户清单文件路径
    PCR_WATCH_PATH=pcr_watch_ids.json

    # 根据需要填写设备ID和类型
    Device_ID=00ABCD123456ABCD123456ABCD123456
    Device_Type='Huawei Meta X'
    ```

2. 填写待监听用户清单

    编辑 *PCR_WATCH_PATH* 参数指定的文件，例：pcr_watch_ids.json

    ```text
    [
        "游戏ID，例：1234567890000",
        "1234567890001",
        "1234567890002",
        ...
    ]
    ```

3. 运行监听脚本

    ```bash
    uv run pcr_watch.py
    ```

4. 预期效果

    ```bash
    Bot:    【PCR】竞技场击剑，启动中

    Bot:    【PCR】登录中

            【PCR】PCR登录验证：自动过码第1次尝试

            【PCR】PCR登录验证：自动过码队列中

            【PCR】当前位置：1，等待10秒

    Bot:    【PCR】PCR登录验证：自动过码成功

    Bot:    【PCR】登录中

            【PCR】登录成功
    
    Bot:    【PCR】排名变动：XXX(用户名)
            普通竞技场（ ↑ 11 ）：0 ➜ 11
            公主竞技场（ ↑ 22 ）：0 ➜ 22

            【PCR】PCR监听用户存在排名变动
    ```