> **Autonomia 2.5:** este documento é compatível com a camada ativa somente como referência histórica. A regra superior é `docs/core.md`. O worker é o ator principal; missão vem antes da ação; Humanizer orienta a estratégia e a forma da conversa antes do rascunho e também participa do gate final.

# Natural Conversation — Autonomia 2.1

O objetivo não é parecer "mais humano" por repetir sinais de conversa humana. É remover decisões linguísticas automáticas que não servem à conversa.

## Antes de escrever

Perguntar internamente:

```text
preciso reconhecer a mensagem ou posso responder direto?
qual é a informação útil agora?
qual é a única mudança que quero provocar?
qual é a menor pergunta que destrava o próximo passo?
```

## Vícios bloqueados

Evitar como reflexo de abertura:

```text
Ótimo!
Perfeito!
Entendi.
Claro!
Com certeza!
```

Essas expressões não são proibidas em toda situação. O problema é a repetição automática, principalmente no começo de cada resposta.

Também evitar excesso de `:` em conversa comum. Dois-pontos permanecem válidos para URLs, horários, código, rótulos necessários e dados estruturados.

## Humanizer + hard gate

O Humanizer continua responsável pela reescrita. Depois dele, `tools/humanize.py` faz uma verificação objetiva.

```text
draft
→ Humanizer
→ lexical/naturalness guard
→ factual QA
→ packaging
→ send
```

Falha no guard = regenerar. Não enviar o rascunho ruim.

## Estado do cliente

A máquina deve reconhecer o ponto em que a pessoa está:

```text
prospect
→ qualified
→ trial_requested
→ trial_started
→ trial_completed
→ offer_sent
→ negotiating
→ won
→ payment_requested
→ payment_verified
→ delivered
→ satisfaction_confirmed
→ review_requested
→ repeat_candidate
```

Não repetir uma etapa que já foi concluída sem motivo. Um cliente que já fez um teste não deve receber o mesmo teste de novo apenas porque a conversa foi reaberta.

## Pós-venda

Depois de entregar, a máquina não termina automaticamente. Ela verifica consequência real, confirma satisfação quando apropriado, pede avaliação somente depois de um sinal positivo e identifica uma próxima oportunidade legítima de repetição.
