#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: PCR532.py(PCR532签到)
Author: sjmy
cron: 10 8 * * *
new Env('PCR532签到');
Update: 2025/07/18

getenv name: PCR532_COOKIE
getenv value: 账号1 username#账号1 password#账号1 USERID&账号2 username#账号2 password#账号2 USERID&...


"""
import base64
import os
import json
import notify
import requests


class PCR532:
    def __init__(self):
        self.username = ''
        self.password = ''
        self.USERID = ''
        self.Log = ""
        self.passB = '' # 解码为：pn532cardreader
        self.UA = 'Dalvik/2.1.0 (Linux; U; Android 15; PJD110 Build/AP3A.240617.008)'

    def pcr_sign(self):
        url = "https://www.rfidfans.com/upload/qiandao.php"

        payload = {
            'username': self.username,
            'passc': self.password,
            'USERID': self.USERID
        }

        headers = {
            'User-Agent': self.UA,
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip"
        }

        try:
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()  # 检查HTTP错误
            j = response.text
            if j :
                self.set_log("🎉" + j)
        except requests.exceptions.RequestException as e:
            self.set_log(f"💥请求失败: {e}")
        except Exception as e:
            self.set_log(f"💥未预期的错误: {e}")
            if 'response' in locals():
                self.set_log(f"💥响应内容: {response.text[:200]}...")  # 只显示前200个字符，避免日志过长

    def info_search(self):
        url = "https://www.rfidfans.com/upload/info_search.php"
        payload = {
            'passB': self.passB,
            'passA': 'ZGV2aWNlbGlzdA==',
            'username': self.username,
            'passc': self.password,
            'USERID': self.USERID
        }
        headers = {
            'User-Agent': self.UA,
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip"
        }
        try:
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()
            j = response.json()
            if isinstance(j, list):
                self.set_log(f"👤账号：`{j[0]['username']}`")
                self.set_log(f"💰金币：`{j[0]['jinbi']}`")
            else:
                self.set_log(f"💥返回内容异常：{response.text}")
        except Exception as e:
            self.set_log(f"💥查询个人设备失败: {e}")
            if 'response' in locals():
                self.set_log(f"💥响应内容: {response.text[:200]}...")

    # 新增日志
    def set_log(self, text):
        print(text)
        self.Log = self.Log + "\n" + text
    # 获取日志
    def get_log(self):
        # return self.Log.replace("\n","\r\n") # 用于 windows 和 Linux 换行符切换
        return self.Log.replace("\n","\n\n") # 用于适配markdown格式输出
        # return self.Log # 正常输出

    def run(self):
        PCR532_COOKIE = os.getenv("PCR532_COOKIE")
        if not PCR532_COOKIE:
            self.set_log("⚠️读取环境变量配置失败，正在读取本地文件。")
            # 2. 尝试读取本地 sjmyConfig.json
            try:
                with open('sjmyConfig.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "PCR532_COOKIE" in config:
                        PCR532_COOKIE = config["PCR532_COOKIE"]
            except Exception as e:
                self.set_log(f'⚠️读取本地文件 PCR532_COOKIE 失败：{e}')
                exit()
            if not PCR532_COOKIE:
                notify.send("PCR532_COOKIE", '🙃PCR532_COOKIE 变量未设置')
                self.set_log('⚠️PCR532_COOKIE 变量未设置')
                exit()
        self.set_log("✅PCR532_COOKIE 变量读取成功")

        ck_list = PCR532_COOKIE.split('&')
        self.set_log("---------共" + str(int(len(ck_list))) + "个账号---------")
        for tokens in ck_list:
            if int(len(ck_list)) > 1:
                self.set_log(f"\n---------第{ck_list.index(tokens) + 1}个账号---------")
            my_token = tokens.split('#')
            if my_token == '' or int(len(my_token)) != 3:
                self.set_log("⚠️账号格式有误，请检查账号后进行重试")
                continue
            self.username = my_token[0]
            self.password = base64.b64encode(my_token[1].encode('utf-8')).decode()
            self.USERID = base64.b64encode(my_token[2].encode('utf-8')).decode()
            self.passB = base64.b64encode('pn532cardreader'.encode('utf-8')).decode()
            self.set_log("\n---------开始签到---------")
            self.pcr_sign()
            # self.set_log("\n---------查询积分---------")
            self.info_search()

        print("\n\n") # 用于与推送通知分割开
        notify.send("PCR532签到", self.get_log())



if __name__ == "__main__":
    pcr532 = PCR532()
    pcr532.run()
