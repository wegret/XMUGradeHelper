基于github actions的厦门大学成绩查询脚本，支持一次部署后自动定时查询并发送新的成绩通知（不需要评教）。通知方式支持github issues、邮件通知。

（配置成qq邮箱后就可以直接用手机qq接受提醒。）

部署后效果如下：

<img src="https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260112200443282.png" alt="image-20260112200443282" style="zoom: 33%;" />

**更新：**

2026.01.20：修改默认不会用github issues通知。增加JSON配置方式。

## 傻瓜配置方式

### 1. 创建仓库

如下图，`Use the template`-`Create a new repository`，使用模板创建一个新的仓库。

<img src="https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260112201050036.png" alt="image-20260112201050036" style="zoom: 50%;" />

然后`Repository name`随便填，需要注意，**`visibility`设置成`private`（很重要很重要很重要！）**。

然后点击`Create Repository`创建成功。

<img src="https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260112201307727.png" alt="image-20260112201307727" style="zoom:50%;" />

### 2. 配置变量

如下，`Settings`-`Secret and variables`-`Actions`，然后点击这里的`New repository secret`。

<img src="https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260112201621337.png" alt="image-20260112201621337" style="zoom:50%;" />

然后这里输入配置：

<img src="https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260120182046158.png" alt="image-20260120182046158" style="zoom:50%;" />

首先输入学号，`Name`这里输入`CONFIG_JSON`，`Secret`填入以下的信息，最后点`Add Secret`。

```json
{
    "XMU_USERNAME": "<学号>",
    "XMU_PASSWORD": "<密码>",
    "EMAIL_HOST": "smtp.qq.com",
    "EMAIL_PORT": 465,
    "EMAIL_USER": "<发件qq邮箱>",
    "EMAIL_PASSWORD": "<授权码>",
    "EMAIL_TO": "<收信邮箱>",
    "REQUEST_INTERVAL": 0.75
}

```

其中配置信息，学号密码就是厦大统一身份认证。如果使用qq邮箱的话，只需要额外再填写`EMAIL_USER`、`EMAIL_PASSWORD`、`EMAIL_TO`三个就行了（也就是说，qq邮箱的话`EMAIL_HOST`、`EMAIL_PORT`不用改。）



<details>
  <summary><span style="font-weight: 700;"><u>什么，你还不会配置邮箱授权码？（点击展开）</u></span></summary>

<blockquote>

QQ邮箱，进入设置-账号与安全。找到一个`POP3/IMAP/SMTP/Exchange/CardDAV 服务`，然后点击生成授权码即可（第一次设置可能要验证一下，无所谓）。

<img src="https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260112203400468.png" alt="image-20260112203400468" style="zoom:50%;" />

</blockquote>

</details>

现在默认是不启用github issues通知的，如果你想启用github issues通知的话，加入`NOTIFY_GITHUB_ISSUE_ENABLED`配置，值设置为`true`即可。

例如下面的最后一行：

```json
{
    "XMU_USERNAME": "<学号>",
    "XMU_PASSWORD": "<密码>",
    "EMAIL_HOST": "smtp.qq.com",
    "EMAIL_PORT": 465,
    "EMAIL_USER": "<发件qq邮箱>",
    "EMAIL_PASSWORD": "<授权码>",
    "EMAIL_TO": "<收信邮箱>",
    "REQUEST_INTERVAL": 0.75,
    "NOTIFY_GITHUB_ISSUE_ENABLED": true
}
```


总之，那一堆secret，配置完成后如下：

<img src="https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260120182847008.png" alt="image-20260120182847008" style="zoom:50%;" />

### 3. actions启动！

如下图：

![image-20260112184552490](https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260112184552490.png)

过一会儿后就会收到类似如下：

![image-20260112184958991](https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260112184958991.png)

然后这个就启动了，等着接收你的好成绩吧。

### （时间设置）

当前设置的是30分钟运行一次，经过精确的计算，是不会超过github actions的免费额度的。

<details>
  <summary><span style="font-weight: 700;"><u>精确的计算</u></span></summary>

<blockquote>

一个任务运行不会超过1分钟，私有仓库每月有2000分钟免费额度。

</blockquote>

</details>

如果你需要更改运行时间，可以修改`.github/workflows/check.yml`中的`cron`配置。

```yml
name: 检查成绩更新

on:
  schedule:
    - cron: '0,30 * * * *'  # 每30分钟运行一次
    # - cron: '0 * * * *'   # 每1小时
    # - cron: '0 */3 * * *' # 每3个小时
```