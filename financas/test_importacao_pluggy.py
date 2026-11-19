"""Testes do importador da Pluggy (P2-13).

Payload inventado: nenhum dado real do dono entra aqui (regra 2 do `AGENTS.md`).
O formato segue a documentação oficial de `GET /v2/transactions`, conferida em
2026-11-10 (`id`, `date`, `amount`, `type`, `status`, `description`, `category`).
"""

from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from .importacao_pluggy import CATEGORIA_PADRAO, importar_transacoes
from .models import Categoria, Conta, Movimento, TipoValor
from .pluggy_api import ErroPluggy


class BaseImportacao(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Conta Itaú",
            tipo=Conta.Tipo.CORRENTE,
            saldo_inicial=Decimal("0.00"),
        )

    def transacao(self, **extra):
        dados = {
            "id": "ID-1",
            "date": "2026-11-05T00:00:00.000Z",
            "amount": -10.5,
            "type": "DEBIT",
            "status": "POSTED",
            "description": "Pix enviado",
            "descriptionRaw": "Pix enviado Fulano de Tal",
            "currencyCode": "BRL",
            "category": "Transfer",
        }
        dados.update(extra)
        return dados


class ImportacaoTests(BaseImportacao):
    def test_uma_transacao_vira_um_movimento_com_os_campos_da_api(self):
        relatorio = importar_transacoes([self.transacao()], self.conta)

        self.assertEqual(relatorio.criados, ["ID-1"])
        movimento = Movimento.objects.get()
        self.assertEqual(movimento.data, date(2026, 11, 5))
        self.assertEqual(movimento.valor, Decimal("10.50"))
        self.assertEqual(movimento.tipo, TipoValor.DESPESA)
        self.assertEqual(movimento.conta, self.conta)
        self.assertEqual(movimento.origem, Movimento.Origem.PLUGGY)
        self.assertEqual(movimento.id_externo, "ID-1")
        self.assertEqual(movimento.descricao, "Pix enviado")
        self.assertEqual(movimento.categoria.nome, "Não categorizado")
        self.assertEqual(movimento.categoria.tipo, TipoValor.DESPESA)

    def test_debit_vira_despesa_e_credit_vira_receita(self):
        entrada = self.transacao(
            id="ID-C", type="CREDIT", amount=750.0, description="Salário"
        )
        importar_transacoes([self.transacao(), entrada], self.conta)

        despesa = Movimento.objects.get(id_externo="ID-1")
        receita = Movimento.objects.get(id_externo="ID-C")
        self.assertEqual(despesa.tipo, TipoValor.DESPESA)
        self.assertEqual(receita.tipo, TipoValor.RECEITA)
        self.assertEqual(receita.categoria.tipo, TipoValor.RECEITA)
        self.assertEqual(receita.categoria.nome, "Não categorizado")

    def test_valor_negativo_e_convertido_para_positivo(self):
        importar_transacoes([self.transacao(amount=-25.9)], self.conta)

        self.assertEqual(Movimento.objects.get().valor, Decimal("25.90"))

    def test_valor_texto_tambem_e_aceito(self):
        importar_transacoes([self.transacao(amount="-1234.56")], self.conta)

        self.assertEqual(Movimento.objects.get().valor, Decimal("1234.56"))

    def test_valor_invalido_ou_zerado_e_erro(self):
        relatorio = importar_transacoes(
            [
                self.transacao(id="ID-A", amount="abc"),
                self.transacao(id="ID-Z", amount=0),
                self.transacao(id="ID-N", amount=None),
                self.transacao(id="ID-B", amount=True),
            ],
            self.conta,
        )

        self.assertEqual(Movimento.objects.count(), 0)
        self.assertEqual(len(relatorio.erros), 4)

    def test_data_ausente_ou_invalida_e_erro(self):
        for valor in ("", None, "2026-13-45", "ontem"):
            with self.subTest(date=valor):
                Movimento.objects.all().delete()
                relatorio = importar_transacoes(
                    [self.transacao(date=valor)], self.conta
                )
                self.assertEqual(Movimento.objects.count(), 0)
                self.assertEqual(len(relatorio.erros), 1)
                self.assertIn("date", relatorio.erros[0].motivo)

    def test_descricao_cai_para_description_raw_e_trunca_em_120(self):
        importar_transacoes(
            [self.transacao(id="ID-VAZIA", description="", descriptionRaw="Só o raw")],
            self.conta,
        )
        self.assertEqual(Movimento.objects.get(id_externo="ID-VAZIA").descricao, "Só o raw")

        Movimento.objects.all().delete()
        importar_transacoes(
            [self.transacao(id="ID-LONGA", description="D" * 200)], self.conta
        )
        self.assertEqual(len(Movimento.objects.get().descricao), 120)

    def test_type_desconhecido_e_erro_e_nao_derruba_as_outras(self):
        invalida = self.transacao(id="ID-X", type="OUTRO")
        valida = self.transacao(id="ID-OK")
        relatorio = importar_transacoes([invalida, valida], self.conta)

        self.assertEqual(relatorio.criados, ["ID-OK"])
        self.assertEqual(len(relatorio.erros), 1)
        self.assertEqual(relatorio.erros[0].id_transacao, "ID-X")
        self.assertIn("type", relatorio.erros[0].motivo)

    def test_transacao_sem_id_e_recusada_e_reportada(self):
        relatorio = importar_transacoes(
            [self.transacao(id=""), self.transacao(id=None)], self.conta
        )

        self.assertEqual(Movimento.objects.count(), 0)
        self.assertEqual(len(relatorio.erros), 2)
        self.assertIn("id", relatorio.erros[0].motivo)

    def test_item_que_nao_e_objeto_e_erro(self):
        relatorio = importar_transacoes(["texto solto"], self.conta)

        self.assertEqual(Movimento.objects.count(), 0)
        self.assertEqual(len(relatorio.erros), 1)


class StatusTests(BaseImportacao):
    def test_pending_e_pulada_e_nao_e_erro(self):
        relatorio = importar_transacoes(
            [self.transacao(id="ID-P", status="PENDING")], self.conta
        )

        self.assertEqual(Movimento.objects.count(), 0)
        self.assertEqual(relatorio.criados, [])
        self.assertEqual(len(relatorio.pulados), 1)
        self.assertIn("PENDING", relatorio.pulados[0].motivo)

    def test_pending_que_virou_posted_entra_na_importacao_seguinte(self):
        importar_transacoes([self.transacao(status="PENDING")], self.conta)
        relatorio = importar_transacoes([self.transacao(status="POSTED")], self.conta)

        self.assertEqual(relatorio.criados, ["ID-1"])
        self.assertEqual(Movimento.objects.count(), 1)

    def test_status_desconhecido_e_erro(self):
        relatorio = importar_transacoes(
            [self.transacao(status="CANCELADO")], self.conta
        )

        self.assertEqual(len(relatorio.erros), 1)
        self.assertIn("status", relatorio.erros[0].motivo)


class IdempotenciaTests(BaseImportacao):
    def test_importar_duas_vezes_deixa_um_movimento_por_id(self):
        importar_transacoes([self.transacao()], self.conta)
        segundo = importar_transacoes([self.transacao()], self.conta)

        self.assertEqual(Movimento.objects.count(), 1)
        self.assertEqual(segundo.criados, [])
        self.assertEqual(len(segundo.pulados), 1)
        self.assertEqual(segundo.pulados[0].id_transacao, "ID-1")

    def test_duplicata_dentro_do_proprio_payload_e_pulada(self):
        relatorio = importar_transacoes(
            [self.transacao(), self.transacao()], self.conta
        )

        self.assertEqual(Movimento.objects.count(), 1)
        self.assertEqual(relatorio.criados, ["ID-1"])
        self.assertEqual(len(relatorio.pulados), 1)
        self.assertIn("payload", relatorio.pulados[0].motivo)

    def test_mesmo_id_externo_em_outra_conta_e_importado(self):
        outra = Conta.objects.create(nome="Outra conta")
        importar_transacoes([self.transacao()], self.conta)
        relatorio = importar_transacoes([self.transacao()], outra)

        self.assertEqual(relatorio.criados, ["ID-1"])
        self.assertEqual(Movimento.objects.count(), 2)


class DryRunTests(BaseImportacao):
    def test_dry_run_nao_grava_movimento_categoria_nem_usuario(self):
        relatorio = importar_transacoes(
            [
                self.transacao(id="ID-1"),
                self.transacao(id="ID-2", type="CREDIT", amount=100.0),
            ],
            self.conta,
            dry_run=True,
        )

        self.assertTrue(relatorio.dry_run)
        self.assertEqual(relatorio.criados, ["ID-1", "ID-2"])
        self.assertEqual(relatorio.total, 2)
        self.assertEqual(Movimento.objects.count(), 0)
        self.assertEqual(Categoria.objects.count(), 0)
        self.assertFalse(
            get_user_model().objects.filter(username="Pluggy").exists()
        )

    def test_dry_run_reporta_o_que_seria_pulado(self):
        importar_transacoes([self.transacao()], self.conta)
        movimentos_antes = Movimento.objects.count()
        categorias_antes = Categoria.objects.count()

        relatorio = importar_transacoes([self.transacao()], self.conta, dry_run=True)

        self.assertEqual(relatorio.criados, [])
        self.assertEqual(len(relatorio.pulados), 1)
        self.assertEqual(Movimento.objects.count(), movimentos_antes)
        self.assertEqual(Categoria.objects.count(), categorias_antes)

    def test_dry_run_conta_as_categorias_da_pluggy_sem_gravar(self):
        relatorio = importar_transacoes(
            [
                self.transacao(category="Transfer"),
                self.transacao(id="ID-2", category="Transfer"),
                self.transacao(id="ID-3", category="Fixed Income Investment"),
                self.transacao(id="ID-4", category=None),
            ],
            self.conta,
            dry_run=True,
        )

        self.assertEqual(
            relatorio.categorias_vistas,
            {"Transfer": 2, "Fixed Income Investment": 1, "(sem categoria)": 1},
        )


class UsuarioTecnicoTests(BaseImportacao):
    def test_cria_usuario_pluggy_sem_senha_utilizavel_e_sem_privilegio(self):
        importar_transacoes([self.transacao()], self.conta)

        usuario = get_user_model().objects.get(username="Pluggy")
        self.assertFalse(usuario.has_usable_password())
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(Movimento.objects.get().criado_por, usuario)

    def test_usuario_informado_assina_o_movimento_sem_criar_o_tecnico(self):
        dono = get_user_model().objects.create_user(
            username="dono", password="senha-de-teste"
        )

        importar_transacoes([self.transacao()], self.conta, usuario=dono)

        self.assertEqual(Movimento.objects.get().criado_por, dono)
        self.assertFalse(
            get_user_model().objects.filter(username="Pluggy").exists()
        )


class ComandoImportarPluggyTests(BaseImportacao):
    """O comando é testado com o cliente trocado por um dublê; nenhuma rede."""

    def setUp(self):
        super().setUp()
        self.saida = StringIO()
        self.erros = StringIO()

    def _rodar(self, **extra):
        opcoes = {
            "conta": self.conta.nome,
            "stdout": self.saida,
            "stderr": self.erros,
        }
        opcoes.update(extra)
        with patch(
            "financas.management.commands.importar_pluggy.PluggyCliente"
        ) as classe:
            classe.return_value.contas.return_value = [
                {
                    "id": "acc-1",
                    "type": "BANK",
                    "name": "Conta corrente",
                    "number": "1234",
                }
            ]
            classe.return_value.transacoes.return_value = [self.transacao()]
            call_command("importar_pluggy", **opcoes)
            self.classe_cliente = classe

    def test_importa_a_conta_bancaria_unica_do_item(self):
        self._rodar()

        self.assertEqual(Movimento.objects.count(), 1)
        self.assertIn("Conta: Conta Itaú", self.saida.getvalue())
        self.assertIn("Criados: 1", self.saida.getvalue())
        self.classe_cliente.return_value.transacoes.assert_called_once_with(
            "acc-1", desde=None, ate=None
        )

    def test_dry_run_nao_grava_e_avisa(self):
        self._rodar(dry_run=True)

        self.assertEqual(Movimento.objects.count(), 0)
        self.assertIn("Simulação", self.saida.getvalue())
        self.assertIn("Seriam criados: 1", self.saida.getvalue())

    def test_dry_run_mostra_as_categorias_da_pluggy(self):
        self._rodar(dry_run=True)

        self.assertIn("Categorias na Pluggy", self.saida.getvalue())
        self.assertIn("Transfer: 1", self.saida.getvalue())

    def test_conta_inexistente_termina_com_erro(self):
        with self.assertRaises(CommandError) as contexto:
            self._rodar(conta="Conta que não existe")

        self.assertIn("Conta não encontrada", str(contexto.exception))
        self.assertEqual(Movimento.objects.count(), 0)

    def test_desde_e_ate_sao_repassados(self):
        self._rodar(desde="2026-11-01", ate="2026-11-30")

        self.classe_cliente.return_value.transacoes.assert_called_once_with(
            "acc-1", desde=date(2026, 11, 1), ate=date(2026, 11, 30)
        )

    def test_desde_depois_de_ate_termina_com_erro(self):
        with self.assertRaises(CommandError):
            self._rodar(desde="2026-11-30", ate="2026-11-01")

    def test_data_invalida_termina_com_erro(self):
        with self.assertRaises(CommandError) as contexto:
            self._rodar(desde="30/11/2026")

        self.assertIn("--desde inválida", str(contexto.exception))

    def test_pluggy_conta_inexistente_lista_as_disponiveis(self):
        with self.assertRaises(CommandError) as contexto:
            self._rodar(**{"pluggy_conta": "acc-que-nao-existe"})

        self.assertIn("acc-que-nao-existe", str(contexto.exception))
        self.assertIn("acc-1", str(contexto.exception))

    def test_mais_de_uma_conta_bancaria_pede_escolha(self):
        with patch(
            "financas.management.commands.importar_pluggy.PluggyCliente"
        ) as classe:
            classe.return_value.contas.return_value = [
                {"id": "acc-1", "type": "BANK", "name": "Corrente", "number": "1"},
                {"id": "acc-2", "type": "BANK", "name": "Poupança", "number": "2"},
            ]
            with self.assertRaises(CommandError) as contexto:
                call_command(
                    "importar_pluggy",
                    conta=self.conta.nome,
                    stdout=self.saida,
                    stderr=self.erros,
                )

        self.assertIn("--pluggy-conta", str(contexto.exception))

    def test_sem_conta_bancaria_termina_com_erro(self):
        with patch(
            "financas.management.commands.importar_pluggy.PluggyCliente"
        ) as classe:
            classe.return_value.contas.return_value = [
                {"id": "cartao", "type": "CREDIT", "name": "Cartão", "number": "9"}
            ]
            with self.assertRaises(CommandError) as contexto:
                call_command(
                    "importar_pluggy",
                    conta=self.conta.nome,
                    stdout=self.saida,
                    stderr=self.erros,
                )

        self.assertIn("Nenhuma conta bancária", str(contexto.exception))

    def test_erro_da_pluggy_termina_com_erro_sem_derrubar_o_comando(self):
        with patch(
            "financas.management.commands.importar_pluggy.PluggyCliente"
        ) as classe:
            classe.return_value.contas.side_effect = ErroPluggy(
                "credencial inválida", status=401
            )
            with self.assertRaises(CommandError) as contexto:
                call_command(
                    "importar_pluggy",
                    conta=self.conta.nome,
                    stdout=self.saida,
                    stderr=self.erros,
                )

        self.assertIn("Pluggy:", str(contexto.exception))
        self.assertIn("HTTP 401", str(contexto.exception))

    def test_transacao_invalida_termina_com_erro(self):
        with patch(
            "financas.management.commands.importar_pluggy.PluggyCliente"
        ) as classe:
            classe.return_value.contas.return_value = [
                {"id": "acc-1", "type": "BANK", "name": "Corrente", "number": "1"}
            ]
            classe.return_value.transacoes.return_value = [
                self.transacao(type="OUTRO")
            ]
            with self.assertRaises(CommandError):
                call_command(
                    "importar_pluggy",
                    conta=self.conta.nome,
                    stdout=self.saida,
                    stderr=self.erros,
                )

        self.assertIn("Erros: 1", self.saida.getvalue())
        self.assertIn("ID-1", self.erros.getvalue())


class CategoriaMappingTests(BaseImportacao):
    """P2-15: mapa da Pluggy, regras por descrição e recategorização."""

    def setUp(self):
        super().setUp()
        self.alimentacao = Categoria.objects.create(
            nome="Alimentação", tipo=TipoValor.DESPESA
        )
        self.impostos = Categoria.objects.create(
            nome="Impostos", tipo=TipoValor.DESPESA
        )
        self.transferencia_despesa = Categoria.objects.create(
            nome="Transferência",
            tipo=TipoValor.DESPESA,
            entra_no_gasto=False,
        )
        self.transferencia_receita = Categoria.objects.create(
            nome="Transferência",
            tipo=TipoValor.RECEITA,
            entra_no_gasto=False,
        )
        self.compras = Categoria.objects.create(
            nome="Compras", tipo=TipoValor.DESPESA
        )
        self.transporte = Categoria.objects.create(
            nome="Transporte", tipo=TipoValor.DESPESA
        )
        self.saude = Categoria.objects.create(
            nome="Saúde", tipo=TipoValor.DESPESA
        )
        self.pets = Categoria.objects.create(
            nome="Pets", tipo=TipoValor.DESPESA
        )
        self.moradia = Categoria.objects.create(
            nome="Moradia", tipo=TipoValor.DESPESA
        )
        self.cartao = Categoria.objects.create(
            nome="Cartão de crédito", tipo=TipoValor.DESPESA
        )
        self.investimento = Categoria.objects.create(
            nome="Investimento",
            tipo=TipoValor.DESPESA,
            entra_no_gasto=False,
        )
        self.salario = Categoria.objects.create(
            nome="Salário", tipo=TipoValor.RECEITA
        )
        self.rendimentos = Categoria.objects.create(
            nome="Rendimentos", tipo=TipoValor.RECEITA
        )
        self.lazer = Categoria.objects.create(
            nome="Lazer", tipo=TipoValor.DESPESA
        )
        self.autor = get_user_model().objects.create_user(
            username="dono", password="senha-de-teste"
        )

    def _movimento_existente(self, categoria, id_externo="ID-1"):
        return Movimento.objects.create(
            data=date(2026, 11, 5),
            valor=Decimal("10.50"),
            tipo=TipoValor.DESPESA,
            conta=self.conta,
            categoria=categoria,
            descricao="Lançamento antigo",
            origem=Movimento.Origem.PLUGGY,
            criado_por=self.autor,
            id_externo=id_externo,
        )

    def test_mapeia_food_delivery_para_alimentacao(self):
        importar_transacoes(
            [self.transacao(category="Food delivery")], self.conta
        )
        self.assertEqual(Movimento.objects.get().categoria, self.alimentacao)

    def test_mapeia_income_taxes_para_impostos(self):
        importar_transacoes(
            [self.transacao(category="Income taxes")], self.conta
        )
        self.assertEqual(Movimento.objects.get().categoria, self.impostos)

    def test_mapeia_transfers_para_transferencia_fora_do_gasto(self):
        importar_transacoes(
            [self.transacao(category="Transfers")], self.conta
        )
        movimento = Movimento.objects.get()
        self.assertEqual(movimento.categoria, self.transferencia_despesa)
        self.assertFalse(movimento.categoria.entra_no_gasto)

    def test_mapeia_transferencia_de_receita_para_a_categoria_do_tipo(self):
        importar_transacoes(
            [
                self.transacao(
                    id="ID-C",
                    type="CREDIT",
                    amount=100.0,
                    category="Transfers",
                )
            ],
            self.conta,
        )
        self.assertEqual(
            Movimento.objects.get().categoria, self.transferencia_receita
        )

    def test_regra_por_descricao_quando_a_pluggy_nao_manda_categoria(self):
        importar_transacoes(
            [
                self.transacao(
                    category=None,
                    description="iFood pedido 123",
                    descriptionRaw="iFood pedido 123",
                )
            ],
            self.conta,
        )
        self.assertEqual(Movimento.objects.get().categoria, self.alimentacao)

    def test_sem_mapa_nem_regra_usa_nao_categorizado(self):
        importar_transacoes(
            [
                self.transacao(
                    category="Outros",
                    description="Loja X",
                    descriptionRaw="Loja X",
                )
            ],
            self.conta,
        )
        movimento = Movimento.objects.get()
        self.assertEqual(movimento.categoria.nome, CATEGORIA_PADRAO)
        self.assertEqual(movimento.categoria.tipo, TipoValor.DESPESA)

    def test_importacao_atualiza_existente_em_nao_categorizado(self):
        padrao = Categoria.objects.create(
            nome=CATEGORIA_PADRAO, tipo=TipoValor.DESPESA
        )
        self._movimento_existente(padrao)

        relatorio = importar_transacoes(
            [self.transacao(category="Food delivery")], self.conta
        )

        self.assertEqual(relatorio.criados, [])
        self.assertEqual(relatorio.atualizados, ["ID-1"])
        self.assertEqual(Movimento.objects.count(), 1)
        self.assertEqual(Movimento.objects.get().categoria, self.alimentacao)

    def test_importacao_nao_sobrescreve_categoria_manual(self):
        self._movimento_existente(self.lazer)

        relatorio = importar_transacoes(
            [self.transacao(category="Food delivery")], self.conta
        )

        self.assertEqual(relatorio.atualizados, [])
        self.assertEqual(len(relatorio.pulados), 1)
        self.assertEqual(Movimento.objects.get().categoria, self.lazer)

    def test_dry_run_conta_atualizacao_sem_gravar(self):
        padrao = Categoria.objects.create(
            nome=CATEGORIA_PADRAO, tipo=TipoValor.DESPESA
        )
        self._movimento_existente(padrao)

        relatorio = importar_transacoes(
            [self.transacao(category="Food delivery")],
            self.conta,
            dry_run=True,
        )

        self.assertEqual(relatorio.atualizados, ["ID-1"])
        self.assertEqual(relatorio.criados, [])
        self.assertEqual(Movimento.objects.get().categoria, padrao)

    def test_mapa_completo_das_despesas(self):
        casos = [
            ("Food delivery", self.alimentacao),
            ("Groceries", self.alimentacao),
            ("Eating out", self.alimentacao),
            ("Electronics", self.compras),
            ("Shopping", self.compras),
            ("Clothing", self.compras),
            ("Gas stations", self.transporte),
            ("Parking", self.transporte),
            ("Pharmacy", self.saude),
            ("Dentist", self.saude),
            ("Hospital clinics and labs", self.saude),
            ("Pet supplies and vet", self.pets),
            ("Services", self.moradia),
            ("Telecommunications", self.moradia),
            ("Credit card payment", self.cartao),
            ("Income taxes", self.impostos),
            ("Digital services", self.lazer),
        ]
        for indice, (categoria_pluggy, esperada) in enumerate(casos):
            with self.subTest(categoria_pluggy=categoria_pluggy):
                Movimento.objects.all().delete()
                importar_transacoes(
                    [self.transacao(id=f"ID-D{indice}", category=categoria_pluggy)],
                    self.conta,
                )
                self.assertEqual(Movimento.objects.get().categoria, esperada)

    def test_mapa_de_investimento_fica_fora_do_gasto(self):
        importar_transacoes(
            [self.transacao(category="Investments")], self.conta
        )
        movimento = Movimento.objects.get()
        self.assertEqual(movimento.categoria, self.investimento)
        self.assertFalse(movimento.categoria.entra_no_gasto)

    def test_mapa_de_receitas(self):
        casos = [
            ("Salary", self.salario),
            ("Proceeds interests and dividends", self.rendimentos),
        ]
        for indice, (categoria_pluggy, esperada) in enumerate(casos):
            with self.subTest(categoria_pluggy=categoria_pluggy):
                Movimento.objects.all().delete()
                importar_transacoes(
                    [
                        self.transacao(
                            id=f"ID-R{indice}",
                            type="CREDIT",
                            amount=100.0,
                            category=categoria_pluggy,
                        )
                    ],
                    self.conta,
                )
                self.assertEqual(Movimento.objects.get().categoria, esperada)

    def test_mapa_das_transferencias_fica_fora_do_gasto(self):
        for indice, categoria_pluggy in enumerate(
            ["Transfers", "Transfer - PIX", "Same person transfer"]
        ):
            with self.subTest(categoria_pluggy=categoria_pluggy):
                Movimento.objects.all().delete()
                importar_transacoes(
                    [self.transacao(id=f"ID-T{indice}", category=categoria_pluggy)],
                    self.conta,
                )
                movimento = Movimento.objects.get()
                self.assertEqual(movimento.categoria, self.transferencia_despesa)
                self.assertFalse(movimento.categoria.entra_no_gasto)
