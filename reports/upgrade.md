# Autonomia V2.0 — revisão de comportamento 2026-10-07

## Objetivo

Reduzir os comportamentos artificiais observados na comunicação e impedir encerramento prematuro do trabalho.

## O que foi reforçado

### Comunicação
- saudação baseada no fuso configurado e no momento real de abertura/reabertura;
- mensagens por bolhas, divididas por sentido e não por corte arbitrário;
- linguagem simples e direta;
- roteiro vivo da conversa comercial;
- objetivo conversacional por turno;
- seleção limitada de mecanismos de persuasão baseados em fatos;
- objeções tratadas pela causa real;
- follow-up com motivo/valor novo e limite de tentativas;
- Humanizer + QA + embalagem por canal como pipeline explícito.

### Autonomia
- `WAITING_FOR_EVENT` separado de `ENDED`;
- ciclo de procura de trabalho quando a fila imediata fica vazia;
- verificação das consequências de ações anteriores antes de esperar;
- acompanhamento oportunístico de WhatsApp/e-mail sem interromper toda tarefa por mensagem não urgente;
- persistência de próximo despertar e estado da tarefa;
- proibição de falso trabalho apenas para manter atividade.

### Persistência
Foram adicionadas entidades para:

```text
conversation_plans
conversation_followups
session_wait_states
```

## Helpers determinísticos

```text
tools/greeting.py
tools/message_segmenter.py
tools/session.py
```

## Validação executada

```text
legacy audit → PASS
decision audit → PASS
schema initialization → PASS
behavioral self-test → PASS
manifest file-size check → PASS
```

## Limite factual

O pacote enviado contém especificações, prompts, políticas, banco e pequenos helpers, mas não contém implementação executável em `core/`, `agents/` ou `adapters/`. Portanto esta revisão reforça o contrato que o runtime externo deve aplicar; ela não simula uma integração que não está presente no arquivo recebido.
