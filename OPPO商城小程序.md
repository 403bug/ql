# OPPO会员小程序签到
```http
GET /activity/signIn/daily?sessionId=gwii54t3DCVl1OgD1Bm8Gfu2nNOZ7fEtBwtuA2KK3nedfEjSkPEV84EPWklYE_eGJw0gpZs3rE8&version=2 HTTP/1.1
Host: omoapplet-api-cn.heytap.com

User-Agent : Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36

```

>[!note]
>属性里的sessionId和version是必传的
>此请求的请求头可以不传


get
```http
HTTP/1.1 200 OK
Server: nginx
Date: Sun, 13 Jul 2025 09:21:28 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: keep-alive
X-Backend-Host: 0895:9900
X-Gateway-Host: b142c0fc22f40f7d6828610ae76e24433f49ef0cb03627023ff6a5beac0b0590aaa6a69672bee83974fc020caf87b5521ea00b3cccfa0b3cd931f6745a779c16

{"ret":"1","errCode":null,"errMsg":null,"data":{"level":0,"integral":1}}
上面是签到成功得到的响应
下面是已经签到的响应
{
  "ret": "0",
  "errCode": "214000023",
  "errMsg": "奖励已发放~",
  "data": null
}



# 积分获取
curl -X GET 'https://omoapplet-api-cn.heytap.com/point/creditsList?sessionId=gwii54t3DCVl1OgD1Bm8GUN5RFx6DTVL0t4jmBJV1Tp_AegBCnky1lBnscXvR6y_XcvIX4uyWmi-pDuj5x7ZkP6ZTez2HvDgBVN8uEEWZUM9G-acuHXBuQ&loadSize=15&lastRecordTimeStamp' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2540611) XWEB/14199'

get示例
{
  "ret": "1",
  "errCode": null,
  "errMsg": null,
  "data": {
    "amount": 882,
    "groups": [
      {
        "addTotAmount": 501,
        "subTotAmount": 102,
        "month": "202507",
        "creditsList": [
          {
            "actionName": null,
            "amount": 1,
            "createTime": "2025-07-15 14:22:29",
            "recordType": 1,
            "description": "[OPPO会员小程序]签到活动积分发放\"每日签到得积分\""
          },
          {
            "actionName": null,
            "amount": 2,
            "createTime": "2025-07-15 14:13:23",
            "recordType": 1,
            "description": "[OPPO商城]签到奖励"
          },
          {
            "actionName": null,
            "amount": 10,
            "createTime": "2025-07-15 13:59:23",
            "recordType": 1,
            "description": "[OPPO商城]活动奖励\"完成任务增加积分\""
          },
          {
            "actionName": null,
            "amount": 2,
            "createTime": "2025-07-15 12:59:53",
            "recordType": 1,
            "description": "[OPPO商城]活动奖励\"完成任务增加积分\""
          },
          {
            "actionName": null,
            "amount": 3,
            "createTime": "2025-07-15 12:59:48",
            "recordType": 1,
            "description": "[OPPO商城]活动奖励\"完成任务增加积分\""
          },
          {
            "actionName": null,
            "amount": 2,
            "createTime": "2025-07-15 12:59:46",
            "recordType": 1,
            "description": "[OPPO商城]活动奖励\"完成任务增加积分\""
          },
          {
            "actionName": null,
            "amount": 5,
            "createTime": "2025-07-15 12:59:43",
            "recordType": 1,
            "description": "[OPPO商城]活动奖励\"完成任务增加积分\""
          },
          {
            "actionName": null,
            "amount": 2,
            "createTime": "2025-07-15 12:59:39",
            "recordType": 1,
            "description": "[OPPO商城]活动奖励\"完成任务增加积分\""
          },
          {
            "actionName": null,
            "amount": 3,
            "createTime": "2025-07-15 12:59:37",
            "recordType": 1,
            "description": "[OPPO商城]活动奖励\"完成任务增加积分\""
          },
          {
            "actionName": null,
            "amount": 10,
            "createTime": "2025-07-15 12:59:35",
            "recordType": 1,
            "description": "[OPPO商城]活动奖励\"完成任务增加积分\""
          },
          {
            "actionName": null,
            "amount": 2,
            "createTime": "2025-07-15 12:59:32",
            "recordType": 1,
            "description": "[会员权益]OPPO会员活动发放\"完成任务增加积分\""
          },
          {
            "actionName": null,
            "amount": 2,
            "createTime": "2025-07-15 08:00:47",
            "recordType": 1,
            "description": "[OPPO商城]活动奖励\"完成任务增加积分\""
          },
          {
            "actionName": null,
            "amount": 2,
            "createTime": "2025-07-15 08:00:40",
            "recordType": 1,
            "description": "[OPPO商城]活动奖励\"完成任务增加积分\""
          },
          {
            "actionName": null,
            "amount": 2,
            "createTime": "2025-07-15 08:00:39",
            "recordType": 1,
            "description": "[OPPO商城]活动奖励\"完成任务增加积分\""
          },
          {
            "actionName": null,
            "amount": 1,
            "createTime": "2025-07-15 08:00:38",
            "recordType": 1,
            "description": "[一加社区]任务积分奖励\"连续签到【3】天\""
          }
        ]
      }
    ],
    "lastRecordTimeStamp": 1752537638000
  }
}