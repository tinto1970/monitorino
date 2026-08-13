# SPDX-FileCopyrightText: Copyright (C) Arduino s.r.l. and/or its affiliated companies
#
# SPDX-License-Identifier: MPL-2.0

"""Monitorino: monitora server sulla rete locale, avvisa via email Gmail,
matrice LED e LED di stato quando uno risulta giu'."""

import logging
import os
import smtplib
import socket
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
        self.summary_hours = {
            int(h.strip())
            for h in os.environ.get("SUMMARY_HOURS", "8,20").split(",")
            if h.strip()
        }

        # The App's Docker container always runs on UTC regardless of the
        # board's system timezone, so SUMMARY_HOURS is interpreted against
        # TZ here (with automatic DST handling via the container's tzdata).
        tz = os.environ.get("TZ", "Europe/Rome")
        os.environ["TZ"] = tz
        if hasattr(time, "tzset"):
            time.tzset()

    @staticmethod
    def _require(name):
        value = os.environ.get(name)
        if not value:
            raise ValueError(
                f"Variabile d'ambiente {name} mancante. "
                f"Copia .env.example in .env e compilala."
            )
        return value


def check_port(host, port, timeout):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_server(server, timeout):
    # Il ping ICMP non e' disponibile dentro il container dell'App (nessun
    # binario 'ping' ne' privilegi per raw socket), quindi la raggiungibilita'
    # si verifica con una connessione TCP sulla porta indicata (default 80).
    host = server["host"]
    port = server.get("port", 80)
    return check_port(host, port, timeout)


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


def build_summary_body(servers, state):
    lines = ["Riepilogo dello stato dei server monitorati:", ""]
    for server in servers:
        name = server["name"]
        host = server["host"]
        port = server.get("port", 80)
        status = "DOWN" if state[name]["is_down"] else "OK"
        lines.append(f"- {name} ({host}:{port}): {status}")
    return "\n".join(lines)


def notify_summary(settings, servers, state):
    all_ok = all(not s["is_down"] for s in state.values())
    subject = (
        "[monitorino] Riepilogo: tutti gli host sono OK"
        if all_ok
        else "[monitorino] Riepilogo: alcuni host in allarme"
    )
    try:
        send_email(settings, subject=subject, body=build_summary_body(servers, state))
    except smtplib.SMTPException as exc:
        log.error("Invio email di riepilogo fallito: %s", exc)


servers = load_config()
settings = Settings()

log.info(
    "Avvio monitorino: %d server, intervallo %ds, soglia guasto %d controlli",
    len(servers), settings.check_interval, settings.failure_threshold,
)

state = {s["name"]: {"failures": 0, "is_down": False} for s in servers}
monitor_status = "ok"
last_summary_date = {}


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

    now = time.localtime()
    if now.tm_hour in settings.summary_hours:
        today = (now.tm_year, now.tm_yday)
        if last_summary_date.get(now.tm_hour) != today:
            notify_summary(settings, servers, state)
            last_summary_date[now.tm_hour] = today

    time.sleep(settings.check_interval)


App.run(user_loop=check_loop)
