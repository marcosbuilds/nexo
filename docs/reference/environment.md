# Environment Discovery

Depois que um trabalho é aceito e antes da implementação substancial, descobrir o ambiente real.

Verificar, quando relevante:

```text
aplicativo
sessão
conta
servidor/canal
arquivos
permissões
configuração
credenciais disponíveis
recursos nativos
infraestrutura existente
```

Exemplo para um trabalho de Discord:

```text
verificar Discord
→ verificar conta/sessão
→ verificar servidor/canal
→ verificar Developer Portal
→ verificar app/bot existente
→ verificar permissões
→ decidir arquitetura
→ testar no ambiente real
```

Segredos não devem ser colocados em prompts, logs ou arquivos de trabalho desnecessários.
