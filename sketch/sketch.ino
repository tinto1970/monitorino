// SPDX-FileCopyrightText: Copyright (C) Arduino s.r.l. and/or its affiliated companies
//
// SPDX-License-Identifier: MPL-2.0

#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>

#include "monitor_frames.h"

Arduino_LED_Matrix matrix;

void setup() {
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

  Bridge.begin();
}

void loop() {
  static bool blinkOn = false;

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
  } else {
    matrix.draw(ok_icon);
    analogWrite(LED3_R, 0);
    analogWrite(LED3_G, 255);
    analogWrite(LED3_B, 0);
    digitalWrite(LED4_R, HIGH);
  }

  delay(500);
}
