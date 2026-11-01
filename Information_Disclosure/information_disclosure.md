Information Disclosure:

Quando uma aplicação acidentalmente revela/vaza informações sensíveis para os usuários.
Exemplos:
Nome de diretórios, estrutura e conteúdo via robots.txt ou listagem de diretório.
Acesso ao código fonte por backups temporários.
Menção a base de dados ou nomes de colunas nas mensagens de erro.
Exposição de informação sensível como detalhes de cartão de crédito.
Chaves API, Endereços de IP, credenciais de Banco de dados e outros no código fonte.

![Exposição acidental de informações](<Images/Exposição acidental de informações.png>)

---

Metodologia:

🐛 Bug Bounty — Construindo nosso Attack Playbook

Vamos trabalhar com três perguntas fundamentais:
1. O que procurar? Quais sinais podem indicar a existência de uma vulnerabilidade?
2. Como investigar? Que testes devemos executar para confirmar ou descartar nossas hipóteses?
3. Como aproveitar a descoberta? Que outras vulnerabilidades podemos encontrar a partir das informações obtidas?

🧭 3. Nosso primeiro Attack Playbook
Com base nos seus labs, proponho esta sequência inicial para a etapa de Information Disclosure.

### Fase 1 — Reconhecimento passivo

- [ ] Inspecionar o HTML das páginas e procurar comentários HTML e referências a endpoints ocultos.
- [ ] Buscar arquivos públicos: `robots.txt`, `sitemap.xml`, `.well-known/security.txt`.
- [ ] Enumerar caminhos comuns com o SecLists:

```bash
ffuf -u https://alvo/FUZZ \
     -w /usr/share/seclists/Discovery/Web-Content/common.txt \
     -t 50 -rate 200 -timeout 7 \
     -mc 200,204,301,302,307,401,403 -fc 404 -s
```

Classificar por status: `200` = conteúdo real; `401/403` = recurso protegido (candidato a bypass); `302` = área autenticada; `200` com tamanho 0 ou idêntico ao 404 = possível soft-404.

- [ ] **Métodos HTTP como fonte de informação**
  - `OPTIONS` → lista métodos permitidos (`Allow`).
  - `TRACE` → reflete os headers do request; revela headers internos injetados pelo front-end (ex.: `X-Custom-IP-Authorization`, `X-Forwarded-For`, headers de proxy).
  - Depois de descobrir o header, testar falsificação de IP (`127.0.0.1`, `localhost`, `X-Forwarded-For`) contra endpoints `401/403`.

### Fase 2 — Descoberta ativa

### Fase 3 — Erros e comportamento

### Fase 4 — Código-fonte e metadados

### Fase 5 — Validação e impacto

### Fase 6 — Relatório
