# monitorino

Piccolo script Python che monitora alcuni server sulla rete locale (ping +
porta TCP opzionale) e invia una email tramite Gmail quando un server risulta
irraggiungibile (e quando torna su).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

1. Modifica `config.yaml` con l'elenco dei tuoi server (`name`, `host`, `port`
   opzionale).
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
python3 monitor.py
```

Lo script gira in loop continuo, ricontrollando tutti i server ogni
`CHECK_INTERVAL_SECONDS` secondi. Un server viene considerato "giu'" solo dopo
`FAILURE_THRESHOLD` controlli falliti consecutivi (per evitare falsi allarmi),
e viene inviata una email sia alla caduta sia al ripristino.

## Esecuzione persistente (systemd)

Il repo include `monitorino.service`. Per installarlo come servizio che parte
al boot e si riavvia in caso di crash:

```bash
sudo cp monitorino.service /etc/systemd/system/monitorino.service
sudo systemctl daemon-reload
sudo systemctl enable --now monitorino.service
```

Comandi utili:

```bash
sudo systemctl status monitorino.service
journalctl -u monitorino.service -f
sudo systemctl restart monitorino.service
```

Il servizio esegue `monitor.py` come utente `arduino` dalla directory del
repo, e legge `.env` da li' — assicurati che `.env` sia gia' compilato prima
di avviarlo.
