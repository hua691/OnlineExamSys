"""PythonAnywhere 部署 WSGI 配置模板。

到 PythonAnywhere 的 Web 页面,把这份文件的内容 复制粘贴进
/var/www/yourname_pythonanywhere_com_wsgi.py 即可。

注意把 `yourname` 替换成你的 PythonAnywhere 用户名。
"""
import os
import sys

# ==========================================================
#  ⚠️  下面两个变量改成你自己的用户名
# ==========================================================
PA_USERNAME = 'yourname'                # 例如 'wanghua'
PROJECT_DIR = f'/home/{PA_USERNAME}/OnlineExamSys'


# 项目目录加进 Python path
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# ==========================================================
#  生产环境变量:启用 DEBUG=False + 域名白名单
# ==========================================================
os.environ['DJANGO_SETTINGS_MODULE'] = 'OnlineExamSys.settings'
os.environ['DJANGO_ENV'] = 'production'
os.environ['DJANGO_ALLOWED_HOSTS'] = f'{PA_USERNAME}.pythonanywhere.com'

# 请换成一个长随机串(可在 https://djecrety.ir 生成一个)
os.environ['DJANGO_SECRET_KEY'] = 'CHANGE-THIS-TO-A-LONG-RANDOM-STRING'

# ==========================================================
#  若用 PythonAnywhere 自带的 MySQL(推荐),取消下面注释并填密码
# ==========================================================
# os.environ['USE_MYSQL'] = '1'
# os.environ['MYSQL_DB'] = f'{PA_USERNAME}$exam'
# os.environ['MYSQL_USER'] = PA_USERNAME
# os.environ['MYSQL_PASSWORD'] = 'your-mysql-password'
# os.environ['MYSQL_HOST'] = f'{PA_USERNAME}.mysql.pythonanywhere-services.com'
# os.environ['MYSQL_PORT'] = '3306'


# ==========================================================
#  Django 启动
# ==========================================================
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
