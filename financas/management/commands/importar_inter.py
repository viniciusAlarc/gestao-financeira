"""Importa um extrato do Inter já salvo em JSON (fase 7).

Não chama a API: o arquivo é o corpo devolvido por `/extrato/completo` (ou só a lista
de transações dele). O comando lê o JSON e grava `Movimento`; com `--dry-run`, mostra
o que faria sem gravar nada e sem criar categoria nem usuário.

Uso:
    .venv/bin/python manage.py importar_inter --arquivo extrato.json \
        --conta "69 450 604 Vinicius Di Franca Alarc"

Sai com código 1 quando alguma transação é recusada (erro), mesmo que as demais
tenham sido importadas.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from financas.importacao_inter import importar_extrato
from financas.models import Conta


class Command(BaseCommand):
    help = "Importa o extrato do Inter (JSON do /extrato/completo) para os movimentos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--arquivo", required=True, help="Caminho do JSON com o extrato."
        )
        parser.add_argument(
            "--conta", required=True, help="Nome exato da conta de destino."
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula a importação sem gravar nada.",
        )

    def handle(self, *args, **opcoes):
        transacoes = self._ler_arquivo(opcoes["arquivo"])
        conta = self._achar_conta(opcoes["conta"])

        relatorio = importar_extrato(
            transacoes, conta, dry_run=opcoes["dry_run"]
        )
        self._imprimir_resumo(relatorio, conta)

        if relatorio.erros:
            raise CommandError(
                f"{len(relatorio.erros)} transação(ões) recusada(s); "
                "a importação terminou com erro."
            )

    def _ler_arquivo(self, caminho_texto):
        caminho = Path(caminho_texto)
        try:
            bruto = json.loads(caminho.read_text(encoding="utf-8"))
        except FileNotFoundError as erro:
            raise CommandError(f"Arquivo não encontrado: {caminho}") from erro
        except OSError as erro:
            raise CommandError(f"Não foi possível ler {caminho}: {erro}") from erro
        except json.JSONDecodeError as erro:
            raise CommandError(f"JSON inválido em {caminho}: {erro}") from erro

        transacoes = bruto.get("transacoes") if isinstance(bruto, dict) else bruto
        if not isinstance(transacoes, list):
            raise CommandError(
                'JSON inesperado: esperado a chave "transacoes" com a lista '
                "de transações, ou o arquivo inteiro sendo essa lista."
            )
        return transacoes

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

    def _imprimir_resumo(self, relatorio, conta):
        if relatorio.dry_run:
            self.stdout.write("Simulação (--dry-run): nada foi gravado.")
        self.stdout.write(f"Conta: {conta.nome}")
        self.stdout.write(f"Transações lidas: {relatorio.total}")
        rotulo_criados = "Seriam criados" if relatorio.dry_run else "Criados"
        self.stdout.write(f"{rotulo_criados}: {len(relatorio.criados)}")
        self.stdout.write(f"Pulados: {len(relatorio.pulados)}")
        self.stdout.write(f"Erros: {len(relatorio.erros)}")
        for pulo in relatorio.pulados:
            self.stdout.write(f"  pulado {pulo.id_transacao}: {pulo.motivo}")
        for erro in relatorio.erros:
            self.stderr.write(
                f"  erro {erro.id_transacao or '(sem id)'}: {erro.motivo}"
            )
