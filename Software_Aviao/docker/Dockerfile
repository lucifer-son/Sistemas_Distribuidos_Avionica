# Usa uma imagem oficial leve do Python
FROM python:3.11-slim

# Define a pasta de trabalho dentro do contentor
WORKDIR /app

# Instala as bibliotecas necessárias (MQTT e Requests para a API)
RUN pip install paho-mqtt requests

# Copia TODOS os 6 códigos dos sensores/sistemas para dentro do contentor
COPY ../sensor_freio.py lider_waic.py sensores_voo.py computador_navegacao.py radar_externo.py fms_distribuido.py ./

# O comando padrão (será substituído pelo docker-compose)
CMD ["python"]