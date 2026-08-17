// SPDX-FileCopyrightText: Copyright (C) Arduino s.r.l. and/or its affiliated companies
//
// SPDX-License-Identifier: MPL-2.0

#include <Arduino_LED_Matrix.h>
#include <ArduinoGraphics.h>
#include <Arduino_RouterBridge.h>
#include <Arduino_Modulino.h>

Arduino_LED_Matrix matrix;
ModulinoBuzzer buzzer;
bool buzzerReady = false;

// Called from Python (via Bridge.notify) once per day at each configured
// SUMMARY_HOURS slot, only while the alarm is still active.
void playAlarmTone() {
  if (!buzzerReady) {
    return;
  }
  // 440Hz rather than a lower pitch: this is a passive piezo buzzer, which
  // is much quieter below ~1kHz (resonance is around 2-4kHz), so a truly
  // "low" tone would barely be audible.
  buzzer.tone(440, 3000);  // 3s; the module times it, so this call is non-blocking
}

// Called from Python (via Bridge.notify) once, right when the alarm clears.
void playRecoveryTone() {
  if (!buzzerReady) {
    return;
  }
  buzzer.tone(523, 600);  // C5
  delay(650);
  buzzer.tone(659, 600);  // E5
  delay(650);
  buzzer.tone(784, 700);  // G5, ~2s total, last note rings out in the background
}

// Queried by Python (via Bridge.call) to log whether the buzzer was found.
bool getBuzzerStatus() {
  return buzzerReady;
}

// Draws "OKn" or "KOn" (no colon: at Font_4x6's 4px/char it wouldn't fit
// the 13-column matrix alongside the label and digit).
void drawCount(const char *label, int count) {
  matrix.clear();
  matrix.beginText(0, 1, 0xFFFFFF);
  matrix.print(label);
  matrix.print(count);
  matrix.endText();
}

void setup() {
  Serial.begin(115200);

  matrix.begin();
  matrix.clear();
  matrix.textFont(Font_4x6);

  pinMode(LED4_R, OUTPUT);
  pinMode(LED4_G, OUTPUT);
  pinMode(LED4_B, OUTPUT);
  digitalWrite(LED4_R, HIGH);  // active-low: HIGH = off
  digitalWrite(LED4_G, HIGH);
  digitalWrite(LED4_B, HIGH);

  analogWrite(LED3_R, 0);
  analogWrite(LED3_G, 0);
  analogWrite(LED3_B, 0);

  // Modulino Buzzer is optional: if it's not physically connected via
  // Qwiic, begin() returns false and playAlarmTone()/playRecoveryTone()
  // become no-ops.
  Modulino.begin();
  buzzerReady = buzzer.begin();

  Bridge.begin();
  Bridge.provide("play_alarm_tone", playAlarmTone);
  Bridge.provide("play_recovery_tone", playRecoveryTone);
  Bridge.provide("get_buzzer_status", getBuzzerStatus);
  Serial.println(buzzerReady ? "Modulino Buzzer found" : "Modulino Buzzer not found, audio alarm disabled");
}

void loop() {
  static bool blinkOn = false;
  static bool showOk = true;
  static unsigned long lastBlink = 0;
  static unsigned long lastSwap = 0;
  unsigned long now = millis();

  String status;
  bool ok = Bridge.call("get_monitor_status").result(status);
  bool alarm = ok && status == "alarm";

  if (now - lastBlink >= 500) {
    lastBlink = now;
    if (alarm) {
      analogWrite(LED3_R, 255);
      analogWrite(LED3_G, 0);
      analogWrite(LED3_B, 0);
      blinkOn = !blinkOn;
      digitalWrite(LED4_R, blinkOn ? LOW : HIGH);
    } else {
      analogWrite(LED3_R, 0);
      analogWrite(LED3_G, 255);
      analogWrite(LED3_B, 0);
      digitalWrite(LED4_R, HIGH);
    }
  }

  // Matrix is too small (8x13) to show "OK: n" and "KO: n" at once, so it
  // alternates between the two counts every 1.5s instead.
  if (now - lastSwap >= 1500) {
    lastSwap = now;
    showOk = !showOk;

    String counts;
    int okCount = 0;
    int koCount = 0;
    if (Bridge.call("get_host_counts").result(counts)) {
      int comma = counts.indexOf(',');
      if (comma >= 0) {
        okCount = counts.substring(0, comma).toInt();
        koCount = counts.substring(comma + 1).toInt();
      }
    }

    drawCount(showOk ? "OK" : "KO", showOk ? okCount : koCount);
  }

  delay(50);  // throttle get_monitor_status polling; still responsive for the 500ms blink
}
