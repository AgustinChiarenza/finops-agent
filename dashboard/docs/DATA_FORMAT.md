# Estructura de Datos en OBS

El dashboard lee toda la informacion desde un bucket de Huawei Cloud OBS.
Los archivos deben seguir exactamente esta estructura de paths y formatos.

## Estructura de Paths

```
<OBS_BUCKET>/
└── <OBS_PREFIX>/
    ├── CTS/
    │   └── traces/
    │       ├── traces_2025-06-01.json
    │       ├── traces_2025-06-02.json
    │       └── ...                    (.json o .jsonl.gz)
    ├── Metrics/
    │   └── CloudEye/
    │       └── cloudeye_metrics.jsonl.gz
    ├── Costs/
    │   └── CostCenter/
    │       └── cost_usage.csv
    ├── Inventory/
    │   └── resource_inventory.json
    └── Manifest/
        └── dataset_manifest.json      (opcional)
```

---

## 1. CTS Traces

**Path:** `CTS/traces/` — uno o mas archivos `.json` o `.jsonl.gz`

### Formato JSON

Un archivo `.json` puede ser un array de traces o un objeto individual:

```json
[
  {
    "trace_id": "trace-001",
    "time": "2025-06-01T14:30:00Z",
    "user": "iam-user-name",
    "resource_type": "ecs",
    "resource_id": "server-abc123",
    "api_name": "createServer",
    "request": {
      "method": "POST",
      "url": "/v1/servers"
    },
    "response": {
      "status_code": 200
    },
    "source_ip": "10.0.1.5",
    "trace_status": "normal"
  }
]
```

### Campos alternativos aceptados

| Campo principal | Alternativa |
|----------------|-------------|
| `time` | `timestamp` |
| `user` | `caller` |
| `api_name` | `operation` |
| `response.status_code` | `response_status` (en el nivel raiz) |

### Formato JSONL.gz

Cada linea es un JSON individual, archivo comprimido con gzip:

```
{"trace_id":"trace-001","time":"2025-06-01T14:30:00Z",...}
{"trace_id":"trace-002","time":"2025-06-01T14:31:00Z",...}
```

---

## 2. CloudEye Metrics

**Path:** `Metrics/CloudEye/cloudeye_metrics.jsonl.gz` — UN solo archivo JSONL comprimido con gzip

### Formato

Cada linea es un JSON con un datapoint de metrica:

```json
{"resource_id": "ecs-001", "resource_name": "web-server-1", "metric_name": "cpu_util", "timestamp": "2025-06-01T00:00:00Z", "value": 45.2, "unit": "%"}
{"resource_id": "ecs-001", "resource_name": "web-server-1", "metric_name": "cpu_util", "timestamp": "2025-06-01T00:05:00Z", "value": 52.1, "unit": "%"}
{"resource_id": "ecs-001", "resource_name": "web-server-1", "metric_name": "network_in_mbps", "timestamp": "2025-06-01T00:00:00Z", "value": 12.5, "unit": "Mbps"}
{"resource_id": "ecs-002", "resource_name": "db-server-1", "metric_name": "cpu_util", "timestamp": "2025-06-01T00:00:00Z", "value": 78.3, "unit": "%"}
```

### Nombres de metricas reconocidos para deteccion de recursos idle

| Metrica | Nombres aceptados |
|---------|-------------------|
| CPU | `cpu_util`, `cpu_utilization`, `CPUUtilization` |
| Network In | `network_in_mbps`, `network_in_bytes`, `NetworkIn` |
| Network Out | `network_out_mbps`, `network_out_bytes`, `NetworkOut` |

---

## 3. Cost Center

**Path:** `Costs/CostCenter/cost_usage.csv` — UN solo archivo CSV

### Formato

```csv
date,service_type,owner,environment,resource_id,resource_name,billing_mode,daily_cost_usd,usage_amount
2025-06-01,ECS,devops-team,production,ecs-001,web-server-1,postpaid,12.50,24.0
2025-06-01,ECS,devops-team,production,ecs-002,api-server-1,postpaid,8.75,24.0
2025-06-01,RDS,backend-team,production,rds-001,main-db,postpaid,8.30,24.0
2025-06-01,OBS,backend-team,production,obs-001,data-bucket,postpaid,0.12,50.0
2025-06-01,ELB,devops-team,production,elb-001,main-lb,postpaid,1.20,24.0
2025-06-02,ECS,devops-team,production,ecs-001,web-server-1,postpaid,12.50,24.0
```

### Columnas alternativas aceptadas

| Columna principal | Alternativa |
|-------------------|-------------|
| `date` | `period` |
| `daily_cost_usd` | `cost` |

---

## 4. Inventory

**Path:** `Inventory/resource_inventory.json` — UN solo archivo JSON

### Formato

```json
{
  "resources": [
    {
      "resource_id": "ecs-001",
      "resource_name": "web-server-1",
      "service_type": "ECS",
      "environment": "production",
      "owner": "devops-team",
      "status": "running",
      "region": "la-south-2",
      "monthly_cost_usd": 375.00,
      "usage_profile": "steady",
      "created_at": "2024-01-15",
      "tags": {
        "team": "platform",
        "cost_center": "engineering"
      }
    },
    {
      "resource_id": "rds-001",
      "resource_name": "main-db",
      "service_type": "RDS",
      "environment": "production",
      "owner": "backend-team",
      "status": "running",
      "region": "la-south-2",
      "monthly_cost_usd": 249.00,
      "usage_profile": "heavy",
      "created_at": "2024-02-10",
      "tags": {
        "team": "backend",
        "cost_center": "engineering"
      }
    }
  ]
}
```

### Alternativas

- Se acepta `monthly_cost` en vez de `monthly_cost_usd`
- Se acepta `created_date` en vez de `created_at`
- Se acepta un array directo sin el wrapper `{"resources": [...]}`

---

## 5. Manifest (opcional)

**Path:** `Manifest/dataset_manifest.json`

Metadata descriptiva del dataset. No es requerido por el dashboard pero sirve como referencia.

---

## Resumen rapido

| Dato | Path | Formato | Cantidad |
|------|------|---------|----------|
| CTS Traces | `CTS/traces/` | `.json` o `.jsonl.gz` | Uno o mas archivos |
| CloudEye Metrics | `Metrics/CloudEye/cloudeye_metrics.jsonl.gz` | JSONL + gzip | 1 archivo |
| Cost Center | `Costs/CostCenter/cost_usage.csv` | CSV | 1 archivo |
| Inventory | `Inventory/resource_inventory.json` | JSON | 1 archivo |
| Manifest | `Manifest/dataset_manifest.json` | JSON | 1 archivo (opcional) |
