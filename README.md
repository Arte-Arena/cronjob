# Cronjob da Arte Arena

Agendador de tarefas backend da Arte Arena, containerizado e preparado para rodar em clusters MicroK8s/Kubernetes. Baseado no framework [Rocketry](https://github.com/Miksus/rocketry) com API FastAPI para controle e observabilidade.

---

## ✨ Visão Geral

Este serviço executa tarefas automatizadas como:

- Sincronizações periódicas com serviços externos
- Envio automático de relatórios e alertas
- Limpezas e manutenção de dados
- Qualquer rotina programável em Python agendada por cron-like ou lógica customizada

É fortemente inspirado no projeto [rocketry-with-fastapi](https://github.com/Miksus/rocketry-with-fastapi), com adaptações para produção e execução containerizada.

---

## ⚙️ Tecnologias

- Python 3.11+
- [Rocketry](https://github.com/Miksus/rocketry)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Motor (MongoDB async)](https://motor.readthedocs.io/)
- [HTTPX](https://www.python-httpx.org/) para clientes assíncronos
- [Pytest](https://docs.pytest.org/) para testes
- Docker
- MicroK8s / Kubernetes
- Uvicorn
- Pydantic

---

## 🚀 Como rodar localmente

```bash
git clone https://github.com/Arte-Arena/cronjob.git
cd cronjob
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## ✅ Testes Automatizados

Os testes são implementados com pytest e httpx.AsyncClient, e validam funcionalidades essenciais como o endpoint de agendamento /schedule-message. Rode os teste com o seguinte comando na raiz do projeto:

`python -m pytest`

Utilizamos httpx.AsyncClient diretamente contra a instância do FastAPI (app=app) nos testes. Essa abordagem permite reproduzir o comportamento do cliente real com maior precisão (especialmente para rotas como /schedule-message, que envolvem persistência assíncrona no MongoDB e criação de tarefas dinâmicas). Desta forma, consesguimos testar a API de forma realista sem subir o servidor com o `uvicorn`.

## 🧭 Importância do start_cond na Integração FastAPI + Rocketry

Na funcionalidade de Agendamento de Envio de Mensagens, o campo start_cond é essencial para definir o momento exato em que a tarefa deve ser executada dentro do Rocketry. Essa condição é gerada dinamicamente pela API FastAPI com base no horário informado (send_at) e determina quando o Rocketry deverá disparar a execução assíncrona da mensagem. 

O uso de `start_cond="once @ {timestamp}"` permite que cada tarefa seja única e programada apenas uma vez, o que é ideal para agendamentos individuais e pontuais como notificações e alertas. Sem essa configuração explícita, a integração perderia a capacidade de agendar tarefas com precisão temporal, comprometendo a previsibilidade e confiabilidade do sistema de envio automático. 

Portanto, o `start_cond` atua como o elo entre o backend assíncrono da API e o scheduler de tarefas do Rocketry, garantindo que a lógica de tempo do usuário seja respeitada na execução.

Rocketry é um agendador declarativo baseado em tempo (start_cond), e não depende de filas de tarefas. As tarefas são registradas no session do Rocketry com instruções como:

```
start_cond="once @ 2025-06-19 14:30"
```

Com isso, o Rocketry mantém internamente o controle de quando executar a função. Nenhuma fila intermediária é necessária. A execução ocorre em background, em workers controlados pelo próprio Rocketry. Quando você registra uma tarefa via FastAPI (/schedule-message), a função salva o agendamento no MongoDB, cria dinamicamente um FuncTask com `start_cond` e adiciona ao `app_rocketry.session`.

Rocketry fica rodando em paralelo ao FastAPI (graças ao asyncio.create_task() em main.py), verificando continuamente suas condições internas e executando tarefas automaticamente no tempo certo, sem a necessidade de enfileiramento externo. Se quiser no futuro, é possível complementar com filas para lidar com cargas altas ou retries complexos, mas para a maioria dos casos de agendamento temporal, o Rocketry resolve de forma nativa e eficiente.

# 📂 Estrutura do projeto

app/
├── api.py           # FastAPI app e rotas
├── db.py            # Conexão com MongoDB via motor
├── scheduler.py     # Rocketry tasks e configurações
├── main.py          # Executor Rocketry + FastAPI
tests/
├── test_schedule_message.py  # Teste da rota /schedule-message

# 🛠️ Manutenção e Escalabilidade

O projeto é modular, facilmente extensível para múltiplos tipos de tarefas, e pode ser escalado horizontalmente em clusters Kubernetes. Tarefas persistidas no MongoDB são carregadas na inicialização via load_schedules().


