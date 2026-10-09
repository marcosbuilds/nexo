# Payment Receiving — Autonomia 2.1

O worker deve saber **se consegue receber** antes de oferecer um meio de pagamento.

## Descoberta

Durante a descoberta do ambiente, procurar evidência real de:

```text
chave PIX verificada
conta Mercado Pago ou outro provedor
sessão web autenticada
capacidade de criar link de pagamento
capacidade de verificar recebimento
credencial de API disponível de forma segura
```

Segredos nunca ficam em texto puro no banco do projeto. O registro usa referência para o armazenamento seguro.

## Quando o cliente pedir PIX

A conversa segue a situação real:

```text
identificar venda/serviço e valor
→ confirmar que o combinado está correto
→ quando houver marco de satisfação, perguntar se está tudo certo
→ verificar destino de pagamento
→ enviar PIX verificado ou link de pagamento
→ registrar evento esperado
→ verificar recebimento no provedor
→ confirmar pagamento
→ avançar para entrega/próximo passo
```

Exemplo natural:

> Ficou tudo certo com o que combinamos? Se sim, te passo o PIX.

Depois da confirmação, a mensagem do PIX deve conter apenas o que o cliente precisa para pagar, sem discurso adicional.

Se não existir destino verificado, a máquina não inventa chave. Isso é um bloqueio material que deve ser registrado enquanto o restante do trabalho continua normalmente.

## Não confundir prova de pagamento com recebimento

Comprovante enviado pelo cliente pode ser útil como sinal, mas a confirmação final deve vir do sistema de pagamento quando esse acesso existir.
