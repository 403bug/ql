# 自动化脚本集合

## 项目简介

本项目是一个多平台、多功能的自动化脚本集合，旨在实现各类网站/应用的自动签到、积分查询、任务自动完成等功能。当前已集成 OPPO 系列自动签到脚本、PCR532 论坛签到脚本，后续将持续扩展更多自定义脚本，满足个人及社区的多样化自动化需求。

## 主要功能

- **OPPO 系列自动签到**
  - OPPO 商城、社区、会员小程序、一加论坛、钱包、阅读等渠道自动签到
  - 自动领取累计签到奖励、自动完成部分任务、商城小程序自动抽奖
  - 查询积分余额、会员等级、积分过期情况、今日积分收支等
- **PCR532 论坛自动签到**
  - 自动签到、查询个人设备信息、金币等
- **多账号支持**
  - 支持通过环境变量或本地配置文件配置多个账号
- **多平台兼容**
  - 支持青龙面板、Linux、Windows 本地运行
- **可扩展性**
  - 你可以轻松添加自己的自定义脚本，统一管理和运行

## 安装与依赖

### 青龙面板部署

1. 在青龙面板 → 脚本管理 → 仓库订阅，添加如下订阅命令`或`上传或同步本项目脚本文件到面板脚本目录：

   ```
   ql repo https://gitee.com/sjmy1/ql.git
   ```

2. 订阅后，脚本会自动拉取到青龙面板的脚本目录。  

3. 在“环境变量”中添加：
   - `OPPO_COOKIE` 例如：
     ```
     账号1TOKENSID#账号1session_id&账号2TOKENSID#账号2session_id
     ```
   - `PCR532_COOKIE` 例如：
     ```
     账号1username#账号1password#账号1USERID&账号2username#账号2password#账号2USERID
     ```

4. 在“定时任务”中添加任务，例如：
   ```
   0 8 * * * python3 /ql/scripts/oppo.py
   0 8 * * * python3 /ql/scripts/PCR532.py
   ```

5. 青龙自带 Python 运行环境，无需手动安装依赖。

### 本地运行部署

1. 获取代码后，安装 Python 依赖：
   ```bash
   pip install requests ujson
   ```
2. 新建 `sjmyConfig.json`，内容示例：

   脚本会优先读取环境变量，因 Windows 设置及更改环境变量较为麻烦，所以代码里针对本地运行时做了特殊处理，会读取本地文件 `sjmyConfig.json`。

   ```json
   {
     "OPPO_COOKIE": "账号1TOKENSID#账号1session_id&账号2TOKENSID#账号2session_id",
     "PCR532_COOKIE": "账号1username#账号1password#账号1USERID&账号2username#账号2password#账号2USERID"
   }
   ```
3. 运行脚本：
   ```bash
   python oppo.py
   python PCR532.py
   ```

   或者打开 `VS Code`、`PyCharm` 等编写代码的程序进行运行、编写代码。

## 使用说明

### 1. 运行现有脚本

- **OPPO 自动签到**
  ```bash
  python oppo.py
  ```
- **PCR532 论坛签到**
  ```bash
  python PCR532.py
  ```
- 脚本会优先读取环境变量，未设置时读取 `sjmyConfig.json`。
- 青龙面板请添加对应环境变量，并设置定时任务。

### 2. 添加自定义脚本

1. 在项目根目录新建你的脚本文件（如 `my_script.py`）。
2. 按需引入 `notify.py` 实现统一推送。
3. 可参考现有脚本的配置读取、日志、推送等结构。
4. 在 `sjmyConfig.json` 增加你的自定义配置项。

### 3. 推送通知

- 支持多种推送方式（如 Bark、Server酱、Telegram、企业微信等），请根据 `notify.py` 配置相关推送参数。

## 参与贡献

1. Fork 本仓库
2. 新建分支
3. 提交代码
4. 新建 Pull Request

## 常见问题

- **账号格式错误/变量未设置**：请检查环境变量或配置文件格式是否正确。
- **部分渠道签到失败**：部分接口可能随时间变化失效，欢迎反馈或自行修复。
- **如何扩展脚本**：直接添加新脚本文件，参考现有结构即可。

---

本项目持续更新，欢迎提出建议和贡献更多自动化脚本！

---

