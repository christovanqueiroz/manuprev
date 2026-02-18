# Sistema de Manutenção Preventiva

API em Flask para gerenciar manutenção preventiva e corretiva de equipamentos, com geração de relatório em PDF e cálculo de indicadores de confiabilidade (MTBF/MTTR).

## Funcionalidades

- Cadastro de equipamentos.
- Plano de manutenção preventiva por equipamento.
- Registro de manutenções corretivas.
- Relatório em PDF consolidado.
- Indicadores de manutenção (MTBF e MTTR).

## Requisitos

- Python 3.11+

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execução

```bash
python -m app.main
```

Servidor disponível em `http://localhost:5000`.

## Endpoints principais

### Equipamentos

- `POST /equipments`
- `GET /equipments`

Exemplo de payload:

```json
{
  "name": "Compressor Atlas",
  "category": "Compressor",
  "serial_number": "COMP-001",
  "location": "Linha A"
}
```

### Plano preventivo

- `POST /preventive-plans`
- `GET /preventive-plans`

Exemplo de payload:

```json
{
  "equipment_id": 1,
  "frequency_days": 30,
  "next_due_date": "2026-03-01",
  "activities": "Inspeção visual, troca de filtro, teste de vibração",
  "active": true
}
```

### Corretivas

- `POST /corrective-records`
- `GET /corrective-records?equipment_id=1`

Exemplo de payload:

```json
{
  "equipment_id": 1,
  "description": "Falha no rolamento principal",
  "failure_start": "2026-02-10T10:00:00",
  "repair_end": "2026-02-10T15:30:00",
  "root_cause": "Lubrificação inadequada",
  "actions_taken": "Substituição do rolamento e revisão do plano de lubrificação"
}
```

### Indicadores

- `GET /indicators` (todos os equipamentos com histórico)
- `GET /indicators?equipment_id=1` (equipamento específico)

### Relatório

- `GET /reports/pdf` retorna arquivo `relatorio_manutencao.pdf`.

## Testes

```bash
pytest -q
```
