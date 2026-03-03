# ✅ 当前脚本的绝对路径：/ql/data/scripts/1.swap.py
# ✅ 当前脚本所在目录：/ql/data/scripts

import json
import os

import requests
import time


import notify

log = ''
Title = ''

def set_log(message):
  global log
  log += message + '\n'
  print(message)


def send_log():
  notify.send(Title, log)


origin_exit = exit


def exit(message=''):
  set_log(message)
  send_log()
  origin_exit()


def getScore(xh, Authorization):
  url = "http://183.64.130.31:8899/score-api/student-score"

  payload = {
    "xh": xh,
    "quarter": ""
  }

  headers = {
    'Host': "183.64.130.31:8899",
    'User-Agent': "Mozilla/5.0 (Linux; Android 16; PJD110 Build/BP2A.250605.015; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/143.0.7499.34 Mobile Safari/537.36 AXINFU2.0 YhkjApp/V6.3.05",
    'Content-Type': "application/json",
    'Authorization': f"Bearer {Authorization}"
  }

  return (requests.post(
    url,
    data=json.dumps(payload),
    headers=headers
  ).json())


def getHistoryScores():
  config_path = 'sjmyConfig.json'
  if not os.path.exists(config_path):
    return {}
  try:
    with open(config_path, 'r', encoding='utf-8') as f:
      config = json.load(f)
      return config.get('historyScores', {})
  except:
    return {}

def update_history_scores(new_history_scores):
  config_path = 'sjmyConfig.json'
  # 1. 读取原有配置文件（保留其他属性）
  if not os.path.exists(config_path):
    print(f"❌ 配置文件不存在，创建默认配置：{config_path}")
    # 若文件不存在，初始化默认结构
    default_config = {
      "historyScores": {}
    }
    with open(config_path, "w", encoding="utf-8") as f:
      json.dump(default_config, f, indent=2, ensure_ascii=False)
    config = default_config
  else:
    with open(config_path, "r", encoding="utf-8") as f:
      config = json.load(f)  # 读取为字典对象

  # 2. 仅修改 historyScores，其他属性完全保留
  config["historyScores"] = new_history_scores  # 直接赋值新对象

  # 3. 写回配置文件（保留原格式，不改动其他属性）
  with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

  set_log("✅ historyScores 修改完成！")
  # 验证结果：打印修改后的完整配置
  # print("修改后配置：")
  # print(json.dumps(config, indent=2, ensure_ascii=False))

hasNewScore = False
isSend = False
zhytConfig = os.getenv("zhytConfig")

if not zhytConfig:
  set_log("⚠️读取环境变量配置失败，正在读取本地文件。")
  # 2. 尝试读取本地sjmyConfig.json
  try:
    with open('sjmyConfig.json', 'r', encoding='utf-8') as f:
      config = json.load(f)
      if "zhytConfig" in config:
        zhytConfig = config["zhytConfig"]
  except Exception:
    exit('⚠️读取本地文件`zhytConfig`失败')
  if not zhytConfig:
    exit('⚠zhytConfig 变量未设置')
set_log('\u2705`zhytConfig` 变量读取成功')

config = zhytConfig.split('&')
if len(config) != 2:
  exit('⚠zhytConfig 变量格式错误')
else:
  Authorization = config[0]
  xhList = config[1].split('|')
  historyScore = getHistoryScores()
  # print("历史记录:", historyScore)
  for xh in xhList:
    response = getScore(xh, Authorization)
    if f"{xh}" in historyScore:
      myHistoryScores = [f"{s['kcmc']}-{s['cj']}" for s in historyScore[xh]]
    else:
      myHistoryScores = []
    set_log(f"\n======== 查询 {response['xh']}-{response['xm']} 成绩 ========")
    # print(myHistoryScores)
    if 'xh' in response:
      scoreInfos = response['studentScoreInfos']
      historyTimestamp = historyScore["timestamp"]
      isSend = int(time.time()) - historyTimestamp >= 84600
      total_xf,total_jd =[0,0]
      # 遍历每一条获取到的成绩记录
      for s in scoreInfos:
        scoreKey = f"{s['kcmc']}-{s['cj']}" # 课程名称-成绩 作为唯一标识
        isNew = scoreKey not in myHistoryScores
        isPass = float(s['cj']) >= 60
        set_log(f"\n<span style='color: {'#56D18B' if isPass else '#FC6189'};\'>"
                f"课程名称: {'🆕'if isNew else ''}{s['kcmc']}-{s['kcxzmc']}-{s['ksxz']}<br/>"
                f"\n成绩: {'✅' if isPass else '❌'}{s['cj']}<br/>"
                f"\n学分: {s['xf']}<br/>"
                f"\n绩点: {s['jd']}<br/>"
                f"\n教师: {s['jsxm']}<br/>"
                f"</span><br/>")
        # 累加学分和绩点
        total_xf += float(s['xf'])
        total_jd += float(s['jd'])
        # 更新历史成绩
        if isNew:
          hasNewScore = True
          historyScore.setdefault(xh, []).append(s)
          # print("没有成绩历史记录，发送通知")
          # print(historyScore)
        else:
          print(f"课程 {s['kcmc']} 成绩 {s['cj']} 已记录，跳过通知。")
      # 统计绩点
      gpa = total_jd / len(scoreInfos)
      set_log(f"\n总学分: {total_xf}<br/>"
              f"\n总绩点: {total_jd}<br/>"
              f"\n平均绩点: {gpa:.2f}<br/>")
    else:
      set_log(f"查询学号 {xh} 失败，错误信息：{response}")
  set_log("===============成绩查询完成================")
  if isSend:
    historyScore["timestamp"] = int(time.time())
  # 更新所有学号的历史成绩记录
  if hasNewScore or isSend:
    update_history_scores(historyScore)
    if hasNewScore: Title = '成绩更新'
    else: Title = '成绩查询'

    exit("\n✅成绩查询完成")
