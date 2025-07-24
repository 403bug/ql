#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: OPPO.py(OPPO签到)
Author-original: ytt447735
Author: sjmy
cron: 0 8 * * *
new Env('OPPO签到');
getenv name: OPPO_COOKIE
getenv value: 账号1 TOKENSID#账号1 session_id&账号2 TOKENSID#账号2 session_id&...
            请阅读 `Problem-3` 进行配置session_id

Update: 2025/07/15

Description:
    1. 新增了token使用期限检查功能，支持多账号签到
    2. 增加了OPPO会员、OPPO商城的微信小程序签到
    3. 增加了OPPO商城、OPPO社区、钱包（代码不完善）、我的一加、一加社区、阅读的签到
    4. 累计签到会自动领取
    5. 任务列表会自动执行去完成（目前就只做了简单的跳转的、开启通知、预约的任务）
    6. OPPO商城微信小程序自动抽奖
    7. OPPO社区点赞帖子任务自动执行

Problem:
    1. 可能会出现签到失败的情况，需要手动检查
    2. 钱包的签到出了点问题，可能无法签到
    3. OPPO会员小程序签到，今日积分收入统计不是依赖token，依赖的是sessionId，需要手动获取,如果不执行相应的流程，可把session_id留空

Future:
    0. 牙膏要一点一点挤，显卡要一刀一刀切，代码要一点一点写，生活要一点一点过，预计亿年内完成。
    1. OPPO商城网站签到未完成.(验证会每天更换，非常困难，估计完不成）
    2. 主题商店签到、装扮萌宠养成未完成。（任务太多，类型太杂，一时间分析不过来）
    3. 阅读APP里累计阅读功能未实现。（还未找到具体的请求逻辑，初步判断有加密）
    4.


"""
import base64
import json
import os
import notify
from datetime import datetime
import ujson
import requests
import re
import time


# 定义 ActivityInfo 类
class ActivityInfo:
    def __init__(self, activityName, apkPkg, activityId, creditsAddActionId, business, s_channel):
        """
        初始化 ActivityInfo 类的实例。
        :param activityName: 活动名称
        :param apkPkg: APK 包名
        :param activityId: 活动 ID
        :param creditsAddActionId: 积分增加动作 ID
        :param business: 业务信息
        :param s_channel: 设备信息
        """
        self.activityName = activityName
        self.apkPkg = apkPkg
        self.activityId = activityId
        self.creditsAddActionId = creditsAddActionId
        self.business = business
        self.s_channel = s_channel

    def toJson(self):
        """
        将对象转换为不包含活动名称的 JSON 格式的字符串。
        :return: JSON 格式的字符串
        """
        # 创建一个不包含 activityName 的字典
        data = {
            "activityId": self.activityId,
            "creditsAddActionId": self.creditsAddActionId,
            "business": self.business
        }
        return json.dumps(data, ensure_ascii=False)


class OPPO:

    def __init__(self):
        self.Log = ""
        # self.set_log("🤖运行了__init__")
        self.ck = ''
        self.apkPkg = 'com.oppo.store'
        self.UA = 'Mozilla/5.0 (Linux; Android 15; PJD110 Build/AP3A.240617.008; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.58 Mobile Safari/537.36 oppostore/404503 ColorOS/V15.0.0 brand/OnePlus model/PJD110'
        # 修改为任务活动对象列表
        self.activityId_taskActivityInfo = []
        self.activity_list = []
        self.session_id = ''

    # 获取签到渠道ID和活动ID
    def get_activityId(self):
        # self.set_log("🤖运行了get_activityId")
        url = "https://hd.opposhop.cn/bp/b371ce270f7509f0?nightModelEnable=true&us=wode&um=qiandaobanner"
        payload = {}
        headers = {
            'Cookie': f"apkPkg={self.apkPkg}; TOKENSID=TOKEN_{self.ck}",
            'User-Agent': self.UA
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        # 确保响应使用UTF-8编码
        response.encoding = 'utf-8'

        # 初始化活动列表（如果还没有初始化）
        if not hasattr(self, 'activity_list') or self.activity_list is None:
            self.activity_list = []

        # 获取所有的活动ID和活动名称
        # 尝试匹配 "activityInfo":{"activityId":"1938150025645531136","activityName":"金钻会员-每日签到-商城客户端（25年7月）"}
        activity_pattern = r'"activityInfo":{"activityId":"(\d+)","activityName":"([^"]+)"'
        activity_matches = re.findall(activity_pattern, response.text)

        # 如果上面的正则表达式没有匹配到，尝试另一种格式
        if not activity_matches:
            self.set_log("🈚️没找到，尝试另一种格式")
            # 尝试匹配 "activityId":"1938150025645531136","activityName":"金钻会员-每日签到-商城客户端（25年7月）"
            alt_pattern = r'"activityId":"(\d+)","activityName":"([^"]+)"'
            activity_matches = re.findall(alt_pattern, response.text)

        if activity_matches:
            # self.set_log("======================================================")
            self.set_log(f"🤓👆🏻找到`{len(activity_matches)}`个活动:")

            # 创建一个集合来存储已经添加的活动ID，避免重复
            existing_activity_ids = {activity.activityId for activity in self.activity_list}

            for i, (activity_id, activity_name) in enumerate(activity_matches):
                # 对活动名称进行解码，处理中文字符
                # 使用json.loads来解码转义的Unicode字符
                try:
                    decoded_name = json.loads(f'"{activity_name}"')
                except json.JSONDecodeError:
                    # 如果json解码失败，尝试使用正则表达式替换Unicode转义序列
                    self.set_log("💥json解码失败，尝试进行正则表达式替换Unicode转义序列")
                    decoded_name = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), activity_name)
                    if decoded_name == activity_name:  # 如果没有变化，可能不是Unicode转义
                        decoded_name = activity_name

                self.set_log(f"🤓👆🏻活动 {i + 1}: `{decoded_name}`")
                # self.set_log(f"🤓👆🏻活动 {i+1}ID: {activity_id}")

                # 检查活动ID是否已经存在于活动列表中
                if activity_id not in existing_activity_ids:
                    # 将活动添加到活动列表
                    self.activity_list.append(
                        ActivityInfo(
                            decoded_name,  # 使用解码后的名称
                            'com.oppo.store',  # 默认使用OPPO商城的包名
                            activity_id,
                            "1788913e6d9e4683b8b9ab0088733560",  # 使用默认的积分增加动作ID
                            1,  # 默认业务类型为1
                            'oppo_appstore'
                        )
                    )
                    existing_activity_ids.add(activity_id)
                else:
                    self.set_log(f"🔄活动：`{decoded_name}`已存在于活动列表中，跳过添加")
                    # self.set_log(f"🔄活动：{decoded_name} ID {activity_id} 已存在于活动列表中，跳过添加")

            # self.set_log("======================================================")
        else:
            self.set_log(f"❌签到失败，未找到活动ID和活动名称！")

        # 获取活动任务 ID
        task_activity_pattern = r'"taskActivityInfo":{"activityId":"(\d+)"(?:,"activityName":"([^"]*)")?'
        task_activity_matches = re.findall(task_activity_pattern, response.text)
        if task_activity_matches:
            # 创建一个集合来存储已经添加的任务活动ID，避免重复
            existing_task_activity_ids = {task_activity.activityId for task_activity in
                                          self.activityId_taskActivityInfo}

            for i, (task_id, activity_name) in enumerate(task_activity_matches):
                # 如果没有找到活动名称，使用默认名称
                activity_name = activity_name if activity_name else f"任务活动{i + 1}"

                # 尝试解码活动名称
                try:
                    decoded_name = json.loads(f'"{activity_name}"')
                except json.JSONDecodeError:
                    decoded_name = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), activity_name)
                    if decoded_name == activity_name:  # 如果没有变化，可能不是Unicode转义
                        decoded_name = activity_name

                if task_id not in existing_task_activity_ids:
                    # 将任务活动添加到列表
                    self.activityId_taskActivityInfo.append(
                        ActivityInfo(
                            decoded_name,  # 活动名称
                            'com.oppo.store',  # 默认使用OPPO商城的包名
                            task_id,  # 活动ID
                            "",  # 使用默认的积分增加动作ID
                            501,  # 默认业务类型为501（对应source_type）
                            'oppo_appstore'  # 默认渠道（对应s_channel）
                        )
                    )
                    existing_task_activity_ids.add(task_id)
                    self.set_log(f"\u2705已添加活动任务:`{decoded_name}`到列表")
                    # self.set_log(f"\u2705已添加活动任务: {decoded_name}, ID: {task_id} 到列表")
                # else:
                #     self.set_log(f"🔄活动任务 : {decoded_name} 已存在于列表中，跳过添加")
                # self.set_log(f"🔄活动任务 ID: {task_id} 已存在于列表中，跳过添加")

            # self.set_log(f"⏩当前活动任务列表: {[task.activityName for task in self.activityId_taskActivityInfo]}")
            # self.set_log(f"⏩当前活动任务列表: {[task.activityId for task in self.activityId_taskActivityInfo]}")
        else:
            self.set_log("❌获取活动任务 ID 获取失败")
        # for activity in self.activity_list:
        #     self.set_log("activity.activityName", activity.activityName)
        #     self.set_log("activity.activityId", activity.activityId)

    # 商城签到
    def shopping_signIn(self):
        # self.set_log("🤖运行了 shopping_signIn")

        # 然后使用activity_list中的活动信息进行签到
        for activity in self.activity_list:
            url = "https://hd.opposhop.cn/api/cn/oapi/marketing/cumulativeSignIn/signIn"

            payload = activity.toJson()  # 直接使用toJson方法返回的JSON字符串

            headers = {
                's_channel': activity.s_channel,
                'Cookie': f"apkPkg={self.apkPkg}; TOKENSID=TOKEN_{self.ck}",
                'User-Agent': self.UA,
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=payload)

            try:
                j = ujson.loads(response.text)
                if j["code"] == 200:
                    awardType = j['data']['awardType']
                    awardValue = j['data']['awardValue']
                    if awardType == 1:
                        self.set_log(f"🎉{activity.activityName} 签到成功，奖励`{awardValue}`积分")
                elif j["code"] == 5008:  # 5008 表示已经签到过了
                    self.set_log(f"➖{activity.activityName} ： `{j['message']}`")
                else:
                    message = j['message']
                    self.set_log(f"❌{activity.activityName} 签到失败，`{message}`")
            except (KeyError, ValueError):
                self.set_log(f"💥{activity.activityName} APP： 解析响应数据出错，可能是登录已失效 {response.text} ")

            time.sleep(2)  # 添加间隔时间，避免请求过快

    # 积分额度查询
    def integral_query(self):
        # self.set_log("🤖运行了 integral_query")
        url = "https://msec.opposhop.cn/users/web/memberCenter/assets?couponStatus=1&couponType=0"
        payload = {}
        headers = {
            'Cookie': f"apkPkg={self.apkPkg}; TOKENSID=TOKEN_{self.ck}",
            'User-Agent': self.UA
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        # self.set_log("integral_query", response.text)
        j = ujson.loads(response.text)
        try:
            if j["code"] == 200:
                self.set_log("💰当前余额：")
                for i, element in enumerate(j["data"]):
                    title = element["title"]
                    text = element["text"]
                    Type = element["type"]
                    if Type == "coupon" or Type == "credit" or Type == "growing":
                        self.set_log(f"👛{title}：`{text}`")
        except (KeyError, ValueError):
            self.set_log(f"💥获取积分额度失败，解析响应数据出错，可能是登录已失效 {response.text} ")

    # 积分过期情况查询
    def check_expire_credits(self):
        # self.set_log("🤖运行了 check_expire_credits")
        url = "https://credit.heytap.com/cn/credit-web/credit-expire-info"

        payload = {
            "country": "CN",
            "appPackage": self.apkPkg,
            "imei": None,
            "model": "PJD110",
            "sessionId": None,
            "timestamp": int(round(time.time() * 1000)),  # 当前时间戳
            "token": f"TOKEN_{self.ck}"
            # 注意：移除sign参数，服务器可能会自动处理或忽略
        }

        headers = {
            'Host': 'credit.heytap.com',
            'content-type': 'application/json;charset=UTF-8',
            'user-agent': self.UA,
            'accept': '*/*',
            'origin': 'https://credit.heytap.com',
            'x-requested-with': self.apkPkg,
            'referer': 'https://credit.heytap.com/credit/detail/index.html?toolbarType=1',
            'accept-language': 'zh-CN',
            'Cookie': f"TOKENSID=TOKEN_{self.ck}"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # 检查HTTP错误

            j = json.loads(response.text)
            if j["result"] == 10000:  # 正常响应
                data = j["data"]

                # 显示过期积分信息
                if data.get("expireCredits", False):
                    expire_amount = data.get("expireAmount", "未知")
                    expire_date = data.get("expireDate", "未知")
                    content = data.get("expireCreditsContent", f"{expire_amount} 积分将于 {expire_date} 到期")
                    self.set_log(f"⚠️ {content}")
                else:
                    self.set_log("✅ 近期没有即将过期的积分")

                # 显示积分规则提示
                # if "clearTips" in data:
                #     self.set_log("\n📝 积分规则：")
                #     for tip in data["clearTips"]:
                #         self.set_log(f"• {tip}")
            else:
                self.set_log(f"❌获取积分过期情况失败：{j.get('resultMsg', '未知错误')}")
        except requests.exceptions.RequestException as e:
            self.set_log(f"💥请求失败: {e}")
        except json.JSONDecodeError as e:
            self.set_log(f"💥解析响应数据失败: {e}")
        except KeyError as e:
            self.set_log(f"💥处理响应数据时出错: {e}")
        except Exception as e:
            self.set_log(f"💥未预期的错误: {e}")
            if 'response' in locals():
                self.set_log(f"响应内容: {response.text[:200]}...")  # 只显示前200个字符，避免日志过长

    # 获取累计签到列表
    def check_cumulative_sign_in(self, activity):
        # self.set_log(f"🤖运行了 check_cumulative_sign_in ")
        self.set_log(f"👀检查`{activity.activityName}`累计签到情况")
        url = f"https://hd.opposhop.cn/api/cn/oapi/marketing/cumulativeSignIn/getSignInDetail?activityId={activity.activityId}"

        headers = {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': self.UA,
            'Cookie': f"apkPkg={activity.apkPkg}; TOKENSID=TOKEN_{self.ck}"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 检查HTTP错误

            j = json.loads(response.text)
            if j["code"] == 200:  # 正常响应
                data = j["data"]

                # 显示当前签到情况
                sign_in_day_num = data.get("signInDayNum", 0)
                today_signed = data.get("todaySignIn", False)

                self.set_log(f"📊 {activity.activityName} 当前已累计签到`{sign_in_day_num}`天")
                self.set_log(f"📅 今日是否已签到: `{'是' if today_signed else '否'}`")

                # # 显示基础签到奖励列表
                # if "baseAwards" in data:
                #     self.set_log("🔄 每日签到奖励列表:")
                #     for award in data["baseAwards"]:
                #         sign_time = award.get("signTime", "未知")
                #         award_type = self._get_award_type_text(award.get("awardType"))
                #         award_value = award.get("awardValue", "未知")
                #         status = award.get("status", 0)
                #         status_text = "已领取" if status == 1 else "未达成" if status == 0 else "可领取"
                #         self.set_log(f"  - {sign_time}: {award_type} x {award_value} ({status_text})")

                # 处理累计签到奖励列表
                if "cumulativeAwards" in data:
                    cumulative_awards = data["cumulativeAwards"]
                    # self.set_log("🎁 累计签到奖励列表:")

                    # 检查是否有可领取的奖励
                    has_available_award = False
                    for award in cumulative_awards:
                        sign_day_num = award.get("signDayNum", 0)
                        award_id = award.get("awardId", 0)
                        award_type = self._get_award_type_text(award.get("awardType"))
                        award_value = award.get("awardValue", "未知")
                        status = award.get("status", 0)
                        status_text = "➖已领取" if status == 1 else "❌未达成" if status == 0 else "✅可领取"
                        # 累计签到列表详情
                        # self.set_log(f"  - 累计 {sign_day_num} 天: {award_type} x {award_value}`{status_text}`")

                        # 如果有可领取的奖励，自动领取
                        if status == 2:  # 可领取状态
                            has_available_award = True
                            self.set_log(
                                f"🎉 发现可领取的累计签到奖励: `累计 {sign_day_num} 天 {award_type} x {award_value}`")
                            self.draw_cumulative_award(activity, award_id)

                    if not has_available_award:
                        self.set_log("➖ 暂无累计签到奖励可领取")

                return True
            else:
                self.set_log(f"❌获取累计签到列表失败：{j.get('errorMessage', '未知错误')}")
                return False
        except requests.exceptions.RequestException as e:
            self.set_log(f"💥请求失败: {e}")
        except json.JSONDecodeError as e:
            self.set_log(f"💥解析响应数据失败: {e}")
        except KeyError as e:
            self.set_log(f"💥处理响应数据时出错: {e}")
        except Exception as e:
            self.set_log(f"💥未预期的错误: {e}")
            if 'response' in locals():
                self.set_log(f"响应内容: {response.text[:200]}...")  # 只显示前200个字符，避免日志过长
        return False

    # 领取累计签到奖励
    def draw_cumulative_award(self, activity, award_id):
        # self.set_log(f"🤖运行了 draw_cumulative_award ")
        self.set_log(f"🔜领取`{activity.activityName}`累计签到奖励")
        url = "https://hd.opposhop.cn/api/cn/oapi/marketing/cumulativeSignIn/drawCumulativeAward"

        payload = {
            "activityId": activity.activityId,
            "awardId": award_id,
            "creditsAddActionId": activity.creditsAddActionId,
            "business": activity.business
        }

        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'User-Agent': self.UA,
            'Cookie': f"apkPkg={activity.apkPkg}; TOKENSID=TOKEN_{self.ck}"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # 检查HTTP错误

            j = json.loads(response.text)
            if j["code"] == 200:  # 正常响应
                data = j["data"]
                award_type = self._get_award_type_text(data.get("awardType"))
                award_value = data.get("awardValue", "未知")
                sign_day_num = data.get("signInDayNum", 0)

                self.set_log(
                    f"🎉 累计签到奖励领取成功! 您已累计签到·`{sign_day_num}`天，获得`{award_type} x {award_value}`")
                return True
            elif j["code"] == 5013:  # 重复领取
                self.set_log(f"ℹ️ {j.get('errorMessage', '累计奖励已领取，重复领取')}")
                return False
            else:
                self.set_log(f"❌领取累计签到奖励失败：{j.get('errorMessage', '未知错误')}")
                return False
        except requests.exceptions.RequestException as e:
            self.set_log(f"💥请求失败: {e}")
        except json.JSONDecodeError as e:
            self.set_log(f"💥解析响应数据失败: {e}")
        except KeyError as e:
            self.set_log(f"💥处理响应数据时出错: {e}")
        except Exception as e:
            self.set_log(f"💥未预期的错误: {e}")
            if 'response' in locals():
                self.set_log(f"响应内容: {response.text[:200]}...")  # 只显示前200个字符，避免日志过长
        return False

    # 获取奖励类型文本
    def _get_award_type_text(self, award_type):
        # 将奖励类型转换为文字
        if award_type == 1:
            return "积分"
        elif award_type == 2:
            return "优惠券"
        elif award_type == 3:
            return "抽奖机会"
        else:
            return f"奖励({award_type})"

    # 小程序抽奖功能
    def do_raffle(self):
        # self.set_log("🤖运行了 do_raffle 抽奖功能")

        # 抽奖活动ID
        activity_id = "1937054297539874816"

        # 先查询抽奖次数
        query_url = f"https://hd.opposhop.cn/api/cn/oapi/marketing/raffle/queryRaffleCount?activityId={activity_id}"

        headers = {
            'User-Agent': self.UA,
            'Accept': "application/json, text/plain, */*",
            'Cookie': f"TOKENSID=TOKEN_{self.ck}; apkPkg=com.oppo.store"
        }

        try:
            # 查询抽奖次数
            response = requests.get(query_url, headers=headers)
            response.raise_for_status()

            count_data = json.loads(response.text)
            if count_data["code"] == 200:
                raffle_count = count_data["data"].get("count", -1)
                if raffle_count == -1:
                    self.set_log("❌ 获取抽奖次数失败,可能是账号状态有误。")
                    return False
                elif raffle_count == 0:
                    self.set_log("➖今日抽奖次数已用完")
                    return True
                else:
                    self.set_log(f"🎁 您当前有`{raffle_count}`次抽奖机会")

                    # 开始抽奖
                    self.set_log("🎲 开始抽奖...")
                    for i in range(raffle_count):
                        self.do_single_raffle(activity_id, i + 1, raffle_count)
                        time.sleep(2)  # 添加间隔时间，避免请求过快

                    return True
            else:
                self.set_log(f"❌ 查询抽奖次数失败: {count_data.get('message', '未知错误')}")
                return False

        except requests.exceptions.RequestException as e:
            self.set_log(f"💥 抽奖请求失败: {e}")
        except json.JSONDecodeError as e:
            self.set_log(f"💥 解析抽奖数据失败: {e}")
        except Exception as e:
            self.set_log(f"💥 抽奖过程中出现未预期的错误: {e}")

        return False

    # 执行单次抽奖
    def do_single_raffle(self, activity_id, current_draw, total_draws):
        raffle_url = f"https://hd.opposhop.cn/api/cn/oapi/marketing/raffle/clickRaffle"

        # 构建查询参数
        params = {
            "activityId": activity_id,
            # "creditsAddActionId": "1788913e6d9e4683b8b9ab0088733560",
            # "creditsDeductActionId": "d5e44c73030a4b1287bff7bfa3df0320",
            # "business": "1",
            # "jimuId": "GG//dAZ99/eP6geYUp/gxg==",
            # "jimuName": "签到赢好礼"
        }

        # 构建请求头
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': self.UA,
            # 'encryption': 'jqU44Ezs8rZKpZ5DQa+MzCkSId6F8m7b7n2SX6SUSPVIizOCngKa6mppYO1jODSPoLftNf7oGSw8Jo30PcWZew==',
            # 'source_type': '503',
            # 's_channel': 'program_wx',
            'Cookie': f"TOKENSID=TOKEN_{self.ck}; apkPkg=com.oppo.store"
        }

        try:
            # 发起抽奖请求
            response = requests.get(raffle_url, params=params, headers=headers)
            response.raise_for_status()

            raffle_data = json.loads(response.text)
            if raffle_data["code"] == 200:
                inspection_code = raffle_data.get("data", {}).get("inspectionQualification", {}).get("code")

                if inspection_code == 204:
                    self.set_log(
                        f"ℹ️ 第`{current_draw}/{total_draws}`次抽奖:`{raffle_data['data']['inspectionQualification']['msg']}`")
                    return False

                raffle_winner = raffle_data.get("data", {}).get("raffleWinnerVO", {})
                award_name = raffle_winner.get("exhibitAwardName", "未知奖品")

                self.set_log(f"🎉 第`{current_draw}/{total_draws}`次抽奖成功，获得: `{award_name}`")
                return True
            else:
                self.set_log(f"❌ 第`{current_draw}/{total_draws}`次抽奖失败: `{raffle_data.get('message', '未知错误')}`")
                return False

        except requests.exceptions.RequestException as e:
            self.set_log(f"💥 抽奖请求失败: {e}")
        except json.JSONDecodeError as e:
            self.set_log(f"💥 解析抽奖结果失败: {e}")
        except Exception as e:
            self.set_log(f"💥 抽奖过程中出现未预期的错误: {e}")

        return False

    # OPPO会员小程序签到
    def oppo_member_app_sign(self):
        # self.set_log("🤖运行了 oppo_member_app_sign")

        url = f"https://omoapplet-api-cn.heytap.com/activity/signIn/daily?sessionId={self.session_id}&version=2"

        headers = {
            'User-Agent': self.UA
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = json.loads(response.text)
            if data["ret"] == "1":
                # 签到成功
                integral = data.get("data", {}).get("integral", 0)
                self.set_log(f"\u2705 OPPO会员小程序签到成功，获得`{integral}`积分")
                return True
            elif data["ret"] == "0" and data.get("errCode") == "214000023":
                # 已经签到过
                self.set_log(f"➖ OPPO会员小程序今日已签到: {data.get('errMsg', '奖励已发放')}")
                return True
            else:
                self.set_log(f"❌ OPPO会员小程序签到失败: {data.get('errMsg', '未知错误')}")
                return False

        except requests.exceptions.RequestException as e:
            self.set_log(f"💥 OPPO会员小程序签到请求失败: {e}")
        except json.JSONDecodeError as e:
            self.set_log(f"💥 解析OPPO会员小程序签到结果失败: {e}")
        except Exception as e:
            self.set_log(f"💥 OPPO会员小程序签到过程中出现未预期的错误: {e}")

        return False

    # 统计今日积分收入
    def today_credits_summary(self):
        # self.set_log("🤖运行了 today_credits_summary")

        today = datetime.now().strftime("%Y-%m-%d")
        total_in = 0
        total_out = 0
        all_today_records = []

        # 初始化为空，第一次请求不带时间戳
        last_timestamp = ""

        # 使用循环获取所有分页数据，直到找到不是今天的记录
        page = 1
        has_more_today_data = True
        found_earlier_date = False

        while has_more_today_data and not found_earlier_date and page <= 10:  # 限制最多查询10页，避免无限循环
            # self.set_log(f"📑 正在获取第 {page} 页积分记录...")

            # 构建分页查询URL
            url_params = f"sessionId={self.session_id}&loadSize=15"
            if last_timestamp:
                url_params += f"&lastRecordTimeStamp={last_timestamp}"

            url = f"https://omoapplet-api-cn.heytap.com/point/creditsList?{url_params}"

            headers = {
                'User-Agent': self.UA
            }

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()

                data = json.loads(response.text)
                if data["ret"] == "1":
                    # 获取下一页的时间戳
                    last_timestamp = data.get("data", {}).get("lastRecordTimeStamp", "")

                    if not last_timestamp:
                        has_more_today_data = False  # 没有更多数据了

                    # 遍历积分组
                    today_records_in_page = []
                    for group in data.get("data", {}).get("groups", []):
                        for record in group.get("creditsList", []):
                            record_time = record.get("createTime", "")
                            record_date = record_time.split(" ")[0] if " " in record_time else ""

                            # 检查是否找到了不是今天的记录
                            if record_date and record_date != today:
                                found_earlier_date = True  # 找到了早于今天的记录，停止查询
                                break

                            # 只处理今天的数据
                            if record_date == today:
                                today_records_in_page.append(record)

                        if found_earlier_date:
                            break

                    # 如果当前页没有今天的记录，则停止查询
                    if not today_records_in_page:
                        has_more_today_data = False
                    else:
                        all_today_records.extend(today_records_in_page)

                    # 如果没有下一页数据，则停止查询
                    if not last_timestamp:
                        has_more_today_data = False

                else:
                    self.set_log(f"❌ 获取积分明细失败: {data.get('errMsg', '未知错误')}")
                    return False

            except requests.exceptions.RequestException as e:
                self.set_log(f"💥 获取积分明细请求失败: {e}")
                return False
            except json.JSONDecodeError as e:
                self.set_log(f"💥 解析积分明细结果失败: {e}")
                return False
            except Exception as e:
                self.set_log(f"💥 获取积分明细过程中出现未预期的错误: {e}")
                return False

            page += 1
            time.sleep(1)  # 添加间隔时间，避免请求过快

        # 处理所有今天的积分记录
        if all_today_records:
            # 获取总积分
            total_amount = data.get("data", {}).get("amount", 0)
            self.set_log(f"📊 当前积分总额:`{total_amount}`")
            self.set_log(f"📝 今日积分收支明细 (共`{len(all_today_records)}`条记录):")

            # 按时间从新到旧排序
            all_today_records.sort(key=lambda x: x.get("createTime", ""), reverse=True)

            # 统计和显示详情
            for record in all_today_records:
                amount = record.get("amount", 0)
                record_type = record.get("recordType", 0)  # 1为收入，2为支出
                description = record.get("description", "未知来源")
                record_time = record.get("createTime", "").split(" ")[1] if " " in record.get("createTime", "") else ""

                if record_type == 1:  # 收入
                    # self.set_log(f"➕ {record_time} +{amount} 积分: {description}")
                    total_in += amount
                elif record_type == 2:  # 支出
                    # self.set_log(f"➖ {record_time} -{amount} 积分: {description}")
                    total_out += amount

            # 显示统计结果
            self.set_log(f"\u2705 今日积分收入: `+{total_in}`")
            if total_out > 0:
                self.set_log(f"⚠️ 今日积分支出: `-{total_out}`")
            self.set_log(f"📈 今日积分净收入: `{total_in - total_out}`")

            return True
        else:
            self.set_log("ℹ️ 今日暂无积分收支记录")
            return True

    # 会员等级
    def membership_grade(self):
        # self.set_log("🤖运行了 membership_grade")
        url = "https://msec.opposhop.cn/users/web/memberCenter/getMemberExpDetail"
        payload = {}
        headers = {
            'Cookie': f"apkPkg={self.apkPkg}; TOKENSID=TOKEN_{self.ck}",
            'User-Agent': self.UA
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        # self.set_log("membership_grade", response.text)
        try:
            j = ujson.loads(response.text)
            if j["code"] == 200:
                gradeName = j['data']['gradeName']
                des = j['data']['des']
                self.set_log(f"🎖️会员等级：`{gradeName}({des})`")
        except (KeyError, ValueError):
            self.set_log(f"💥获取会员等级失败，解析响应数据出错，可能是登录已失效 {response.text} ")

    # 获取任务列表
    def get_task(self):
        # self.set_log("🤖运行了 get_task")
        # 如果任务活动ID列表为空，直接返回
        if not self.activityId_taskActivityInfo:
            return
        for task_activity in self.activityId_taskActivityInfo:
            url = f"https://hd.opposhop.cn/api/cn/oapi/marketing/task/queryTaskList?activityId={task_activity.activityId}&source=c"
            payload = {}
            headers = {
                'Cookie': f"apkPkg={task_activity.apkPkg}; TOKENSID=TOKEN_{self.ck}",
                'Accept': 'application/json, text/plain, */*',
                's_channel': task_activity.s_channel,
                'source_type': str(task_activity.business),
                'User-Agent': self.UA
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            # self.set_log("get_task", response.text)
            try:
                j = ujson.loads(response.text)
                if j["code"] == 200:
                    # self.set_log(f"🤓👆🏻获取任务列表成功")
                    activity_name = j["data"]["activityName"]
                    # 更新活动名称，如果API返回的名称不为空
                    if activity_name and activity_name.strip():
                        task_activity.activityName = activity_name

                    self.set_log(f"⏩正在执行任务列表：`{task_activity.activityName}`")
                    for i, element in enumerate(j["data"]["taskDTOList"]):
                        taskName = element['taskName']
                        taskId = element['taskId']
                        activityId = element['activityId']
                        taskType = element['taskType']  # 1=浏览，4=预约， 6=开卡/购买
                        taskStatus = element['taskStatus']  # 是否完成 1=未完成，2=可领取，3=已领取
                        skuId = ''
                        if element['attachConfigTwo']:
                            attachConfigTwo_link = element['attachConfigTwo']['link']
                            match = re.search(r'skuId=(\d+)', attachConfigTwo_link)
                            if match:
                                skuId = match.group(1)

                        # self.set_log(f"🤓👆🏻获取到任务：{taskName}，任务ID：{taskId}，活动ID：{activityId}，任务类型：{taskType}，任务状态：{taskStatus}，skuId：{skuId}")
                        if taskStatus == 1:  # 未完成
                            self.set_log(f"🤓👆🏻`{taskName}` 任务还未完成，即将执行：")
                            # 这里写判断类型，并进行相应的操作
                            if taskType in [1, 3, 9, 16, 17]:  # 经典提交任务即可领取奖励类型
                                self.task_signInOrShareTask(taskName, taskId, activityId)
                            elif taskType in [4, 5, 6, 10]:  # 预约任务
                                # self.set_log(f"skuId={skuId}")
                                self.subscribes(skuId, taskName, taskId, activityId)
                            elif taskType in [23]:  # 打开通知任务
                                self.PushSwitch(activityId, False)  # 关闭通知
                                self.PushSwitch(activityId, True)  # 打开通知
                                self.task_receiveAward(taskName, taskId, activityId)  # 领取奖励
                            elif taskType in [18]:  # 内容点赞
                                self.thumbsupList()  # 点赞
                                self.task_receiveAward(taskName, taskId, activityId)  # 领取奖励
                            else:
                                self.set_log(
                                    f"❌`{taskName}`任务执行失败，未分配类型：{taskType}:{element['taskTypeName']}")
                        elif taskStatus == 2:
                            self.set_log(f"⏬`{taskName}`任务已完成，即将领取奖励：")
                            self.task_receiveAward(taskName, taskId, activityId)
                        elif taskStatus == 3:
                            self.set_log(f"➖`{taskName}`任务已完成，无需再执行签到。")
                            # 等待完善输出逻辑
                        elif taskStatus == 6:
                            self.set_log(f"➖`{taskName}`任务已领光。")
                        else:
                            self.set_log(f"❌`{taskName}`任务状态未知")
                        time.sleep(2)
                else:
                    self.set_log(f"⚠️获取任务列表失败，`{j['message']}`")
            except (KeyError, ValueError):
                self.set_log(f"💥获取任务列表失败，解析响应数据出错，可能是登录已失效 {response.text} ")

    # 提交任务
    def task_signInOrShareTask(self, taskName, taskId, activityId):
        # self.set_log("🤖运行了 task_signInOrShareTask")
        url = f"https://hd.opposhop.cn/api/cn/oapi/marketing/taskReport/signInOrShareTask?taskId={taskId}&activityId={activityId}&taskType=1"
        payload = {}
        headers = {
            'Cookie': f"apkPkg={self.apkPkg}; TOKENSID=TOKEN_{self.ck}",
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': self.UA
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        # self.set_log("task_signInOrShareTask", response.text)
        try:
            j = ujson.loads(response.text)
            if j["code"] == 200:
                self.task_receiveAward(taskName, taskId, activityId)
            else:
                message = j['message']
                self.set_log(f"❌{taskName} 任务提交失败，{message}")
        except (KeyError, ValueError):
            self.set_log(f"💥{taskName} 任务提交失败，解析响应数据出错，可能是登录已失效 {response.text} ")

    # 领取任务奖励
    def task_receiveAward(self, taskName, taskId, activityId):
        # self.set_log("🤖运行了 task_receiveAward")
        url = f"https://hd.opposhop.cn/api/cn/oapi/marketing/task/receiveAward?taskId={taskId}&activityId={activityId}"
        payload = {}
        headers = {
            'Cookie': f"apkPkg={self.apkPkg}; TOKENSID=TOKEN_{self.ck}",
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': self.UA
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        # self.set_log("task_receiveAward", response.text)
        try:
            j = ujson.loads(response.text)
            if j["code"] == 200:
                awardType = j['data']['awardType']
                awardValue = j['data']['awardType']
                if awardType == 1:
                    self.set_log(f"🎉`{taskName}`任务完成，奖励`{awardValue}`积分")
            else:
                self.set_log(f"❌`{taskName}`任务失败，`{j['message']}`")
        except (KeyError, ValueError):
            self.set_log(f"💥`{taskName}` 任务失败，解析响应数据出错，可能是登录已失效： {response.text} ")

    # 预约任务
    def subscribes(self, skuId, taskName, taskId, activityId):
        # self.set_log("🤖运行了 subscribes")
        url = "https://msec.opposhop.cn/goods/web/subscribes/goodsSubscribeV1"
        payload = f"type=1&skuId={skuId}"
        headers = {
            'Cookie': f"apkPkg={self.apkPkg}; TOKENSID=TOKEN_{self.ck}",
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'okhttp/4.9.3.6'
        }
        response = requests.post(url, data=payload, headers=headers)
        # response = requests.request("POST", url, headers=headers, data=payload)
        # self.set_log("subscribes", response.text)
        j = ujson.loads(response.text)
        if j["code"] == 200:
            self.task_receiveAward(taskName, taskId, activityId)
        else:
            message = j['errorMessage']
            self.set_log(f"❌{taskName} 预约失败，{message}")

    # 打开通知
    def PushSwitch(self, activityId, Switch):
        # self.set_log("🤖运行了 PushSwitch")

        url = f"https://hd.opposhop.cn/api/cn/oapi/marketing/userEvent/openPushSwitch?activityId={activityId}&eventType={5 if Switch else 4}"
        headers = {
            'User-Agent': self.UA,
            'Accept': "application/json, text/plain, */*",
            'Cookie': f"apkPkg={self.apkPkg}; TOKENSID=TOKEN_{self.ck}"
        }
        response = requests.get(url, headers=headers)
        try:
            j = ujson.loads(response.text)
            self.set_log(f"{'✅打开' if Switch else '关闭'}通知权限：`{j['message']}`")
        except (KeyError, ValueError):
            self.set_log(f"💥签到失败，解析响应数据出错 {response.text} ")

    # 获取点赞列表
    def thumbsupList(self):
        # self.set_log("🤖运行了 thumbsupList")
        url = "https://hd.opposhop.cn/api/cn/oapi/java/ugc/frontend/hot/thread/v1/list?contentId=30&viewType=2&dataType=2&limit=10&page=1"

        headers = {
            'User-Agent': self.UA,
            'Accept': "application/json, text/plain, */*",
            'sa_distinct_id': "MEZ5RTA0N2REY3BWcXBZdmxSSzQ5QT09, MEZ5RTA0N2REY3BWcXBZdmxSSzQ5QT09",
            'Cookie': f"apkPkg=com.oppo.community; TOKENSID=TOKEN_{self.ck}"
        }

        response = requests.get(url, headers=headers)

        try:
            j = ujson.loads(response.text)
            if j["code"] == 200:
                # self.set_log("\u2705获取点赞列表成功")
                for row in j["data"]["rows"]:
                    tid = row["threadBaseInfoVO"]["tid"]
                    uid = row["author"]["uid"]
                    praise_status = row["praiseStatus"]
                    # self.set_log(f"⏩准备点赞帖子 tid: {tid}, uid: {uid}")
                    self.thumbsup(tid, uid)
                    if praise_status != 0:  # 0 表示未点赞
                        # self.set_log(f"\u2705帖子 tid: {tid} 已点赞，正在取消并再次签到")
                        self.thumbsup(tid, uid)
            else:
                self.set_log(f"❌获取点赞列表失败，{j['msg']}")
        except (KeyError, ValueError):
            self.set_log(f"💥获取点赞列表失败，解析响应数据出错 {response.text} ")

    # 点赞
    def thumbsup(self, tid, uid):
        # self.set_log("🤖运行了 thumbsup")
        url = "https://hd.opposhop.cn/api/cn/oapi/java/ugc/frontend/praise/thread"
        payload = {
            'tid': tid,
            'uid': uid
        }
        headers = {
            'User-Agent': self.UA,
            'Cookie': f"apkPkg=com.oppo.community; TOKENSID=TOKEN_{self.ck}",
        }
        response = requests.post(url, data=payload, headers=headers)
        try:
            j = ujson.loads(response.text)
            if j["code"] == 200:
                self.set_log(f"🎉帖子 tid: {tid} ： {j['msg']}")
            else:
                self.set_log(f"❌帖子 tid: {tid} 点赞失败，{j['msg']}")
        except (KeyError, ValueError):
            self.set_log(f"💥帖子 tid: {tid} 点赞失败，解析响应数据出错 {response.text} ")

    # 钱包签到
    def continueSign(self):
        # self.set_log("🤖运行了 continueSign")
        url = "https://hwallet.finzfin.com/act/usersign/v1/continueSign"

        payload = ujson.dumps({
            "actId": "AID202207111442220933",
            "funcId": "CONTINUEV2202209161649037309"
        })

        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 15; PJD110 Build/AP3A.240617.008; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.58 Mobile Safari/537.36;webank/h5face;webank/2.0 JSBridge/1 wallet/5.37.5_a921687_250522 FinshellWebSDK/4.0.0.18",
            'Accept': "application/json;charset=UTF-8",
            'Content-Type': "application/json",
            'x-token': f"TOKEN_{self.ck}",
        }

        response = requests.post(url, data=payload, headers=headers)
        # response = requests.request("POST", url, headers=headers, data=payload)
        # self.set_log("continueSign", response.text)
        try:
            j = ujson.loads(response.text)
            if j.get("success"):
                award_name = j["data"]["name"]
                self.set_log(f"🎉签到成功，获得`{award_name}`")
            else:
                error_msg = j["error"]["msg"]
                self.set_log(f"❌签到失败，`{error_msg}`")
        except (KeyError, ValueError):
            self.set_log(f"💥签到失败，解析响应数据出错 {response.text} ")

    # 一加论坛签到
    def bbsSign(self):
        # self.set_log("🤖运行了 bbsSign")
        url = "https://bbs-api-cn.oneplus.com/task/api/sign/v1/create"
        params = {
            'ver': "bbs44102",
            'timestamp': int(round(time.time() * 1000)),
            # 'sign': "9ca3735c9d81a55663e6659b282afadb1b9dea4595cd4fedb3597c7f57a1c9ef"
        }
        headers = {
            'User-Agent': "bbs/android/bbs44102",
            'Accept-Encoding': "gzip",
            'model': "PJD110",
            'osver': "android15",
            'romv': "PJD110_15.0.0.701(CN01)",
            'lang': "zh-CN",
            'token': f"TOKEN_{self.ck}",
            'tz': "Asia/Shanghai"
        }
        response = requests.post(url, params=params, headers=headers)
        # self.set_log(response.text)
        try:
            j = ujson.loads(response.text)
            if j["code"] == 200:
                if 'todaySigned' in j["data"]:
                    self.set_log('➖今天已经签到过啦！')
                else:
                    self.set_log('🎉`今天签到成功！`')
                self.set_log('📝累计签到：`' + str(j['data']['signDays']) + '`天')
                self.set_log('📝连续签到：`' + str(j['data']['continuousSignDays']) + '`天')
                self.set_log('📝再连续签到`' + str(j['data']['extSignDays']) + '`天，可额外获得' + str(
                    j['data']['extCredit']) + '积分')
            else:
                self.set_log(f"❌一加论坛签到失败，`{j['msg']}`")
        except (KeyError, ValueError):
            self.set_log(f"💥一加论坛签到失败，解析响应数据出错{response.text}")

    #  阅读签到
    def zhangyueSign(self):
        # self.set_log("🤖运行了 zhangyueSign")

        url = "https://webboot.zhangyue.com/zycl/newwelfare/sign?usr=i4791337318"

        headers = {
            'User-Agent': self.UA,
        }

        response = requests.get(url, headers=headers)

        try:
            j = ujson.loads(response.text)
            if j["code"] == 0:
                # 签到成功，返回 signTitle 的结果
                self.set_log(f'🎉`{j["body"]["signTitle"]}`')
            else:
                # 其他错误情况
                self.set_log(f"➖阅读签到失败：`{j['msg']}`")
        except (KeyError, ValueError):
            self.set_log(f"💥阅读签到失败，解析响应数据出错{response.text}")

    # 新增日志
    def set_log(self, text):
        print(text)
        self.Log = self.Log + "\n" + text

    # 获取日志
    def get_log(self):
        # return self.Log.replace("\n","\r\n")
        return self.Log.replace("\n","\n\n") # 用于适配markdown格式输出
        # return self.Log

    # token检测
    def tokenCheck(self):
        # self.set_log("🤖正在检测token合法性.......")
        try:
            # 分割JWT的三个部分
            parts = (self.ck.split('.'))
            if len(parts) != 3:
                self.set_log("⚠️输入的token有误，请检查token后进行重试")
                return False
                # 解码载荷
            payload = json.loads(
                base64.b64decode(
                    (parts[1] +
                     ('=' * (4 - (len(parts[1]) % 4)))).
                    replace('-', '+').
                    replace('_', '/')
                ))
            if payload:
                # 解析并格式化exp字段
                if 'exp' in payload:
                    current_time = datetime.now().timestamp()
                    token_exp_time = payload['exp'] / 1000 if payload['exp'] > 1000000000000 else payload['exp']

                    # 检查token是否已过期
                    if token_exp_time < current_time:
                        self.set_log("⚠️token已过期，请更新token")
                        return False

                    endReflashTime = (datetime
                                      .fromtimestamp(token_exp_time)
                                      .astimezone()
                                      .strftime('%Y-%m-%d %H:%M:%S %Z'))
                    self.set_log(f"📆该token有效期至：`{endReflashTime}`")
                    return True
                else:
                    self.set_log("⚠️token格式异常，未找到过期时间")
                    return False
            else:
                self.set_log("⚠️token载荷解析失败")
                return False
        except Exception as e:
            self.set_log(f"💥解析JWT时出错: {e}")
            return False

    # 运行列表
    def run(self):
        # 1. 优先读取环境变量
        OPPO_COOKIE = os.getenv("OPPO_COOKIE")
        if not OPPO_COOKIE:
            self.set_log("⚠️读取环境变量配置失败，正在读取本地文件。")
            # 2. 尝试读取本地oppoConfig.json
            try:
                with open('sjmyConfig.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "OPPO_COOKIE" in config:
                        OPPO_COOKIE = config["OPPO_COOKIE"]
            except Exception:
                self.set_log('⚠️读取本地文件`OPPO_COOKIE`失败')
                exit()
            if not OPPO_COOKIE:
                notify.send("OPPO_COOKIE", '🙃`OPPO_COOKIE` 变量未设置')
                self.set_log('⚠️OPPO_COOKIE 变量未设置')
                exit()
        self.set_log('\u2705`OPPO_COOKIE` 变量读取成功')
        # 初始化活动列表（如果还没有初始化）
        if not hasattr(self, 'activity_list') or self.activity_list is None:
            self.activity_list = []

        # 初始化任务活动列表
        self.activityId_taskActivityInfo.extend([
            ActivityInfo(  # 我的一加应用内签到任务
                '做任务赚积分-MYOPPO客户端（25年5月）',
                'com.oneplus.member',
                '1906916561005060096',
                "",
                502,
                'jfstore'
            ),
            ActivityInfo(  # OPPO社区APP里的任务
                '【社区签到】任务中心（25年1-7月）',
                'com.oppo.community',
                '1872557968655130624',
                "",
                506,
                'oppo_community'
            ),
            ActivityInfo(  # OPPO商城微信小程序里的任务
                '25年07月小程序签到任务',
                'com.oppo.store',
                '1937073820783616000',
                "",
                503,
                'program_wx'
            ),
            ActivityInfo(  # OPPO商城APP内签到任务
                '【商城签到】任务中心（25年1-7月）',
                'com.oppo.store',
                '1872557850459643904',
                "",
                501,
                'oppo_appstore'
            )
        ])

        self.activity_list.extend([
            ActivityInfo("我的一加 APP",
                         'com.oneplus.member',
                         "1939610017808523264",
                         "ed4d8b155251413a982577737cd41b4f",
                         2,
                         'jfstore'),
            ActivityInfo("OPPO商城 APP",
                         'com.oppo.store',
                         "1938150025645531136",
                         "1788913e6d9e4683b8b9ab0088733560",
                         1,
                         'oppo_appstore'),
            ActivityInfo("OPPO商城-微信小程序",
                         'com.oppo.store',
                         "1937045637514403840",
                         "1788913e6d9e4683b8b9ab0088733560",
                         1,
                         'program_wx'),
            ActivityInfo("OPPO社区 APP",
                         'com.oppo.community',
                         "1938143899864539136",
                         "1788913e6d9e4683b8b9ab0088733560",
                         1,
                         'oppo_community')
        ])

        ck_list = OPPO_COOKIE.split('&')
        self.set_log(f"---------共`{str(int(len(ck_list)))}`个账号---------")
        for tokens in ck_list:
            if int(len(ck_list)) > 1:
                self.set_log(f"\n---------第`{ck_list.index(tokens) + 1}`个账号---------")
            my_token = tokens.split('#')
            if my_token == '' or int(len(my_token)) != 2:
                self.set_log("⚠️账号格式有误，请检查账号后进行重试")
                continue
            # try:
            self.ck = my_token[0]
            self.session_id = my_token[1]
            self.set_log(f"\n---------账号Token合法性检测开始处理---------")
            # 检测token是否合法，如果不合法则跳过此账号
            if not self.tokenCheck():
                self.set_log("⚠️Token不合法，跳过此账号")
                continue
            self.set_log("\n---------一加论坛---------")
            self.bbsSign()  # 一加论坛签到
            self.set_log("\n---------钱包任务---------")
            self.continueSign()  # 钱包签到
            self.set_log("\n----------阅读----------")
            self.zhangyueSign()  # 阅读签到
            self.set_log("\n---------活动列表---------")
            self.get_activityId()  # 获取签到标识，同时添加动态获取的活动到activity_list
            if self.session_id != "":
                self.set_log("\n-----OPPO会员小程序签到-----")
                self.oppo_member_app_sign()  # OPPO会员小程序签到
            self.set_log("\n--------各渠道签到--------")
            self.shopping_signIn()  # 执行签到，包括原有活动ID和activity_list中的活动
            self.set_log("\n--------累计签到奖励--------")
            for activity in self.activity_list:  # 使用专门地累计签到列表
                self.check_cumulative_sign_in(activity)  # 检查累计签到奖励并领取
            self.set_log("\n------各渠道小任务签到------")
            self.get_task()  # 获取任务列表
            self.set_log("\n-----OPPO商城小程序抽奖-----")
            self.do_raffle()  # 执行抽奖
            if self.session_id != "":
                self.set_log("\n------今日积分收入统计------")
                self.today_credits_summary()  # 今日积分收入统计
            self.set_log("\n---------会员等级---------")
            self.membership_grade()  # 会员等级
            self.set_log("\n---------积分额度---------")
            self.integral_query()  # 积分额度查询
            self.set_log("\n--------积分过期情况--------")
            self.check_expire_credits()  # 积分过期情况查询
            #
            # print(self.get_log())

            notify.send("OPPO签到", self.get_log())
            # except Exception as e:
            # self.set_log("💥出错了！详细错误👇错误CK👉" + mt_token)
            # self.set_log(e)
            # notify.send("OPPO", "出错了！详细错误👇错误CK👉" + mt_token +"\n错误内容:" + str(e))


if __name__ == '__main__':
    oppoRun = OPPO()
    oppoRun.run()