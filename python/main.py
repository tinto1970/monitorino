# SPDX-FileCopyrightText: Copyright (C) Arduino s.r.l. and/or its affiliated companies
#
# SPDX-License-Identifier: MPL-2.0

"""Monitorino: monitora server sulla rete locale, avvisa via email Gmail,
matrice LED e LED di stato quando uno risulta giu'."""

import logging
import os
import smtplib
import socket
import subprocess
import time
from email.mime.text import MIMEText
from pathlib import Path

import yaml
from dotenv import load_dotenv

from arduino.app_utils import App, Bridge

# python/main.py -> risali di un livello per arrivare alla root dell'app
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("monitorino")


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    servers = data.get("servers") or []
    if not servers:
        raise ValueError(f"Nessun server definito in {CONFIG_PATH}")
    return servers


class Settings:
    def __init__(self):
        load_dotenv(BASE_DIR / ".env")
        self.gmail_user = self._require("GMAIL_USER")
        self.gmail_app_password = self._require("GMAIL_APP_PASSWORD")
        self.gmail_to = [addr.strip() for addr in self._require("GMAIL_TO").split(",")]
        self.check_interval = int(os.environ.get("CHECK_INTERVAL_SECONDS", "60"))
        self.check_timeout = int(os.environ.get("CHECK_TIMEOUT_SECONDS", "3"))
        self.failure_threshold = int(os.environ.get("FAILURE_THRESHOLD", "3"))

    @staticmethod
    def _require(name):
        value = os.environ.get(name)
        if not value:
            raise ValueError(
                f"Variabile d'ambiente {name} mancante. "
                f"Copia .env.example in .env e compilala."
            )
        return value


def ping(host, timeout):
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except FileNotFoundError:
        log.warning("Comando 'ping' non trovato nel container")
        return False


def check_port(host, port, timeout):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_server(server, timeout):
    host = server["host"]
    if not ping(host, timeout):
        return False
    port = server.get("port")
    if port and not check_port(host, port, timeout):
        return False
    return True


def send_email(settings, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.gmail_user
    msg["To"] = ", ".join(settings.gmail_to)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(settings.gmail_user, settings.gmail_app_password)
        smtp.sendmail(settings.gmail_user, settings.gmail_to, msg.as_string())

    log.info("Email inviata: %s", subject)


def notify_down(settings, name, host):
    try:
        send_email(
            settings,
            subject=f"[monitorino] {name} NON RAGGIUNGIBILE",
            body=(
                f"Il server '{name}' ({host}) non risponde da "
                f"{settings.failure_threshold} controlli consecutivi."
            ),
        )
    except smtplib.SMTPException as exc:
        log.error("Invio email di allarme fallito per %s: %s", name, exc)


def notify_up(settings, name, host):
    try:
        send_email(
            settings,
            subject=f"[monitorino] {name} di nuovo raggiungibile",
            body=f"Il server '{name}' ({host}) e' tornato raggiungibile.",
        )
    except smtplib.SMTPException as exc:
        log.error("Invio email di ripristino fallito per %s: %s", name, exc)


servers = load_config()
settings = Settings()

log.info(
    "Avvio monitorino: %d server, intervallo %ds, soglia guasto %d controlli",
    len(servers), settings.check_interval, settings.failure_threshold,
)

state = {s["name"]: {"failures": 0, "is_down": False} for s in servers}
monitor_status = "ok"


def get_monitor_status():
    return monitor_status


Bridge.provide("get_monitor_status", get_monitor_status)


def check_loop():
    global monitor_status

    for server in servers:
        name = server["name"]
        host = server["host"]
        up = check_server(server, settings.check_timeout)
        st = state[name]

        if up:
            if st["is_down"]:
                log.info("%s (%s) e' tornato su", name, host)
                notify_up(settings, name, host)
            st["failures"] = 0
            st["is_down"] = False
        else:
            st["failures"] += 1
            log.warning(
                "%s (%s) non risponde (%d/%d)",
                name, host, st["failures"], settings.failure_threshold,
            )
            if st["failures"] >= settings.failure_threshold and not st["is_down"]:
                st["is_down"] = True
                notify_down(settings, name, host)

    monitor_status = "alarm" if any(s["is_down"] for s in state.values()) else "ok"
    time.sleep(settings.check_interval)


App.run(user_loop=check_loop)
