# 🕒 Cronjob da Arte Arena

Agendador de tarefas assíncronas da Arte Arena, containerizado e pronto para produção em clusters MicroK8s/Kubernetes. Desenvolvido com [Rocketry](https://github.com/Miksus/rocketry) para agendamento declarativo e [FastAPI](https://fastapi.tiangolo.com/) para controle via API HTTP. Persistência em MongoDB e execução desacoplada, eficiente e confiável.

---

## ✨ Visão Geral

Este serviço executa tarefas automatizadas como:

- Agendamento de mensagens e notificações
- Sincronizações com serviços externos
- Envio automático de relatórios e alertas
- Limpeza de dados, manutenção e rotinas recorrentes
- Qualquer lógica programável em Python com base em tempo

Inspirado em [rocketry-with-fastapi](https://github.com/Miksus/rocketry-with-fastapi), mas com diversas adaptações para uso real em produção, incluindo integração completa com MongoDB, execução assíncrona robusta e testes automatizados.

---

## ⚙️ Tecnologias Utilizadas

- Python 3.11+
- [Rocketry](https://github.com/Miksus/rocketry)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Motor](https://motor.readthedocs.io/) (driver async do MongoDB)
- [HTTPX](https://www.python-httpx.org/) para chamadas assíncronas
- [Uvicorn](https://www.uvicorn.org/) como servidor ASGI
- [Pydantic v1](https://docs.pydantic.dev/1.10/)
- [Pytest](https://docs.pytest.org/) + [pytest-asyncio](https://pypi.org/project/pytest-asyncio/)
- Docker / Kubernetes / MicroK8s

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

Os testes utilizam pytest e httpx.AsyncClient, validando funcionalidades como:

- Persistência no MongoDB
- Agendamento correto com start_cond
- Retorno esperado do endpoint /schedule-message

Para rodar os testes:

`python -m pytest`

Os testes não sobem o servidor (uvicorn), mas interagem diretamente com a instância FastAPI in-memory. Isso permite testes rápidos, assíncronos e realistas.

## 🧠 Como funciona o agendamento com Rocketry

Quando a API `/schedule-message` é chamada, um novo agendamento é salvo no MongoDB e uma tarefa dinâmica é criada com a seguinte instrução:

    Quando a API /schedule-message é chamada, um novo agendamento é salvo no MongoDB e uma tarefa dinâmica é criada com a seguinte instrução:

Rocketry então:

- Registra a tarefa como FuncTask com base na start_cond
- Monitora a execução em background, sem depender de filas externas
- Executa automaticamente no momento certo, sem intervenção manual

Essa abordagem garante:

- Precisão temporal confiável
- Execução direta via `async def`
- Nenhuma dependência de Celery, Redis, RabbitMQ ou brokers externos
- Escalabilidade via múltiplas réplicas Kubernetes com base no MongoDB

---

## 📂 Estrutura do Projeto

    app/
    ├── api.py             # Rotas da API FastAPI
    ├── db.py              # Conexão MongoDB (motor async)
    ├── scheduler.py       # Tarefas Rocketry
    ├── main.py            # Executor principal (FastAPI + Rocketry)
    ├── models.py          # Esquemas Pydantic/MongoDB (se necessário)
    tests/
    └── test_schedule_message.py  # Teste da API de agendamento

---

## 🛠️ Deploy e Escalabilidade

- Deploy via MicroK8s com dois containers separados:
-- `cronjob-api` (FastAPI)
-- `cronjob-scheduler` (Rocketry)
- TLS com cert-manager e ClusterIssuer
- Observabilidade via `/healthcheck`
- Ingress separado para API (`api.cronjob.spacearena.net`)
- Persistência em MongoDB remoto com autenticação
- Condições de inicialização sincronizadas via `load_schedules()`

---

## 🔐 Considerações de Produção

- Use variáveis de ambiente para segredos e URIs
- Habilite autenticação nos endpoints (ex: Bearer Token)
- Monitorar logs com `kubectl logs` ou ferramentas de observabilidade (Grafana, Loki, etc.)
- Reforce a persistência com índices no MongoDB (por ex: `send_at`)

---

## 📎 Exemplo de Payload para /schedule-message

    {
    "to": "5511999999999",
    "body": "Olá, {{1}}! Seu pedido será entregue em {{2}}.",
    "userId": "abc123",
    "type": "template",
    "templateName": "notificacao_entrega",
    "params": ["Leandro", "2 dias úteis"],
    "send_at": "2025-06-21T14:00:00-03:00"
    }

A API substituirá os placeholders dinamicamente e criará uma tarefa com:

    start_cond = "once @ 2025-06-21 14:00"

---

## 🧭 start_cond é o elo entre FastAPI e Rocketry

Rocketry trabalha baseado em `condições declarativas`, não filas. A cada requisição da API:
- A tarefa é registrada dinamicamente
- É verificada continuamente por Rocketry no background
- Executa no tempo certo, sem delay de polling

Ideal para:

- Agendamentos únicos e pontuais (ex: notificações por WhatsApp)
- Situações onde precisão temporal é crítica
- Execução assíncrona leve sem brokers

---

## 🧩 Futuras melhorias (sugestões)

- Painel de agendamentos com status
- Reagendamento com retry policy
- Webhook para status de execução
- Workers paralelos com fila opcional
- Validação avançada com schemas por tipo de tarefa


