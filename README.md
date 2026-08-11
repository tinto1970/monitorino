# monitorino

Arduino UNO Q app that monitors a few servers on the local network (TCP
connection check on a port) and reports problems in three ways:

- **email** via Gmail (alert on failure, notice on recovery)
- **8x13 LED matrix**: checkmark when everything is ok, X when at least one
  server is down
- **status LEDs** (LED3/LED4 on the MCU): solid green when ok, blinking red
  during an alarm

An audio alarm via the `sound_generator` Brick was planned but requires a
speaker connected to the board (jack, USB, or HDMI) — not present at the
moment; it can be added back later (see git history for the already-working
implementation).

## Architecture

- `python/main.py` (MPU/Linux): runs the server checks, sends the emails,
  and publishes the status ("ok"/"alarm") on the Bridge.
- `sketch/sketch.ino` (MCU): periodically polls the status via
  `Bridge.call("get_monitor_status")` and updates the LED matrix and status
  LEDs.

## Setup

1. Copy `config.yaml.sample` to `config.yaml` and edit it with your own list
   of servers (`name`, `host`, `port` — optional, defaults to 80 if omitted;
   ICMP ping is not used because it's not available inside the App's
   container).
2. Copy `.env.example` to `.env` and fill it in:
   - `GMAIL_USER`: your sending Gmail address.
   - `GMAIL_APP_PASSWORD`: a Gmail [App Password](https://myaccount.google.com/apppasswords)
     (requires 2-Step Verification enabled on the Google account).
   - `GMAIL_TO`: notification recipient(s), comma-separated.
   - `CHECK_INTERVAL_SECONDS`, `CHECK_TIMEOUT_SECONDS`, `FAILURE_THRESHOLD`:
     monitoring parameters (sensible defaults already set).

`config.yaml` and `.env` must never be committed — both are already in
`.gitignore` so your local network layout and credentials stay private.

## Usage

```bash
arduino-app-cli app start ~/ArduinoApps/monitorino
arduino-app-cli app logs  ~/ArduinoApps/monitorino --follow
arduino-app-cli monitor                                       # MCU serial log
```

**Note:** only one App can run at a time on the board — `app start`
automatically stops whichever one is currently running.

A server is only considered "down" after `FAILURE_THRESHOLD` consecutive
failed checks (to avoid false alarms). On the transition to "down", an email
is sent and the matrix/LEDs switch to the "alarm" state; on recovery
everything returns to the "ok" state and a confirmation email is sent.
