"""Testes do importador do extrato do Inter (T1 da rodada 2026-11-05-b).

Payload inventado: nenhum dado real do dono entra aqui (regra 2 do `AGENTS.md`).
O schema do extrato é o documentado em `docs-dev/a-codar/03-decisao-d4-escopo-inter.md`;
o sandbox ainda vai confirmar sinal do valor e estabilidade do `idTransacao` (P2-3).
"""

import json
import tempfile
from datetime import date
from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from .importacao_inter import importar_extrato
from .models import Categoria, Conta, Movimento, TipoValor


class BaseImportacao(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Conta Inter", tipo=Conta.Tipo.CORRENTE, saldo_inicial=Decimal("0.00")
        )

    def transacao(self, **extra):
        dados = {
            "idTransacao": "ID-1",
            "dataTransacao": "2026-11-05",
            "dataInclusao": "2026-11-06",
            "tipoTransacao": "PIX",
            "tipoOperacao": "D",
            "valor": "10.50",
            "titulo": "Pix enviado",
            "descricao": "Fulano de Tal",
        }
        dados.update(extra)
        return dados


class ImportacaoTests(BaseImportacao):
    def test_uma_transacao_vira_um_movimento_com_os_campos_do_extrato(self):
        relatorio = importar_extrato([self.transacao()], self.conta)

        self.assertEqual(relatorio.criados, ["ID-1"])
        movimento = Movimento.objects.get()
        self.assertEqual(movimento.data, date(2026, 11, 5))
        self.assertEqual(movimento.valor, Decimal("10.50"))
        self.assertEqual(movimento.tipo, TipoValor.DESPESA)
        self.assertEqual(movimento.conta, self.conta)
        self.assertEqual(movimento.origem, Movimento.Origem.INTER)
        self.assertEqual(movimento.id_externo, "ID-1")
        self.assertEqual(movimento.descricao, "Pix enviado Fulano de Tal")
        self.assertEqual(movimento.categoria.nome, "Não categorizado")
        self.assertEqual(movimento.categoria.tipo, TipoValor.DESPESA)

    def test_tipo_operacao_d_vira_despesa_e_c_vira_receita(self):
        entrada = self.transacao(
            idTransacao="ID-C", tipoOperacao="C", valor="7.00"
        )
        importar_extrato([self.transacao(), entrada], self.conta)

        despesa = Movimento.objects.get(id_externo="ID-1")
        receita = Movimento.objects.get(id_externo="ID-C")
        self.assertEqual(despesa.tipo, TipoValor.DESPESA)
        self.assertEqual(receita.tipo, TipoValor.RECEITA)
        self.assertEqual(receita.categoria.tipo, TipoValor.RECEITA)
        self.assertEqual(receita.categoria.nome, "Não categorizado")

    def test_valor_negativo_e_convertido_para_positivo(self):
        importar_extrato([self.transacao(valor="-25,90")], self.conta)

        self.assertEqual(Movimento.objects.get().valor, Decimal("25.90"))

    def test_valor_com_separador_de_milhar_brasileiro(self):
        importar_extrato([self.transacao(valor="1.234,56")], self.conta)

        self.assertEqual(Movimento.objects.get().valor, Decimal("1234.56"))

    def test_data_vazia_cai_para_data_de_inclusao(self):
        for vazio in ("", None):
            with self.subTest(dataTransacao=vazio):
                Movimento.objects.all().delete()
                importar_extrato(
                    [
                        self.transacao(
                            idTransacao=f"SEM-DATA-{vazio}", dataTransacao=vazio
                        )
                    ],
                    self.conta,
                )
                self.assertEqual(Movimento.objects.get().data, date(2026, 11, 6))

    def test_data_invalida_e_erro_da_transacao(self):
        relatorio = importar_extrato(
            [self.transacao(dataTransacao="2026-13-45")], self.conta
        )

        self.assertEqual(Movimento.objects.count(), 0)
        self.assertEqual(len(relatorio.erros), 1)
        self.assertIn("data", relatorio.erros[0].motivo)

    def test_descricao_junta_titulo_e_descricao_e_trunca_em_120(self):
        titulo = "T" * 70
        descricao = "D" * 80
        importar_extrato(
            [self.transacao(titulo=titulo, descricao=descricao)], self.conta
        )

        movimento = Movimento.objects.get()
        self.assertEqual(len(movimento.descricao), 120)
        self.assertTrue(movimento.descricao.startswith("T" * 70))

    def test_investimento_usa_categoria_propria_e_fica_fora_do_gasto(self):
        importar_extrato(
            [
                self.transacao(
                    tipoTransacao="INVESTIMENTO", titulo="Aplicação", descricao=""
                )
            ],
            self.conta,
        )

        movimento = Movimento.objects.get()
        self.assertEqual(movimento.tipo, TipoValor.DESPESA)
        self.assertEqual(movimento.categoria.nome, "Investimento")
        self.assertEqual(movimento.categoria.tipo, TipoValor.DESPESA)
        self.assertFalse(movimento.categoria.entra_no_gasto)

    def test_estorno_e_cashback_tem_categoria_propria(self):
        estorno = self.transacao(
            idTransacao="ID-ESTORNO", tipoTransacao="ESTORNO", tipoOperacao="C"
        )
        cashback = self.transacao(
            idTransacao="ID-CASHBACK", tipoTransacao="CASHBACK", tipoOperacao="C"
        )
        importar_extrato([estorno, cashback], self.conta)

        categoria_estorno = Categoria.objects.get(nome="Estorno")
        categoria_cashback = Categoria.objects.get(nome="Cashback")
        self.assertEqual(categoria_estorno.tipo, TipoValor.RECEITA)
        self.assertEqual(categoria_cashback.tipo, TipoValor.RECEITA)
        self.assertTrue(categoria_estorno.entra_no_gasto)
        self.assertTrue(categoria_cashback.entra_no_gasto)

    def test_transacao_sem_id_transacao_e_recusada_e_reportada(self):
        relatorio = importar_extrato(
            [self.transacao(idTransacao=""), self.transacao(idTransacao=None)],
            self.conta,
        )

        self.assertEqual(Movimento.objects.count(), 0)
        self.assertEqual(len(relatorio.erros), 2)
        self.assertIn("idTransacao", relatorio.erros[0].motivo)

    def test_tipo_operacao_desconhecido_e_erro_e_nao_derruba_as_outras(self):
        invalida = self.transacao(idTransacao="ID-X", tipoOperacao="X")
        valida = self.transacao(idTransacao="ID-OK")
        relatorio = importar_extrato([invalida, valida], self.conta)

        self.assertEqual(relatorio.criados, ["ID-OK"])
        self.assertEqual(len(relatorio.erros), 1)
        self.assertEqual(relatorio.erros[0].id_transacao, "ID-X")
        self.assertIn("tipoOperacao", relatorio.erros[0].motivo)
        self.assertFalse(Movimento.objects.filter(id_externo="ID-X").exists())

    def test_valor_invalido_ou_zerado_e_erro(self):
        relatorio = importar_extrato(
            [
                self.transacao(idTransacao="ID-A", valor="abc"),
                self.transacao(idTransacao="ID-Z", valor="0.00"),
            ],
            self.conta,
        )

        self.assertEqual(Movimento.objects.count(), 0)
        self.assertEqual(len(relatorio.erros), 2)


class IdempotenciaTests(BaseImportacao):
    def test_importar_duas_vezes_deixa_um_movimento_por_id_transacao(self):
        importar_extrato([self.transacao()], self.conta)
        segundo = importar_extrato([self.transacao()], self.conta)

        self.assertEqual(Movimento.objects.count(), 1)
        self.assertEqual(segundo.criados, [])
        self.assertEqual(len(segundo.pulados), 1)
        self.assertEqual(segundo.pulados[0].id_transacao, "ID-1")

    def test_duplicata_dentro_do_proprio_payload_e_pulada(self):
        relatorio = importar_extrato(
            [self.transacao(), self.transacao()], self.conta
        )

        self.assertEqual(Movimento.objects.count(), 1)
        self.assertEqual(relatorio.criados, ["ID-1"])
        self.assertEqual(len(relatorio.pulados), 1)
        self.assertIn("payload", relatorio.pulados[0].motivo)

    def test_mesmo_id_externo_em_outra_conta_e_importado(self):
        outra = Conta.objects.create(nome="Outra conta")
        importar_extrato([self.transacao()], self.conta)
        relatorio = importar_extrato([self.transacao()], outra)

        self.assertEqual(relatorio.criados, ["ID-1"])
        self.assertEqual(Movimento.objects.count(), 2)


class DryRunTests(BaseImportacao):
    def test_dry_run_nao_grava_movimento_categoria_nem_usuario(self):
        relatorio = importar_extrato(
            [
                self.transacao(
                    idTransacao="ID-INV", tipoTransacao="INVESTIMENTO"
                ),
                self.transacao(
                    idTransacao="ID-EST",
                    tipoTransacao="ESTORNO",
                    tipoOperacao="C",
                ),
            ],
            self.conta,
            dry_run=True,
        )

        self.assertTrue(relatorio.dry_run)
        self.assertEqual(relatorio.criados, ["ID-INV", "ID-EST"])
        self.assertEqual(relatorio.total, 2)
        self.assertEqual(Movimento.objects.count(), 0)
        self.assertEqual(Categoria.objects.count(), 0)
        self.assertFalse(
            get_user_model().objects.filter(username="Inter").exists()
        )

    def test_dry_run_reporta_o_que_seria_pulado(self):
        importar_extrato([self.transacao()], self.conta)
        movimentos_antes = Movimento.objects.count()
        categorias_antes = Categoria.objects.count()

        relatorio = importar_extrato([self.transacao()], self.conta, dry_run=True)

        self.assertEqual(relatorio.criados, [])
        self.assertEqual(len(relatorio.pulados), 1)
        self.assertEqual(Movimento.objects.count(), movimentos_antes)
        self.assertEqual(Categoria.objects.count(), categorias_antes)


class UsuarioTecnicoTests(BaseImportacao):
    def test_cria_usuario_inter_sem_senha_utilizavel_e_sem_privilegio(self):
        importar_extrato([self.transacao()], self.conta)

        usuario = get_user_model().objects.get(username="Inter")
        self.assertFalse(usuario.has_usable_password())
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(Movimento.objects.get().criado_por, usuario)

    def test_usuario_informado_assina_o_movimento_sem_criar_o_tecnico(self):
        dono = get_user_model().objects.create_user(
            username="dono", password="senha-de-teste"
        )

        importar_extrato([self.transacao()], self.conta, usuario=dono)

        self.assertEqual(Movimento.objects.get().criado_por, dono)
        self.assertFalse(
            get_user_model().objects.filter(username="Inter").exists()
        )


class ComandoImportarInterTests(BaseImportacao):
    def setUp(self):
        super().setUp()
        self.saida = StringIO()
        self.erros = StringIO()

    def _arquivo(self, conteudo):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        caminho = Path(pasta.name) / "extrato.json"
        caminho.write_text(
            json.dumps(conteudo, ensure_ascii=False), encoding="utf-8"
        )
        return caminho

    def _rodar(self, caminho, **extra):
        opcoes = {
            "arquivo": str(caminho),
            "conta": self.conta.nome,
            "stdout": self.saida,
            "stderr": self.erros,
        }
        opcoes.update(extra)
        call_command("importar_inter", **opcoes)

    def test_importa_o_envelope_com_a_chave_transacoes(self):
        caminho = self._arquivo({"transacoes": [self.transacao()]})

        self._rodar(caminho)

        self.assertEqual(Movimento.objects.count(), 1)
        self.assertIn("Criados: 1", self.saida.getvalue())
        self.assertIn("Conta: Conta Inter", self.saida.getvalue())

    def test_aceita_o_arquivo_sendo_a_lista_de_transacoes(self):
        caminho = self._arquivo([self.transacao()])

        self._rodar(caminho)

        self.assertEqual(Movimento.objects.count(), 1)

    def test_dry_run_nao_grava_e_avisa(self):
        caminho = self._arquivo({"transacoes": [self.transacao()]})

        self._rodar(caminho, dry_run=True)

        self.assertEqual(Movimento.objects.count(), 0)
        self.assertIn("Simulação", self.saida.getvalue())
        self.assertIn("Seriam criados: 1", self.saida.getvalue())

    def test_conta_inexistente_termina_com_erro(self):
        caminho = self._arquivo({"transacoes": [self.transacao()]})

        with self.assertRaises(CommandError) as contexto:
            self._rodar(caminho, conta="Conta que não existe")

        self.assertIn("Conta não encontrada", str(contexto.exception))
        self.assertEqual(Movimento.objects.count(), 0)

    def test_transacao_invalida_termina_com_codigo_de_erro(self):
        caminho = self._arquivo(
            {"transacoes": [self.transacao(tipoOperacao="X")]}
        )

        with self.assertRaises(CommandError):
            self._rodar(caminho)

        self.assertIn("Erros: 1", self.saida.getvalue())
        self.assertIn("ID-1", self.erros.getvalue())

    def test_erro_em_uma_transacao_nao_impede_as_validas(self):
        caminho = self._arquivo(
            {
                "transacoes": [
                    self.transacao(idTransacao="ID-OK"),
                    self.transacao(idTransacao="ID-X", tipoOperacao="X"),
                ]
            }
        )

        with self.assertRaises(CommandError):
            self._rodar(caminho)

        self.assertEqual(Movimento.objects.count(), 1)
        self.assertTrue(Movimento.objects.filter(id_externo="ID-OK").exists())

    def test_arquivo_inexistente_termina_com_erro(self):
        with self.assertRaises(CommandError) as contexto:
            self._rodar(Path("/tmp/nao-existe-extrato-xyz.json"))

        self.assertIn("Arquivo não encontrado", str(contexto.exception))
