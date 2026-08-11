// SPDX-FileCopyrightText: Copyright (C) Arduino s.r.l. and/or its affiliated companies
//
// SPDX-License-Identifier: MPL-2.0

#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>
#include <Arduino_Modulino.h>

#include "monitor_frames.h"

Arduino_LED_Matrix matrix;
ModulinoBuzzer buzzer;
bool buzzerReady = false;

void playAlarmTone() {
  if (!buzzerReady) {
    return;
  }
  buzzer.tone(880, 150);
  delay(200);
  buzzer.tone(659, 150);
  delay(200);
  buzzer.tone(880, 150);
  delay(200);
  buzzer.noTone();
}

void setup() {
  Serial.begin(115200);

  matrix.begin();
  matrix.clear();

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
  // Qwiic, begin() returns false and playAlarmTone() becomes a no-op.
  Modulino.begin();
  buzzerReady = buzzer.begin();
  Serial.println(buzzerReady ? "Modulino Buzzer found" : "Modulino Buzzer not found, audio alarm disabled");

  Bridge.begin();
}

void loop() {
  static bool blinkOn = false;
  static bool wasAlarm = false;

  String status;
  bool ok = Bridge.call("get_monitor_status").result(status);
  bool alarm = ok && status == "alarm";

  if (alarm) {
    matrix.draw(alarm_icon);
    analogWrite(LED3_R, 255);
    analogWrite(LED3_G, 0);
    analogWrite(LED3_B, 0);

    blinkOn = !blinkOn;
    digitalWrite(LED4_R, blinkOn ? LOW : HIGH);

    if (!wasAlarm) {
      playAlarmTone();  // beep once, right when the alarm starts
    }
  } else {
    matrix.draw(ok_icon);
    analogWrite(LED3_R, 0);
    analogWrite(LED3_G, 255);
    analogWrite(LED3_B, 0);
    digitalWrite(LED4_R, HIGH);
  }

  wasAlarm = alarm;
  delay(500);
}
