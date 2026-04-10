# 📁 KYC Platform - Índice de Archivos

## 📄 Documentación

```
├── README.md                    # Documentación completa del proyecto
├── QUICKSTART.md               # Guía de inicio rápido (5 minutos)
├── EXECUTIVE_SUMMARY.md        # Resumen ejecutivo para stakeholders
└── PROJECT_INDEX.md            # Este archivo
```

## 🚀 Backend (API)

```
api/
└── main.py                     # API principal FastAPI
                                # - Endpoints REST
                                # - Orquestador de módulos
                                # - Sistema de scoring
                                # - Gestión de checks
```

## 🧩 Módulos de Verificación

```
modules/
├── rnd_scraper.py             # Scraper RND (SSPC)
│                              # - Búsqueda de detenciones
│                              # - Resolución de captcha (OCR + 2captcha)
│                              # - BeautifulSoup + requests
│
├── curp_validator.py          # Validador de CURP
│                              # - Validación de formato
│                              # - Dígito verificador
│                              # - Verificación en BD
│                              # - Normalización de nombres
│
├── enrichment.py              # Enriquecimiento de datos
│                              # - Email (HIBP, Hunter.io)
│                              # - Teléfono (NumVerify)
│                              # - Detección de spam
│
├── sanctions.py               # Listas de sanciones
│                              # - OFAC SDN
│                              # - ONU Consolidated List
│                              # - OpenSanctions (PEPs)
│                              # - SAT Lista 69-B
│                              # - Fuzzy matching
│
└── relationship.py            # Motor de relaciones
                               # - Grafo de conocimiento
                               # - NetworkX / Neo4j
                               # - Detección de patrones
                               # - Exportación Cytoscape.js
```

## 💾 Base de Datos

```
database/
├── db_manager.py              # Gestor PostgreSQL
│                              # - Pool de conexiones asyncpg
│                              # - CRUD operations
│                              # - Estadísticas
│                              # - Auditoría
│
└── init.sql                   # Schema SQL completo
                               # - Tablas principales
                               # - Índices optimizados
                               # - Funciones útiles
                               # - Vistas de estadísticas
```

## 🎨 Frontend

```
frontend/
├── package.json               # Dependencias NPM
│                              # - React 18
│                              # - Recharts
│                              # - Tailwind CSS
│
└── src/
    └── components/
        └── Dashboard.jsx      # Dashboard principal
                               # - Visualizaciones
                               # - Formulario de checks
                               # - Resultados detallados
                               # - Gráficas interactivas
```

## 🛠️ Utilidades

```
utils/
├── scoring.py                 # Cálculo de riesgo
│                              # - Algoritmo ponderado
│                              # - Score global (0-100)
│                              # - Niveles de riesgo
│
└── reporting.py               # Generación de reportes
                               # - PDFs con ReportLab
                               # - Visualizaciones
                               # - Branding corporativo
```

## 🐳 Infraestructura

```
├── Dockerfile                 # Imagen Docker de la API
│                              # - Python 3.11-slim
│                              # - Tesseract OCR
│                              # - Dependencies
│
├── docker-compose.yml         # Orquestación completa
│                              # - API (FastAPI)
│                              # - PostgreSQL
│                              # - Neo4j
│                              # - Redis
│                              # - Frontend
│                              # - Nginx
│
├── requirements.txt           # Dependencias Python
│
└── .env.example              # Template de variables de entorno
```

## 📊 Estructura de Directorios Completa

```
kyc-platform/
│
├── 📄 Documentación
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── EXECUTIVE_SUMMARY.md
│   └── PROJECT_INDEX.md
│
├── 🚀 API Backend
│   └── api/
│       └── main.py
│
├── 🧩 Módulos de Verificación
│   └── modules/
│       ├── rnd_scraper.py
│       ├── curp_validator.py
│       ├── enrichment.py
│       ├── sanctions.py
│       └── relationship.py
│
├── 💾 Base de Datos
│   └── database/
│       ├── db_manager.py
│       └── init.sql
│
├── 🎨 Frontend
│   └── frontend/
│       ├── package.json
│       └── src/
│           └── components/
│               └── Dashboard.jsx
│
├── 🛠️ Utilidades
│   └── utils/
│       ├── scoring.py
│       └── reporting.py
│
├── ⚙️ Configuración
│   ├── .env.example
│   └── requirements.txt
│
└── 🐳 Docker
    ├── Dockerfile
    └── docker-compose.yml
```

## 📦 Instalación y Uso

### Instalación Rápida (Docker)

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd kyc-platform

# 2. Configurar variables
cp .env.example .env
# Editar .env con tus API keys

# 3. Levantar servicios
docker-compose up -d

# 4. Acceder
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/api/docs
# Neo4j: http://localhost:7474
```

### Instalación Local

```bash
# 1. Entorno virtual
python -m venv venv
source venv/bin/activate

# 2. Dependencias
pip install -r requirements.txt

# 3. Base de datos
createdb kyc_db
psql kyc_db < database/init.sql

# 4. Configurar .env
cp .env.example .env

# 5. Iniciar API
uvicorn api.main:app --reload

# 6. Iniciar Frontend
cd frontend
npm install
npm run dev
```

## 🔧 Customización

### Agregar Nuevo Módulo de Verificación

1. Crear archivo en `modules/nuevo_modulo.py`
2. Implementar clase con método `async def verify(...)`
3. Integrar en `api/main.py`:
   ```python
   from modules.nuevo_modulo import NuevoModulo
   nuevo = NuevoModulo()
   resultado = await nuevo.verify(...)
   ```
4. Agregar peso en `utils/scoring.py`
5. Actualizar documentación

### Modificar Scoring

Editar `utils/scoring.py`:

```python
# Cambiar ponderaciones
weights = {
    "email": 0.20,      # 20%
    "phone": 0.15,      # 15%
    "identity": 0.40,   # 40%
    "network": 0.25     # 25%
}
```

### Agregar Fuente de Datos

1. Obtener API key
2. Agregar a `.env`
3. Implementar en módulo correspondiente
4. Actualizar `sources_consulted` en respuesta

## 📚 Recursos Adicionales

### APIs Utilizadas
- [HaveIBeenPwned](https://haveibeenpwned.com/API/v3)
- [Hunter.io](https://hunter.io/api-documentation)
- [NumVerify](https://numverify.com/documentation)
- [OpenSanctions](https://www.opensanctions.org/docs/api/)
- [2captcha](https://2captcha.com/2captcha-api)

### Tecnologías
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Neo4j](https://neo4j.com/docs/)
- [Recharts](https://recharts.org/)

### Frameworks de Cumplimiento
- [LFPDPPP](http://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf)
- [ISO 27001](https://www.iso.org/isoiec-27001-information-security.html)
- [GDPR](https://gdpr.eu/)

## 🆘 Soporte

### Problemas Comunes

**Error: Puerto 8000 ocupado**
```bash
# Cambiar puerto en docker-compose.yml
ports: ["8080:8000"]
```

**Error: PostgreSQL no inicia**
```bash
docker-compose logs postgres
docker-compose restart postgres
```

**Error: Neo4j necesita más RAM**
```bash
# En .env:
USE_NEO4J=false
```

### Contacto

- **Documentación**: Ver README.md
- **Issues**: GitHub Issues
- **Email**: support@kycplatform.mx

## 📄 Licencia

Propietario - Todos los derechos reservados

---

**Versión**: 2.0.0  
**Última actualización**: Enero 2024  
**Total de archivos**: 17  
**Líneas de código**: ~5,000+
