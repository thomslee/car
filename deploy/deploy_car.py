# -*- coding: utf-8 -*-
"""汽车档案系统部署工具（paramiko，凭据走命令行参数，不硬编码）。

用法：
    python deploy_car.py --host <ip> --user ubuntu --password <pwd> upload_backend
    python deploy_car.py --host <ip> --user ubuntu --password <pwd> upload_frontend
    python deploy_car.py --host <ip> --user ubuntu --password <pwd> run "docker ps --format '{{.Names}}'"
"""
import argparse
import os
import sys

import paramiko

LOCAL_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + r"\backend"
LOCAL_DIST = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + r"\frontend\dist"
REMOTE_BACKEND = "/home/ubuntu/car/backend"
REMOTE_RELEASE_DIR = "/var/www/car/releases/v1"

# 上传时排除的目录/文件
EXCLUDE_DIRS = {".venv", "__pycache__", "data", ".git"}
EXCLUDE_FILES = {"test_ai_deepseek.py"}


def connect(host, user, password):
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(host, port=22, username=user, password=password, timeout=20)
    return cli


def run(cli, cmd, timeout=300):
    _, out, err = cli.exec_command(cmd, timeout=timeout)
    return (out.read().decode("utf-8", "replace") + err.read().decode("utf-8", "replace")).strip()


def upload_dir(sftp, local, remote):
    try:
        sftp.mkdir(remote)
    except OSError:
        pass
    for name in os.listdir(local):
        if name in EXCLUDE_DIRS or name in EXCLUDE_FILES:
            continue
        lp = os.path.join(local, name)
        rp = f"{remote}/{name}"
        if os.path.isdir(lp):
            try:
                sftp.mkdir(rp)
            except OSError:
                pass
            upload_dir(sftp, lp, rp)
        else:
            sftp.put(lp, rp)
            print(f"  put {lp} -> {rp}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", required=True)
    p.add_argument("--user", default="ubuntu")
    p.add_argument("--password", required=True)
    sub = p.add_subparsers(dest="action", required=True)

    r = sub.add_parser("run"); r.add_argument("cmd", nargs="+")
    u = sub.add_parser("upload_backend")
    f = sub.add_parser("upload_frontend")
    sub.add_parser("deploy_all")

    args = p.parse_args()
    cli = connect(args.host, args.user, args.password)
    try:
        if args.action == "run":
            print(run(cli, " ".join(args.cmd)))
        elif args.action == "upload_backend":
            sftp = cli.open_sftp()
            print("上传 backend ->", REMOTE_BACKEND)
            upload_dir(sftp, LOCAL_BACKEND, REMOTE_BACKEND)
            sftp.close()
            print("backend 上传完成")
        elif args.action == "upload_frontend":
            sftp = cli.open_sftp()
            print("上传 dist ->", REMOTE_RELEASE_DIR)
            upload_dir(sftp, LOCAL_DIST, REMOTE_RELEASE_DIR)
            sftp.close()
            print(run(cli, f"ln -sfn {REMOTE_RELEASE_DIR} /var/www/car/current && readlink /var/www/car/current"))
            print("frontend 上传并切换 current 完成")
        elif args.action == "deploy_all":
            sftp = cli.open_sftp()
            upload_dir(sftp, LOCAL_BACKEND, REMOTE_BACKEND)
            sftp.close()
            print(run(cli, f"cd {REMOTE_BACKEND} && docker compose up -d --build", timeout=600))
    finally:
        cli.close()


if __name__ == "__main__":
    main()
