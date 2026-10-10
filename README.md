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
- **futureppo 自动签到**
  - 自动登录、每日签到、查询账号额度余额（余额 quota 除以 500000 为「元」）
- **agentrouter 额度查询**
  - 自动登录、查询账号额度余额（无签到，余额 quota 除以 500000 为「元」）
- **justwoker 额度查询**
  - New-API 新版 JWT 认证：`status` → `refresh` 换 access_token → 查询额度余额（quota 除以 500000 为「元」）
  - `new_api_refresh` 是轮换凭证，脚本会自动把轮换后的新值存到 `.justwoker_state.json` 滚动续期
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
   - `FUTUREPPO_COOKIE` 例如：
     ```
     账号1username#账号1password&账号2username#账号2password
     ```
   - `AGENTROUTER_COOKIE` 例如：
     ```
     账号1username#账号1password&账号2username#账号2password
     ```
   - `JUSTWOKER_COOKIE` 例如：
     ```
     账号1凭证&账号2凭证
     ```

4. 在“定时任务”中添加任务，例如：
   ```
   0 8 * * * python3 /ql/scripts/oppo.py
   0 8 * * * python3 /ql/scripts/PCR532.py
   0 4 * * * python3 /ql/scripts/futureppo.py
   0 4 * * * python3 /ql/scripts/agentrouter.py
   0 4 * * * python3 /ql/scripts/justwoker.py
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
     "PCR532_COOKIE": "账号1username#账号1password#账号1USERID&账号2username#账号2password#账号2USERID",
     "FUTUREPPO_COOKIE": "账号1username#账号1password&账号2username#账号2password",
     "AGENTROUTER_COOKIE": "账号1username#账号1password&账号2username#账号2password",
     "JUSTWOKER_COOKIE": "账号1凭证&账号2凭证"
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
- **agentrouter 额度查询**
  ```bash
  python agentrouter.py
  ```
- **justwoker 额度查询**
  ```bash
  python justwoker.py
  ```
- 脚本会优先读取环境变量，未设置时读取 `sjmyConfig.json`。

### 关于 justwoker 的 `new_api_refresh` 轮换

`api.justwoker.icu` 是 New-API 新版（`v1.0.0-rc.23`），认证走 JWT：

1. `GET /api/status` —— 公开接口，拿站点配置（`checkin_enabled`、`quota_per_unit`）
2. `POST /api/user/auth/refresh` —— 携带 `new_api_refresh` Cookie，换取 `access_token`（JWT，约 15 分钟有效）
3. `GET /api/user/self` —— 携带 `Authorization: Bearer <access_token>` 查询用户信息

关键点：**`new_api_refresh` 不是长期稳定的凭证**（实测结论）：

- 每次 `refresh` 成功，服务端都会下发一个新的 secret（sid 不变）
- 旧值**不会立刻失效**：刷新后 7 秒内旧值仍可用，但约 **15 分钟后**旧值就返回 `401 AUTH_SESSION_REVOKED`
- session 本身也可能被整体撤销（例如在别处重新登录），届时该 session 下所有值一起失效
- `refresh` 接口有**频率限制**：触发后返回 `429` 并带 `Retry-After`（实测 720 秒）

`JUSTWOKER_COOKIE` 支持三种写法（脚本自动识别）：

| 写法 | 示例 | 说明 |
|---|---|---|
| refresh Cookie | `a2565661-...-beb795.596f681b...` | 从 DevTools → Application → Cookies → `new_api_refresh` 复制 |
| 用户ID#系统访问令牌 | `39149#sk-xxxxxxxx` | 在站点「个人设置 → 系统访问令牌」生成，**长期有效不会滚动失效，青龙首选** |
| username#password | `user@qq.com#password` | 本站开启 Turnstile 人机验证，密码登录通常会被拦截 |

脚本对凭证失效的处理：

- 首次用你配置的凭证换到 `access_token`，同时把服务端下发的新 Cookie 存进状态文件 `.justwoker_state.json`
- 之后每次运行**优先用状态文件里的 Cookie**（永远是最新值），成功后再覆盖保存
- 状态文件里的 Cookie 失效时，自动回退用配置里的原始凭证再试一次
- 你在配置/环境变量里换了新凭证时，脚本检测到「来源指纹变了」会自动丢弃旧状态，以新凭证为准
- ⚠️ 浏览器和脚本共用同一个 session，你在浏览器访问该站同样会触发滚动，把脚本存的 Cookie 顶掉。要长期稳定，建议脚本专用一个 session，或直接用 `用户ID#sk-xxx`

相关环境变量：`JUSTWOKER_DELAY_MAX`（随机延迟分钟数，默认 15，0 = 不延迟）、`JUSTWOKER_CHECKIN`（设为 1 才签到，默认关闭）。
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
