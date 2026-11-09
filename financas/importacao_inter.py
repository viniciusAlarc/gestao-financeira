"""Importação do extrato enriquecido do Inter para `Movimento` (fase 7, T1).

O mapeamento é o decidido em `docs-dev/a-codar/04-decisao-d4-p2-8-importacao.md`:

- data: `dataTransacao`; se vazia, `dataInclusao` (a que muda o fechamento do mês é a
  primeira, então a reserva só entra quando ela falta).
- valor: sempre positivo, em `Decimal`; o sinal vem de `tipoOperacao` (D = despesa,
  C = receita). Qualquer outro valor é erro daquela transação, reportado, nunca ignorado.
- chave antiduplicidade: `idTransacao` em `Movimento.id_externo`. Transação sem id é
  recusada — não existe chave composta de reserva, porque ela geraria duplicata falsa.
- categoria: INVESTIMENTO → "Investimento" (despesa, fora do gasto); ESTORNO e CASHBACK
  → "Estorno"/"Cashback" do tipo da transação; o resto → "Não categorizado" do tipo.
- autoria: usuário técnico `Inter`, sem senha utilizável e sem privilégio.

Nada aqui chama a API: a função recebe a lista de transações já lida do JSON.
O sinal do `valor` e a estabilidade do `idTransacao` ainda serão confirmados no sandbox
(P2-3); até lá, a regra é a documentada.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from .models import Categoria, Movimento, TipoValor

USUARIO_TECNICO = "Inter"
TAMANHO_MAXIMO_DESCRICAO = 120
CATEGORIA_PADRAO = "Não categorizado"
CATEGORIA_INVESTIMENTO = "Investimento"
CATEGORIAS_POR_TIPO_TRANSACAO = {
    "ESTORNO": "Estorno",
    "CASHBACK": "Cashback",
}
TIPOS_POR_OPERACAO = {
    "D": TipoValor.DESPESA,
    "C": TipoValor.RECEITA,
}


@dataclass(frozen=True)
class TransacaoPulada:
    """Transação que não entrou porque já existia (idempotência)."""

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
    pulados: list[TransacaoPulada] = field(default_factory=list)
    erros: list[TransacaoComErro] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Quantas transações foram lidas (cada uma cai em criados, pulados ou erros)."""
        return len(self.criados) + len(self.pulados) + len(self.erros)


def importar_extrato(transacoes, conta, usuario=None, dry_run=False):
    """Converte as transações do `/extrato/completo` em `Movimento` da conta.

    `transacoes` é a lista de itens do extrato (dicionários vindos do JSON). `usuario`
    é o autor gravado em `criado_por`; sem ele, o usuário técnico `Inter` é criado.
    Com `dry_run=True` nada é escrito — nem movimento, nem categoria, nem usuário — e
    o relatório mostra o que *seria* feito.
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
            TransacaoComErro("", "item do extrato não é um objeto JSON")
        )
        return

    id_transacao = _texto(bruta.get("idTransacao"))
    if not id_transacao:
        relatorio.erros.append(
            TransacaoComErro(
                "",
                "sem idTransacao; transação recusada (não há chave composta de reserva)",
            )
        )
        return

    if id_transacao in ids_vistos:
        relatorio.pulados.append(
            TransacaoPulada(id_transacao, "duplicata no próprio payload")
        )
        return
    ids_vistos.add(id_transacao)

    if Movimento.objects.filter(conta=conta, id_externo=id_transacao).exists():
        relatorio.pulados.append(
            TransacaoPulada(id_transacao, "já importado nesta conta")
        )
        return

    tipo = TIPOS_POR_OPERACAO.get(_texto(bruta.get("tipoOperacao")).upper())
    if tipo is None:
        relatorio.erros.append(
            TransacaoComErro(
                id_transacao,
                "tipoOperacao inesperado: "
                f"{bruta.get('tipoOperacao')!r} (esperado D ou C)",
            )
        )
        return

    data_movimento = _ler_data(bruta)
    if data_movimento is None:
        relatorio.erros.append(
            TransacaoComErro(
                id_transacao, "dataTransacao/dataInclusao ausente ou inválida"
            )
        )
        return

    valor = _ler_valor(bruta.get("valor"))
    if valor is None:
        relatorio.erros.append(
            TransacaoComErro(id_transacao, f"valor inválido: {bruta.get('valor')!r}")
        )
        return

    if dry_run:
        relatorio.criados.append(id_transacao)
        return

    nome_categoria, tipo_categoria, entra_no_gasto = _categoria_da_transacao(
        bruta.get("tipoTransacao"), tipo
    )
    categoria = _garantir_categoria(
        cache_categorias, nome_categoria, tipo_categoria, entra_no_gasto
    )

    # A checagem acima já descarta o caso comum; o `atomic` existe para uma corrida
    # entre a checagem e a gravação não derrubar a importação inteira.
    try:
        with transaction.atomic():
            Movimento.objects.create(
                data=data_movimento,
                valor=valor,
                tipo=tipo,
                conta=conta,
                categoria=categoria,
                descricao=_montar_descricao(bruta),
                origem=Movimento.Origem.INTER,
                criado_por=autor,
                id_externo=id_transacao,
            )
    except IntegrityError:
        relatorio.pulados.append(
            TransacaoPulada(id_transacao, "já importado nesta conta")
        )
        return

    relatorio.criados.append(id_transacao)


def _categoria_da_transacao(tipo_transacao, tipo):
    """(nome, tipo da categoria, entra_no_gasto) conforme a decisão do P2-8.

    "Investimento" é a categoria de despesa criada fora do gasto; mesmo um
    INVESTIMENTO com `tipoOperacao=C` (resgate) usa essa categoria, como escrito na
    decisão. O sandbox (P2-3) ainda vai dizer se esse caso aparece.
    """
    nome = _texto(tipo_transacao).upper()
    if nome == "INVESTIMENTO":
        return CATEGORIA_INVESTIMENTO, TipoValor.DESPESA, False
    if nome in CATEGORIAS_POR_TIPO_TRANSACAO:
        return CATEGORIAS_POR_TIPO_TRANSACAO[nome], tipo, True
    return CATEGORIA_PADRAO, tipo, True


def _garantir_categoria(cache, nome, tipo, entra_no_gasto):
    chave = (nome, tipo)
    if chave not in cache:
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
    """`dataTransacao` e, se ela estiver vazia, `dataInclusao`.

    Data presente mas inválida também é erro: cair para o outro campo mascararia
    um formato inesperado da API.
    """
    for campo in ("dataTransacao", "dataInclusao"):
        texto = _texto(bruta.get(campo))
        if not texto:
            continue
        try:
            return date.fromisoformat(texto[:10])
        except ValueError:
            return None
    return None


def _ler_valor(bruto) -> Decimal | None:
    """Valor positivo com 2 casas, ou None quando o conteúdo não é um valor válido.

    Aceita vírgula decimal e separador de milhar no formato brasileiro, porque o
    formato exato que a API devolve ainda não foi visto (P2-3).
    """
    texto = _texto(bruto)
    if not texto:
        return None
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", ".")
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
    partes = [_texto(bruta.get("titulo")), _texto(bruta.get("descricao"))]
    return " ".join(parte for parte in partes if parte)[:TAMANHO_MAXIMO_DESCRICAO]
