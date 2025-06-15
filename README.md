# Procesador de Horas Laborales

Una aplicación web desarrollada con Streamlit para procesar horas laborales desde archivos Excel, calculando automáticamente sobretiempos, horas nocturnas y feriados según la legislación laboral peruana.

## Características

- **Carga de archivos Excel**: Procesa archivos con formato específico de horas laborales
- **Cálculos automáticos**:
  - Horas diurnas (06:00-22:00) y nocturnas (22:00-06:00)
  - Horas normales (hasta 8 horas) y extras
  - Sobretiempo con recargo del 25% y 35%
  - Tratamiento especial para domingos y feriados
  - Descuento automático de refrigerio (13:00-14:00)
- **Interfaz intuitiva**: Aplicación web fácil de usar
- **Exportación**: Descarga resultados en formato Excel

## Formato de archivo requerido

El archivo Excel debe contener una hoja llamada "Horas" con las siguientes columnas:

- `DIA`: Día de la semana (lunes, martes, miércoles, jueves, viernes, sábado, domingo)
- `Hora Inicio Labores`: Hora de inicio en formato HH:MM:SS
- `Hora Término Labores`: Hora de término en formato HH:MM:SS
- `Hora Inicio Refrigerio`: (Opcional) Hora de inicio del refrigerio
- `Hora Término Refrigerio`: (Opcional) Hora de término del refrigerio

## Instalación local

1. Clona este repositorio
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta la aplicación:
   ```bash
   streamlit run app.py
   ```

## Despliegue en Streamlit Cloud

1. Haz fork de este repositorio
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu repositorio de GitHub
4. Selecciona `app.py` como archivo principal
5. Haz clic en "Deploy"

## Estructura del proyecto

```
├── app.py                    # Aplicación principal de Streamlit
├── utils/
│   └── hour_calculator.py    # Lógica de cálculo de horas
├── .streamlit/
│   └── config.toml          # Configuración de Streamlit
├── requirements.txt         # Dependencias Python
└── README.md               # Este archivo
```

## Tecnologías utilizadas

- **Streamlit**: Framework web para aplicaciones de datos
- **Pandas**: Procesamiento de datos y archivos Excel
- **OpenPyXL**: Lectura y escritura de archivos Excel
- **Python DateTime**: Cálculos de tiempo y fechas