# 🚀 PythonAnywhere 部署指南(零失败版)

> 目标:把项目部署到 `https://yourname.pythonanywhere.com`,5-10 分钟完成。

---

## 📦 第 0 步:本地准备(已完成)

项目已经生产化改造,包含:

- ✅ `settings.py` 读环境变量,DEBUG / SECRET_KEY / ALLOWED_HOSTS 全自动切换
- ✅ `whitenoise` 中间件负责生产静态文件
- ✅ `mysqlclient` 加入 requirements,可切 MySQL
- ✅ `deploy/wsgi_pythonanywhere.py` 模板文件
- ✅ 本命令先在本地确认无误:

```powershell
# 本地模拟生产模式跑一次(可选)
$env:DJANGO_ENV='production'; $env:DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost'
python manage.py collectstatic --noinput
python manage.py runserver
# 验证完退出:Ctrl+C
Remove-Item Env:DJANGO_ENV; Remove-Item Env:DJANGO_ALLOWED_HOSTS
```

---

## 🌐 第 1 步:注册 PythonAnywhere 账号

1. 打开 **https://www.pythonanywhere.com/**
2. 右上 **Pricing & signup** → 选 **Create a Beginner account**(永久免费)
3. 填用户名(这会是你最终域名的一部分,**记住它**)、邮箱、密码
4. 登录进 Dashboard

> 用户名示例假设为 `wanghua`,后续全部替换成你自己的。

---

## 📤 第 2 步:把代码传上去

### 方式 A:Git(最推荐)

先把本地项目推到 GitHub:

```powershell
cd "d:\AAAAAAAAAA教育平台\Online Examination System\OnlineExamSys"
git init
git add .
git commit -m "initial commit"
# 在 GitHub 建好仓库后:
git remote add origin https://github.com/yourname/OnlineExamSys.git
git branch -M main
git push -u origin main
```

然后在 PythonAnywhere 顶部 **Consoles** → **Bash**:

```bash
cd ~
git clone https://github.com/yourname/OnlineExamSys.git
cd OnlineExamSys
ls  # 确认 manage.py 在
```

### 方式 B:ZIP 直传(没 GitHub 的话)

1. 本地把 `OnlineExamSys` 文件夹压成 zip(排除 `__pycache__`, `.venv`, `db.sqlite3` 可选)
2. PythonAnywhere 顶部 **Files** → 拖拽 zip 到根目录
3. 顶部 **Consoles** → **Bash**:
```bash
cd ~
unzip OnlineExamSys.zip
cd OnlineExamSys
ls
```

---

## 🐍 第 3 步:创建虚拟环境 + 装依赖

在刚打开的 Bash 控制台里:

```bash
# 1. 创建 Python 3.11 虚拟环境
mkvirtualenv --python=python3.11 examenv

# 2. 装依赖(会花 2-3 分钟)
cd ~/OnlineExamSys
pip install -r requirements.txt

# 3. 若 mysqlclient 装不上,先跳过(我们先用 SQLite):
pip install -r requirements.txt --no-deps mysqlclient || true
```

如果 `mysqlclient` 失败不用管,**先用 SQLite 跑通**,后面再切 MySQL。

---

## 🗄️ 第 4 步:数据库初始化

### 选项 A:用 SQLite(简单,推荐先走通)

```bash
cd ~/OnlineExamSys
python manage.py migrate
python manage.py seed_rich_demo   # 可选:生成演示数据(班级、学生、老师、试卷)
python manage.py collectstatic --noinput
```

### 选项 B:用 MySQL(更稳,需多做一步)

1. 顶部 **Databases** Tab
2. **Initialize MySQL** → 设密码(**记住这个密码**)
3. 在 Bash 里:

```bash
mysql -u wanghua -h wanghua.mysql.pythonanywhere-services.com -p
# 输入密码后进入 MySQL:
CREATE DATABASE `wanghua$exam` CHARACTER SET utf8mb4;
exit
```

然后在 WSGI 文件里(下一步)开启 MySQL 相关环境变量,再跑 migrate。

---

## ⚙️ 第 5 步:配置 Web 应用

1. 顶部 **Web** Tab → **Add a new web app**
2. Next → 选 **Manual configuration (including virtualenvs)**
3. 选 Python **3.11**
4. Next → 完成,进入配置页

### 必填 4 个字段

| 字段 | 填什么 |
|---|---|
| **Source code** | `/home/wanghua/OnlineExamSys` |
| **Working directory** | `/home/wanghua/OnlineExamSys` |
| **Virtualenv** | `/home/wanghua/.virtualenvs/examenv` |
| **WSGI 配置文件** | 点链接打开,清空,**粘贴下一步的内容** |

### WSGI 文件内容(重点!)

点开 `/var/www/wanghua_pythonanywhere_com_wsgi.py`,**全部清空**,粘贴:

```python
import os, sys

PA_USERNAME = 'wanghua'   # ⚠️ 换成你的用户名
PROJECT_DIR = f'/home/{PA_USERNAME}/OnlineExamSys'
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'OnlineExamSys.settings'
os.environ['DJANGO_ENV'] = 'production'
os.environ['DJANGO_ALLOWED_HOSTS'] = f'{PA_USERNAME}.pythonanywhere.com'
os.environ['DJANGO_SECRET_KEY'] = '换成一个长随机串'  # 可用 Python 生成

# 如果要用 MySQL,取消注释:
# os.environ['USE_MYSQL'] = '1'
# os.environ['MYSQL_DB'] = f'{PA_USERNAME}$exam'
# os.environ['MYSQL_USER'] = PA_USERNAME
# os.environ['MYSQL_PASSWORD'] = '你的数据库密码'
# os.environ['MYSQL_HOST'] = f'{PA_USERNAME}.mysql.pythonanywhere-services.com'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

> 生成 SECRET_KEY 的快捷方法:在 Bash 里跑
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```
> 把输出贴到 SECRET_KEY 位置。

### 配静态文件映射

在 Web 页面往下翻到 **Static files** 区块,加两行:

| URL | Directory |
|---|---|
| `/static/` | `/home/wanghua/OnlineExamSys/staticfiles` |
| `/media/` | `/home/wanghua/OnlineExamSys/media` |

---

## 🎬 第 6 步:启动!

Web 页面顶部 **绿色 Reload 按钮** 点一下。

打开浏览器访问:
```
https://wanghua.pythonanywhere.com
```

应该能看到登录页。用演示数据的话:
- 管理员:`admin` / `admin123`
- 教师:`teacher1` / `teacher123`
- 学生:`student1` / `student123`

---

## 🧪 第 7 步:验证核心流程

- [ ] 登录页打开,CSS 样式正确(Windows 字体栈 / 朱红主题)
- [ ] 教师登录能看到「我教的课」
- [ ] 学生登录能看到「我听的课」
- [ ] 学生提交试卷 → 弹出朱红 Modal → 确认 → 立即出客观分
- [ ] 顶部铃铛有红点,通知中心能展开
- [ ] `/admin/` 管理后台能进

---

## 🧯 常见坑 & 解决

### 1. 浏览器报 `DisallowedHost`
WSGI 的 `DJANGO_ALLOWED_HOSTS` 没设对。确认和你的域名一致。

### 2. 静态文件 404、页面没样式
- 忘了 `python manage.py collectstatic --noinput`
- 或 Web 页 Static files 映射路径写错(必须是 `/home/<username>/OnlineExamSys/staticfiles`)

### 3. 500 Server Error
Web 页面底部 **Error log** 能看到真实堆栈,99% 是 SECRET_KEY 没改 / ALLOWED_HOSTS 错 / 依赖没装全。

### 4. jieba / scikit-learn 装不上
免费版有 CPU 限额,`pip install scikit-learn` 可能需要 3-5 分钟。耐心等。

### 5. `database is locked`
生产环境必须切 MySQL(SQLite 在高并发会锁)。按第 4 步选项 B 做。

### 6. 账号 3 个月不登录会休眠
每隔两个月登录一次,点一下 Reload 按钮即可保活。

---

## 🎯 进阶:绑定自定义域名

免费版不支持。升级 **Hacker 套餐**($5/月)可绑 `exam.yourdomain.com`。

---

做完后把你的访问链接发我,我帮你做最后的烟测。祝部署顺利 🎉
