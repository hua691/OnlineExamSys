#!/usr/bin/env bash
# Render 构建脚本:装依赖 → 打包静态文件 → 迁移数据库
# 在 Render Web Service 的 Build Command 里填 `./build.sh`(或把命令直接展开填)

set -o errexit  # 任何命令失败立即退出

echo "==> 1. 安装 Python 依赖"
pip install -r requirements.txt

echo "==> 2. 打包静态文件(WhiteNoise 指纹化)"
python manage.py collectstatic --noinput

echo "==> 3. 数据库迁移"
python manage.py migrate --noinput

# 首次部署时取消下面一行注释,填入示例数据(部署后要再次 commit 去掉)
# python manage.py seed_rich_demo

echo "==> 构建完成"
