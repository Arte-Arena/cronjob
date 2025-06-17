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
- Docker
- MicroK8s / Kubernetes
- Uvicorn
- Pydantic
- Pytest (para testes)

---

## 🚀 Como rodar localmente

```bash
git clone https://github.com/Arte-Arena/cronjob.git
cd cronjob
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
