"""
File: agentrouter.py(agentrouter 额度查询)
Author: sjmy
cron: 0 4 * * *
new Env('agentrouter额度查询');
Update: 2026/10/10

getenv name: AGENTROUTER_COOKIE
getenv value: 账号1 username#账号1 password&账号2 username#账号2 password&...

说明:
    API 地址: https://agentrouter.org
    该站基于 New-API，登录接口会返回 Set-Cookie 头，携带 session；查询接口需带上 session。
    与 futureppo 不同，本站没有每日签到，登录后直接查询账号额度即可。
    quota 单位换算：500000 等于 1 元。

    运行时间建议 cron `0 4 * * *`，即每天 4 点执行；为了避免同一时间请求过多，默认随机延迟 1~15 分钟。
    如需关闭随机延迟，可设置环境变量 AGENTROUTER_DELAY_MAX 为 0，表示不延迟。
"""
import os
import json
import random
import time

import requests

import notify


class AgentRouter:
    BASE_URL = "https://ps.air-outer.com"
    QUOTA_PER_YUAN = 500000

    def __init__(self):
        self.username = ''
        self.password = ''
        self.user_id = ''
        self.Log = ""
        self.session = None

        self.UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/154.0.0.0 Safari/537.36 Edg/154.0.0.0')

    def _headers(self, referer=None):
        headers = {
            'host': 'agentrouter.org',
            'user-agent': self.UA,
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cache-control': 'no-store',
            'pragma': 'no-cache',
            'origin': self.BASE_URL,
            'referer': referer or f"{self.BASE_URL}/console",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }
        if self.user_id:
            headers['new-api-user'] = str(self.user_id)
        return headers

    # 登录获取 session 凭证
    def login(self):
        url = f"{self.BASE_URL}/api/user/login?turnstile="
        payload = {
            'username': self.username,
            'password': self.password,
        }
        headers = self._headers(referer=f"{self.BASE_URL}/login")
        headers['content-type'] = 'application/json'

        resp = self.session.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        j = resp.json()

        session = self.session.cookies.get('session') or resp.cookies.get('session')
        if not session:
            # 兜底从 Set-Cookie 头解析
            set_cookie = resp.headers.get('set-cookie', '')
            for part in set_cookie.split(';'):
                part = part.strip()
                if part.startswith('session='):
                    session = part[len('session='):]
                    break

        if not j.get('success') or not session:
            raise Exception(f"登录失败: {j.get('message') or resp.text[:200]}")

        user_id = (j.get('data') or {}).get('id')
        if user_id:
            self.user_id = user_id
        return session

    # 查询用户信息
    def info(self):
        url = f"{self.BASE_URL}/api/user/self"
        headers = self._headers(referer=f"{self.BASE_URL}/console")

        resp = self.session.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        j = resp.json()

        if not j.get('success'):
            self.set_log(f"  ❌查询用户信息失败:{j.get('message')}")
            return j

        data = j.get('data', {}) or {}
        if data.get('id'):
            self.user_id = data.get('id')
        quota = data.get('quota', 0)
        used = data.get('used_quota', 0)
        total = quota + used
        self.set_log(f"  👤用户名:`{data.get('display_name') or data.get('username') or self.username}`")
        self.set_log(f"  💰当前余额:`{quota}({quota / self.QUOTA_PER_YUAN:.2f}元)`")
        self.set_log(f"  📊已用额度:`{used}({used / self.QUOTA_PER_YUAN:.2f}元)`")
        self.set_log(f"  🧾累计额度:`{total}({total / self.QUOTA_PER_YUAN:.2f}元)`")
        self.set_log(f"  🔢请求次数:`{data.get('request_count', 0)}`")
        return j

    # 记录日志
    def set_log(self, text):
        print(text)
        self.Log = self.Log + "\n" + text

    # 获取日志
    def get_log(self):
        return self.Log.replace("\n", "\n\n")  # 适配 markdown 换行

    # 随机延迟，默认 1~15 分钟；可通过 AGENTROUTER_DELAY_MAX 控制最大分钟，0 表示不延迟
    def random_delay(self):
        try:
            max_min = float(os.getenv("AGENTROUTER_DELAY_MAX", "15"))
        except ValueError:
            max_min = 15
        if max_min <= 0:
            return
        # 随机延迟 1 到 max_min 分钟
        delay = random.uniform(1, max_min)
        self.set_log(f"⏰随机延迟 {delay:.1f} 分钟后继续执行...")
        time.sleep(delay * 60)

    def run(self):
        AGENTROUTER_COOKIE = os.getenv("AGENTROUTER_COOKIE")
        if not AGENTROUTER_COOKIE:
            self.set_log("❌未读取到 AGENTROUTER_COOKIE，请检查环境变量或配置文件")
            try:
                with open('sjmyConfig.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "AGENTROUTER_COOKIE" in config:
                        AGENTROUTER_COOKIE = config["AGENTROUTER_COOKIE"]
            except Exception as e:
                self.set_log(f'❌读取配置文件获取 AGENTROUTER_COOKIE 失败：{e}')
                exit()
            if not AGENTROUTER_COOKIE:
                notify.send("AGENTROUTER_COOKIE", '❌AGENTROUTER_COOKIE 未配置')
                self.set_log('❌AGENTROUTER_COOKIE 未配置')
                exit()
        self.set_log("✅AGENTROUTER_COOKIE 读取成功")

        self.random_delay()

        ck_list = AGENTROUTER_COOKIE.split('&')
        self.set_log("---------共" + str(len(ck_list)) + "个账号---------")
        for index, tokens in enumerate(ck_list):
            if len(ck_list) > 1:
                self.set_log(f"\n---------第{index + 1}个账号---------")
            my_token = tokens.split('#')
            if len(my_token) != 2:
                self.set_log("❌账号格式错误，应为 username#password")
                continue
            self.username = my_token[0]
            self.password = my_token[1]
            self.user_id = ''
            self.session = requests.Session()

            self.set_log("\n---------开始查询额度---------")
            try:
                self.login()
                self.set_log("  ✅登录成功")
            except Exception as e:
                self.set_log(f"  ❌登录失败:{e}")
                continue

            try:
                self.info()
            except Exception as e:
                self.set_log(f"  ❌查询用户信息失败:{e}")

        print("\n\n")  # 分隔通知消息
        notify.send("agentrouter额度查询", self.get_log())


if __name__ == "__main__":
    agentrouter = AgentRouter()
    agentrouter.run()
