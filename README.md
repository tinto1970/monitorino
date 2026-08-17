# monitorino

Arduino UNO Q app that monitors a few servers on the local network (TCP
connection check on a port) and reports problems in four ways:

- **email** via Gmail (alert on failure, notice on recovery, plus a daily
  summary at configurable hours listing every monitored host and its status)
- **8x13 LED matrix**: alternates every 1.5s between `OK<n>` and `KO<n>`,
  showing the current count of reachable and unreachable hosts (the display
  is too small to fit both counts on screen at once)
- **status LEDs** (LED3/LED4 on the MCU): solid green when ok, blinking red
  during an alarm
- **audio alarm** (optional): a [Modulino Buzzer](https://docs.arduino.cc/hardware/modulino-buzzer/)
  connected via Qwiic. While an alarm is active, a low 3-second tone plays at
  each `SUMMARY_HOURS` slot (same schedule as the summary email) as a daily
  reminder, until the alarm clears; on recovery, a cheerful 2-second tone
  plays once. The buzzer is entirely optional — if it's not connected, the
  sketch detects that at boot and simply skips the sound; email, matrix and
  status LEDs work either way.

An audio alarm via the `sound_generator` Brick was tried first but requires
a speaker connected to the board's audio output — not available on a
headless setup. The Modulino Buzzer works over I2C instead, so it doesn't
have that requirement (see git history for the `sound_generator` version).

## Architecture

- `python/main.py` (MPU/Linux): runs the server checks, sends the emails,
  and publishes the status ("ok"/"alarm") on the Bridge.
- `sketch/sketch.ino` (MCU): periodically polls the status via
  `Bridge.call("get_monitor_status")`, updates the LED matrix and status
  LEDs, and plays a tone on the Modulino Buzzer (if connected) on the
  transition to "alarm".

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
   - `SUMMARY_HOURS`: comma-separated hours (0-23) at which to send a daily
     summary email listing all monitored hosts and their current status,
     regardless of alarms. Defaults to `8,20`.
   - `TZ`: timezone used to interpret `SUMMARY_HOURS` (e.g. `Europe/Rome`,
     with automatic DST handling). The App's Docker container always runs on
     UTC regardless of the board's own system timezone, so this is set
     independently. Defaults to `Europe/Rome`.

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

## License

MIT — see [LICENSE](LICENSE).
