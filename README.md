# 🍴 Backend ChileBite

Este es el **backend** de ChileBite, encargado de la API, manejo de base de datos, autenticación, usuarios, recetas, locales de comida y comentarios.  
Está construido con **Django 5.x** + **Django REST Framework**, y puede levantarse localmente o mediante **Docker**.

---

## 📦 Tecnologías principales

* **Python 3.12+** – Lenguaje principal del backend.  
* **Django 5.x** – Framework web y ORM.  
* **Django REST Framework (DRF)** – Creación de endpoints RESTful.  
* **PostgreSQL** – Base de datos relacional.  
* **Docker & Docker Compose** – Contenedores para desarrollo y despliegue.  
* **pip** – Gestión de dependencias y paquetes.

---

## ⚙️ Requisitos previos

Antes de levantar el backend necesitas:

1.  **Python 3.12+** y **pip**  
    ```bash
    python --version
    pip --version
    ```
2.  **PostgreSQL** si no usarás Docker.  
3.  **Docker y Docker Compose** si usarás contenedores.  
4.  **Frontend corriendo (opcional)** si quieres probar la integración completa.

---

## 📂 Archivos clave

| Archivo / Carpeta      | Descripción |
| :---                   | :--- |
| `manage.py`            | Script principal para comandos Django (runserver, migrate, etc.). |
| `backend/settings.py`  | Configuración principal: DB, middlewares, apps instaladas. |
| `apps/`                | Carpeta que contiene las apps Django (usuarios, recetas, locales, etc.). |
| `apps/<app>/models.py` | Modelos de datos de cada app. |
| `apps/<app>/serializers.py` | Serializadores para DRF. |
| `apps/<app>/views.py`  | Lógica de endpoints y vistas. |
| `apps/<app>/urls.py`   | Rutas de cada app. |
| `apps/<app>/fixtures/` | Datos iniciales de prueba (opcional). |
| `.env`                 | Variables de entorno (DB, puertos, etc.). |

> [!TIP]
> **Nota:** Modifica `.env` si cambias el puerto o la URL de la base de datos. Ejemplo:
> ```env
> DB_NAME=chilebite
> DB_USER=usuario
> DB_PASSWORD=contraseña
> DB_HOST=localhost
> DB_PORT=5432
> ```

---

## 💻 Instalación local (sin Docker)

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/tu_usuario/ChileBiteBack.git
    cd ChileBiteBack
    ```
2.  **Crear y activar entorno virtual:**
    ```bash
    python -m venv venv

    # Linux/Mac
    source venv/bin/activate

    # Windows
    venv\Scripts\activate
    ```
3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Aplicar migraciones:**
    ```bash
    python manage.py migrate
    ```
5.  **Levantar servidor de desarrollo:**
    ```bash
    python manage.py runserver 8000
    ```
6.  **Abrir en navegador:**  
    Acceso a la API: [http://localhost:8000/api](http://localhost:8000/api)

---

## 🐳 Uso con Docker

Si prefieres usar contenedores para evitar conflictos y automatizar la base de datos:

1.  **Construir y levantar contenedores:**
    ```bash
    docker-compose up --build
    ```
    *Esto levantará backend, base de datos y frontend (si está configurado).*

2.  **Acceso:**  
    [http://localhost:8000/api](http://localhost:8000/api)

### Comandos útiles de Docker

| Acción                   | Comando |
| :---                     | :--- |
| Ejecutar migraciones     | `docker-compose exec backend python manage.py migrate` |
| Crear superusuario       | `docker-compose exec backend python manage.py createsuperuser` |
| Reiniciar backend        | `docker-compose restart backend` |
| Ver logs en tiempo real  | `docker-compose logs -f backend` |

---

## ⚡ Scripts importantes (manage.py)

| Comando                  | Función |
| :---                     | :--- |
| `runserver`              | Levanta el servidor de desarrollo. |
| `migrate`                | Aplica cambios en la base de datos. |
| `createsuperuser`        | Crear usuario admin para `/admin`. |
| `loaddata <fixture>`     | Cargar datos iniciales de prueba. |

---

## 🔧 Guía de Modificación y Contribución

**Dónde hacer cambios:**

* Apps Django (`apps/`) → Contienen `models.py`, `serializers.py`, `views.py`, `urls.py`.  
* Configuración (`backend/settings.py`) → Gestión de base de datos, middlewares y apps instaladas.  
* Datos iniciales → `apps/<app>/fixtures/`.

### Flujo de contribución

```bash
# Crear rama para tu feature
git checkout -b feature/nombre-de-tu-mejora

# Hacer cambios y commit
git commit -m "Descripción clara del cambio"

# Subir cambios al repositorio
git push origin feature/nombre-de-tu-mejora
```
## 🌐 Recursos útiles

* [Documentación oficial de Django](https://docs.djangoproject.com/)
* [Django REST Framework](https://www.django-rest-framework.org/)
* [PostgreSQL Tutorial](https://www.postgresql.org/docs/)
* [Docker Documentation](https://docs.docker.com/)

---

## 🚀 Próximos pasos / Roadmap

* Integrar autenticación JWT para usuarios.
* Mejorar permisos y seguridad en endpoints.
* Crear fixtures con datos iniciales de prueba.
* Añadir tests unitarios y de integración.

---

## 🏷️ Badges 

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.x-green)
![Docker](https://img.shields.io/badge/Docker-enabled-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 📌 Tips visuales y notas importantes

* Siempre ejecuta comandos Django desde la raíz del backend (`ChileBiteBack/`).
* Si cambias el puerto en `.env`, recuerda actualizar también los endpoints del frontend.
* Para problemas de Docker con Postgres, revisa que el contenedor `db` esté activo antes de correr migraciones.
* Usa `docker-compose logs -f backend` para depurar errores en tiempo real.

---

**© 2026 ChileBite Team. Todos los derechos reservados.**

