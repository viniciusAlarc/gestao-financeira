# Retrabalho

- 2026-11-03 — **Fase 4, ação "Paguei":** o pagamento filtrava o previsto pela conta padrão e
  retornava 404 quando a conta padrão mudava. Corrigido para usar a conta do próprio previsto.
  Causa: assumi que a conta padrão delimitava o escopo do pagamento.
