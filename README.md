基于github actions的厦门大学成绩查询脚本，支持一次部署后自动定时查询并发送新的成绩通知（不需要评教）。通知方式支持github issues、邮件通知。

（配置成qq邮箱后就可以直接用手机qq接受提醒。）

（啥也不配置的话，github app可以接收提醒）

部署后效果如下：

<img src="https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260112200443282.png" alt="image-20260112200443282" style="zoom: 33%;" />

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

然后这里输入配置，首先输入学号，`Name`这里输入`XMU_USERNAME`，`Secret`填入学号。

<img src="https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260112202331574.png" alt="image-20260112202331574" style="zoom:50%;" />

除了学号外，还需要配置厦大账号密码、邮箱配置等。这是一个示例的`.env`文件：

```bash
# 必填的（没有这个怎么查成绩？）
XMU_USERNAME=<学号>
XMU_PASSWORD=<密码>

# 可选的（设置了qq邮箱后）
EMAIL_HOST=smtp.qq.com	 # qq邮箱的话不用该
EMAIL_PORT=465			# qq邮箱的话不用改
EMAIL_USER=<发件qq邮箱>
EMAIL_PASSWORD=<授权码>
EMAIL_TO=<收信邮箱>
```

如上，总而言之，需要配置`XMU_USERNAME`、`XMU_PASSWORD`两个必填的secret。

和可选的`EMAIL_HOST`、`EMAIL_PORT`、`EMAIL_USER`、`EMAIL_PASSWORD`、`EMAIL_TO`五个可选的secret。

<details>
  <summary><span style="font-weight: 700;"><u>什么，你还不会配置邮箱授权码？（点击展开）</u></span></summary>

<blockquote>

QQ邮箱，进入设置-账号与安全。找到一个`POP3/IMAP/SMTP/Exchange/CardDAV 服务`，然后点击生成授权码即可（第一次设置可能要验证一下，无所谓）。

<img src="https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260112203400468.png" alt="image-20260112203400468" style="zoom:50%;" />

</blockquote>

</details>



总之，那一堆secret，配置完成后如下：

<img src="https://wegret-pic.oss-cn-beijing.aliyuncs.com/image-20260112184418251.png" alt="image-20260112184418251" style="zoom:50%;" />

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