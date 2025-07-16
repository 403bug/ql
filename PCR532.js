// 描述：PCR532 多账号签到 + PushPlus 推送 + 全程日志

const notify = require('./sendNotify'); // 青龙自带推送模块


// 环境变量 PCR532_ACCOUNTS 格式： user:pass:userid&user2:pass2:userid2
const accounts = process.env.PCR532_ACCOUNTS ? process.env.PCR532_ACCOUNTS.split('&') : [];

console.log('📢 开始 RFIDFans 多账号签到任务...');
if (accounts.length === 0) {
    console.log('❌ 未检测到环境变量 PCR532_ACCOUNTS，请检查配置！');
    process.exit(0);
}

(async () => {
    let allResults = [];
    for (let i = 0; i < accounts.length; i++) {
        const [username, password, userid] = accounts[i].split(':');
        console.log(`\n👉 开始第 ${i + 1} 个账号：${username}`);

        try {
            const res = await fetch('https://www.rfidfans.com/upload/qiandao.php', {
                method: 'POST',
                headers: {
                    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 15; PJD110 Build/AP3A.240617.008)',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: username,
                    passc: password,
                    USERID: userid,
                }),
            });

            const text = await res.text();
            if (text) {
                console.log(`✅ 第 ${i + 1} 个账号签到结果：${text}`);
                allResults.push(`账号 ${i + 1} (${username}): ${text}`);
            } else {
                console.log(`⚠️ 第 ${i + 1} 个账号无有效返回`);
                allResults.push(`账号 ${i + 1} (${username}): 无有效返回`);
            }
        } catch (err) {
            console.log(`❌ 第 ${i + 1} 个账号签到失败: ${err.message}`);
            allResults.push(`账号 ${i + 1} (${username}): 签到失败 (${err.message})`);
        }
    }

    // 汇总推送
    const notifyTitle = '📢 PCR532 签到结果';
    const notifyMsg = allResults.join('\n');
    console.log('\n📤 准备推送签到结果到微信...');
    await notify.sendNotify(notifyTitle, notifyMsg);
    console.log('✅ 推送完成');
})();
