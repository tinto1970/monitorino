# monitorino

App per Arduino UNO Q che monitora alcuni server sulla rete locale (verifica
di connessione TCP su una porta) e segnala eventuali problemi in tre modi:

- **email** via Gmail (allarme alla caduta, avviso al ripristino)
- **matrice LED 8x13**: segno di spunta se tutto ok, X se almeno un server e' giu'
- **LED di stato** (LED3/LED4 sull'MCU): verde fisso se tutto ok, rosso
  lampeggiante durante un allarme

Un tono d'allarme via Brick `sound_generator` era previsto ma richiede uno
speaker collegato alla board (jack, USB o HDMI) — non presente al momento;
si puo' riaggiungere in futuro (vedi cronologia git per l'implementazione
gia' pronta).

## Architettura

- `python/main.py` (MPU/Linux): esegue i controlli sui server, invia le
  email e pubblica lo stato ("ok"/"alarm") sul Bridge.
- `sketch/sketch.ino` (MCU): interroga periodicamente lo stato via
  `Bridge.call("get_monitor_status")` e aggiorna matrice LED e LED di stato.

## Setup

1. Modifica `config.yaml` con l'elenco dei tuoi server (`name`, `host`, `port`
   opzionale — default 80 se omessa; il ping ICMP non e' usato perche' non
   disponibile dentro il container dell'App).
2. Copia `.env.example` in `.env` e compilalo:
   - `GMAIL_USER`: il tuo indirizzo Gmail mittente.
   - `GMAIL_APP_PASSWORD`: una [App Password](https://myaccount.google.com/apppasswords)
     Gmail (richiede la verifica in 2 passaggi attiva sull'account Google).
   - `GMAIL_TO`: destinatario/i delle notifiche (separati da virgola).
   - `CHECK_INTERVAL_SECONDS`, `CHECK_TIMEOUT_SECONDS`, `FAILURE_THRESHOLD`:
     parametri di monitoraggio (valori di default sensati gia' impostati).

`.env` non va mai committato (e' gia' in `.gitignore`).

## Uso

```bash
arduino-app-cli app start ~/ArduinoApps/monitorino
arduino-app-cli app logs  ~/ArduinoApps/monitorino --follow
arduino-app-cli monitor                                       # log seriali MCU
```

**Attenzione:** solo un'App alla volta puo' girare sulla board — `app start`
ferma automaticamente quella attualmente in esecuzione.

Un server viene considerato "giu'" solo dopo `FAILURE_THRESHOLD` controlli
falliti consecutivi (per evitare falsi allarmi). Alla transizione a "giu'"
vengono attivati email e stato "alarm" su matrice/LED; al ripristino tutto
torna allo stato "ok" ed e' inviata un'email di conferma.
