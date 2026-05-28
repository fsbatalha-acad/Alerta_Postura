import cv2
import mediapipe as mp
import time
import os
import sys

# Função para garantir que o executável ache o arquivo da IA
def encontra_caminho_recurso(caminho_relativo):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, caminho_relativo)

# Configurações da API do MediaPipe
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=encontra_caminho_recurso('pose_landmarker_full.task')),
    running_mode=VisionRunningMode.VIDEO
)

# VARIÁVEIS DE CONTROLE DA POSTURA E TEMPO
distancia_referencia = None  
calibrado = False
tempo_inicio_postura_ruim = None  

# VARIÁVEIS PARA O RELATÓRIO
contador_alertas = 0             # Quantidade de vezes que o alerta vermelho ativou
tempo_total_postura_ruim = 0.0   # Acumulador de tempo em postura inadequada
alerta_ativo_atualmente = False  # Flag para saber se o alerta já estava computado
momento_inicio_alerta = None     # Marca o início do alerta crítico

# Variáveis globais para os comandos dos botões
comando_calibrar = False
comando_encerrar = False

# FUNÇÃO QUE DETECTA CLIQUES DO MOUSE
def detectar_clique(event, x, y, flags, param):
    global comando_calibrar, comando_encerrar
    if event == cv2.EVENT_LBUTTONDOWN:  
        # Verifica se o clique foi na área do Botão Calibrar (no lado direito da faixa, Y entre 5 e 45)
        if largura_tela - 200 <= x <= largura_tela - 110 and 5 <= y <= 45:
            comando_calibrar = True
        
        # Verifica se o clique foi na área do Botão Sair (no lado direito da faixa, Y entre 5 e 45)
        if largura_tela - 100 <= x <= largura_tela - 10 and 5 <= y <= 45:
            comando_encerrar = True

webcam = cv2.VideoCapture(0)

cv2.namedWindow("Monitor de Postura")
cv2.setMouseCallback("Monitor de Postura", detectar_clique)

# Guarda o momento exato em que o monitoramento começou de verdade
tempo_inicio_sessao = None

with PoseLandmarker.create_from_options(options) as landmarker:
    print("APLICAÇÃO INICIADA COM SUCESSO!")
    
    while webcam.isOpened():
        sucesso, frame = webcam.read()
        if not sucesso:
            break

        frame = cv2.flip(frame, 1)
        altura_tela, largura_tela, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        timestamp = int(webcam.get(cv2.CAP_PROP_POS_MSEC))
        
        resultado = landmarker.detect_for_video(mp_image, timestamp)

        y_nariz = None
        y_linha_ombros = None

        if resultado.pose_landmarks:
            for landmarks in resultado.pose_landmarks:
                pos_y_nariz = int(landmarks[0].y * altura_tela)
                pos_y_ombro_esq = int(landmarks[11].y * altura_tela)
                pos_y_ombro_dir = int(landmarks[12].y * altura_tela)

                y_linha_ombros = (pos_y_ombro_esq + pos_y_ombro_dir) / 2
                y_nariz = pos_y_nariz

                # Desenha os pontos de feedback da IA
                cv2.circle(frame, (int(landmarks[0].x * largura_tela), pos_y_nariz), 6, (255, 255, 0), cv2.FILLED)
                cv2.circle(frame, (int(landmarks[11].x * largura_tela), pos_y_ombro_esq), 6, (0, 255, 255), cv2.FILLED)
                cv2.circle(frame, (int(landmarks[12].x * largura_tela), pos_y_ombro_dir), 6, (0, 255, 255), cv2.FILLED)

        # LÓGICA DO BOTÃO CALIBRAR
        if comando_calibrar:
            comando_calibrar = False  
            if y_nariz is not None and y_linha_ombros is not None:
                distancia_referencia = y_linha_ombros - y_nariz
                calibrado = True
                tempo_inicio_sessao = time.time() # Inicia a contagem do tempo total
                print("Sistema Calibrado!")

        # LÓGICA DE EXIBIÇÃO DE STATUS E ACUMULAÇÃO DE DADOS
        postura_critica = False
        texto_status = ""
        cor_texto = (0, 0, 0) 
        
        if not calibrado:
            texto_status = "Clique em CALIBRAR para iniciar"
            cor_texto = (0, 0, 0)
        else:
            if y_nariz is not None and y_linha_ombros is not None:
                distancia_atual = y_linha_ombros - y_nariz
                limite_critico = distancia_referencia * 0.83

                if distancia_atual < limite_critico:
                    if tempo_inicio_postura_ruim is None:
                        tempo_inicio_postura_ruim = time.time()
                    
                    segundos_passados = time.time() - tempo_inicio_postura_ruim

                    if segundos_passados >= 5.0:
                        postura_critica = True 
                        texto_status = "ALERTA: CORRIJA SUA POSTURA!"
                        cor_texto = (0, 0, 255) 

                        if not alerta_ativo_atualmente:
                            contador_alertas += 1
                            alerta_ativo_atualmente = True
                            momento_inicio_alerta = time.time()
                    else:
                        tempo_restante = 5 - int(segundos_passados)
                        texto_status = f"Postura Ruim... Alertando em: {tempo_restante}s"
                        cor_texto = (0, 165, 255) 
                else:
                    tempo_inicio_postura_ruim = None
                    texto_status = "Postura: OK"
                    cor_texto = (0, 150, 0) 

                    if alerta_ativo_atualmente:
                        tempo_duracao_alerta = time.time() - momento_inicio_alerta
                        tempo_total_postura_ruim += tempo_duracao_alerta
                        alerta_ativo_atualmente = False

        # 1. Cria o overlay transparente da faixa branca
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (largura_tela, 50), (255, 255, 255), cv2.FILLED)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        
        # 2. Renderiza textos e botões na tela
        cv2.putText(frame, texto_status, (20, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor_texto, 2)
        cv2.rectangle(frame, (largura_tela - 200, 5), (largura_tela - 110, 45), (0, 180, 0), cv2.FILLED)
        cv2.putText(frame, "CALIBRAR", (largura_tela - 185, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 2)
        cv2.rectangle(frame, (largura_tela - 100, 5), (largura_tela - 10, 45), (0, 0, 255), cv2.FILLED)
        cv2.putText(frame, "SAIR", (largura_tela - 67, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 2)

        if postura_critica:
            cv2.rectangle(frame, (0, 0), (largura_tela, altura_tela), (0, 0, 255), 15)

        cv2.imshow("Monitor de Postura", frame)

        if comando_encerrar or (cv2.waitKey(1) & 0xFF == ord('q')):
            if alerta_ativo_atualmente and momento_inicio_alerta is not None:
                tempo_total_postura_ruim += (time.time() - momento_inicio_alerta)
            break

webcam.release()
cv2.destroyAllWindows()

# --- CONSTRUÇÃO E GRAVAÇÃO DO RELATÓRIO ERGONÔMICO ---
if calibrado and tempo_inicio_sessao is not None:
    tempo_total_monitorado = time.time() - tempo_inicio_sessao
    
    # Nova Lógica: Tempo Correto = Tempo Total - Tempo Ruim
    tempo_total_postura_correta = max(0.0, tempo_total_monitorado - tempo_total_postura_ruim)
    
    # Conversões para formato legível (Minutos e Segundos)
    m_tot, s_tot = divmod(int(tempo_total_monitorado), 60)
    m_ruim, s_ruim = divmod(int(tempo_total_postura_ruim), 60)
    m_corr, s_corr = divmod(int(tempo_total_postura_correta), 60)
    
    # Cálculos de porcentagem
    porcentagem_ruim = (tempo_total_postura_ruim / tempo_total_monitorado) * 100 if tempo_total_monitorado > 0 else 0
    porcentagem_correta = (tempo_total_postura_correta / tempo_total_monitorado) * 100 if tempo_total_monitorado > 0 else 0

    # Monta a string do relatório
    relatorio_texto = (
        "=============================================\n"
        "       RELATÓRIO DE SAÚDE ERGONÔMICA       \n"
        "=============================================\n"
        f" Data/Hora do Fim: {time.strftime('%d/%m/%Y %H:%M:%S')}\n"
        "---------------------------------------------\n"
        f" • Tempo Total Monitorado: {m_tot}m {s_tot}s\n"
        f" • Alertas de Postura Emitidos: {contador_alertas} vez(es)\n"
        f" • Tempo em Postura Correta: {m_corr}m {s_corr}s ({porcentagem_correta:.1f}% do tempo)\n"
        f" • Tempo em Postura Inadequada: {m_ruim}m {s_ruim}s ({porcentagem_ruim:.1f}% do tempo)\n"
        "=============================================\n"
    )
    
    # 1. Mostra o relatório no terminal
    print("\n" + relatorio_texto)
    
    # 2. SALVA NO ARQUIVO .TXT
    try:
        with open("relatorio_postura.txt", "w", encoding="utf-8") as arquivo:
            arquivo.write(relatorio_texto)
        print("💾 Relatório salvo com sucesso em 'relatorio_postura.txt'!")
    except Exception as e:
        print(f"❌ Erro ao salvar o arquivo de texto: {e}")
else:
    print("\nO sistema não foi calibrado. Nenhuma estatística foi gerada.")