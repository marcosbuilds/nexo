# Contas e identidade

O sistema descobre as contas reais disponíveis. Nada importante é hardcoded.

## Descoberta

Mapear:

- perfis do navegador;
- contas Google;
- Gmail/Drive/Calendar quando utilizáveis;
- WhatsApp;
- redes sociais;
- plataformas já autenticadas;
- aplicativos locais relevantes.

## Pool Google

As três contas Google existentes formam o conjunto inicial. A máquina deve descobrir a função mais adequada de cada uma antes de criar outra.

Registrar:

```text
email
display_name
browser_profile
logged_in
services
platform_links
purpose
status
last_verified
```

## Nova conta

Criar somente quando houver necessidade real e sem usar contas extras para burlar restrições, bans, limites ou identidade.

Usar exclusivamente dados reais do proprietário.

## Identificadores exatos

Quando o proprietário fornecer diretamente telefone, e-mail, URL ou ID:

```text
normalizar
→ usar como chave de resolução
→ confirmar pelo estado externo
```

Nunca tratar correspondência aproximada como identidade confirmada.

## Manual

CAPTCHA, OTP, verificação de identidade e criação manual de conta entram na fila humana quando não puderem ser resolvidos por caminho permitido. Não interromper toda a sessão apenas porque um item exige intervenção.
