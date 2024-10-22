# Leetcode Bot

## Setup

Make sure you are running Python version 3.12

Try running `python3 --version`. If the version is not 3.12, press WinKey -> Edit environment variables for your account -> Path -> Edit -> New, then type in your python interpreter path (run `where python3` in cmd). If it is a windows install, then you might need `%localappdata%\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_some_id_here`. Move this all the way up.

Run this command

`pip3 install -r requirements.txt`

Install [PostgreSQL 17](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)

In an elevated terminal, run `createdb lc-bot-data -U postgres`

Configure keys in .env file:
* PG_USER=postgres
* PG_PASSWORD=postgres_or_account_password_here
* PG_DATABASE=lc-bot-data
* PG_HOST=localhost
* PG_PORT=5432

Run with `python3 bot.py`