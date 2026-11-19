"""Importa o extrato da Pluggy (Open Finance) para os movimentos (fase 7).

Lê as contas do item configurado em `PLUGGY_ITEM_ID` e as transações da conta
escolhida, e grava `Movimento` com `origem = pluggy`. Com `--dry-run`, mostra o
que faria sem gravar nada e sem criar categoria nem usuário.

Uso:
    .venv/bin/python manage.py importar_pluggy --conta "Conta corrente" --dry-run

Sem `--pluggy-conta`, o comando usa a única conta bancária (`BANK`) do item; se
houver mais de uma, lista os ids e pede a escolha. `--desde` e `--ate`
(AAAA-MM-DD) limitam o período e são inclusivos.

Sai com código 1 quando alguma transação é recusada (erro), mesmo que as demais
tenham sido importadas.
"""

from datetime import date

from django.core.management.base import BaseCommand, CommandError

from financas.importacao_pluggy import importar_transacoes
from financas.models import Conta
from financas.pluggy_api import ErroPluggy, PluggyCliente


class Command(BaseCommand):
    help = "Importa o extrato da Pluggy (Open Finance) para os movimentos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--conta", required=True, help="Nome exato da conta de destino no app."
        )
        parser.add_argument(
            "--pluggy-conta",
            help=(
                "Id da conta na Pluggy. Sem ele, usa a única conta bancária (BANK) "
                "do item."
            ),
        )
        parser.add_argument(
            "--desde", help="Data inicial do período (AAAA-MM-DD), inclusiva."
        )
        parser.add_argument(
            "--ate", help="Data final do período (AAAA-MM-DD), inclusiva."
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula a importação sem gravar nada.",
        )

    def handle(self, *args, **opcoes):
        conta = self._achar_conta(opcoes["conta"])
        desde = self._ler_data("--desde", opcoes["desde"])
        ate = self._ler_data("--ate", opcoes["ate"])
        if desde and ate and desde > ate:
            raise CommandError("--desde não pode ser depois de --ate.")

        cliente = PluggyCliente()
        try:
            conta_pluggy = self._escolher_conta_pluggy(
                cliente, opcoes["pluggy_conta"]
            )
            transacoes = cliente.transacoes(
                conta_pluggy["id"], desde=desde, ate=ate
            )
        except ErroPluggy as erro:
            raise CommandError(f"Pluggy: {erro}") from erro

        relatorio = importar_transacoes(
            transacoes, conta, dry_run=opcoes["dry_run"]
        )
        self._imprimir_resumo(relatorio, conta, conta_pluggy)

        if relatorio.erros:
            raise CommandError(
                f"{len(relatorio.erros)} transação(ões) recusada(s); "
                "a importação terminou com erro."
            )

    def _achar_conta(self, nome):
        conta = Conta.objects.filter(nome=nome).first()
        if conta is None:
            disponiveis = (
                ", ".join(Conta.objects.values_list("nome", flat=True)) or "nenhuma"
            )
            raise CommandError(
                f"Conta não encontrada: {nome!r}. Contas existentes: {disponiveis}."
            )
        return conta

    def _ler_data(self, rotulo, texto):
        if not texto:
            return None
        try:
            return date.fromisoformat(texto)
        except ValueError as erro:
            raise CommandError(
                f"{rotulo} inválida: {texto!r} (use o formato AAAA-MM-DD)"
            ) from erro

    def _escolher_conta_pluggy(self, cliente, id_pedido):
        """Devolve a conta da Pluggy a ler, exigindo escolha quando há ambiguidade."""
        contas = cliente.contas()
        if id_pedido:
            for conta in contas:
                if conta.get("id") == id_pedido:
                    return conta
            raise CommandError(
                f"Conta da Pluggy não encontrada: {id_pedido!r}. "
                f"Contas do item: {self._listar_contas(contas)}."
            )

        bancarias = [conta for conta in contas if conta.get("type") == "BANK"]
        if len(bancarias) == 1:
            return bancarias[0]
        if not bancarias:
            raise CommandError(
                "Nenhuma conta bancária (BANK) no item da Pluggy. "
                f"Contas existentes: {self._listar_contas(contas)}."
            )
        raise CommandError(
            "Mais de uma conta bancária no item; escolha com --pluggy-conta: "
            f"{self._listar_contas(bancarias)}."
        )

    def _listar_contas(self, contas):
        partes = []
        for conta in contas:
            rotulo = " ".join(
                parte
                for parte in (_texto(conta.get("name")), _texto(conta.get("number")))
                if parte
            )
            partes.append(f"{conta.get('id')} ({conta.get('type')}: {rotulo or 'sem nome'})")
        return "; ".join(partes) or "nenhuma"

    def _imprimir_resumo(self, relatorio, conta, conta_pluggy):
        if relatorio.dry_run:
            self.stdout.write("Simulação (--dry-run): nada foi gravado.")
        self.stdout.write(f"Conta: {conta.nome}")
        nome_pluggy = " ".join(
            parte
            for parte in (
                _texto(conta_pluggy.get("name")),
                _texto(conta_pluggy.get("number")),
            )
            if parte
        )
        self.stdout.write(
            f"Conta na Pluggy: {nome_pluggy or 'sem nome'} ({conta_pluggy.get('id')})"
        )
        self.stdout.write(f"Transações lidas: {relatorio.total}")
        rotulo_criados = "Seriam criados" if relatorio.dry_run else "Criados"
        self.stdout.write(f"{rotulo_criados}: {len(relatorio.criados)}")
        rotulo_atualizados = (
            "Seriam atualizados" if relatorio.dry_run else "Atualizados"
        )
        self.stdout.write(f"{rotulo_atualizados}: {len(relatorio.atualizados)}")
        self.stdout.write(f"Pulados: {len(relatorio.pulados)}")
        self.stdout.write(f"Erros: {len(relatorio.erros)}")
        for pulo in relatorio.pulados:
            self.stdout.write(f"  pulado {pulo.id_transacao}: {pulo.motivo}")
        for erro in relatorio.erros:
            self.stderr.write(
                f"  erro {erro.id_transacao or '(sem id)'}: {erro.motivo}"
            )
        if relatorio.categorias_vistas:
            self.stdout.write("Categorias na Pluggy (para o mapeamento do P2-15):")
            for nome, quantidade in sorted(
                relatorio.categorias_vistas.items(), key=lambda item: (-item[1], item[0])
            ):
                self.stdout.write(f"  {nome}: {quantidade}")


def _texto(valor) -> str:
    if valor is None:
        return ""
    return str(valor).strip()
