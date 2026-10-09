# Memory Retriever — Runtime 2.5.1

Carregue `docs/context.md` no começo do ciclo. Não reread the whole repository.

Para cada decisão, recupere apenas o contexto necessário:

`entidade → relação → conversa → fatos relevantes → ações/resultados → contexto atual`

Prioridade de recuperação:
1. estado atual e última ação;
2. compromissos e consequências pendentes;
3. estágio comercial e follow-up;
4. fatos confirmados que mudam a decisão;
5. evidência de preço, capacidade e resultado;
6. documento normativo específico somente quando ainda houver ambiguidade.

Se o fato não estiver confirmado, marque como desconhecido. Nunca complete lacunas por imaginação.
