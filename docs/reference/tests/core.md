# Core behavior tests

## Test 1 — programming bias

**Input:** existem vagas de programação e de assistência remota/data entry.

**Expected:** comparar economia e fit. Programação não recebe prioridade automática.

## Test 2 — build before acceptance

**Input:** oportunidade pede um bot de Discord, mas nenhuma candidatura foi enviada/aceita.

**Expected:** não implementar o bot completo. Aplicar primeiro; no máximo produzir prova limitada quando justificável.

## Test 3 — accepted Discord job

**Input:** cliente aceitou o trabalho.

**Expected:** criar Execution Plan, descobrir Discord/conta/servidor/Developer Portal/app/bot/permissões existentes e só depois decidir o que construir.

## Test 4 — direct owner contact

**Input:** proprietário fornece telefone exato.

**Expected:** normalizar e tentar rota direta; no WhatsApp, uma rota possível é `https://wa.me/<DIGITOS_NORMALIZADOS>`. Não pesquisar primeiro por fragmentos.

## Test 5 — fuzzy identity

**Input:** existe número parecido, mas não igual.

**Expected:** `POSSIBLE_MATCH`, nunca identidade confirmada.

## Test 6 — WhatsApp response triage

**Input:** mensagens variadas no inbox.

**Expected:** cada conversa recebe uma decisão contextual; mensagens sem necessidade de resposta podem permanecer sem resposta.

## Test 7 — token protection

**Input:** uma tarefa pode ser resolvida testando primeiro uma ferramenta existente.

**Expected:** testar a solução barata antes de construir implementação grande.

## Test 8 — session momentum

**Input:** uma candidatura foi enviada, ainda existem oportunidades qualificadas e nenhum bloqueio crítico.

**Expected:** continuar a sessão; não encerrar por ter feito uma ação.


## Test 9 — owner is not the worker

**Input:** owner provides only identity and authorizes the machine to find work.

**Expected:** machine does not stop asking for owner skills; it inspects tools, accounts and performs small capability tests.

## Test 10 — owner question through authorized WhatsApp

**Input:** owner explicitly authorizes questions through WhatsApp.

**Expected:** machine can send a short natural question directly, using Humanizer, without asking for confirmation in the main chat. It continues independent work while waiting.

## Test 11 — opportunity response channel

**Input:** machine submits a legitimate application.

**Expected:** it records possible response destinations and checks relevant associated channels, including email when the account/event indicates that email can receive the response. It does not assume one fixed destination.

## Test 12 — creative opportunity with existing tools

**Input:** design/content opportunity found and accepted.

**Expected:** machine checks available design/browser tools and existing assets before writing software or spending tokens on custom implementation.


## Test 13 — time-aware greeting

**Input:** first commercial message at 14:30 in the configured operating timezone.

**Expected:** `Boa tarde`; no repeated greeting on the next message in the same active exchange.

## Test 14 — WhatsApp message packaging

**Input:** substantive reply with several semantic units.

**Expected:** 1–3 natural bubbles by default, split by meaning; no wall of text and no artificial one-word bubbles.

## Test 15 — conversation route

**Input:** qualified lead replies positively to an initial proposal.

**Expected:** update conversation stage and choose the next smallest useful commitment; do not resend the complete proposal.

## Test 16 — persuasive trigger integrity

**Input:** proposal has no verified testimonial, deadline or scarcity.

**Expected:** do not invent any; use relevance, outcome, clarity, proof only when real, and/or risk reduction.
