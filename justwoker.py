"""
File: justwoker.py(justwoker 额度查询)
Author: sjmy
cron: 0 4 * * *
new Env('justwoker额度查询');
Update: 2026/10/11

配置来源：只读脚本目录下的 sjmyConfig.json，键名 JUSTWOKER_COOKIE。
（不再读取环境变量。）

说明:
    API 地址: https://api.justwoker.icu
    本站是 New-API 新版，认证方式：
      1. GET  /api/status              公开接口，拿站点配置（quota_per_unit）
      2. POST /api/user/auth/refresh   携带 new_api_refresh Cookie，换取 access_token
                                       （JWT，约 15 分钟有效），响应里已含完整用户信息
    quota 单位换算：默认 500000 等于 1 元，实际以 /api/status 返回的 quota_per_unit 为准。

    运行时间建议 cron `0 4 * * *`，即每天 4 点执行；为了避免同一时间请求过多，默认随机延迟 1~15 分钟。
    如需关闭随机延迟，可设置环境变量 JUSTWOKER_DELAY_MAX 为 0，表示不延迟。
"""
import os
import json
import random
import time

import requests

import notify


class JustWoker:
    BASE_URL = "https://api.justwoker.icu"
    DEFAULT_QUOTA_PER_UNIT = 500000
    CONFIG_FILE = "sjmyConfig.json"
    CONFIG_KEY = "JUSTWOKER_COOKIE"

    def __init__(self):
        self.refresh_cookie = ''
        self.access_token = ''
        self.user_id = ''
        self.quota_per_unit = self.DEFAULT_QUOTA_PER_UNIT
        self.Log = ""
        self.session = None
        self.config = {}

        self.UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/154.0.0.0 Safari/537.36 Edg/154.0.0.0')

    def _headers(self, referer=None):
        headers = {
            'host': 'api.justwoker.icu',
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
        if self.access_token:
            headers['authorization'] = f'Bearer {self.access_token}'
        return headers

    # ---------- 站点配置（公开接口） ----------
    def status(self):
        url = f"{self.BASE_URL}/api/status"
        resp = self.session.get(url, headers=self._headers(f"{self.BASE_URL}/"), timeout=30)
        resp.raise_for_status()
        j = resp.json()
        data = j.get('data') or {}

        try:
            self.quota_per_unit = int(data.get('quota_per_unit') or self.DEFAULT_QUOTA_PER_UNIT)
        except (TypeError, ValueError):
            self.quota_per_unit = self.DEFAULT_QUOTA_PER_UNIT

        self.set_log(f"  ⚙️站点:`{data.get('system_name') or '未知'}` "
                     f"版本:`{data.get('version') or '未知'}` "
                     f"换算:`{self.quota_per_unit}/元`")
        return j

    # ---------- 用 new_api_refresh Cookie 换取 access_token + 用户信息 ----------
    def refresh(self, cookie):
        url = f"{self.BASE_URL}/api/user/auth/refresh"
        headers = self._headers(f"{self.BASE_URL}/console")
        headers['content-length'] = '0'

        resp = self.session.post(url, headers=headers, timeout=30,
                                 cookies={'new_api_refresh': cookie})
        if resp.status_code == 429:
            retry_after = resp.headers.get('retry-after') or '?'
            raise Exception(f"429 触发接口限流，请 {retry_after} 秒后再试（refresh 接口有频率限制，别频繁手动跑）")
        try:
            j = resp.json()
        except ValueError:
            raise Exception(f"刷新接口返回非 JSON（HTTP {resp.status_code}）")

        if not j.get('success'):
            code = j.get('code') or resp.status_code
            message = j.get('message') or '刷新凭证失败'
            raise Exception(f"{code} {message}")

        data = j.get('data') or {}
        token = data.get('access_token') or ''
        if not token:
            raise Exception('刷新成功但未返回 access_token')

        self.access_token = token
        user = data.get('user') or {}
        if user.get('id'):
            self.user_id = user['id']

        # 服务端下发的新 Cookie（轮换后的），交给调用方保存
        # 优先用 requests 的 cookie jar；拿不到时兜底解析 Set-Cookie 响应头。
        # 注意 Path=/api/user/auth，jar 有时按 path 匹配拿不到，所以兜底必不可少。
        new_cookie = resp.cookies.get('new_api_refresh') or ''
        if not new_cookie:
            # 多条 Set-Cookie 会被 requests 用逗号合并成一行，需先按逗号切分，
            # 再在每段里找 new_api_refresh= 并截到第一个 ; 之前。
            for segment in resp.headers.get('set-cookie', '').split(','):
                for part in segment.split(';'):
                    part = part.strip()
                    if part.startswith('new_api_refresh='):
                        new_cookie = part[len('new_api_refresh='):].strip()
                        break
                if new_cookie:
                    break

        expires_at = data.get('access_expires_at')
        if expires_at:
            self.set_log(f"  🔑access_token 有效期至:`{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expires_at))}`")
        return new_cookie if new_cookie and new_cookie != cookie else '', user

    def _print_user(self, data):
        quota = data.get('quota', 0) or 0
        used = data.get('used_quota', 0) or 0
        total = quota + used
        unit = self.quota_per_unit or self.DEFAULT_QUOTA_PER_UNIT
        name = data.get('display_name') or data.get('username') or self.user_id
        self.set_log(f"  👤用户名:`{name}`")
        self.set_log(f"  💰当前余额:`{quota}({quota / unit:.2f}元)`")
        self.set_log(f"  📊已用额度:`{used}({used / unit:.2f}元)`")
        self.set_log(f"  🧾累计额度:`{total}({total / unit:.2f}元)`")
        self.set_log(f"  🔢请求次数:`{data.get('request_count', 0)}`")
        return data

    # ---------- 配置读写：只动 JUSTWOKER_COOKIE 这一项 ----------
    def load_cookie(self):
        """读取 sjmyConfig.json 的 JUSTWOKER_COOKIE，兼容字符串和对象两种写法。"""
        with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        value = self.config.get(self.CONFIG_KEY)
        if isinstance(value, dict):
            cookies = value.get('cookies') or []
            return (cookies[0] if cookies else '').strip()
        if isinstance(value, str):
            return value.strip()
        return ''

    def save_cookie(self, new_cookie):
        """把轮换后的新 Cookie 写回 JUSTWOKER_COOKIE，其他配置项原样保留。"""
        self.config[self.CONFIG_KEY] = {
            'cookies': [new_cookie],
            'updated_at': int(time.time()),
        }
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    # ---------- 记录日志 ----------
    def set_log(self, text):
        print(text)
        self.Log = self.Log + "\n" + text

    def get_log(self):
        return self.Log.replace("\n", "\n\n")  # 适配 markdown 换行

    # ---------- 随机延迟 ----------
    def random_delay(self):
        try:
            max_min = float(os.getenv("JUSTWOKER_DELAY_MAX", "15"))
        except ValueError:
            max_min = 15
        if max_min <= 0:
            return
        delay = random.uniform(1, max_min)
        self.set_log(f"⏰随机延迟 {delay:.1f} 分钟后继续执行...")
        time.sleep(delay * 60)

    # ---------- 单账号处理 ----------
    def run_account(self):
        self.refresh_cookie = ''
        self.access_token = ''
        self.user_id = ''
        self.session = requests.Session()

        try:
            cookie = self.load_cookie()
        except Exception as e:
            self.set_log(f"❌读取 {self.CONFIG_FILE} 失败:{e}")
            return
        if not cookie:
            self.set_log(f"❌{self.CONFIG_KEY} 未配置或为空，已跳过")
            return

        self.set_log("\n---------开始查询额度---------")
        try:
            self.status()
        except Exception as e:
            self.set_log(f"  ⚠️读取站点配置失败:{e}")

        self.set_log("  🔐认证方式:`new_api_refresh Cookie`")
        self.refresh_cookie = cookie
        try:
            new_cookie, user = self.refresh(cookie)
        except Exception as e:
            self.set_log(f"  ❌认证失败:{e}")
            self.set_log("  💡提示：new_api_refresh 已被轮换或 session 被撤销，"
                         "请在浏览器重新登录后重新复制 Cookie 填到 "
                         f"{self.CONFIG_FILE} 的 {self.CONFIG_KEY}，脚本会自动接管后续轮换")
            return

        self.set_log("  ✅换取 access_token 成功")
        # 保存轮换后的新 Cookie
        if new_cookie:
            try:
                self.save_cookie(new_cookie)
                self.set_log(f"  💾已保存轮换后的 new_api_refresh 到 `{self.CONFIG_FILE}`")
            except Exception as e:
                self.set_log(f"  ⚠️写入 {self.CONFIG_FILE} 失败:{e}")
        else:
            self.set_log("  ℹ️服务端未下发新 Cookie，沿用当前值")

        # refresh 响应里已含完整用户信息，直接展示
        self._print_user(user)

    def run(self):
        try:
            cookie = self.load_cookie()
        except Exception as e:
            notify.send("JUSTWOKER_COOKIE", f'❌读取 {self.CONFIG_FILE} 失败：{e}')
            self.set_log(f"❌读取 {self.CONFIG_FILE} 失败:{e}")
            exit()
        if not cookie:
            notify.send("JUSTWOKER_COOKIE", f'❌{self.CONFIG_KEY} 未配置')
            self.set_log(f'❌{self.CONFIG_KEY} 未配置')
            exit()
        self.set_log("✅JUSTWOKER_COOKIE 读取成功")

        self.random_delay()
        self.run_account()

        print("\n\n")  # 分隔通知消息
        notify.send("justwoker额度查询", self.get_log())


if __name__ == "__main__":
    justwoker = JustWoker()
    justwoker.run()
