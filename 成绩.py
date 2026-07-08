# ✅ 当前脚本的绝对路径：/ql/data/scripts/1.swap.py
# ✅ 当前脚本所在目录：/ql/data/scripts

import json
import os
import requests
import time
import notify

config_path = 'sjmyConfig.json'
logs = [{
  'Title' : '',
  'message' : ''
}]
zhytConfig=''
history_scores = {}
def add_log(index, message = None, title=None):
  global logs
  if index >= len(logs):
    logs.append({
      'Title' : title or '',
      'message' : message or ''
    })
  if title: logs[index]['Title'] = title
  if message:
    logs[index]['message'] += message + '\n'
    print(message)

def send_log(index=None,title = None, is_final=False):
  global send_count
  # 最后的总结不受限制，一定要发送
  if is_final:
    all_title = title or '成绩查询汇总'
    all_message = ''
    for log in logs:
      all_message += f"<hr/><h1>{log['Title']}</h1>{log['message']}"
    notify.send(all_title, all_message)
    return
  # 检查是否超过最大发送次数
  if send_count >= MAX_SEND_COUNT:
    print(f"⚠️ 已达到最大发送次数 {MAX_SEND_COUNT}，跳过本次通知")
    return
  if index is not None:
    notify.send(logs[index]['Title'], logs[index]['message'])
    send_count += 1
  else:
    all_title = title or '成绩查询汇总'
    all_message = ''
    for log in logs:
      all_message += f"<hr/><h1>{log['Title']}</h1>{log['message']}"
    notify.send(all_title, all_message)
    send_count += 1

origin_exit = exit

def exit(message='', title=None):
  add_log(-1,message)
  send_log(title=title, is_final=True)
  origin_exit()
# 读取配置文件
def init_data_from_config():
  global zhytConfig,history_scores
  zhytConfig = os.getenv("zhytConfig")
  try:
    if not os.path.exists(config_path):
      print(f"❌ 配置文件不存在，创建默认配置：{config_path}")
      # 若文件不存在，初始化默认结构
      default_history_scores = {
        "historyScores": {}
      }
      with open(config_path, "w", encoding="utf-8") as f:
        json.dump(default_history_scores, f, indent=2, ensure_ascii=False)
      history_scores = {}
    else:
      with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        if not zhytConfig:
          add_log(0, "⚠️读取环境变量配置失败，正在读取本地文件。")
          if "zhytConfig" in config:
            zhytConfig = config["zhytConfig"]
          else:
            exit('⚠本地配置文件里也不存在 zhytConfig 信息,请检查本地配置后重试!')
        history_scores = config.get("historyScores",{})
        add_log(0,'✅`zhytConfig` 变量读取成功')
  except:
    exit('⚠️读取本地文件`zhytConfig`失败')

def update_history_scores(new_history_scores):
  config_data = {
      "historyScores": {}
  }
  # 1. 读取原有配置文件（保留其他属性）
  if not os.path.exists(config_path):
    print(f"❌ 配置文件不存在，创建默认配置：{config_path}")
    # 若文件不存在，初始化默认结构
    default_history_scores = {
      "historyScores": {}
    }
    with open(config_path, "w", encoding="utf-8") as f:
      json.dump(default_history_scores, f, indent=2, ensure_ascii=False)
    config_data = default_history_scores
  else:
    with open(config_path, "r", encoding="utf-8") as f:
      config_data = json.load(f)  # 读取为字典对象

  # 2. 仅修改 historyScores，其他属性完全保留
  config_data["historyScores"] = new_history_scores  # 直接赋值新对象

  # 3. 写回配置文件（保留原格式，不改动其他属性）
  with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config_data, f, indent=2, ensure_ascii=False)

  add_log(-1,"✅ historyScores 修改完成！")
  # 验证结果：打印修改后的完整配置
  # print("修改后配置：")
  # print(json.dumps(config, indent=2, ensure_ascii=False))


def get_score(xh):
  global Authorization
  return requests.post(
    "http://183.64.130.31:8899/score-api/student-score",
    data=json.dumps({
      "xh": xh,
      "quarter": "2025-2026学年 第2学期"
    }),
    headers={
      'Host': "183.64.130.31:8899",
      'User-Agent': "Mozilla/5.0 (Linux; Android 16; PJD110 Build/BP2A.250605.015; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/143.0.7499.34 Mobile Safari/537.36 AXINFU2.0 YhkjApp/V6.3.05",
      'Content-Type': "application/json",
      'Authorization': f"Bearer {Authorization}"
    }
  ).json()

globals_hasNewScore = False
send_count = 0  # 发送次数计数器
MAX_SEND_COUNT = 4  # 最大发送次数
# 初始化配置信息
init_data_from_config()
# 解析配置
config = zhytConfig.split('&')
if len(config) != 2:
  exit('⚠zhytConfig 变量格式错误')
else:
  Authorization = config[0]
  xhList = config[1].split('|')
  last_push_time= history_scores.get("timestamp",1420070400)

  for xh in xhList:
    # 添加新的log组
    index = len(logs)
    add_log(index,title=f'{xh}成绩查询')
    hasNewScore = False # 是否存在新的成绩,用于推送判断
    name = ''
    try:
      response = get_score(xh)
      print(response)
      if f"{xh}" in history_scores:
        myHistoryScores = [f"{s['kcmc']}-{s['cj']}" for s in history_scores[xh]]
      else:
        myHistoryScores = []
      # print(myHistoryScores)
      if 'xh' in response:
        # 返回正常数据
        scoreInfos = response['studentScoreInfos']
        name = response.get("xm",'')
        add_log(index, title=f'{name}-{xh}')
        total_xf,total_jd =[0,0]
        # 遍历每一条获取到的成绩记录
        for s in scoreInfos:
          scoreKey = f"{s['kcmc']}-{s['cj']}" # 课程名称-成绩 作为唯一标识
          isNew = scoreKey not in myHistoryScores
          isPass = float(s['cj']) >= 60
          add_log(index,f"\n<span style='color: {'#56D18B' if isPass else '#FC6189'};\'>"
                  f"课程名称: {'🆕'if isNew else ''}{s['kcmc']}-{s['kcxzmc']}-{s['ksxz']}<br/>"
                  f"\n成绩: {'✅' if isPass else '❌'}{s['cj']}<br/>"
                  f"\n学分: {s['xf']}<br/>"
                  f"\n绩点: {s['jd']}<br/>"
                  # f"\n教师: {s['jsxm']}<br/>"
                  f"</span><br/>")
          # 累加学分和绩点
          total_xf += float(s['xf'])
          total_jd += float(s['jd'])
          # 更新历史成绩
          if isNew:
            hasNewScore = True
            globals_hasNewScore = True
            history_scores.setdefault(xh,[]).append(s)
            print(f"查询到新记录:课程 {s['kcmc']} 成绩 {s['cj']}。")
            # print("没有成绩历史记录，发送通知")
            # print(historyScore)
          else:
            print(f"课程 {s['kcmc']} 成绩 {s['cj']} 已记录，跳过通知。")
        # 统计绩点
        gpa = total_jd / len(scoreInfos)
        add_log(index,f"\n总学分: {total_xf}<br/>"
                f"\n总绩点: {total_jd}<br/>"
                f"\n平均绩点: {gpa:.2f}<br/>")
      else:
        add_log(index,f"查询{name}{xh} 失败，错误信息：{response}")
    except :
      add_log(index,f'⚠️获取{name}{xh}的数据过程中发生错误')
    if hasNewScore: send_log(index)
  add_log(len(logs),"===============成绩查询完成================")
  # 更新所有学号的历史成绩记录
  if globals_hasNewScore or int(time.time()) - last_push_time >= 84600:
    history_scores["timestamp"] = int(time.time())  # 更新时间戳
    update_history_scores(history_scores)  # 保存到文件
    exit("\n✅成绩查询完成", '成绩更新' if globals_hasNewScore else '成绩查询')
