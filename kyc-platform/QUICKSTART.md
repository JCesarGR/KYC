# 🚀 Guía de Inicio Rápido - KYC Platform

## ⚡ Levanta la plataforma en 5 minutos

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/kyc-platform.git
cd kyc-platform
```

### Paso 2: Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# MÍNIMO REQUERIDO para empezar:
# Edita .env y configura solo:
DATABASE_URL=postgresql://kyc_user:kyc_password@localhost:5432/kyc_db
```

> 💡 **Nota**: Las API keys son opcionales al inicio. La plataforma funcionará sin ellas, pero con funcionalidad limitada.

### Paso 3: Levantar con Docker

```bash
docker-compose up -d
```

Eso es todo! 🎉

### Paso 4: Verificar que Todo Funciona

```bash
# Ver status de servicios
docker-compose ps

# Debería mostrar:
# kyc-api       ✓ Running
# postgres      ✓ Running  
# neo4j         ✓ Running
# redis         ✓ Running
# frontend      ✓ Running
# nginx         ✓ Running
```

### Paso 5: Acceder a la Plataforma

Abre tu navegador en:

- 🌐 **Frontend**: http://localhost:3000
- 📚 **API Docs**: http://localhost:8000/api/docs
- 🔍 **Neo4j Browser**: http://localhost:7474 (user: neo4j, pass: kyc_neo4j_password)

## 🧪 Hacer tu Primer Background Check

### Opción A: Desde la Web UI

1. Ve a http://localhost:3000
2. Haz clic en "Nuevo Check"
3. Llena el formulario:
   ```
   Nombre Completo: Juan García López
   Nombre: Juan
   Apellido Paterno: García
   Apellido Materno: López
   CURP: GALJ850615HDFRPN01
   Email: test@example.com
   Teléfono: +525512345678
   ID de Consentimiento: TEST-001
   Solicitado por: admin
   ```
4. Clic en "Ejecutar Verificación"
5. ¡Listo! Verás los resultados

### Opción B: Desde la API

```bash
curl -X POST "http://localhost:8000/api/v1/background-check" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Juan García López",
    "first_name": "Juan",
    "paternal_surname": "García",
    "maternal_surname": "López",
    "birth_date": "15/06/1985",
    "curp": "GALJ850615HDFRPN01",
    "email": "test@example.com",
    "phone": "+525512345678",
    "consent_id": "TEST-001",
    "requested_by": "admin",
    "include_rnd_check": true,
    "include_sanctions": true,
    "include_enrichment": true,
    "include_network_analysis": true
  }'
```

## 📊 Ver Estadísticas

```bash
# Desde la terminal
curl http://localhost:8000/api/v1/stats | jq

# O en la web
# http://localhost:3000 → Tab "Dashboard"
```

## 🔧 Configuración Avanzada (Opcional)

### Agregar API Keys para Funcionalidad Completa

Edita `.env` y agrega tus keys:

```bash
# Enriquecimiento de Email
HIBP_API_KEY=tu_key_aqui        # https://haveibeenpwned.com/API/Key
HUNTER_API_KEY=tu_key_aqui      # https://hunter.io/api

# Validación de Teléfono
NUMVERIFY_API_KEY=tu_key_aqui   # https://numverify.com

# Listas de Sanciones
OPENSANCTIONS_API_KEY=tu_key_aqui  # https://opensanctions.org

# Resolución de Captcha (RND)
TWOCAPTCHA_API_KEY=tu_key_aqui  # https://2captcha.com (opcional)
```

Reinicia los servicios:

```bash
docker-compose restart kyc-api
```

### Usar Base de Datos Propia

Si ya tienes PostgreSQL instalado:

```bash
# 1. Crear base de datos
createdb kyc_db

# 2. Ejecutar migrations
psql kyc_db < database/init.sql

# 3. Actualizar .env
DATABASE_URL=postgresql://tu_user:tu_pass@localhost:5432/kyc_db

# 4. Reiniciar
docker-compose restart kyc-api
```

## 🐛 Troubleshooting

### Error: "Puerto 8000 ya en uso"

```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8080:8000"  # Cambia 8000 a 8080
```

### Error: "Cannot connect to database"

```bash
# Ver logs de PostgreSQL
docker-compose logs postgres

# Verificar que está corriendo
docker-compose ps postgres

# Reiniciar PostgreSQL
docker-compose restart postgres
```

### Error: "Neo4j no inicia"

```bash
# Neo4j necesita al menos 2GB de RAM disponible
# Si tu máquina tiene menos, deshabilita Neo4j:

# En .env:
USE_NEO4J=false

# Reinicia:
docker-compose restart kyc-api
```

### Ver Logs en Tiempo Real

```bash
# Todos los servicios
docker-compose logs -f

# Solo API
docker-compose logs -f kyc-api

# Solo Frontend
docker-compose logs -f frontend
```

## 🧹 Limpiar Todo

```bash
# Detener servicios
docker-compose down

# Detener y eliminar volúmenes (CUIDADO: borra datos)
docker-compose down -v

# Limpiar todo (imágenes, contenedores, volúmenes)
docker system prune -a --volumes
```

## 📚 Próximos Pasos

1. **Leer la documentación completa**: Ver `README.md`
2. **Explorar la API**: http://localhost:8000/api/docs
3. **Revisar ejemplos**: Ver carpeta `examples/`
4. **Configurar producción**: Ver `docs/deployment.md`

## 🆘 Necesitas Ayuda?

- 📖 Documentación: `README.md`
- 💬 Issues: GitHub Issues
- 📧 Email: support@kycplatform.mx

---

**¡Disfruta usando KYC Platform!** 🎉
