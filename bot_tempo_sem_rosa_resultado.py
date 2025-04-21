import json
import time
import requests
from datetime import datetime, timedelta
from collections import defaultdict

# Constantes
ARQUIVO_ENTRADA = "data/sem_vela_rosa.json"
ARQUIVO_SAIDA = "data/sem_vela_rosa_resultado.json"
TOKEN = "7026461077:AAEfwA-3I706oywyYn4rvOQQzlqlxMzzlOs"
CHAT_ID = "-1002688788017"
URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# Histórico de alertas enviados (em memória)
alertas_ja_enviados = set()

# Função para enviar mensagens ao Telegram
def enviar_telegram(mensagem):
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem
    }
    requests.post(URL, data=payload)

print("🚀 Bot tempo_sem_rosa_resultado rodando a cada 15 segundos...\n")

# Loop principal
while True:
    try:
        with open(ARQUIVO_ENTRADA, "r", encoding="utf-8") as f:
            dados = json.load(f)

        velas_rosa = []
        velas_100x = []
        registro_por_hora = defaultdict(lambda: {'azul': 0, 'roxa': 0, 'rosa': 0})

        ultima_entrada = dados[-1]
        dt_ultima_entrada = datetime.strptime(ultima_entrada["datetime"], "%Y-%m-%d %H:%M:%S")

        for v in dados:
            if "datetime" not in v or not v["datetime"]:
                continue
            try:
                dt = datetime.strptime(v["datetime"], "%Y-%m-%d %H:%M:%S")
                v["vela_float"] = float(v["vela"])
                hora_chave = dt.replace(minute=0, second=0)
                registro_por_hora[hora_chave][v["classificacao"]] += 1

                if v["vela_float"] >= 10:
                    velas_rosa.append((dt, v))
                if v["vela_float"] >= 100:
                    velas_100x.append((dt, v))
            except:
                continue


        if not velas_rosa:
            print("[ERRO] Nenhuma vela rosa encontrada no JSON.")
            time.sleep(3)
            continue

        # Últimas velas
        ultima_rosa_dt, ultima_rosa_v = velas_rosa[-1]
        ultima_100x_dt, ultima_100x_v = velas_100x[-1] if velas_100x else (None, None)

        tempo_sem_rosa = dt_ultima_entrada - ultima_rosa_dt
        tempo_formatado_rosa = str(tempo_sem_rosa).split(".")[0]

        if ultima_100x_dt:
            tempo_sem_100x = dt_ultima_entrada - ultima_100x_dt
            tempo_formatado_100x = str(tempo_sem_100x).split(".")[0]
        else:
            tempo_sem_100x = None
            tempo_formatado_100x = "Sem registro ainda"

        # Média entre rosas
        ultimas_15_rosas = velas_rosa[-15:]
        tempos = [(ultimas_15_rosas[i][0] - ultimas_15_rosas[i - 1][0]).total_seconds() / 60 for i in range(1, len(ultimas_15_rosas))]
        media_min_rosa = round(sum(tempos) / len(tempos), 2) if tempos else None
        minutos_int = int(media_min_rosa)
        segundos_restantes = int((media_min_rosa - minutos_int) * 60)
        media_formatada = f"{minutos_int:02d}:{segundos_restantes:02d} minutos"

        # Distribuição por hora
        distribuicao_horaria = {}
        for hora, contagem in sorted(registro_por_hora.items()):
            key = f"{hora.strftime('%H:00')} - {(hora + timedelta(hours=1)).strftime('%H:00')}"
            distribuicao_horaria[key] = contagem

        # Alertas automáticos
        minutos_decorridos = int(tempo_sem_rosa.total_seconds() // 60)
        alertas_enviados = []

        for alerta_minuto in [5, 10, 15, 20, 25, 30]:
            if minutos_decorridos == alerta_minuto and alerta_minuto not in alertas_ja_enviados:
                mensagem = (
    f"🚨 Já se passaram {alerta_minuto} minutos🚨\n\n"
    f"sem vela rosa!🌺\n\n"
    f"📊 Análise: Com base na média,\n🤔 já era pra ter saído."
)
                enviar_telegram(mensagem)
                alertas_enviados.append(mensagem)
                alertas_ja_enviados.add(alerta_minuto)

        if ultima_entrada['classificacao'] == 'rosa':
            minutos_desde_anterior = round((dt_ultima_entrada - ultima_rosa_dt).total_seconds() / 60, 2)
            if minutos_desde_anterior > media_min_rosa and ultima_entrada['datetime'] != ultima_rosa_v['datetime']:
                mensagem = f"🌸 Saiu vela rosa após {minutos_desde_anterior:.2f} minutos!"
                enviar_telegram(mensagem)
                alertas_enviados.append(mensagem)
                alertas_ja_enviados.clear()

        # Resultado
        resultado = {
            "media_minutos_entre_rosas": media_formatada,
            "ultima_rosa": {
                "vela": ultima_rosa_v["vela"],
                "horario": ultima_rosa_v["horario"],
                "data": ultima_rosa_v["data"],
                "datetime": ultima_rosa_v["datetime"]
            },
            "tempo_desde_ultima_rosa": tempo_formatado_rosa,
            "tempo_desde_ultima_100x": {
                "descricao": f"Já fazem {tempo_formatado_100x} que não sai uma vela de 100x"
                if ultima_100x_v else "Nenhuma vela 100x encontrada.",
                "ultima": {
                    "valor": ultima_100x_v["vela"] if ultima_100x_v else None,
                    "horario": ultima_100x_v["horario"] if ultima_100x_v else None,
                    "data": ultima_100x_v["data"] if ultima_100x_v else None,
                    "datetime": ultima_100x_v["datetime"] if ultima_100x_v else None,
                } if ultima_100x_v else {}
            },
            "velas_por_horario": distribuicao_horaria,
            "alertas_enviados": alertas_enviados
        }

        with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f_out:
            json.dump(resultado, f_out, indent=2, ensure_ascii=False)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Análise atualizada")
        time.sleep(3)

    except Exception as e:
        print(f"[ERRO] {e}")
        time.sleep(3)
