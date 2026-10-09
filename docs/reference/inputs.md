# Media & Inputs — Autonomia 2.1

A mensagem recebida não é necessariamente texto. O worker deve primeiro descobrir o que realmente consegue acessar e só então decidir como interpretar.

## Regra operacional

```text
mensagem
→ classificar tipo
→ verificar capacidade real da sessão/plataforma
→ tentar a menor operação útil
→ registrar sucesso ou falha
→ responder com base no resultado
```

Tipos mínimos: texto, áudio, imagem, vídeo, documento, sticker e visualização única.

O worker não pode dizer que ouviu, viu ou assistiu algo sem uma operação de acesso/análise concluída.

## Áudio

Se o arquivo puder ser baixado e transcrito, usar a transcrição como entrada da conversa.

Quando a transcrição falhar, a resposta deve ser curta e operacional:

> Não consegui ouvir esse áudio agora. Pode me mandar em texto?

A mesma regra vale para WhatsApp, Facebook, Instagram, e-mail ou outro canal. O canal muda a ferramenta, não a honestidade do diagnóstico.

## Visualização única

Quando a sessão web não consegue abrir mídia de visualização única, não insistir em cliques repetidos nem fingir que o conteúdo foi lido.

Solicitar mídia normal ou texto. O cliente não precisa saber detalhes internos do navegador.

## Imagens e vídeos

Quando existir capacidade real de preview/visão, executar antes de perguntar ao cliente o que há na mídia.

Se a tentativa falhar, pedir reenvio normal ou descrição apenas quando a mídia for necessária para continuar.

## Evidência

Cada tentativa de mídia deve registrar:

```text
media_type
access_status
operation
status
error_class
capability_evidence_ref
```

Isso permite aprender quais capacidades são realmente confiáveis por plataforma e conta, em vez de assumir que "WhatsApp suporta X".
