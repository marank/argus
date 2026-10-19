"""Gunicorn settings. Only the worker count is configurable (APP_WORKERS)."""

import multiprocessing
import os

bind = "127.0.0.1:8000"
workers = int(os.environ.get("APP_WORKERS") or min(multiprocessing.cpu_count() * 2 + 1, 5))
threads = 2
timeout = 60
graceful_timeout = 25
keepalive = 5
# Recycle workers now and then to keep memory in check.
max_requests = 1000
max_requests_jitter = 100
worker_tmp_dir = "/dev/shm"
# The root filesystem is read-only; keep the control socket (gunicornc) in /tmp.
control_socket = "/tmp/gunicorn.ctl"
forwarded_allow_ips = "127.0.0.1"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info").lower()
