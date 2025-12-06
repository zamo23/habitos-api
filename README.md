# API REST de Hábitos 🌟

Esta API REST es un componente del Sistema de Gestión de Hábitos, diseñada para proporcionar los endpoints necesarios para la gestión y seguimiento de hábitos diarios. Sirve como backend para aplicaciones cliente (web, móvil, etc.) proporcionando funcionalidades para la gestión de usuarios, hábitos, grupos ( en desarrollo), suscripciones y reportes ( en desarrollo ).

## 🔗 Integración con el Sistema
Esta API forma parte de un ecosistema más amplio y puede integrarse con:
- 🖥️ Aplicaciones web de gestión de hábitos
- 📱 Aplicaciones móviles
- 🤖 Otros servicios automatizados
- 📊 Sistemas de análisis de datos

## 🚀 Características Principales

- Gestión de usuarios con Clerk Authentication
- Control de hábitos personales
- Grupos colaborativos
- Sistema de suscripciones y pagos
- Reportes y estadísticas
- Gestión de zonas horarias
- Sistema de notificaciones

- 🤖 **Agente de Coaching con IA** - Asistente inteligente impulsado por Google Gemini (gemini-2.5-flash-lite) para proporcionar coaching personalizado y recomendaciones de hábitos

## 🛠 Tecnologías Utilizadas

- Python 3.13
- Flask (Framework web)
- MySQL (Base de datos)
- Clerk (Autenticación y gestión de usuarios)
- Dependency Injection (Container)
- Sistema de logging configurado

## ⚙️ Configuración del Entorno

### Variables de Entorno (.env)

Para ejecutar la aplicación, necesitas configurar las siguientes variables en tu archivo `.env`:

```env
# Environment Configuration
FLASK_ENV=development
DEBUG=True
PORT=5000
TIMEZONE_DEFAULT=UTC
CORS_ORIGINS=*

# Clerk Authentication
CLERK_SECRET_KEY=tu_clerk_secret_key
CLERK_JWKS_URL=https://tu-dominio.clerk.accounts.dev/.well-known/jwks.json
CLERK_API_BASE=https://api.clerk.dev/v1
CLERK_JWT_TEMPLATE_ID=tu_jwt_template_id

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=habitos
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña

# Mail Configuration
MAIL_SERVER=tu_servidor_smtp.com
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USE_TLS=False
MAIL_USERNAME=tu_correo@dominio.com
MAIL_PASSWORD=tu_contraseña_email
MAIL_DEFAULT_SENDER=tu_correo@dominio.com

API_GEMINI=TOKEN...API
GEMINI_MODEL=gemini-2.5-flash-lite
```

### Configuración de Clerk

La API utiliza [Clerk](https://clerk.dev/) para la gestión de usuarios y autenticación. Para configurar Clerk:

1. Crea una cuenta en Clerk
2. Configura una nueva aplicación
3. Obtén tus credenciales (SECRET_KEY y JWKS_URL)
4. Crea un JWT Template con los siguientes claims:
   ```json
   {
     "email": "{{user.primary_email_address}}",
     "nombre_completo": "{{user.full_name}}"
   }
   ```
5. Obtén el ID de tu JWT Template (CLERK_JWT_TEMPLATE_ID)
6. Actualiza el archivo `.env` con tus credenciales

## 🚀 Instalación y Ejecución

1. Clona el repositorio
```bash
git clone https://github.com/zamo23/habitos-api.git
cd habitos-api
```

2. Crea un entorno virtual
```bash
python -m venv env
```

3. Activa el entorno virtual
```bash
# Windows
env\\Scripts\\activate

# Linux/Mac
source env/bin/activate
```

4. Instala las dependencias
```bash
pip install -r requirements.txt
```

5. Configura la base de datos
```bash
# Ejecuta el script SQL en tu servidor MySQL
mysql -u tu_usuario -p tu_base_de_datos < database/estructura.sql
```

6. Ejecuta la aplicación
```bash
python app.py
```

## 🌐 Endpoints Principales

La API incluye los siguientes módulos principales:

- `/users` - Gestión de usuarios
- `/habits` - Gestión de hábitos
- `/groups` - Gestión de grupos
- `/plans` - Planes de suscripción
- `/subscriptions` - Gestión de suscripciones
- `/payments` - Procesamiento de pagos
- `/reports` - Generación de reportes
- `/system` - Configuraciones del sistema

## 🔐 Seguridad

- Autenticación mediante tokens JWT con Clerk
- CORS configurado para control de acceso
- Validación de roles y permisos

## 📝 Logs

La aplicación incluye un sistema de logging configurado que guarda los registros en:
- `logs/app.log`

## 🤝 Contribución

Si deseas contribuir al proyecto:

1. Haz un fork del repositorio
2. Crea una nueva rama para tu feature
3. Realiza tus cambios
4. Envía un pull request

## 📜 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE.md para más detalles. Esto significa que puedes usar, copiar, modificar y distribuir el proyecto libremente, siempre y cuando incluyas el aviso de licencia original.

## 🆘 Soporte

Para soporte y preguntas, por favor abre un issue en el repositorio o contacta al equipo de desarrollo.

---
⌨️ con ❤️ por Luis Zamora
