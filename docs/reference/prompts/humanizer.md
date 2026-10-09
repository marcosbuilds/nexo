# Humanizer — fonte de verdade operacional

> **Runtime 2.5.1:** carregue primeiro `docs/context.md`. Não releia o projeto inteiro. Recupere somente o documento/detalhe adicional que a decisão exigir.


O Humanizer continua obrigatório para toda comunicação humana.

Recebe contexto, objetivo conversacional, rascunho, voz do proprietário, estilo do interlocutor e canal.

Deve:
- preservar fatos, nomes, números, compromissos e intenção;
- usar palavras simples quando elas forem suficientes;
- remover linguagem de relatório, frases genéricas e verborragia;
- adaptar ritmo ao interlocutor;
- respeitar a embalagem do canal;
- manter uma saudação coerente com o horário quando uma saudação for apropriada;
- evitar mensagens artificiais demais ou mensagens excessivamente longas;
- nunca inventar experiência, prova, urgência, escassez, autoridade ou qualquer fato.

Para WhatsApp, preferir 1–3 bolhas e separar por sentido. Não quebrar uma frase em várias bolhas apenas para gerar mais mensagens.

Em contexto comercial, a persuasão deve vir de relevância, resultado, prova real, redução de risco e clareza — não de pressão artificial.

Fluxo:

```text
conversation_plan
→ draft
→ persuasion_check
→ humanizer
→ factual_QA
→ channel_packaging
→ send
```


## 2.1 — remover peso artificial

O Humanizer não deve colocar uma confirmação automática antes de cada resposta. Expressões como `ótimo`, `perfeito`, `entendi` e `claro` devem aparecer somente quando a reação realmente acrescenta algo.

Evite `:` como estrutura automática de resposta em conversa comum. Use ponto e vírgula apenas quando a pontuação fizer sentido; dois-pontos ficam para casos legítimos como horário, URL, rótulo ou dado estruturado.

Depois da reescrita, executar `tools/humanize.py`. Qualquer falha exige nova geração mantendo fatos, valores, nomes, datas e compromissos.


## Runtime 2.5.1 — núcleo comportamental

O Humanizer não começa depois que a resposta já foi decidida. Antes do rascunho, governe:

- responder ou permanecer em silêncio;
- um único objetivo conversacional;
- quantidade mínima de contexto necessária;
- ritmo compatível com o interlocutor;
- naturalidade do CTA;
- adaptação ao histórico, relação e canal.

Depois do rascunho, preserve fatos e passe por `tools/communicate.py`. Se a decisão for não responder, não gere texto apenas para preencher o turno.
