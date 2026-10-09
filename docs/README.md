# Documentação do Nexo

## Ativo

- [core.md](core.md): único núcleo normativo geral.
- [context.md](context.md): pacote curto carregado por ciclo.
- [foundations.md](foundations.md): pesquisa e fundamentos usados sob demanda.

## Referência sob demanda

`reference/` contém playbooks de canal, domínio e operação. Eles detalham uma
decisão específica e não substituem o núcleo.

## Histórico

`legacy/` contém documentos das arquiteturas 2.x. Eles podem explicar decisões
anteriores, mas não são instruções do runtime. O plano extenso foi retirado do
fluxo operacional justamente para não consumir contexto nem reintroduzir regras
contraditórias.

## Regra de precedência

1. limites executáveis e estado real;
2. `config/identity.json` e `docs/core.md`;
3. `docs/context.md`;
4. política específica necessária para a operação;
5. fundamentos e playbooks sob demanda;
6. histórico apenas para entender uma migração.

Quando duas fontes discordarem, não concilie por texto: registre o conflito,
aplique a fonte superior e remova ou arquive a fonte inferior.
