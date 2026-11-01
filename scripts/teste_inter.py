"""Teste de conexão com a API do Inter (fase 1 do projeto).

Objetivo: provar, no sandbox, que (1) o certificado mTLS é aceito,
(2) o token sai e (3) extrato e saldo voltam. Não grava nada em disco
e não imprime segredo nenhum.

Uso:
    .venv/Scripts/python scripts/teste_inter.py

Credenciais vêm de .env — nunca do código.
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# Console do Windows pode não estar em UTF-8; evita UnicodeEncodeError.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URLS = {
    "sandbox": "https://cdpj-sandbox.partners.bancointer.com.br",
    "producao": "https://cdpj.partners.bancointer.com.br",
}

CAMINHO_TOKEN = "/oauth/v2/token"
CAMINHO_SALDO = "/banking/v2/saldo"
CAMINHO_EXTRATO = "/banking/v2/extrato"
ESCOPO = "extrato.read"

# Endpoints acima seguem a documentação pública do Inter Empresas.
# Ainda não conferidos no ambiente real: se der 404, o corpo da resposta
# aparece no terminal e é o primeiro lugar a olhar.


def carregar_configuracao() -> dict:
    load_dotenv()

    obrigatorias = (
        "INTER_CLIENT_ID",
        "INTER_CLIENT_SECRET",
        "INTER_CERT_PATH",
        "INTER_KEY_PATH",
    )
    faltando = [nome for nome in obrigatorias if not os.getenv(nome, "").strip()]
    if faltando:
        sys.exit(
            "Faltam variáveis no .env: "
            + ", ".join(faltando)
            + "\nVeja .env.example para o formato esperado."
        )

    ambiente = os.getenv("INTER_AMBIENTE", "sandbox").strip().lower()
    if ambiente not in BASE_URLS:
        sys.exit("INTER_AMBIENTE precisa ser 'sandbox' ou 'producao'.")

    for nome in ("INTER_CERT_PATH", "INTER_KEY_PATH"):
        caminho = Path(os.getenv(nome))
        if not caminho.is_file():
            sys.exit(f"{nome} aponta para um arquivo que não existe: {caminho}")

    return {
        "ambiente": ambiente,
        "base_url": BASE_URLS[ambiente],
        "client_id": os.getenv("INTER_CLIENT_ID").strip(),
        "client_secret": os.getenv("INTER_CLIENT_SECRET").strip(),
        "cert": (os.getenv("INTER_CERT_PATH"), os.getenv("INTER_KEY_PATH")),
        "conta": os.getenv("INTER_CONTA_CORRENTE", "").strip(),
    }


def criar_sessao(config: dict) -> requests.Session:
    sessao = requests.Session()
    sessao.cert = config["cert"]
    return sessao


def obter_token(sessao: requests.Session, config: dict) -> str:
    resposta = sessao.post(
        config["base_url"] + CAMINHO_TOKEN,
        headers={
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials", "scope": ESCOPO},
        timeout=30,
    )
    if resposta.status_code != 200:
        raise RuntimeError(
            f"Token recusado (HTTP {resposta.status_code}):\n{resposta.text[:800]}"
        )

    dados = resposta.json()
    token = dados.get("access_token")
    if not token:
        raise RuntimeError(f"Resposta de token sem access_token:\n{dados}")
    print(f"  token obtido, expira em {dados.get('expires_in', '?')}s")
    return token


def cabecalhos(config: dict, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if config["conta"]:
        headers["x-conta-corrente"] = config["conta"]
    return headers


def consultar_saldo(sessao: requests.Session, config: dict, headers: dict) -> dict:
    resposta = sessao.get(
        config["base_url"] + CAMINHO_SALDO, headers=headers, timeout=30
    )
    if resposta.status_code != 200:
        raise RuntimeError(
            f"Saldo falhou (HTTP {resposta.status_code}):\n{resposta.text[:800]}"
        )
    return resposta.json()


def consultar_extrato(
    sessao: requests.Session, config: dict, headers: dict, inicio: date, fim: date
) -> dict:
    resposta = sessao.get(
        config["base_url"] + CAMINHO_EXTRATO,
        headers=headers,
        params={"dataInicio": inicio.isoformat(), "dataFim": fim.isoformat()},
        timeout=30,
    )
    if resposta.status_code != 200:
        raise RuntimeError(
            f"Extrato falhou (HTTP {resposta.status_code}):\n{resposta.text[:800]}"
        )
    return resposta.json()


def main() -> int:
    config = carregar_configuracao()
    print(f"Ambiente: {config['ambiente']} ({config['base_url']})")
    print(f"Conta corrente informada: {'sim' if config['conta'] else 'não'}")

    sessao = criar_sessao(config)
    try:
        print("\n[1/3] Autenticando com certificado mTLS...")
        token = obter_token(sessao, config)
        headers = cabecalhos(config, token)

        print("\n[2/3] Consultando saldo...")
        saldo = consultar_saldo(sessao, config, headers)
        print(f"  disponível: {saldo.get('disponivel')}")
        for chave, valor in saldo.items():
            if chave != "disponivel":
                print(f"  {chave}: {valor}")

        fim = date.today()
        inicio = fim - timedelta(days=30)
        print(f"\n[3/3] Consultando extrato de {inicio} a {fim}...")
        extrato = consultar_extrato(sessao, config, headers, inicio, fim)

        transacoes = extrato.get("transacoes", [])
        print(f"  {len(transacoes)} transação(ões) retornada(s)")
        for item in transacoes[:5]:
            print(
                f"  {item.get('dataEntrada', '?')} | "
                f"{item.get('tipoTransacao', '?')} | "
                f"{item.get('valor', '?')} | {item.get('descricao', '')}"
            )
        if len(transacoes) > 5:
            print(f"  ... e mais {len(transacoes) - 5}")

        print("\nSucesso: certificado, token, saldo e extrato funcionaram.")
        return 0

    except requests.exceptions.SSLError as erro:
        print(f"\nFalha de SSL/mTLS: {erro}")
        print("O certificado e a chave em PEM batem? O certificado está ativo no banco?")
        return 1
    except requests.exceptions.RequestException as erro:
        print(f"\nFalha de rede: {erro}")
        return 1
    except RuntimeError as erro:
        print(f"\n{erro}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
