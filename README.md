# Reportería Técnica Clientes

Este proyecto es una aplicación web de reportería operativa que permite visualizar métricas, tiempos de atención y detalle de solicitudes técnicas procesadas desde un archivo CSV.

## 📊 Funcionalidades principales

- Resumen por técnico: cantidad de tickets y duración total
- Resumen por cliente: total de solicitudes y costo asociado
- Estado de solicitudes: agrupadas por estado actual
- Detalle por técnico y cliente
- Filtros dinámicos por cliente, técnico, estado y fecha
- Visualización en tiempo real con frontend HTML + JS

## 🛠️ Tecnologías utilizadas

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python + FastAPI
- **Base de datos**: Archivo CSV (no incluido en el repositorio)
- **Estilos**: Personalizados y responsivos

## 🚫 Consideraciones

> El archivo CSV utilizado contiene datos internos y ha sido excluido mediante `.gitignore`.

## 📂 Estructura del proyecto

```
backend/
│   ├── main.py
│   ├── utils.py
│   └── datos/ (excluido)
frontend/
│   ├── index.html
│   ├── main.js
│   └── estilos.css
README.md
.gitignore
```

## ✍️ Autor

Proyecto anonimizado para publicación pública en GitHub.
