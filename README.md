# Zyxel Toolkit

This toolkit contains a collection of Python scripts for interacting with Zyxel modems. Tools allow you to log in to a modem, fetch and decrypt configuration data, edit accounts and log settings, upload TR069 data and more. The `scripts/` directory provides standalone utilities while common functionality lives under `src/`.

## Setup
1. Ensure Python 3.11 or later is installed.
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

The scripts rely on Selenium for browser automation and Cryptodome for AES operations.

## Running the Toolkit
All utilities can be launched through the command line interface:

```bash
python scripts/cli.py
```

The CLI lists available scripts and runs the selected one with the correct `PYTHONPATH` so modules in `src/` are found.

## Credentials
Scripts that log in to the modem expect credentials to be provided through environment variables:

- `MODEM_USERNAME` – username for the admin interface
- `MODEM_PASSWORD` – password for the admin interface

Set these variables in your shell before running the CLI so the login process can pick them up.
