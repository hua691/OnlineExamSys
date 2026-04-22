# 📚 长江·云阅卷 · 在线考试自动阅卷系统

> 基于 Django 的多角色在线考试平台,支持客观题自动判分 + 主观题 **jieba + TF-IDF** 语义辅助评分。
> 朱红主题 UI、雨课堂风格,一站式覆盖**学生、教师、管理员**三角色。

---

## ✨ 核心功能

### 🎓 学生端
- 加入班级 / 我听的课
- 我的待办(按截止时间排序,紧急程度着色)
- 在线答题(单选 / 多选 / 判断 / 简答)
- 自动评分 + 主观题 AI 建议分
- 成绩详情 + 错题集(自动收录未得满分题目)
- 消息中心(考试提醒 / 成绩通知 / 系统广播)

### 👨‍🏫 教师端
- 创建班级(邀请码加入)、课程、试题、试卷
- 课程多 Tab:公告 / 试卷 / 讨论区 / 成绩单
- 阅卷中心:主观题批阅 + AI 相似度建议分
- 成绩导出 Excel
- 试卷成绩分析(Chart.js 分数分布图 + 及格率饼图)

### 🛡️ 管理员端
- 仪表盘概览(用户增长 / 试卷 / 答卷统计)
- 用户管理(新建 / 编辑 / 重置密码 / 禁用 / 改角色)
- 班级 / 课程 / 试卷管理
- 系统通知广播(全员 / 学生 / 教师 / 指定班级)

---

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11 · Django 4.2.16 |
| 数据库 | SQLite(默认,可切 MySQL) |
| 前端 | Django 模板 + 原生 CSS + Chart.js 4 |
| 分词 | jieba 0.42.1 |
| 相似度 | scikit-learn TF-IDF + cosine |
| Excel | openpyxl 3.1.2 |

---

## 📁 目录结构(简)

```
OnlineExamSys/
├── manage.py
├── requirements.txt
├── OnlineExamSys/          # 项目设置
│   ├── settings.py
│   └── urls.py
├── users/                  # 用户 + 管理员后台
│   ├── models.py           # UserProfile(role: student/teacher/admin)
│   ├── views.py            # 登录 / 注册
│   └── admin_views.py      # 管理员朱红后台(用户/班级/课程/试卷/广播)
├── classes/                # 班级 + 课程 + 公告 + 讨论区
│   ├── models.py           # ClassRoom / Course / CourseAnnouncement / DiscussionTopic
│   └── views.py
├── exams/                  # 试题 + 试卷 + 答题 + 阅卷
│   ├── models.py           # Question / ExamPaper / ExamRecord / AnswerRecord / WrongQuestion
│   ├── views.py            # 含 Excel 导出 + 试卷统计
│   └── urls.py
├── scoring/                # 主观题评分算法
│   └── utils.py            # jieba 分词 + TF-IDF + 关键词命中
├── notifications/          # 消息通知
│   └── models.py           # Notification(含 notify 便捷函数)
└── templates/
    ├── base.html           # 朱红主题 + 顶部导航
    ├── users/              # login / register
    ├── exams/              # dashboard / my_todo / 答题 / 阅卷 / 统计
    ├── classes/            # my_classes / course_detail(多 Tab)
    ├── notifications/      # 消息中心
    └── admin_panel/        # 管理员朱红后台模板
```

---

## 🚀 从零启动(5 步)

### 前置条件
- 已安装 Python **3.10+**(推荐 3.11)
- 推荐创建虚拟环境(可选)

### 1. 安装依赖

```powershell
pip install -r requirements.txt
```

### 2. 数据库迁移

> **重要**:每次拉取最新代码或修改模型字段后必须执行,否则访问时会报
> `no such column: xxx` 错误。

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 3. 填充演示数据(一次性,可重复执行)

```powershell
python manage.py seed_demo
```

这条命令会创建:
- 管理员 1 人、教师 2 人、学生 3 人
- 1 个班级(计算机 2101 班)+ 1 门课程(数据结构)
- 6 道示例试题(各题型全覆盖)+ 1 份示例试卷

### 4. 启动开发服务器

```powershell
python manage.py runserver 8000
```

浏览器打开 **<http://127.0.0.1:8000/>** 即可。

> 遇到 8000 端口被占用时:`python manage.py runserver 8080`

### 5. 停止服务器
按 `Ctrl + C`,或强杀 Python 进程:
```powershell
taskkill /F /IM python.exe
```

---

## 🧑 演示账号

| 角色 | 用户名 | 密码 | 备注 |
|---|---|---|---|
| 🛡️ 管理员 | `admin` | `admin123` | 可进系统管理、发广播 |
| 👨‍🏫 教师 | `teacher1` | `teacher123` | 张老师(班主任) |
| 👨‍🏫 教师 | `teacher2` | `teacher123` | 李老师(任课) |
| 🎓 学生 | `student1` | `student123` | 王小明 |
| 🎓 学生 | `student2` | `student123` | 赵小红 |
| 🎓 学生 | `student3` | `student123` | 孙小强 |

班级邀请码:`5Y2DQY`(新学生可用此码加入班级)

---

## 🧪 运行测试

```powershell
# 全部测试(13 个角色隔离 + 权限测试)
python manage.py test

# 指定 app
python manage.py test users
```

---

## ⚠️ 常见问题

### Q1. 提示 `no such column: xxx`
忘记执行迁移。请运行:
```powershell
python manage.py makemigrations
python manage.py migrate
```

### Q2. 主观题评分结果看起来很低
jieba + TF-IDF 是**词袋**方法,答案里必须包含与标准答案重合的关键词才有高分。
可在试题编辑页"主观题关键词得分点"里填入关键词 JSON,如:
```json
[{"keyword":"递归","weight":0.3}, {"keyword":"栈","weight":0.2}]
```

### Q3. 登录时提示"该账号不是「xxx」身份"
登录页要先选对角色单选框再输入账号密码。三种角色登录后跳转的首页不同。

### Q3.5. 注册密码到底有什么要求?
演示/教学环境已放宽,只保留 **最少 4 位** 这一条规则(见 `settings.py`
的 `AUTH_PASSWORD_VALIDATORS`):

| 规则 | 说明 |
|---|---|
| **至少 4 位** | `MinimumLengthValidator(min_length=4)` |

**✅ 通过示例**:`1234` · `abcd` · `abc1234` · `demo12345`
**❌ 失败示例**:只有 `123`、`ab` 这种短于 4 位的会被拒

> 若需要生产级密码强度,可在 `settings.py` 里加回
> `NumericPasswordValidator`、`CommonPasswordValidator`、
> `UserAttributeSimilarityValidator` 三条校验。

### Q4. 想切换到 MySQL
编辑 `OnlineExamSys/settings.py` 里的 `DATABASES` 配置,然后重新执行
`makemigrations` + `migrate`。

### Q5. 背景图怎么换
将新图覆盖到 `OnlineExamSys/static/images/login-bg.jpg` 即可,登录/注册页均使用该图。

---

## 📐 主观题评分算法(核心)

文件:`scoring/utils.py::subjective_auto_score`

```
final_ratio = 0.5 * similarity_ratio + 0.5 * keyword_ratio

similarity_ratio:
    sim >= threshold → 1.0
    sim <= 0.3       → 0.0
    中间线性折算

keyword_ratio = sum(命中?× weight) / sum(weight)

auto_score = round(final_ratio × 题目满分, 2)
```

- `similarity`:jieba 分词后 TF-IDF 余弦相似度(0-1)
- `threshold`:教师在试题编辑页可调(默认 0.6)
- `keyword_points`:教师预设关键词清单 + 权重

---

## 🎯 快捷 URL 速查

| 路径 | 说明 |
|---|---|
| `/users/login/` | 登录页 |
| `/exams/` | 仪表盘(按角色自动分流) |
| `/exams/student/todo/` | 学生:我的待办 |
| `/exams/wrong/` | 学生:错题集 |
| `/exams/teacher/correction/` | 教师:阅卷中心 |
| `/exams/teacher/paper/<id>/stats/` | 教师:试卷成绩分析 |
| `/exams/teacher/export-records.xlsx` | 教师:导出成绩 Excel |
| `/classes/mine/` | 我的班级 / 课程 |
| `/users/manage/users/` | 管理员:用户管理 |
| `/users/manage/broadcast/` | 管理员:发送系统通知 |
| `/notifications/` | 消息中心 |
| `/admin/` | Django 原生后台(无 UI 入口,需直接输入) |

---

## 📝 开发者命令速查

```powershell
# 创建超级管理员账号
python manage.py createsuperuser

# 清空数据库重建(慎用)
del db.sqlite3
python manage.py migrate
python manage.py seed_demo

# Django shell(交互式)
python manage.py shell

# 收集静态文件(生产)
python manage.py collectstatic
```

---

© 2026 长江·云阅卷 · 仅用于教学演示
