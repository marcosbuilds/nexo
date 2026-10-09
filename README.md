# Nexo

Nexo é um worker digital orientado a resultado. O nome representa a ligação
entre contexto, memória, decisão e ação; não é o nome da empresa em que ele
opera nem o nome do proprietário das contas.

Esta árvore inicia uma linha de desenvolvimento limpa em `0.1.0`. O worker
restaura estado, escolhe uma missão, planeja a menor ação útil, executa por
adaptadores, verifica consequências e registra aprendizado. Ele não fica
esperando ordens para cada clique e não pede micropermissão para ações rotineiras
já cobertas por acesso conectado e mandato.

## Comece pela arquitetura curta

- `docs/core.md` — contrato comportamental único.
- `docs/context.md` — pacote compacto para cada ciclo.
- `docs/foundations.md` — pesquisa que sustenta o desenho, sob demanda.
- `config/identity.json` — identidade do software e separação do dono.
- `manifest.json` — requisitos de release e fontes ativas.

O runtime não deve carregar o projeto inteiro. Políticas específicas entram
quando a operação precisar delas; histórico em `docs/legacy/` nunca é regra.

## Execução local

```powershell
python -m pytest -q
python -m compileall -q agents adapters core runtime tools
python tools/package.py
python tools/audit.py
python tools/legacy.py
```

O worker pode operar sem executor externo para planejar e registrar uma missão.
Adaptadores de navegador, Gmail, WhatsApp e mídia são conectados somente quando
as contas, permissões e dependências reais existirem.

## Dados privados

`memory/owner.json` é runtime local e não deve ser versionado.
Comece por `config/owner.example.json`. Banco operacional, perfis de
navegador, logs, screenshots e arquivos de sessão ficam fora do pacote.

## Versionamento e publicação

O versionador fica fora deste diretório em `D:\Project\tools\nexo-versioner`.
Ele exige testes, compilação, auditorias, manifesto consistente, versão
semântica, ausência de PII/segredos, working tree controlado, tag e remote antes
de permitir um upload.

```powershell
python D:\Project\tools\nexo-versioner\versioner.py audit --repo D:\Project\testes\autonomia
python D:\Project\tools\nexo-versioner\versioner.py release --repo D:\Project\testes\autonomia --version 0.1.0 --message "Initial Nexo release" --push --confirm
```

O repositório inicial deve ser privado. Torná-lo público é uma decisão separada
porque adaptadores, políticas e exemplos podem revelar mais contexto operacional
do que o necessário.
