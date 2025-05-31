# FastAPI CI/CD Pipeline

Este documento describe el flujo de trabajo para la integración y entrega continua (CI/CD) de una API desarrollada con FastAPI. El pipeline se ejecuta automáticamente al realizar un push a la rama `main` y se encarga de validar, empaquetar y desplegar la aplicación en AWS Lambda.

## Descripción General

El pipeline se divide en dos grandes etapas:

1. **CI (Integración Continua):**
   - **Checkout del Código:** Se clona el repositorio para obtener la versión actualizada.
   - **Configuración del Entorno de Python:** Se instala Python 3.12 en el runner.
   - **Cache de Dependencias:** Se almacenan las dependencias de pip para acelerar ejecuciones futuras.
   - **Instalación de Dependencias:** Se crea un entorno virtual y se instalan las librerías necesarias según el archivo `requirements.txt`.
   - **Ejecución de Pruebas:** Se ejecutan los tests unitarios usando `pytest` para garantizar la integridad del código.
   - **Empaquetado de la API:** Se comprimen los archivos necesarios (incluyendo los paquetes instalados) en un archivo `api.zip`.
   - **Subida del Artefacto:** Se almacena el archivo comprimido en GitHub Actions para que esté disponible en el proceso de despliegue.

2. **CD (Entrega Continua):**
   - **Configuración de Credenciales AWS:** Se configuran las credenciales para interactuar con AWS.
   - **Descarga del Artefacto:** Se recupera el archivo `api.zip` generado en el proceso de CI.
   - **Verificación del Archivo:** Se comprueba que el archivo `api.zip` existe.
   - **Subida a S3:** Se sube el artefacto a un bucket en S3.
   - **Actualización de la Función Lambda:** Se actualiza el código de la función Lambda usando el archivo subido.
   - **Espera Activa:** Se realiza un bucle de espera hasta que el estado de la actualización de Lambda sea "Successful".
   - **Publicación de Nueva Versión:** Se publica una nueva versión de la función Lambda.

## Diagrama del Proceso

```mermaid
graph TD;
    A[Push a la rama main] -->|Acciona el Workflow| B[Checkout del repositorio];
    B --> C[Configura Python 3.12];
    C --> D[Cache de dependencias pip];
    D --> E[Instalación de dependencias];
    E --> F[Ejecución de pruebas con pytest];
    F --> G[Empaquetado de la API];
    G --> H[Subida del artefacto generado];
    H --> I[Configuración de credenciales AWS];
    I --> J[Descarga del artefacto];
    J --> K[Verificación del archivo zip];
    K --> L[Subida a S3];
    L --> M[Actualización de Lambda];
    M --> N[Espera de actualización];
    N --> O[Publicación de nueva versión de Lambda];
