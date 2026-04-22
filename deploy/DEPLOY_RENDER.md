# 🚀 Render.com 部署指南(零失败版)

> 目标:**5 分钟**把项目部署到 `https://online-exam.onrender.com`,完全免费。

---

## ✅ 配置文件已就绪(我已经帮你做好)

- `render.yaml` — Infrastructure as Code,Render 读取后**自动创建** Web 服务 + PostgreSQL 数据库
- `build.sh` — 构建脚本(装依赖 + 静态文件 + 迁移)
- `requirements.txt` — 已加 `gunicorn / dj-database-url / psycopg2-binary`
- `settings.py` — 自动识别 `DATABASE_URL` 环境变量

---

## 🛠️ 部署前只需做 2 件事

### 1. 安装依赖本地验证(可选)

```powershell
pip install gunicorn dj-database-url psycopg2-binary
python manage.py check
```

### 2. 代码推到 GitHub

如果还没 GitHub 仓库:

```powershell
cd "d:\AAAAAAAAAA教育平台\Online Examination System\OnlineExamSys"
git init
git add .
git commit -m "ready for render deploy"

# 去 https://github.com/new 建一个仓库,比如叫 OnlineExamSys,然后:
git remote add origin https://github.com/你的用户名/OnlineExamSys.git
git branch -M main
git push -u origin main
```

---

## 🚀 Render 操作 5 步

### 1️⃣ 注册/登录 Render

打开 **https://render.com/** → **Get Started** → 用 **GitHub 账号登录**(一键授权)

### 2️⃣ 创建 Blueprint(读取 render.yaml 一键创建所有服务)

1. 进 Dashboard 后点右上 **New +** → **Blueprint**
2. 选你刚才推到 GitHub 的仓库 `OnlineExamSys`
3. Render 自动识别 `render.yaml`,显示即将创建:
   - ✅ Web Service: `online-exam`
   - ✅ PostgreSQL: `online-exam-db`
4. 点 **Apply** → 开始构建

### 3️⃣ 等构建完成(3-5 分钟)

构建日志里你会看到:
```
==> Installing dependencies
Successfully installed Django-4.2.16 ...
==> Running 'pip install -r requirements.txt && python manage.py collectstatic --noinput'
==> Build succeeded
==> Deploying
==> Starting service with 'python manage.py migrate --noinput && gunicorn ...'
==> Your service is live 🎉
```

如果某一步失败,看红色错误信息,对照文末 **故障排查** 章节。

### 4️⃣ 首次部署要初始化示例数据(可选但推荐)

数据库建好了但里面是空的。进 Web 服务页 → 左侧 **Shell** Tab → 弹出在线终端:

```bash
python manage.py seed_rich_demo
```

这会生成:
- 3 个教师账号(`teacher1~3 / teacher123`)
- 9 个学生账号(`student1~9 / student123`)
- 1 个管理员(`admin / admin123`)
- 3 个班级、4 门课程、若干试卷和答题记录

### 5️⃣ 访问你的站点

顶部有个 URL 链接,形如:

```
https://online-exam.onrender.com
```

或 `https://online-exam-xxxx.onrender.com`(后缀防冲突)。

**把这个 URL 发给老师/同学**就能访问了!

---

## ⚠️ 免费版关键限制

| 项目 | Render 免费版 |
|---|---|
| Web Service 内存 | 512 MB |
| Web Service 月时长 | 750 小时(一个服务开着也够用整月) |
| **15 分钟无访问休眠** | ✅ 是(访问时冷启动 **30-60 秒**) |
| PostgreSQL 免费期 | **90 天**(到期后每月 $7,或迁到 Neon/Supabase 继续免费) |
| 自定义域名 | ✅ 支持(但免费版 SSL 要自己配置) |
| SSL 证书 | ✅ 自带(*.onrender.com 域) |

### 💡 关于冷启动

**演示时提前 1 分钟访问一次让它预热**,之后的 15 分钟内就很快。

或者用 **UptimeRobot** 免费监控每 5 分钟 ping 一次你的 URL,让它永不休眠。

### 💡 关于 90 天后数据库

到期前会邮件提醒。两个方案:
1. **迁移到 Neon**(永久免费 500MB PostgreSQL,最简单):
   - 去 https://neon.tech 注册
   - 复制它的 `DATABASE_URL`
   - 在 Render Web 服务的 Environment 里改 `DATABASE_URL` 为 Neon 的
2. **升级** Render PostgreSQL $7/月

---

## 🧯 故障排查

### 构建失败:`psycopg2-binary` 编译错误
Render 默认 Python 3 环境能直接装二进制版,一般不会。若失败:
- 检查 `requirements.txt` 里是 `psycopg2-binary`(带 `-binary`),不是 `psycopg2`

### 启动失败:`DisallowedHost`
Web 服务 Environment 里 `DJANGO_ALLOWED_HOSTS` 必须包含你的 `.onrender.com` 子域。
`render.yaml` 已设为 `.onrender.com`(开头有点),匹配所有子域,应该没问题。

### 500 Server Error
点 Web 服务的 **Logs** Tab,看 gunicorn 输出的 Python 堆栈,99% 是:
- SECRET_KEY 没生成(应自动 `generateValue: true`)
- 迁移没跑(看 Deploy 日志里有没有 "OK" 行)

### 样式丢失
- WhiteNoise 已在 settings 中间件里(第 2 个位置,紧跟 SecurityMiddleware)
- 构建日志里应有 "N static files copied to staticfiles" 字样

### 部署很慢(5 分钟+)
免费版共享 CPU,首次装 scikit-learn + scipy + numpy 会比较慢。耐心等第一次,之后缓存加速。

---

## 🎯 完成后把你的 URL 发我

我帮你远程烟测:
- 登录页是否显示
- 静态文件是否 200
- 提交试卷是否秒出客观分
- 通知铃铛是否有红点

祝部署顺利 🎉
