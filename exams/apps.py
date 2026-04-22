from django.apps import AppConfig
from django.db.backends.signals import connection_created


def _set_sqlite_pragma(sender, connection, **kwargs):
    """给每个 SQLite 连接开启 WAL + NORMAL 同步,降低并发锁冲突。"""
    if connection.vendor != 'sqlite':
        return
    cursor = connection.cursor()
    cursor.execute('PRAGMA journal_mode=WAL;')
    cursor.execute('PRAGMA synchronous=NORMAL;')
    cursor.close()


class ExamsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exams'

    def ready(self):
        # 每当 Django 建立新 DB 连接(多线程 runserver 每线程独立连接)时生效
        connection_created.connect(_set_sqlite_pragma)
