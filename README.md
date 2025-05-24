## [hackernewsbot](https://github.com/qwtoe/hackernewsbot)

将 HackerNews  ask 板块中的新闻标题以及链接发送到 telegram 机器人。

 ![](https://moonpic.oss-cn-beijing.aliyuncs.com/img/20250524235810.png)

### 获取 Telegram 机器人令牌和聊天 ID

#### 创建 Telegram 机器人（BOT_TOKEN）

要创建一个 Telegram 机器人，您需要通过 Telegram 的官方机器人管理账户 BotFather 进行注册：


1. 打开 Telegram 应用，搜索 [BotFather](https://t.me/BotFather)（确保是官方账户，带有蓝色勾选标记）。
2. 点击“开始”或发送 /start。
3. 发送 /newbot 命令。
4. BotFather 会提示您输入机器人名称（例如 “Hacker News Ask Bot”）和用户名（必须以 “Bot” 结尾，例如 @HackerNewsAskBot）。
5. 如果用户名可用，BotFather 将返回一个 API 令牌（格式如 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11）。

#### 获取 Telegram 聊天 ID（CHAT_ID）

机器人需要知道向哪个 Telegram 账户发送消息，这需要您的聊天 ID：


1. 在 Telegram 中搜索 [@myidbot](https://t.me/myidbot)。（注意myidbot仿冒账号）
2. 点击“开始”或发送 /start。
3. 发送 /getid 命令，机器人将返回您的聊天 ID（一个数字，如 123456789）。

### 代理

因为访问 hackernews 需要代理，默认 clash 的 7890 端口。测试代理是否能够访问 hackernews：

```bash
curl --proxy http://127.0.0.1:7890 https://hacker-news.firebaseio.com/v0/askstories.json

# 返回下面内容表示成功
[44081418,44079303,44069690,44012549,44050009,44077040,44051755,44071908,44065091,44080679,44053119,44006381,44073573,44062543,44060282,44043885,44050863,44049365,44049581,44068504,44077159,44077226,44044909,44048101,44076083,44065351,44063967,44057239,44075038,44035397,44038591,44053034,44078006,44011645,44077845,44028106]
```

### systemd Timer

systemd 是 Ubuntu 的默认初始化系统，提供定时任务功能（systemd.timer)。

1、创建 systemd 服务文件

1）创建 /etc/systemd/system/hn-bot.service

```bash
sudo vim /etc/systemd/system/hn-bot.service
```

2）添加以下内容

```bash
[Unit]
Description=Hacker News Ask Bot Service
After=network.target

[Service]
Type=oneshot
ExecStart=/data/venv/bin/python /data/test.py
WorkingDirectory=/data
Environment="PYTHONUNBUFFERED=1"
```

* ExecStart：指定虚拟环境的 Python 运行脚本。
* WorkingDirectory：设置工作目录。
* Type=oneshot：任务运行一次后退出，适合脚本。


2、创建 systemd 定时器文件：

1）创建 /etc/systemd/system/hn-bot.timer

```bash
sudo vim /etc/systemd/system/hn-bot.timer
```

2）添加以下内容

```bash
[Unit]
Description=Hacker News Ask Bot Timer

[Timer]
OnCalendar=*-*-* 08:00:00 Asia/Hong_Kong
OnCalendar=*-*-* 12:00:00 Asia/Hong_Kong
OnCalendar=*-*-* 18:00:00 Asia/Hong_Kong
OnCalendar=*-*-* 22:00:00 Asia/Hong_Kong
Unit=hn-bot.service
Persistent=true

[Install]
WantedBy=timers.target
```

* OnCalendar：指定每天 8:00、12:00、18:00、22:00（HKT）运行。
* Persistent=true：如果系统在调度时间离线，启动后补跑任务。
* Unit：关联服务文件。


3、启动定时器

```bash
sudo systemctl enable hn-bot.timer
sudo systemctl start hn-bot.timer
```


4、验证定时器

```bash
# 查看定时器状态
systemctl status hn-bot.timer

# 查看下次运行时间
systemctl list-timers

# 查看任务日志
journalctl -u hn-bot.service # 输出包含脚本的 print 语句（如 消息发送成功）和错误。
```


5、测试立即运行脚本

```bash
sudo systemctl start hn-bot.service
```

查看机器人是否收到消息。


6、调试

```bash
# 1.如果运行失败，检查日志
journalctl -u hn-bot.service -b

# 2.确保代理（127.0.0.1:7890）运行
curl --proxy http://127.0.0.1:7890 https://hacker-news.firebaseio.com/v0/askstories.json
```


7、管理定时器

1）修改时间，编辑 `/etc/systemd/system/hn-bot.timer`，然后运行

```bash
sudo systemctl daemon-reload
sudo systemctl restart hn-bot.timer
```

2）日志查看：`journalctl -u hn-bot.service` 提供详细输出，无需手动配置日志文件。
3）停止/禁用：`sudo systemctl stop hn-bot.timer` 或 `sudo systemctl disable hn-bot.timer`。