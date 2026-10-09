# Nexo

Nexo é o nome público deste repositório e do software de origem. O runtime
instalado não usa esse nome como identidade externa: ele carrega o nome do
proprietário ou da empresa autorizado em `memory/owner.json`.

## O que mudou nesta linha

- núcleo comportamental curto, em inglês, carregado uma vez por ciclo;
- conhecimento separado em regras, lições, métodos e fontes JSONL;
- busca local FTS5 com recuperação top-k e proveniência;
- lições para permissões repetidas, contexto misturado, falhas sem recibo,
  pesquisa sem decisão, follow-up sem sinal, identidade e ruído visual;
- humanizer reduzido ao runtime determinístico, sem README, SKILL, changelog ou
  comandos de instalação no pacote instalado;
- zip de runtime separado do repositório público, sem banco operacional, perfil
  privado ou identidade do software.

## Validar a árvore pública

```powershell
python -m pytest -q
python -m compileall -q agents adapters core runtime tools
python tools/index.py --output runtime_data/knowledge.sqlite3
python tools/retrieve.py --query "customer did not reply"
python tools/package.py
python tools/package.py --bundle
python tools/audit.py
python tools/legacy.py
```

O índice e o banco operacional são locais e ignorados pelo Git. O zip atual é
`release/worker-0.2.0.zip`.

## Instalar e atualizar

Gere o pacote e instale em uma pasta de runtime separada:

```powershell
python tools/package.py --bundle
python tools/install.py `
  --bundle release/worker-0.2.0.zip `
  --target D:\Runtime\worker `
  --owner-name "Nome do proprietário" `
  --company-name "Nome da empresa"
```

O instalador não apaga `memory/owner.json`, `runtime_data/`, `.env` ou arquivos
locais existentes. Sem os argumentos de identidade, preenche apenas um perfil
local vazio a partir de `config/profile.json`; não invente dados.

Para atualizar código e conhecimento sem substituir o banco ou o perfil:

```powershell
python tools/package.py --bundle
python tools/update.py `
  --bundle release/worker-0.2.0.zip `
  --target D:\Runtime\worker
```

## Rodar no Codex ou Claude

Depois da instalação, os dois podem executar a mesma pasta de runtime. O
projeto não depende de um plugin de instalação nem carrega a documentação do
repositório inteiro:

```powershell
cd D:\Runtime\worker
python tools/index.py
python tools/execute.py --once
```

Para ciclo contínuo, use `python tools/execute.py --daemon`. Conectores reais
devem ser configurados no ambiente autorizado (`WORKER_DB`,
`WORKER_EXECUTOR_CMD` e `WORKER_BROWSER_PROFILE` quando aplicável). A falta de
um executor não é tratada como sucesso.

## Arquitetura curta

- `docs/core.md`: contrato comportamental ativo.
- `docs/context.md`: pacote mínimo por ciclo.
- `knowledge/*.jsonl`: regras, métodos e lições recuperáveis.
- `knowledge/sources.json`: proveniência e claims de cada registro.
- `tools/index.py` e `tools/retrieve.py`: índice e busca local.
- `config/identity.json`: separação entre identidade externa autorizada e nome
  público do software.
- `tools/package.py`: auditoria e bundle limpo.
- `D:\Project\tools\nexo-versioner\versioner.py`: gate externo de release.

## Release

O versionador externo só libera uma versão após testes, compilação, auditorias,
validação do schema e fontes, auditoria do zip, privacidade, working tree
revisada, commit, tag nova e remote explícito:

```powershell
python D:\Project\tools\nexo-versioner\versioner.py audit `
  --repo D:\Project\testes\autonomia

python D:\Project\tools\nexo-versioner\versioner.py release `
  --repo D:\Project\testes\autonomia `
  --version 0.2.0 `
  --message "Add structured knowledge retrieval and clean runtime bundle" `
  --push --confirm
```

O repositório público contém fontes e instruções de desenvolvimento. O zip
instalado contém apenas o que o worker precisa para atuar.
