"""Run in the activated PythonAnywhere virtualenv after uploading data and media."""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser(description='Prepara o AI Atlas no PythonAnywhere.')
    parser.add_argument('--host', default=f'{getpass.getuser()}.pythonanywhere.com')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', args.host) or '.' not in args.host:
        parser.error('Informe somente o dominio, sem https:// ou barras.')
    root = Path(__file__).resolve().parent.parent
    database = root / 'db.sqlite3'
    if not database.is_file():
        parser.error('Envie e extraia os pacotes de dados primeiro. O banco db.sqlite3 esta ausente.')
    with closing(sqlite3.connect(f'{database.as_uri()}?mode=ro', uri=True)) as connection:
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            parser.error('A verificacao do banco falhou. Envie novamente a copia local.')
        count = connection.execute('SELECT COUNT(*) FROM archive_project').fetchone()[0]
    private = Path.home() / '.config/ai-atlas/production.json'
    private.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if private.exists():
        existing = json.loads(private.read_text(encoding='utf-8'))
        if existing.get('host') != args.host or not isinstance(existing.get('secret_key'), str) or len(existing['secret_key']) < 50:
            parser.error('Ja existe uma configuracao diferente ou incompleta. Revise o arquivo privado sem substituir a chave automaticamente.')
    else:
        with private.open('x', encoding='utf-8') as output:
            json.dump({'host': args.host, 'secret_key': secrets.token_urlsafe(64)}, output)
    private.chmod(0o600)
    backup = database.with_name('db.before-pythonanywhere-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f') + '.sqlite3')
    with closing(sqlite3.connect(database)) as source, closing(sqlite3.connect(backup)) as target:
        source.backup(target)
    environment = {**os.environ, 'DJANGO_SETTINGS_MODULE': 'config.pythonanywhere', 'ATLAS_CONFIG_PATH': str(private)}
    for command in [('check',), ('migrate', '--noinput'), ('collectstatic', '--noinput')]:
        subprocess.run([sys.executable, 'manage.py', *command], cwd=root, env=environment, check=True)
    print(f'Preparacao concluida: {count} projetos. A chave secreta foi guardada fora do repositorio.')
    print(f'Na aba Web, configure o dominio {args.host}, o ambiente ai-atlas-env e o arquivo WSGI.')
    print(f'Arquivos estaticos: /static/ -> {root / "staticfiles"}')
    print(f'Midias: /media/ -> {root / "media"}')
    print('Ative Force HTTPS antes de abrir o site e clique em Reload.')


if __name__ == '__main__':
    main()
