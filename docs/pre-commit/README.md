# Guía: Cómo Documentar Cada Herramienta del Pre-commit

Esta sección de la documentación describe el **estándar de documentación** que se espera para cada herramienta que se agregue a nuestro proceso de _pre-commit_. El objetivo es concientizar a los desarrolladores sobre qué hace cada herramienta, por qué la usamos y cómo pueden ejecutarla o configurarla individualmente para asegurar calidad y consistencia en el código.

---

## ¿Por qué necesitamos un README para cada herramienta?

1. **Conciencia y entendimiento:** Al documentar cada herramienta, el equipo entiende claramente su propósito y sus beneficios.  
2. **Facilidad de uso:** Ayuda a cualquier desarrollador (nuevo o experimentado) a instalar y configurar la herramienta por su cuenta.  
3. **Mejores prácticas:** Garantiza que el equipo adopte flujos de trabajo coherentes y entienda cómo ignorar archivos o líneas de código en casos especiales.  
4. **Mantenibilidad:** Con el tiempo, la herramienta podría actualizarse o cambiar su configuración. Tener documentación clara y centralizada facilita este proceso.

---

## Estructura de la Documentación

Cada herramienta del pre-commit **debe** contar con un README que responda, al menos, las siguientes preguntas:

1. **¿Qué es esta herramienta?**  
   - Profundiza en su funcionalidad y menciona tecnologías o conceptos relacionados (por ejemplo, en caso de Mypy, explica qué son las anotaciones de tipo en Python, etc.).

2. **¿Qué problema resuelve y en qué nos beneficia?**  
   - Explica por qué se utiliza y cómo ayuda a mejorar la calidad o eficiencia del desarrollo.

3. **¿Por qué adjuntarla en el pre-commit?**  
   - Justifica por qué es importante que se ejecute automáticamente antes de cada commit (evitar errores en producción, prevenir mala calidad de código, etc.).

4. **¿Cómo usarla individualmente?**  
   - **4.1 Instalación**: pasos o comandos para instalar localmente.  
   - **4.2 Configuración**: ejemplo de archivo de configuración y opciones recomendadas (modos "strict", rutas a ignorar, etc.).  
   - Comando para correrla manualmente (ej.: `mypy .`, `flake8 .`, etc.).

5. **¿Cómo ignorar archivos o líneas específicas?**  
   - Explica la forma correcta de anotar exclusiones (en caso de Mypy, usar `# type: ignore`, o configurar `.mypyignore`, etc.). 
   - Menciona las convenciones de exclusión que se seguiran para esta herramienta. 
   - Menciona los riesgos de abusar de estas exclusiones.

6. **Configuración en Nuestro Proyecto**
   - **Configuración del Pre-commit Hook**: Muestra el fragmento de código en `.pre-commit-config.yaml` que configura esta herramienta.
   - **Configuración Específica**: Detalla los archivos de configuración específicos (por ejemplo, `mypy.ini`, `.flake8`, etc.) y explica las opciones seleccionadas para el proyecto.

7. **Recursos adicionales (opcional)**  
   - Documentación oficial, artículos recomendados, ejemplos de uso en proyectos reales, buenas prácticas, etc.

---

## Ejemplo de Template en Markdown

A continuación, un ejemplo de README que podrías adaptar a tu herramienta: [template](./template.md)

