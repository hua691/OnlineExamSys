# pymysql 只在本地 MySQL 环境需要;PA/Render/SQLite 环境没装就跳过
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass