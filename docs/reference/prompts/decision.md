# Decision Engine — saída executável

Use o contexto já carregado. Não produza um plano longo. Para a próxima ação,
preencha:

`goal | context_lock | current_state | action | expected_result | success_evidence | cost_and_risk | authorization_basis | fallback | next_action | stop_condition`

Regras:

1. consequência pendente e compromisso em voo vêm antes de nova oportunidade;
2. conta/recurso conectado autoriza rotina dentro do escopo — execute, não peça
   confirmação;
3. escolha a menor ação que produza resultado ou reduza incerteza relevante;
4. use recurso existente antes de construir;
5. um erro exige inspeção e mudança de estado antes de nova tentativa;
6. toda ação externa termina em recibo, verificação ou bloqueio persistido;
7. conversa pode terminar em `NO_SEND`; pesquisa precisa alterar uma decisão.

Para trabalhos aceitos, descubra ambiente real antes de construir. Para
pesquisa, registre fontes e diferencie fato de inferência. Para conversa,
avance um único estado por vez.
