# Memória — Autonomia v2.0

A memória deve impedir esquecimento e, principalmente, impedir mistura de contextos.

## Entidades

```text
OWNER
ACCOUNT
PERSON
RELATIONSHIP
CONVERSATION
MESSAGE
OPPORTUNITY
APPLICATION
JOB
TASK
GOAL
ACTION
DECISION
FACT
EVIDENCE
TOOL
STRATEGY
EXPERIMENT
SESSION
BLOCKER
FINANCIAL_EVENT
```

## Regra de recuperação

Quando o contexto atual não contém um fato importante:

```text
buscar histórico
→ verificar evidência
→ carregar contexto
→ agir
```

Nunca preencher lacunas por imaginação.

## Fatos

Cada fato persistente deve registrar fonte, confiança e data da última confirmação. Informações voláteis devem ser verificadas no ambiente real quando influenciarem uma decisão.

## Relações

Memória social deve guardar relacionamento e contexto sem transformar automaticamente amigos ou conversas pessoais em leads.

## Decisões

Guardar motivo resumido, opções consideradas, resultado e evidência. O banco não deve depender de transcrições do raciocínio interno do modelo.

## Diário

`workspace/journal/` + tabela `work_diary` registram passos operacionais, resultados e próximos passos.

## Memória comercial 2.1

Para contatos comerciais, guardar o ciclo de relacionamento e eventos materiais:

```text
trial
proposal
negotiation
payment
delivery
satisfaction
review
repeat
```

O histórico é usado para impedir repetição inútil. Exemplo: `trial_completed` significa que o mesmo teste não deve ser solicitado novamente, salvo uma razão nova e registrada.

Scores de prioridade e estados de pagamento também devem registrar evidência e confiança separadamente.
