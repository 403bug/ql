# ✅ 当前脚本的绝对路径：/ql/data/scripts/1.swap.py
# ✅ 当前脚本所在目录：/ql/data/scripts

import json
import os

import requests

import notify

log = ''


def set_log(message):
  global log
  log += message + '\n'
  print(message)


def send_log():
  notify.send("zhytConfig成绩查询", log)


origin_exit = exit


def exit():
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

  return requests.post(url, data=json.dumps(payload), headers=headers).json()


def load_local_score(xh):
  config_path = 'sjmyConfig.json'
  if not os.path.exists(config_path):
    return []
  try:
    with open(config_path, 'r', encoding='utf-8') as f:
      config = json.load(f)
      return config.get('score', {}).get(str(xh), [])
  except:
    return []


def compare_and_notify(xh, new_score_list):
  old_score_list = load_local_score(xh)
  old_keys = {(s['kcmc'], s['quarter'], s['jsxm']) for s in old_score_list}
  new_keys = {(s['kcmc'], s['quarter'], s['jsxm']) for s in new_score_list}

  added = [s for s in new_score_list if (s['kcmc'], s['quarter'], s['jsxm']) not in old_keys]

  if added:
    msg = f"学号 {xh} 发现 {len(added)} 条新成绩：\n"
    for s in added:
      msg += f"• {s['kcmc']} ({s['quarter']}) - {s['jsxm']}: {s['cj']}\n"
    notify.send("成绩更新通知", msg)
    set_log(f"✅ 已发送新成绩通知：{len(added)} 条")
  else:
    set_log(f"ℹ️ 学号 {xh} 无新成绩")


def save_score_to_config(xh, score_list):
  config_path = 'sjmyConfig.json'
  config_data = {}

  if os.path.exists(config_path):
    try:
      with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    except Exception:
      set_log('⚠️读取本地文件`sjmyConfig.json`失败，将创建新文件')
      config_data = {}

  if 'score' not in config_data or not isinstance(config_data['score'], dict):
    config_data['score'] = {}

  config_data['score'][str(xh)] = score_list

  try:
    with open(config_path, 'w', encoding='utf-8') as f:
      json.dump(config_data, f, ensure_ascii=False, indent=2)
    set_log(f'✅已保存学号 {xh} 的成绩到本地配置文件')
  except Exception as e:
    set_log(f'⚠️保存成绩到本地配置文件失败: {e}')


zhytConfig = os.getenv("zhytConfig")

if not zhytConfig:
  set_log("⚠️读取环境变量配置失败，正在读取本地文件。")
  try:
    with open('sjmyConfig.json', 'r', encoding='utf-8') as f:
      config = json.load(f)
      if "zhytConfig" in config:
        zhytConfig = config["zhytConfig"]
  except Exception:
    set_log('⚠️读取本地文件`zhytConfig`失败')
    exit()
  if not zhytConfig:
    notify.send("zhytConfig", '🙃`zhytConfig` 变量未设置')
    set_log('⚠zhytConfig 变量未设置')
    exit()
set_log('\u2705`zhytConfig` 变量读取成功')

config = zhytConfig.split('&')
if len(config) != 2:
  notify.send("zhytConfig", '🙃`zhytConfig` 变量格式错误')
  set_log('⚠zhytConfig 变量格式错误')
else:
  Authorization = config[0]
  xhList = config[1].split('|')
  for xh in xhList:
    response = getScore(xh, Authorization)
    if 'xh' in response:
      set_log(f"学号: {response['xh']}"
              f"\n姓名: {response['xm']}")
      studentScoreInfos = response['studentScoreInfos']

      score_list = []
      for scoreInfo in studentScoreInfos:
        score_entry = {
          "kcmc": scoreInfo['kcmc'],
          "quarter": scoreInfo.get('quarter', ''),
          "jsxm": scoreInfo['jsxm'],
          "ksxz": scoreInfo['ksxz'],
          "kcxzmc": scoreInfo['kcxzmc'],
          "xf": scoreInfo['xf'],
          "jd": scoreInfo['jd'],
          "cj": scoreInfo['cj']
        }
        score_list.append(score_entry)

        set_log(
          f"\n课程名称: {scoreInfo['kcmc']}-{scoreInfo['kcxzmc']}-{scoreInfo['ksxz']}"
          f"\n成绩: {scoreInfo['cj']}"
          f"\n学分: {scoreInfo['xf']}"
          f"\n绩点: {scoreInfo['jd']}"
          f"\n教师: {scoreInfo['jsxm']}")

      # 对比并通知新增成绩
      compare_and_notify(xh, score_list)

      # 保存最新成绩到本地
      save_score_to_config(xh, score_list)

    else:
      set_log(f"查询学号 {xh} 失败，错误信息：{response}")
