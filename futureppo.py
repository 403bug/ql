"""
File: futureppo.py(futureppo 签到)
Author: sjmy
cron: 0 4 * * *
new Env('futureppo签到');
Update: 2026/10/10

getenv name: FUTUREPPO_COOKIE
getenv value: 账号1 username#账号1 password&账号2 username#账号2 password&...

说明:
    API 地址: https://api2.futureppo.top/
    登录接口会返回 Set-Cookie 头，携带 session；签到/查询接口需带上 session。
    下面代码通过登录接口拿到 session 后，再请求签到和用户信息。
    quota 单位换算：500000 等于 1 元。

    运行时间建议 cron `0 4 * * *`，即每天 4 点执行；为了避免同一时间请求过多，默认随机延迟 1~15 分钟。
    如需关闭随机延迟，可设置环境变量 FUTUREPPO_DELAY_MAX 为 0，表示不延迟。
"""
import os
import json
import random
import time

import requests

import notify


class FuturePPO:
    BASE_URL = "https://api2.futureppo.top/"
    QUOTA_PER_YUAN = 500000

    def __init__(self):
        self.username = ''
        self.password = ''
        self.user_id = ''
        self.Log = ""
        self.session = None

        self.UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/144.0.0.0 Safari/537.36')

    def _headers(self, referer="https://api2.futureppo.top/console"):
        headers = {
            'host': 'api2.futureppo.top',
            'user-agent': self.UA,
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'origin': self.BASE_URL,
            'referer': referer,
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        if self.user_id:
            headers['new-api-user'] = str(self.user_id)
        if self.session:
            headers['cookie'] = f'session={self.session}'
        return headers

    # 登录获取 session 凭证
    def login(self):
        url = f"{self.BASE_URL}/api/user/login?turnstile="
        payload = {
            'username': self.username,
            'password': self.password,
        }
        headers = self._headers(referer=f"{self.BASE_URL}/login")
        headers.pop('cookie', None)  # 登录接口不需要 cookie

        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()

        session = resp.cookies.get('session')
        if not session:
            # 兜底从 Set-Cookie 头解析
            set_cookie = resp.headers.get('set-cookie', '')
            for part in set_cookie.split(';'):
                part = part.strip()
                if part.startswith('session='):
                    session = part[len('session='):]
                    break

        j = resp.json()
        if not j.get('success') or not session:
            raise Exception(f"登录失败: {j.get('message') or resp.text[:200]}")

        self.session = session
        user_id = j.get('data', {}).get('id')
        if user_id:
            self.user_id = user_id
        return session

    # 签到
    def checkin(self):
        url = f"{self.BASE_URL}/api/user/checkin"
        headers = self._headers(referer=f"{self.BASE_URL}/console/personal")
        headers['content-length'] = '0'

        resp = requests.post(url, headers=headers, timeout=30)
        resp.raise_for_status()
        j = resp.json()

        if j.get('success'):
            data = j.get('data', {}) or {}
            quota = data.get('quota_awarded', 0)
            self.set_log(f"  ✅签到结果:{j.get('message') or '成功'}")
            self.set_log(f"  🎁获得奖励:{quota}")
        else:
            self.set_log(f"  ❌签到结果:{j.get('message') or '签到失败'}")
        return j

    # 查询用户信息
    def info(self):
        url = f"{self.BASE_URL}/api/user/self"
        headers = self._headers(referer=f"{self.BASE_URL}/console")

        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        j = resp.json()

        if not j.get('success'):
            self.set_log(f"  ❌查询用户信息失败:{j.get('message')}")
            return j

        data = j.get('data', {}) or {}
        quota = data.get('quota', 0)
        used = data.get('used_quota', 0)
        self.set_log(f"  👤用户名:`{data.get('display_name') or self.username}`")
        self.set_log(f"  💰当前余额:`{quota}({quota / self.QUOTA_PER_YUAN:.2f}元)`")
        self.set_log(f"  📊已用额度:`{used}({used / self.QUOTA_PER_YUAN:.2f}元)`")
        return j

    # 记录日志
    def set_log(self, text):
        print(text)
        self.Log = self.Log + "\n" + text

    # 获取日志
    def get_log(self):
        return self.Log.replace("\n", "\n\n")  # 适配 markdown 换行

    # 随机延迟，默认 1~5 分钟；可通过 FUTUREPPO_DELAY_MAX 控制最大分钟，0 表示不延迟
    def random_delay(self):
        try:
            max_min = float(os.getenv("FUTUREPPO_DELAY_MAX", "5"))
        except ValueError:
            max_min = 5
        if max_min <= 0:
            return
        # 随机延迟 1 到 max_min 分钟
        delay = random.uniform(1, max_min)
        self.set_log(f"⏰随机延迟 {delay:.1f} 分钟后继续执行...")
        time.sleep(delay * 60)

    def run(self):
        FUTUREPPO_COOKIE = os.getenv("FUTUREPPO_COOKIE")
        if not FUTUREPPO_COOKIE:
            self.set_log("❌未读取到 FUTUREPPO_COOKIE，请检查环境变量或配置文件")
            try:
                with open('sjmyConfig.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "FUTUREPPO_COOKIE" in config:
                        FUTUREPPO_COOKIE = config["FUTUREPPO_COOKIE"]
            except Exception as e:
                self.set_log(f'❌读取配置文件获取 FUTUREPPO_COOKIE 失败：{e}')
                exit()
            if not FUTUREPPO_COOKIE:
                notify.send("FUTUREPPO_COOKIE", '❌FUTUREPPO_COOKIE 未配置')
                self.set_log('❌FUTUREPPO_COOKIE 未配置')
                exit()
        self.set_log("✅FUTUREPPO_COOKIE 读取成功")

        self.random_delay()

        ck_list = FUTUREPPO_COOKIE.split('&')
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
            self.session = None
            self.user_id = ''

            self.set_log("\n---------开始签到---------")
            try:
                self.login()
                self.set_log("  ✅登录成功")
            except Exception as e:
                self.set_log(f"  ❌登录失败:{e}")
                continue

            try:
                self.checkin()
            except Exception as e:
                self.set_log(f"  ❌签到失败:{e}")

            try:
                self.info()
            except Exception as e:
                self.set_log(f"  ❌查询用户信息失败:{e}")

        print("\n\n")  # 分隔通知消息
        notify.send("futureppo签到", self.get_log())


if __name__ == "__main__":
    futureppo = FuturePPO()
    futureppo.run()
