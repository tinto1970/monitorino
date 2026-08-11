/*
 * SPDX-FileCopyrightText: Copyright (C) Arduino s.r.l. and/or its affiliated companies
 *
 * SPDX-License-Identifier: MPL-2.0
 */

// Icone per la matrice LED 8x13 (per-pixel grayscale, 0..7).
// Ogni riga qui sotto rappresenta 13 colonne; ci sono 8 righe.

// Segno di spunta (tutto ok)
const uint8_t ok_icon[104] = {
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0,
  0, 0, 0, 7, 0, 0, 0, 7, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 7, 0, 7, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};

// X (allarme, almeno un server e' giu')
const uint8_t alarm_icon[104] = {
  0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 7, 0, 0,
  0, 0, 0, 0, 7, 0, 0, 0, 0, 7, 0, 0, 0,
  0, 0, 0, 0, 0, 7, 0, 0, 7, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 7, 7, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 7, 7, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 7, 0, 0, 7, 0, 0, 0, 0,
  0, 0, 0, 0, 7, 0, 0, 0, 0, 7, 0, 0, 0,
  0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 7, 0, 0,
};
