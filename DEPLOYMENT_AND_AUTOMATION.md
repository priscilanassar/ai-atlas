# AI Atlas: guia de publicação e automação

## Adicionar um projeto pelo admin

1. Preencha o título em inglês, criador, categoria, descrição e link da fonte. Registre a confirmação de uso de IA pelo fluxo de curadoria existente.
2. Envie a capa no campo **Cover file**. Ao salvar, o sistema cria uma miniatura WebP de até 320 pixels e estima a cor predominante quando **Dominant color** está em branco. O arquivo original é preservado.
3. Deixe **Project type**, **Media format** e **Creative field** em branco para usar a classificação automática. Preencha esses campos quando quiser definir a classificação manualmente. O admin mostra os valores utilizados e indica se vieram da curadoria ou de uma regra automática.
4. Na próxima abertura ou atualização da página, os filtros, as contagens e os grupos do mapa já incluem o novo projeto. Não é necessário manter ou gerar um catálogo JSON separado.

A classificação é executada pelo próprio código do projeto, sem serviço externo de IA nem cobrança de API. O arquivo `archive/classification.py` lê `archive/classification_rules.json` uma vez por processo. As regras são avaliadas na ordem em que aparecem. Depois de editar o JSON, reinicie a aplicação ou publique uma nova versão. Os campos deixados em branco passam a usar as novas regras; as escolhas manuais da curadoria continuam tendo prioridade. Use apenas os valores disponíveis nas opções do modelo.

- **Tipo — Project type:** considera título e descrição. As regras de experimento ou conceito vêm antes das regras comerciais. Quando nenhuma corresponde, usa Art.
- **Área criativa — Creative field:** usa primeiro a escolha manual, depois as regras do título e, por último, a categoria cadastrada.
- **Formato — Media format:** usa primeiro a escolha manual. Depois, considera quantidade e tipo das mídias, link da fonte, categoria e menções a séries no texto. Vários itens de mídia formam uma Series, mesmo que alguns sejam vídeos.
- **Cor — Dominant color:** analisa a capa enviada como arquivo. É uma estimativa que pode ser corrigida manualmente. Uma cor já salva é preservada; para recalculá-la depois de trocar a capa, limpe o campo e salve novamente.
- **Ano — Year:** considera primeiro a data do projeto, depois a data de publicação e, por último, o ano cadastrado, como já ocorre em Maps.
- **País e confirmação de uso de IA:** dependem de informações verificadas. As regras não preenchem essas evidências nem aprovam a publicação de um projeto.

Uma imagem cadastrada apenas por **Image URL**, sem envio de arquivo, continua funcionando, mas não é baixada automaticamente. Nesse caso, falta uma capa local para analisar ou otimizar. Envie a capa revisada pelo admin. Importações que usam `bulk_create` ou `QuerySet.update` não executam a rotina de salvamento do modelo; após essas importações, rode o comando de preparação abaixo.

## Preparar projetos existentes ou revisar um lote

Na pasta que contém `manage.py`, usando o ambiente Python do projeto, execute:

```sh
python manage.py migrate
python manage.py prepare_atlas --dry-run --report reports/atlas-preview.json
python manage.py prepare_atlas --report reports/atlas-prepared.json
```

O primeiro comando aplica as alterações da estrutura do banco. O segundo simula a preparação e gera um relatório sem modificar os projetos ou suas imagens. O terceiro prepara as capas e gera o relatório do resultado.

O comando de preparação pode ser repetido: ele pula capas já preparadas, preenche somente cores ausentes e preserva a classificação manual. Também não baixa arquivos remotos, não confirma uso de IA e não publica projetos. A opção `--force-thumbnails` regenera as miniaturas quando suas configurações mudam ou quando um arquivo original é substituído no mesmo caminho de armazenamento. As imagens e os vídeos originais são preservados.

O arquivo `archive/thumbnails.py` usa a API de armazenamento do Django. Para que os uploads funcionem em Workers, ainda é necessário configurar um serviço de armazenamento compatível com a Cloudflare. A geração de miniaturas precisa ser testada com esse serviço, incluindo a compatibilidade da biblioteca Pillow e os limites de processamento. Conversões maiores de vídeo devem acontecer em uma etapa separada do salvamento pelo admin.

## Otimizações aplicadas

- A página inicial, as coleções, os projetos relacionados e os cartões de seleção do admin usam miniaturas WebP. As imagens são carregadas conforme necessário e decodificadas de forma assíncrona. A página de detalhes mantém a arte original.
- Os vídeos da galeria usam os previews leves existentes, sem carregamento antecipado: até dois simultâneos no celular e quatro no desktop. A reprodução pausa quando a página fica oculta. As fontes de vídeos inativos são liberadas após cinco segundos. Em conexões 2G ou com economia de dados, a reprodução automática é desativada; passar o mouse ou dar foco ainda pode solicitar um preview.
- O efeito de ampliação pelo ponteiro processa apenas cartões de projetos, reduzindo o trabalho feito sobre os quadrados decorativos do globo.
- A consulta da página inicial evita carregar legendas originais do Instagram e campos de evidência que ela não exibe. Metadados de criadores, ferramentas e letras que os mapas não usam foram retirados do HTML.
- As páginas com controles da sessão, coleções pessoais ou tokens CSRF continuam sem cache público compartilhado.

## Publicar tudo na Cloudflare Workers

A arquitetura prevista é: **Python Workers** para executar o Django via WSGI, **D1** para o banco de dados, **R2** para as mídias enviadas e **Workers Static Assets** para CSS, JavaScript, fontes e arquivos estáticos do admin.

Documentação oficial de referência:

- [Django em Python Workers e adaptadores django-cf](https://developers.cloudflare.com/workers/languages/python/packages/django/)
- [Arquivos estáticos em Workers](https://developers.cloudflare.com/workers/static-assets/)
- [Armazenamento R2](https://developers.cloudflare.com/r2/)

**Situação atual: a aplicação local está otimizada. A publicação em Workers ainda não foi configurada, testada ou realizada.** Enviar a pasta inteira não basta: o projeto atual usa um banco SQLite e mídias armazenados localmente. Antes de colocar o site em produção, siga estas etapas:

1. **Preparar o Worker Python.** Use o adaptador WSGI compatível com Django e inclua os templates e o JSON de classificação no pacote. Fixe versões compatíveis de Django, Pillow e django-cf depois de testá-las no ambiente Workers.
2. **Preparar e migrar o banco para D1.** Crie o banco, configure sua conexão com o Worker e teste a migração usando uma cópia atualizada dos dados. Preserve os identificadores e as relações entre usuários, projetos, coleções e projetos salvos. O arquivo `db.sqlite3` não deve ser publicado como arquivo estático público.
3. **Revisar as operações que usam transações.** Os adaptadores D1 e Durable Objects documentados para `django-cf` não oferecem transações com rollback, ou seja, reversão automática das alterações quando uma operação falha. Este projeto usa `transaction.atomic()` na criação de coleções, publicação de itens da curadoria, importações e exclusão de projetos. Esses fluxos precisam de adaptação e testes de falha, repetição e consistência. Trocar apenas a configuração do banco não conclui essa migração.
4. **Configurar o R2 para as mídias.** Transfira os arquivos preservando seus nomes e caminhos e atualize, quando necessário, os endereços de mídia gravados nos dados. Teste novos uploads, miniaturas, vídeos, requisições Range — usadas para carregar trechos dos vídeos — e exclusão de registros. Mantenha backups privados separados dos arquivos públicos.
5. **Preparar os arquivos estáticos.** Execute `collectstatic` para uma pasta de saída dedicada e publique somente essa saída em Static Assets. Confira fontes, CSS do admin e arquivos com versões. Configure cache para mídias e arquivos estáticos; páginas autenticadas, admin, login, coleções pessoais e respostas a POST não devem usar cache público compartilhado.
6. **Configurar o ambiente de produção.** Cadastre uma nova chave secreta em Worker secrets, use `DEBUG=False`, informe os domínios permitidos e as origens confiáveis para CSRF e configure cookies de sessão e CSRF para HTTPS. Use o domínio real de produção e mantenha as credenciais fora do código versionado.
7. **Validar antes de conectar o domínio público.** Em um ambiente de prévia, teste login no admin, inclusão de projetos, classificação e miniaturas automáticas, todos os modos do mapa, privacidade das coleções, ações de salvar e excluir e reprodução de vídeos no celular.

Deixe fora do pacote de código do Worker: `.venv`, `.tools`, `__pycache__`, bancos e backups locais, exportações de scrapers, capturas de tela e a pasta bruta `media`. As mídias devem ser transferidas para o armazenamento próprio. A conversão de vídeos com FFmpeg ou subprocessos deve continuar como uma etapa de preparação separada; o comando atual de preparação de vídeos foi feito para um ambiente Python local.
