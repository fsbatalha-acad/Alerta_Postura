# 🖥️ Monitor de Postura Inteligente com IA

Este projeto é uma aplicação de visão computacional em Python que monitora a postura do usuário em tempo real utilizando a webcam. O sistema ajuda a prevenir problemas ergonômicos durante longas sessões de estudo ou trabalho.

## ✨ Funcionalidades
- **Detecção Facial e Corporal:** Utiliza a API do Google MediaPipe (versão 2026).
- **Interface Interativa:** Botões transparentes integrados na tela para calibrar e sair.
- **Filtro Temporal:** O alerta só dispara se o usuário permanecer na postura incorreta por mais de 5 segundos.
- **Relatório de Saúde:** Gera estatísticas de tempo em postura correta vs. incorreta e exporta um arquivo `.txt` ao finalizar.

## 🚀 Como Rodar o Projeto

1. Instale as dependências necessárias:

   ```bash
   pip install opencv-python mediapipe
   ```
   
2. Baixe o modelo de IA do MediaPipe (pose_landmarker_full.task) e coloque-o na pasta raiz.


3. Execute o programa:

   ```bash
   python main.py
   ```


## 🚀 Comandos do Git no Terminal

Agora, abra o terminal do VS Code dentro da pasta do projeto e execute a sequência de comandos abaixo:

1. Inicializar o repositório local

   ```bash
   git init
   ```
📦 Como Gerar o Aplicativo Executável
Como os arquivos de build e o próprio executável final ficam muito pesados para serem hospedados no GitHub (passam do limite de 100 MB), você pode gerar o aplicativo na sua própria máquina usando o PyInstaller.

Basta abrir o terminal na pasta do projeto e rodar o comando abaixo:

```bash
python -m PyInstaller --noconfirm --onedir --windowed --add-data "pose_landmarker_full.task;." --hidden-import mediapipe.python._framework_bindings.image --hidden-import mediapipe.python._framework_bindings.image_frame main.py
```