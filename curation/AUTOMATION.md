# Automação da curadoria do AI Atlas

Proposta; nenhuma conta, cobrança, coleta agendada ou integração externa foi ativada.

## Caminho recomendado

Apify Instagram Scraper → coleta semanal de perfis selecionados → normalização para a fila do Django → revisão editorial → publicação no Atlas.

1. Crie uma conta na Apify e abra https://apify.com/apify/instagram-scraper.
2. Cole os perfis de creator-watchlist.txt. Selecione posts, inicialmente 20 por perfil, e faça uma execução pequena para conferir custo e qualidade.
   Respeite as decisões registradas em `profile-shortlist-awaiting-approval.json`: `blumquist_` foi recusado pela usuária em 25/10/2026 e não deve ser incluído. Mindeye, Gizem Akdag e Ege Berkina foram aprovados.
3. Para uma carga inicial, escolha um período mais amplo. Nas atualizações, use a opção de posts mais recentes que 7 dias e crie um Schedule semanal. A plataforma permite agendamento: https://docs.apify.com/actors/running/schedules.
4. Entregue o dataset ao backend por consulta periódica à API ou webhook autenticado: https://docs.apify.com/integrations/webhooks. Um servidor na internet é necessário para receber webhooks; o endereço 127.0.0.1 atual só atende ao computador local.
5. Implemente um adaptador que transforme os campos do fornecedor no formato de CurationSubmission: URL original, shortcode, autor, data, legenda e capa. O importador atual import_curation já evita repetir o shortcode, mas o JSON bruto da Apify precisa dessa conversão.
6. Uma etapa editorial prepara título e descrição em inglês, registra a evidência de IA, exclui cursos, anúncios de eventos, entrevistas e fotografias sem confirmação. Essa etapa não é uma função de tradução do scraper.
7. Confirme a obra no Curation inbox do admin e publique. O projeto já permite essa revisão. Obras diferentes do mesmo post/carrossel devem ser avaliadas como um projeto, sem multiplicar slides como projetos independentes.
8. Ao publicar, salve a capa localmente, classifique sua cor e preserve os créditos e a fonte. A detecção de cor de capas locais já existe no projeto.

## O que ainda precisa ser conectado

- Conta e token do fornecedor, guardado em variável de ambiente do backend.
- Adaptador Apify → fila de curadoria, com validação e deduplicação.
- Agendamento da coleta e recepção autenticada dos resultados.
- Preparação editorial em inglês, com revisão antes de publicar.
- Orçamento e limite de posts por execução, definidos na conta do fornecedor.

## Alternativa

Bright Data também oferece API de posts públicos e saída estruturada em JSON: https://docs.brightdata.com/products/scrapers/overview. O comando import_instagram_scrape do projeto já trabalha com o formato usado nos lotes anteriores; novos resultados ainda precisam de revisão editorial antes da publicação.

Uma base genérica de imagens geradas por IA pode ajudar na pesquisa visual, mas não garante autores, projetos publicados e links originais para esta curadoria. A base própria de criadores é o caminho indicado para manter o estilo do Atlas.
