# Publicar o AI Atlas no PythonAnywhere

Conta: `priscilanassar`. Pasta do projeto: `/home/priscilanassar/ai-atlas`.

## 1. Enviar os dados e a configuração

Na aba **Files**, abra `/home/priscilanassar/ai-atlas` e use **Upload a file** para enviar os três pacotes preparados: `atlas-config.zip`, `atlas-dados-01.zip` e `atlas-dados-02.zip`.

O banco contém os projetos, as contas e as coleções. Ele deve ficar na pasta do projeto, fora de `staticfiles` e `media`. Os pacotes incluem somente mídias referenciadas pelos projetos atuais. As mídias originais no computador permanecem intactas.

No console Bash:

```bash
cd ~/ai-atlas
unzip -n atlas-config.zip
unzip -n atlas-dados-01.zip
unzip -n atlas-dados-02.zip
workon ai-atlas-env
python deploy/setup_pythonanywhere.py --host priscilanassar.pythonanywhere.com
```

`unzip -n` preserva arquivos que já existam. Estes pacotes são para a primeira publicação; não devem substituir o banco de um site que já recebeu novas contas ou alterações. O script verifica o banco, guarda uma cópia antes das migrações, cria uma chave secreta privada, aplica as migrações e reúne os arquivos estáticos. Ele pode ser executado novamente sem trocar a chave. A chave fica em `~/.config/ai-atlas/production.json` e não é mostrada no console.

Se o endereço exibido na aba Web for diferente, use esse endereço no argumento `--host`. Se o script retornar erro, corrija-o antes de configurar o site público.

## 2. Configurar a aplicação na aba Web

1. Selecione **Add a new web app**, **Manual configuration** e **Python 3.13**. Não use a opção que cria um novo projeto Django.
2. Em **Source code** e **Working directory**, informe `/home/priscilanassar/ai-atlas`.
3. Em **Virtualenv**, informe `/home/priscilanassar/.virtualenvs/ai-atlas-env`.
4. Abra o link **WSGI configuration file**, substitua o conteúdo pelo arquivo `deploy/pythonanywhere_wsgi.py` e salve.
5. Em **Static files**, configure:

| URL | Directory |
| --- | --- |
| `/static/` | `/home/priscilanassar/ai-atlas/staticfiles` |
| `/media/` | `/home/priscilanassar/ai-atlas/media` |

6. Ative **Force HTTPS** e clique em **Reload**.
7. Abra o endereço HTTPS indicado na aba Web. Confira o mapa, uma página de projeto com vídeo, o login, o admin e a criação de uma coleção.

As contas do banco enviado continuam disponíveis; a nova chave exige um novo login. Se precisar criar outro administrador, rode no console:

```bash
workon ai-atlas-env
cd ~/ai-atlas
python manage.py createsuperuser --settings=config.pythonanywhere
```

Digite a senha diretamente no terminal; não a envie pelo chat.

## 3. Manutenção

Após confirmar que a extração e a preparação terminaram sem erros, os três arquivos ZIP enviados podem ser excluídos pela aba Files para liberar espaço. Preserve o banco e a pasta `media`. Faça backup dos dados antes de migrações e acompanhe a cota de armazenamento e a renovação da aplicação gratuita.

Novos projetos cadastrados no admin recebem as classificações automáticas e miniaturas já implementadas. Conversões de vídeos com FFmpeg continuam sendo preparadas separadamente.

Os novos arquivos de configuração também devem ser incluídos no próximo commit do código. Dados e mídias continuam fora do Git. Não configure a raiz inteira do projeto como uma pasta pública de arquivos estáticos.

Referências: [publicação de Django](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/), [upload de arquivos](https://help.pythonanywhere.com/pages/UploadingAndDownloadingFiles), [arquivos estáticos](https://help.pythonanywhere.com/pages/DjangoStaticFiles).
