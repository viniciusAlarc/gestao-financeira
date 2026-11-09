#!/usr/bin/env bash
#
# preparar_acesso_celular.sh — descobre o IPv4 desta máquina na rede de casa e prepara a
# linha DJANGO_ALLOWED_HOSTS do `.env`, para o celular abrir o app em http://<ip>:8000.
#
# Sem argumento só imprime o bloco para colar no `.env` e não altera nada.
# Com --aplicar, cria/atualiza a linha no `.env` sem apagar as outras variáveis e sem
# imprimir nenhum valor do arquivo: segredo mora só lá (G13), e o `.env` é do dono.
#
# Uso:
#   scripts/preparar_acesso_celular.sh            # só mostra o IP e o bloco
#   scripts/preparar_acesso_celular.sh --aplicar  # grava/atualiza a linha no .env
#   scripts/preparar_acesso_celular.sh --help

set -euo pipefail

USO="Uso: scripts/preparar_acesso_celular.sh [--aplicar]"

erro() {
    printf 'Erro: %s\n' "$*" >&2
    exit 1
}

APLICAR=0
for argumento in "$@"; do
    case "$argumento" in
        --aplicar) APLICAR=1 ;;
        -h | --help)
            printf '%s\n' "$USO"
            exit 0
            ;;
        *)
            printf 'Argumento desconhecido: %s\n%s\n' "$argumento" "$USO" >&2
            exit 2
            ;;
    esac
done

# A raiz é a pasta acima de scripts/, de onde o Django lê o `.env` (BASE_DIR / ".env").
SCRIPT="$(readlink -f -- "${BASH_SOURCE[0]}")"
RAIZ="$(dirname -- "$(dirname -- "$SCRIPT")")"
ARQUIVO_ENV="$RAIZ/.env"

# 1. O primeiro IPv4 do `hostname -I` (IPv6 não serve para o endereço da rede de casa).
ENDERECOS=()
if SAIDA_HOSTNAME="$(hostname -I 2>/dev/null)"; then
    read -r -a ENDERECOS <<< "$SAIDA_HOSTNAME"
fi

IPV4S=()
for endereco in "${ENDERECOS[@]}"; do
    case "$endereco" in
        *:* | *[!0-9.]*) continue ;; # IPv6 ou coisa que não é IPv4
        127.* | 0.0.0.0) continue ;; # loopback/curinga não servem ao celular
    esac
    IPV4S+=("$endereco")
done

[ "${#IPV4S[@]}" -ge 1 ] ||
    erro "não encontrei IPv4 em 'hostname -I'. Esta máquina está na rede de casa?"

IP="${IPV4S[0]}"
VALOR_NOVO="localhost,127.0.0.1,$IP"
LINHA_NOVA="DJANGO_ALLOWED_HOSTS=$VALOR_NOVO"
ENDERECO_CELULAR="http://$IP:8000"

printf '\nAcesso pelo celular — rede de casa\n\n'
printf 'IP desta máquina: %s\n' "$IP"
if [ "${#IPV4S[@]}" -gt 1 ]; then
    printf 'Outros IPv4 vistos: %s\n' "$(IFS=', '; printf '%s' "${IPV4S[*]:1}")"
    printf '  (pontes de container como 172.x também aparecem aqui; o IP da rede de casa é o que o celular alcança)\n'
fi
printf 'Endereço a abrir no celular: %s\n\n' "$ENDERECO_CELULAR"
printf 'Bloco para o .env (na raiz do projeto):\n\n'
printf '%s\n\n' "$LINHA_NOVA"

if [ ! -f "$ARQUIVO_ENV" ]; then
    printf 'Aviso: o .env ainda não existe.\n'
    printf '  Sem ele vale o padrão localhost,127.0.0.1 e o celular recebe "DisallowedHost".\n'
    printf '  Para criar e já configurar: %s --aplicar\n\n' "${BASH_SOURCE[0]}"
fi

if [ "$APLICAR" -eq 0 ]; then
    printf 'Nada foi alterado (só impressão). Para gravar no .env:\n'
    printf '  %s --aplicar\n\n' "${BASH_SOURCE[0]}"
    printf 'Depois, reinicie o servidor para o Django reler o .env.\n'
    exit 0
fi

# 2. Com --aplicar: calcula o valor final preservando o que já existe na linha.
#    Nada além da linha DJANGO_ALLOWED_HOSTS é lido ou impresso.
trim() {
    local texto="$1"
    texto="${texto#"${texto%%[![:space:]]*}"}"
    texto="${texto%"${texto##*[![:space:]]}"}"
    printf '%s' "$texto"
}

LINHA_ATUAL=""
if [ -f "$ARQUIVO_ENV" ]; then
    LINHA_ATUAL="$(grep -E '^[[:space:]]*(export[[:space:]]+)?DJANGO_ALLOWED_HOSTS[[:space:]]*=' "$ARQUIVO_ENV" | tail -n 1 || true)"
fi

VALORES=()
VALOR_ATUAL=""
if [ -n "$LINHA_ATUAL" ]; then
    VALOR_ATUAL="$(trim "${LINHA_ATUAL#*=}")"
    VALOR_ATUAL="${VALOR_ATUAL#\"}"
    VALOR_ATUAL="${VALOR_ATUAL%\"}"
    VALOR_ATUAL="${VALOR_ATUAL#\'}"
    VALOR_ATUAL="${VALOR_ATUAL%\'}"
    IFS=',' read -r -a PARTES <<< "$VALOR_ATUAL"
    for parte in "${PARTES[@]}"; do
        item="$(trim "$parte")"
        [ -n "$item" ] || continue
        repetido=0
        for existente in "${VALORES[@]}"; do
            [ "$existente" = "$item" ] && repetido=1
        done
        [ "$repetido" -eq 1 ] || VALORES+=("$item")
    done
fi

# Sem linha (ou linha vazia), parte do padrão do Django, igual ao bloco recomendado.
if [ -z "$LINHA_ATUAL" ] || [ -z "$VALOR_ATUAL" ]; then
    VALORES=(localhost 127.0.0.1)
fi

repetido=0
for existente in "${VALORES[@]}"; do
    [ "$existente" = "$IP" ] && repetido=1
done
[ "$repetido" -eq 1 ] || VALORES+=("$IP")

VALOR_FINAL="$(IFS=','; printf '%s' "${VALORES[*]}")"
LINHA_FINAL="DJANGO_ALLOWED_HOSTS=$VALOR_FINAL"

if [ ! -f "$ARQUIVO_ENV" ]; then
    {
        printf '# Criado por scripts/preparar_acesso_celular.sh em %s.\n' "$(date +%Y-%m-%d)"
        printf '# Só a linha do celular. Segredo do Inter mora aqui também, mas só o dono escreve (G13).\n'
        printf '%s\n' "$LINHA_FINAL"
    } > "$ARQUIVO_ENV"
    chmod 600 "$ARQUIVO_ENV"
    printf 'Criei o .env com a linha do celular (nenhum outro valor, nenhum segredo):\n'
    printf '%s\n\n' "$LINHA_FINAL"
elif [ "$LINHA_FINAL" = "DJANGO_ALLOWED_HOSTS=$(trim "${LINHA_ATUAL#*=}")" ]; then
    printf 'O .env já tem o IP %s no DJANGO_ALLOWED_HOSTS. Nada a fazer.\n\n' "$IP"
else
    # Reescreve só a linha do ALLOWED_HOSTS; as outras variáveis passam intactas.
    TEMP="$(mktemp)"
    trap 'rm -f "$TEMP"' EXIT
    awk -v nova="$LINHA_FINAL" '
        /^[[:space:]]*(export[[:space:]]+)?DJANGO_ALLOWED_HOSTS[[:space:]]*=/ {
            if (!achou) { print nova; achou = 1 }
            next
        }
        { print }
        END { if (!achou) print nova }
    ' "$ARQUIVO_ENV" > "$TEMP"
    cat "$TEMP" > "$ARQUIVO_ENV" ||
        erro "não consegui gravar em $ARQUIVO_ENV (permissão?)"
    printf 'Atualizei a linha DJANGO_ALLOWED_HOSTS no .env; as outras variáveis não foram tocadas:\n'
    printf '%s\n\n' "$LINHA_FINAL"
fi

printf 'Reinicie o servidor (Ctrl+C e subir de novo) para o Django reler o .env.\n'
