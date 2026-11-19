"""Importação do extrato da Pluggy para `Movimento` (fase 7, P2-13).

Mapeamento decidido em 2026-11-10, sobre a documentação oficial de
`GET /v2/transactions`:

- data: campo `date` (ISO 8601 em UTC), truncado para a data. Não há campo de
  reserva: `createdAt` é a data de criação do registro na Pluggy, não a do
  lançamento. A doc manda converter para GMT-3 na exibição; o truncamento foi
  adotado porque o exemplo oficial vem como meia-noite UTC (data pura) e a
  conversão jogaria essas transações para o dia anterior. A primeira importação
  real confirma o formato (P2-13).
- tipo: campo `type`; `DEBIT` é despesa e `CREDIT` é receita. Valor diferente
  disso é erro daquela transação, reportado, nunca ignorado.
- valor: sempre positivo, em `Decimal`, a partir de `abs(amount)`. O `amount` da
  Pluggy já vem com sinal (saída negativa, entrada positiva); o sinal não é
  usado porque o `type` diz a mesma coisa de forma explícita.
- status: **só `POSTED` entra**. `PENDING` é pulado e aparece no relatório
  (decisão do dono em 2026-11-10: pendente ainda pode mudar). Se a mesma
  transação virar `POSTED` com o mesmo `id`, entra na importação seguinte.
- chave antiduplicidade: campo `id` em `Movimento.id_externo`. Transação sem id
  é recusada.
- descrição: `description`; se vazia, `descriptionRaw`; truncada em 120.
- categoria: mapa da `category` da Pluggy para as categorias do app (as 23
  categorias do histórico: Alimentação, Compras, Transporte, Saúde, Pets,
  Moradia, Cartão de crédito, Impostos, Investimento, Salário, Rendimentos,
  Lazer e Transferência), depois regras por descrição e, por fim,
  `Não categorizado` do tipo. Uma categoria mapeada só é usada se existir no
  app com o tipo da transação. Movimentos já importados que estão em
  `Não categorizado` são atualizados quando a transação é revista, preservando
  os que o dono categorizou à mão.
- autoria: usuário técnico `Pluggy`, sem senha utilizável e sem privilégio.
- origem: `Movimento.Origem.PLUGGY`.

Nada aqui chama a API: a função recebe a lista de transações já lida pelo
cliente (`pluggy_api.py`). Isso permite testar o mapeamento sem rede.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from .models import Categoria, Movimento, TipoValor

USUARIO_TECNICO = "Pluggy"
TAMANHO_MAXIMO_DESCRICAO = 120
CATEGORIA_PADRAO = "Não categorizado"
# Categoria da Pluggy -> (nome no app, entra no gasto). O nome precisa existir
# no app com o tipo da transação; senão, o importador cai no fallback.
MAPA_CATEGORIAS_PLUGGY = {
    "Food delivery": ("Alimentação", True),
    "Groceries": ("Alimentação", True),
    "Eating out": ("Alimentação", True),
    "Electronics": ("Compras", True),
    "Shopping": ("Compras", True),
    "Clothing": ("Compras", True),
    "Gas stations": ("Transporte", True),
    "Parking": ("Transporte", True),
    "Pharmacy": ("Saúde", True),
    "Dentist": ("Saúde", True),
    "Hospital clinics and labs": ("Saúde", True),
    "Pet supplies and vet": ("Pets", True),
    "Services": ("Moradia", True),
    "Telecommunications": ("Moradia", True),
    "Credit card payment": ("Cartão de crédito", True),
    "Income taxes": ("Impostos", True),
    "Investments": ("Investimento", False),
    "Salary": ("Salário", True),
    "Proceeds interests and dividends": ("Rendimentos", True),
    "Digital services": ("Lazer", True),
    "Transfer - PIX": ("Transferência", False),
    "Same person transfer": ("Transferência", False),
    "Transfers": ("Transferência", False),
}
# Regras por descrição, usadas quando a Pluggy não manda uma categoria mapeada.
# As palavras são comparadas sem acento e em minúsculas.
REGRAS_DESCRICAO = (
    (("ifood", "rappi", "uber eats"), "Alimentação", True),
    (("darf", "receita federal"), "Impostos", True),
    (("transferencia entre contas", "ted"), "Transferência", False),
)
TIPOS_POR_TRANSACAO = {
    "DEBIT": TipoValor.DESPESA,
    "CREDIT": TipoValor.RECEITA,
}
STATUS_QUE_ENTRAM = {"POSTED"}


@dataclass(frozen=True)
class TransacaoPulada:
    """Transação que não entrou porque já existia ou ainda está pendente."""

    id_transacao: str
    motivo: str


@dataclass(frozen=True)
class TransacaoComErro:
    """Transação recusada por dado inválido; o motivo vai no relatório, nunca em silêncio."""

    id_transacao: str
    motivo: str


@dataclass
class RelatorioImportacao:
    """Resultado de uma importação. `dry_run` diz se algo foi gravado de fato."""

    dry_run: bool = False
    criados: list[str] = field(default_factory=list)
    atualizados: list[str] = field(default_factory=list)
    pulados: list[TransacaoPulada] = field(default_factory=list)
    erros: list[TransacaoComErro] = field(default_factory=list)
    # Quantas transações de cada `category` da Pluggy vieram no payload; serve à
    # decisão de mapeamento de categoria (P2-15), sem gravar nada.
    categorias_vistas: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        """Quantas transações foram lidas (cada uma cai em criados, atualizados, pulados ou erros)."""
        return (
            len(self.criados)
            + len(self.atualizados)
            + len(self.pulados)
            + len(self.erros)
        )


def importar_transacoes(transacoes, conta, usuario=None, dry_run=False):
    """Converte as transações do `/v2/transactions` em `Movimento` da conta.

    `transacoes` é a lista de itens devolvida pela API. `usuario` é o autor
    gravado em `criado_por`; sem ele, o usuário técnico `Pluggy` é criado. Com
    `dry_run=True` nada é escrito — nem movimento, nem categoria, nem usuário —
    e o relatório mostra o que *seria* feito.
    """
    if conta is None:
        raise ValueError("Informe a conta de destino dos movimentos.")

    relatorio = RelatorioImportacao(dry_run=dry_run)
    ids_vistos: set[str] = set()
    autor = usuario
    if autor is None and not dry_run:
        autor = usuario_tecnico()
    cache_categorias: dict[tuple[str, str], Categoria] = {}

    for bruta in transacoes:
        _importar_uma(
            bruta,
            conta=conta,
            autor=autor,
            dry_run=dry_run,
            relatorio=relatorio,
            ids_vistos=ids_vistos,
            cache_categorias=cache_categorias,
        )
    return relatorio


def usuario_tecnico():
    """Usuário que assina os movimentos importados: sem senha utilizável e sem privilégio."""
    Usuario = get_user_model()
    usuario, criado = Usuario.objects.get_or_create(username=USUARIO_TECNICO)
    if criado:
        usuario.set_unusable_password()
        usuario.save(update_fields=["password"])
    return usuario


def _importar_uma(
    bruta, *, conta, autor, dry_run, relatorio, ids_vistos, cache_categorias
):
    if not isinstance(bruta, dict):
        relatorio.erros.append(
            TransacaoComErro("", "item da resposta não é um objeto JSON")
        )
        return

    _contar_categoria(relatorio, bruta.get("category"))

    id_transacao = _texto(bruta.get("id"))
    if not id_transacao:
        relatorio.erros.append(
            TransacaoComErro("", "sem id; transação recusada (não há chave de reserva)")
        )
        return

    if id_transacao in ids_vistos:
        relatorio.pulados.append(
            TransacaoPulada(id_transacao, "duplicata no próprio payload")
        )
        return
    ids_vistos.add(id_transacao)

    status = _texto(bruta.get("status")).upper()
    if status not in STATUS_QUE_ENTRAM:
        if status == "PENDING":
            relatorio.pulados.append(
                TransacaoPulada(
                    id_transacao, "status PENDING; entra quando virar POSTED"
                )
            )
        else:
            relatorio.erros.append(
                TransacaoComErro(
                    id_transacao,
                    f"status inesperado: {bruta.get('status')!r} "
                    "(esperado POSTED ou PENDING)",
                )
            )
        return

    tipo = TIPOS_POR_TRANSACAO.get(_texto(bruta.get("type")).upper())
    if tipo is None:
        relatorio.erros.append(
            TransacaoComErro(
                id_transacao,
                f"type inesperado: {bruta.get('type')!r} (esperado DEBIT ou CREDIT)",
            )
        )
        return

    data_movimento = _ler_data(bruta.get("date"))
    if data_movimento is None:
        relatorio.erros.append(
            TransacaoComErro(id_transacao, "date ausente ou inválida")
        )
        return

    valor = _ler_valor(bruta.get("amount"))
    if valor is None:
        relatorio.erros.append(
            TransacaoComErro(id_transacao, f"amount inválido: {bruta.get('amount')!r}")
        )
        return

    descricao = _montar_descricao(bruta)
    nome_categoria, entra_no_gasto = _escolher_categoria(
        bruta, tipo, descricao, cache_categorias
    )

    existente = (
        Movimento.objects.filter(conta=conta, id_externo=id_transacao)
        .select_related("categoria")
        .first()
    )
    if existente is not None:
        if (
            existente.categoria.nome == CATEGORIA_PADRAO
            and existente.categoria.tipo == tipo
            and nome_categoria != CATEGORIA_PADRAO
        ):
            if dry_run:
                relatorio.atualizados.append(id_transacao)
                return
            existente.categoria = _garantir_categoria(
                cache_categorias, nome_categoria, tipo, entra_no_gasto
            )
            existente.save(update_fields=["categoria"])
            relatorio.atualizados.append(id_transacao)
            return
        relatorio.pulados.append(
            TransacaoPulada(id_transacao, "já importado nesta conta")
        )
        return

    if dry_run:
        relatorio.criados.append(id_transacao)
        return

    categoria = _garantir_categoria(
        cache_categorias, nome_categoria, tipo, entra_no_gasto
    )

    # A busca acima já descarta o caso comum; o `atomic` existe para uma corrida
    # entre a checagem e a gravação não derrubar a importação inteira.
    try:
        with transaction.atomic():
            Movimento.objects.create(
                data=data_movimento,
                valor=valor,
                tipo=tipo,
                conta=conta,
                categoria=categoria,
                descricao=descricao,
                origem=Movimento.Origem.PLUGGY,
                criado_por=autor,
                id_externo=id_transacao,
            )
    except IntegrityError:
        relatorio.pulados.append(
            TransacaoPulada(id_transacao, "já importado nesta conta")
        )
        return

    relatorio.criados.append(id_transacao)


def _contar_categoria(relatorio, categoria):
    nome = _texto(categoria) or "(sem categoria)"
    relatorio.categorias_vistas[nome] = relatorio.categorias_vistas.get(nome, 0) + 1


def _escolher_categoria(bruta, tipo, descricao, cache):
    """Nome e `entra_no_gasto` da categoria do app para a transação.

    Ordem: mapa da `category` da Pluggy, regras por descrição e, por último,
    `Não categorizado`. Uma categoria mapeada só é usada se existir no app com
    o tipo da transação; senão, o fallback evita criar categoria por engano.
    """
    escolha = MAPA_CATEGORIAS_PLUGGY.get(_texto(bruta.get("category")))
    if escolha is not None:
        nome, entra_no_gasto = escolha
        if _categoria_existente(cache, nome, tipo) is not None:
            return nome, entra_no_gasto

    descricao_normalizada = _normalizar_texto(descricao)
    for palavras, nome, entra_no_gasto in REGRAS_DESCRICAO:
        if any(palavra in descricao_normalizada for palavra in palavras):
            if _categoria_existente(cache, nome, tipo) is not None:
                return nome, entra_no_gasto
    return CATEGORIA_PADRAO, True


def _categoria_existente(cache, nome, tipo):
    chave = (nome, tipo)
    if chave not in cache:
        cache[chave] = Categoria.objects.filter(nome=nome, tipo=tipo).first()
    return cache[chave]


def _normalizar_texto(texto):
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(
        caractere for caractere in decomposto if not unicodedata.combining(caractere)
    ).casefold()


def _garantir_categoria(cache, nome, tipo, entra_no_gasto):
    chave = (nome, tipo)
    if chave not in cache or cache[chave] is None:
        categoria, _ = Categoria.objects.get_or_create(
            nome=nome, tipo=tipo, defaults={"entra_no_gasto": entra_no_gasto}
        )
        cache[chave] = categoria
    return cache[chave]


def _texto(valor) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _ler_data(bruta) -> date | None:
    """`date` ISO 8601 (`2026-11-05T00:00:00.000Z`) vira `date`; inválida é erro."""
    texto = _texto(bruta)
    if not texto:
        return None
    try:
        return date.fromisoformat(texto[:10])
    except ValueError:
        return None


def _ler_valor(bruto) -> Decimal | None:
    """Valor positivo com 2 casas, ou None quando o conteúdo não é um valor válido.

    A Pluggy devolve número JSON (float) em `amount`; a conversão passa por `str`
    para não herdar o erro de representação binária. Texto também é aceito.
    """
    if bruto is None or isinstance(bruto, bool):
        return None
    if isinstance(bruto, (int, float)):
        bruto = str(bruto)
    texto = _texto(bruto)
    if not texto:
        return None
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        return None
    if not valor.is_finite():
        return None
    valor = abs(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if valor <= 0:
        return None
    return valor


def _montar_descricao(bruta) -> str:
    texto = _texto(bruta.get("description")) or _texto(bruta.get("descriptionRaw"))
    return texto[:TAMANHO_MAXIMO_DESCRICAO]
