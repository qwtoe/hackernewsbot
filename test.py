import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging
import ssl
import urllib3
from urllib3.util.ssl_ import create_urllib3_context
from datetime import datetime
import pytz

# 禁用 InsecureRequestWarning（仅调试用）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logging.basicConfig(filename='hn_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 配置
BOT_TOKEN = 'YOUR_BOT_TOKEN'  # 替换为您的 Telegram 机器人令牌
CHAT_ID = 'YOUR_CHAT_ID'      # 替换为您的 Telegram 聊天 ID
PROXY = 'http://127.0.0.1:7890'  # HTTP 代理
# PROXY = 'socks5://127.0.0.1:7890'  # SOCKS5 代理，需安装 pysocks
proxies = {'http': PROXY, 'https': PROXY} if PROXY else None
VERIFY_SSL = False  # 调试用，设为 True 或证书路径（如 '/data/proxy_ca.pem'）

# 设置自定义 SSL 上下文，尝试 TLS 1.2
context = create_urllib3_context(ssl_minimum_version=ssl.TLSVersion.TLSv1_2)
urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'  # 放宽密码套件要求

# 设置请求会话和重试机制
session = requests.Session()
retry = Retry(total=3, connect=3, read=3, backoff_factor=0.5, status_forcelist=[502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retry, pool_connections=1, pool_maxsize=1))

# 自定义翻译函数
def translate_title(title, proxies, session):
    url = f"https://api.mymemory.translated.net/get?langpair=en-US|zh-CN&q={requests.utils.quote(title)}"
    try:
        response = session.get(url, proxies=proxies, timeout=30, verify=VERIFY_SSL)
        response.raise_for_status()
        return response.json()['responseData']['translatedText']
    except Exception as e:
        logging.error(f"翻译标题失败: {e}")
        print(f"翻译标题失败: {e}")
        return title  # 翻译失败时返回原文

# 获取 Hacker News Ask 故事 ID
try:
    response = session.get('https://hacker-news.firebaseio.com/v0/askstories.json', proxies=proxies, timeout=30, verify=VERIFY_SSL)
    logging.info(f"Response status code: {response.status_code}")
    logging.info(f"Response content: {response.text}")
    response.raise_for_status()  # 检查 HTTP 状态码
    story_ids = response.json()[:30]  # 取前 30 个 ID
except requests.exceptions.RequestException as e:
    logging.error(f"请求失败: {e}")
    print(f"请求失败: {e}")
    exit(1)
except requests.exceptions.JSONDecodeError as e:
    logging.error(f"JSON 解析错误: {e}, 响应内容: {response.text}")
    print(f"JSON 解析错误: {e}, 响应内容: {response.text}")
    exit(1)

# 获取标题和 URL
titles = []
urls = []
for story_id in story_ids:
    try:
        response = session.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json', proxies=proxies, timeout=30, verify=VERIFY_SSL)
        response.raise_for_status()
        story = response.json()
        title = story['title'].replace('Ask HN:', '').strip()  # 移除 "Ask HN:" 并清理空格
        titles.append(title)
        urls.append(f"https://news.ycombinator.com/item?id={story_id}")
    except requests.exceptions.RequestException as e:
        logging.error(f"获取标题 {story_id} 失败: {e}")
        print(f"获取标题 {story_id} 失败: {e}")
        titles.append(f"无法获取标题 {story_id}")
        urls.append("")  # 失败时添加空 URL
    except requests.exceptions.JSONDecodeError as e:
        logging.error(f"标题 {story_id} JSON 解析错误: {e}")
        print(f"标题 {story_id} JSON 解析错误: {e}")
        titles.append(f"无法解析标题 {story_id}")
        urls.append("")  # 失败时添加空 URL

# 翻译标题为中文
translated_titles = []
for title in titles:
    translated_titles.append(translate_title(title, proxies, session))

# 获取当前时间（香港时间）
hkt = pytz.timezone('Asia/Hong_Kong')
current_time = datetime.now(hkt).strftime('%Y-%m-%d %H:%M:%S HKT')

# 格式化消息，添加 URL
formatted_titles = [
    f"URL: {url}\n{i+1}. {en}\n   {cn}\n" if url else f"{i+1}. {en}\n   {cn}\n"
    for i, (url, en, cn) in enumerate(zip(urls, titles, translated_titles))
]
message = f"每日 Hacker News Ask 前 30 标题（{current_time}）:\n\n" + "\n".join(formatted_titles)

# 通过 Telegram 发送消息，考虑分批发送以避免超长
url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
if len(message) > 4096:
    # 分批发送，每批 10 个标题
    for i in range(0, len(formatted_titles), 10):
        batch_message = f"每日 Hacker News Ask 前 30 标题（{current_time}） - Part {i//10 + 1}:\n\n" + "\n".join(formatted_titles[i:i+10])
        params = {'chat_id': CHAT_ID, 'text': batch_message}
        try:
            response = session.get(url, params=params, proxies=proxies, timeout=30, verify=VERIFY_SSL)
            response.raise_for_status()
            logging.info(f"消息分批发送成功: Part {i//10 + 1}")
            print(f"消息分批发送成功: Part {i//10 + 1}")
        except requests.exceptions.RequestException as e:
            logging.error(f"消息分批发送失败 (Part {i//10 + 1}): {e}")
            print(f"消息分批发送失败 (Part {i//10 + 1}): {e}")
else:
    # 直接发送
    params = {'chat_id': CHAT_ID, 'text': message}
    try:
        response = session.get(url, params=params, proxies=proxies, timeout=30, verify=VERIFY_SSL)
        response.raise_for_status()
        logging.info("消息发送成功")
        print("消息发送成功")
    except requests.exceptions.RequestException as e:
        logging.error(f"消息发送失败: {e}")
        print(f"消息发送失败: {e}")