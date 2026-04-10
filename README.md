# 🛡️ KYC Platform - Background Checks & Compliance

Plataforma completa de **Background Checks** y **KYC (Know Your Customer)** para México, que unifica múltiples fuentes de datos y proporciona verificación integral de identidad con análisis de riesgo.

## 🌟 Características Principales

### ✅ Módulos Integrados

1. **Validación de CURP**
   - Validación de formato con algoritmo de dígito verificador
   - Verificación contra base de datos oficial (RENAPO)
   - Detección de palabras inconvenientes
   - Extracción de componentes (fecha, estado, sexo)

2. **RND - Registro Nacional de Detenciones**
   - Búsqueda automática en el sistema de la SSPC
   - Resolución de captcha con OCR (Tesseract) y fallback a 2captcha
   - Detección de registros de detención con detalles completos

3. **Enriquecimiento de Datos**
   - **Email**: HaveIBeenPwned, Hunter.io, Gravatar
   - **Teléfono**: NumVerify, ShouldIAnswer (spam detection)
   - Detección de emails desechables
   - Validación de operador y tipo de línea

4. **Listas de Sanciones y PEPs**
   - OFAC SDN (Sanciones EE.UU.)
   - ONU Consolidated List
   - OpenSanctions (40+ fuentes consolidadas)
   - SAT Lista 69-B (México)
   - DOF y SCJN (registros judiciales)
   - Fuzzy matching para nombres en español

5. **Motor de Relaciones (Graph Database)**
   - Construcción de grafo de conocimiento
   - Detección de redes ocultas
   - Análisis de patrones sospechosos
   - Visualización con Cytoscape.js
   - Soporte para NetworkX y Neo4j

6. **Dashboard Web Interactivo**
   - Visualización de métricas en tiempo real
   - Gráficas de distribución de riesgo
   - Formulario de verificación intuitivo
   - Resultados detallados con alertas visuales

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│  Dashboard, Forms, Visualizaciones, Alertas                │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────────────┐
│                  API Gateway (FastAPI)                      │
│  Orquestador, Autenticación, Rate Limiting                 │
└─┬──────┬──────┬──────┬──────┬──────┬────────────────────────┘
  │      │      │      │      │      │
  │      │      │      │      │      │
  ▼      ▼      ▼      ▼      ▼      ▼
┌───┐  ┌───┐  ┌───┐  ┌───┐  ┌───┐  ┌───┐
│RND│  │Val│  │Enr│  │San│  │Rel│  │DB │
│   │  │CUR│  │ich│  │cti│  │Gra│  │Mgr│
│Scr│  │P  │  │men│  │ons│  │ph │  │   │
└───┘  └───┘  └───┘  └───┘  └───┘  └─┬─┘
                                       │
                     ┌─────────────────┼─────────────────┐
                     ▼                 ▼                 ▼
              ┌───────────┐    ┌───────────┐    ┌───────────┐
              │PostgreSQL │    │  Neo4j    │    │   Redis   │
              │(Checks DB)│    │(Graph DB) │    │  (Cache)  │
              └───────────┘    └───────────┘    └───────────┘
```

## 🚀 Instalación Rápida

### Opción 1: Docker (Recomendado)

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/kyc-platform.git
cd kyc-platform

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# 3. Levantar todos los servicios
docker-compose up -d

# 4. Verificar que todo esté corriendo
docker-compose ps

# 5. Acceder a la plataforma
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/api/docs
# Neo4j Browser: http://localhost:7474
```

### Opción 2: Instalación Local

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Instalar Tesseract OCR
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# macOS:
brew install tesseract tesseract-lang

# Windows: Descargar de https://github.com/UB-Mannheim/tesseract/wiki

# 4. Configurar PostgreSQL
createdb kyc_db
psql kyc_db < database/init.sql

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env con configuración local

# 6. Iniciar API
uvicorn api.main:app --reload --port 8000

# 7. Iniciar Frontend (en otra terminal)
cd frontend
npm install
npm start
```

## 📋 Variables de Entorno

Crear archivo `.env` con las siguientes variables:

```bash
# Base de Datos
DATABASE_URL=postgresql://kyc_user:kyc_password@localhost:5432/kyc_db

# Neo4j (opcional - usar NetworkX si está deshabilitado)
USE_NEO4J=false
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu_password

# APIs de Enriquecimiento
HIBP_API_KEY=tu_key_haveibeenpwned
HUNTER_API_KEY=tu_key_hunter_io
NUMVERIFY_API_KEY=tu_key_numverify
APILAYER_KEY=tu_key_apilayer

# Sanciones / PEPs
OPENSANCTIONS_API_KEY=tu_key_opensanctions

# Captcha (opcional - fallback para RND)
TWOCAPTCHA_API_KEY=tu_key_2captcha

# Configuración
FUZZY_THRESHOLD=82
ENVIRONMENT=development
LOG_LEVEL=INFO

# Seguridad
JWT_SECRET_KEY=tu_secret_key_super_seguro
API_KEY=tu_api_key_para_clientes
```

## 🔑 Obtener API Keys

| Servicio | URL | Plan Gratuito |
|----------|-----|---------------|
| HaveIBeenPwned | [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key) | Sí (limitado) |
| Hunter.io | [hunter.io/api](https://hunter.io/api) | 25/mes |
| NumVerify | [numverify.com](https://numverify.com) | 100/mes |
| OpenSanctions | [opensanctions.org](https://www.opensanctions.org) | 1000/mes |
| 2captcha | [2captcha.com](https://2captcha.com) | Pago ($1/1000) |

## 📖 Uso de la API

### Endpoint Principal: Background Check Completo

```bash
POST /api/v1/background-check
Content-Type: application/json

{
  "full_name": "Juan García López",
  "first_name": "Juan",
  "paternal_surname": "García",
  "maternal_surname": "López",
  "birth_date": "15/06/1985",
  "curp": "GALJ850615HDFRPN01",
  "rfc": "GALJ850615AB1",
  "email": "juan.garcia@email.com",
  "phone": "+525512345678",
  "address": "Calle Principal 123, CDMX",
  "state": "Nacional",
  "consent_id": "CONSENT-2024-001",
  "requested_by": "operador_01",
  "include_rnd_check": true,
  "include_sanctions": true,
  "include_enrichment": true,
  "include_network_analysis": true
}
```

### Respuesta Ejemplo

```json
{
  "check_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T10:30:00Z",
  "subject": {
    "full_name": "Juan García López",
    "curp": "GALJ850615HDFRPN01",
    "email": "juan.garcia@email.com",
    "phone": "+525512345678"
  },
  "global_risk_score": 35.5,
  "global_risk_level": "MEDIO",
  "flags": [
    "⚠️ Email encontrado en 2 brechas de datos",
    "✅ CURP válido y verificado",
    "✅ No se encontraron registros en RND"
  ],
  "critical_alerts": [],
  "rnd_results": [...],
  "enrichment_results": {...},
  "sanctions_results": {...},
  "network_analysis": {...},
  "curp_validation": {...},
  "sources_consulted": [
    "CURP Database",
    "RND (SSPC)",
    "HaveIBeenPwned",
    "Hunter.io",
    "OFAC SDN",
    "OpenSanctions"
  ],
  "processing_time_ms": 2500,
  "consent_id": "CONSENT-2024-001",
  "requested_by": "operador_01"
}
```

### Otros Endpoints

```bash
# Validar solo CURP
POST /api/v1/validate-curp
{
  "curp": "GALJ850615HDFRPN01",
  "full_name": "Juan García López",
  "birth_date": "15/06/1985"
}

# Obtener estadísticas
GET /api/v1/stats

# Consultar check previo
GET /api/v1/check/{check_id}

# Visualización de red
GET /api/v1/network/visualize/{person_id}?depth=2

# Health check
GET /api/health
```

## 📊 Dashboard Web

El dashboard incluye:

### 1. Vista General (Overview)
- Cards con métricas principales
- Gráfica de distribución de riesgo (pie chart)
- Top indicadores de riesgo
- Línea de tiempo de actividad

### 2. Nuevo Check
- Formulario intuitivo organizado por secciones
- Validación en tiempo real
- Opciones configurables (módulos a incluir)
- Campos de cumplimiento obligatorios

### 3. Resultados
- Score de riesgo prominente
- Alertas críticas destacadas
- Resultados organizados por módulo
- Visualización de flags e indicadores

## 🔒 Seguridad y Cumplimiento

### LFPDPPP (Ley Federal de Protección de Datos)

- ✅ Campo `consent_id` obligatorio en cada solicitud
- ✅ Registro de auditoría completo
- ✅ Trazabilidad de quién consultó qué y cuándo
- ✅ No se almacenan datos sensibles en logs

### ISO 27001

- ✅ Autenticación JWT (implementar antes de producción)
- ✅ Rate limiting por cliente
- ✅ Cifrado TLS en endpoints
- ✅ Separación de redes (BD en red privada)
- ✅ Rotación de API keys

### Mejores Prácticas

1. **Implementar autenticación** antes de producción
2. **Usar Azure Key Vault** o HashiCorp Vault para secrets
3. **Habilitar HTTPS** con certificados válidos
4. **Configurar alertas** para actividad inusual
5. **Realizar auditorías** periódicas de acceso

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=api --cov=modules --cov-report=html

# Tests específicos
pytest tests/test_curp_validator.py
pytest tests/test_rnd_scraper.py
```

## 📈 Monitoreo

### Logs

```bash
# Ver logs en tiempo real (Docker)
docker-compose logs -f kyc-api

# Ver logs locales
tail -f logs/kyc-platform.log
```

### Métricas

- Tiempo de procesamiento por check
- Tasa de éxito de cada módulo
- Distribución de niveles de riesgo
- Fuentes más utilizadas

## 🛠️ Desarrollo

### Estructura del Proyecto

```
kyc-platform/
├── api/
│   └── main.py              # FastAPI app principal
├── modules/
│   ├── rnd_scraper.py       # RND scraper
│   ├── curp_validator.py    # Validador CURP
│   ├── enrichment.py        # Enriquecimiento
│   ├── sanctions.py         # Listas negras
│   └── relationship.py      # Motor de relaciones
├── database/
│   ├── db_manager.py        # Gestor PostgreSQL
│   └── init.sql             # Schema inicial
├── frontend/
│   └── src/
│       └── components/
│           └── Dashboard.jsx
├── utils/
│   ├── scoring.py           # Cálculo de riesgo
│   └── reporting.py         # Generación de PDFs
├── config/
│   └── settings.py          # Configuración
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

### Agregar Nuevo Módulo

1. Crear archivo en `modules/nuevo_modulo.py`
2. Implementar clase con método async
3. Integrar en `api/main.py`
4. Actualizar cálculo de scoring en `utils/scoring.py`
5. Agregar tests

## 🚀 Despliegue en Producción

### Azure Container Apps

```bash
# 1. Crear Container Registry
az acr create --resource-group kyc-rg --name kycregistry --sku Basic

# 2. Build y push imagen
az acr build --registry kycregistry --image kyc-platform:latest .

# 3. Crear Container App
az containerapp create \
  --name kyc-platform \
  --resource-group kyc-rg \
  --image kycregistry.azurecr.io/kyc-platform:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars DATABASE_URL=... NEO4J_URI=...
```

### Railway

```bash
# Conectar repositorio GitHub
railway link

# Configurar variables de entorno en Railway Dashboard

# Desplegar
railway up
```

## 📞 Soporte

- **Email**: support@kycplatform.mx
- **Documentación**: [docs.kycplatform.mx](https://docs.kycplatform.mx)
- **Issues**: GitHub Issues

## 📄 Licencia

Propietario - Todos los derechos reservados

## 🙏 Agradecimientos

- SSPC por el Registro Nacional de Detenciones
- RENAPO por el catálogo de CURPs
- Comunidad de OpenSanctions
- Tesseract OCR Project

---

**⚠️ IMPORTANTE**: Esta plataforma debe usarse exclusivamente con el **consentimiento previo y documentado** del titular de los datos, conforme al Art. 8 de la LFPDPPP. El uso indebido puede resultar en sanciones legales.
