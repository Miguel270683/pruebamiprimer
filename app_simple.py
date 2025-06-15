import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta, time

# Función para convertir hora a string si es necesario
def convertir_a_str(hora):
    if isinstance(hora, time):
        return hora.strftime("%H:%M:%S")
    elif isinstance(hora, str):
        return hora
    return None

# Función de cálculo de horas
def calcular_horas(inicio_raw, fin_raw, refrigerio_inicio_raw=None, refrigerio_fin_raw=None):
    formato = "%H:%M:%S"
    inicio_str = convertir_a_str(inicio_raw)
    fin_str = convertir_a_str(fin_raw)
    refrigerio_inicio_str = convertir_a_str(refrigerio_inicio_raw)
    refrigerio_fin_str = convertir_a_str(refrigerio_fin_raw)

    if not inicio_str or not fin_str:
        return [0]*8

    try:
        inicio = datetime.strptime(inicio_str, formato)
        fin = datetime.strptime(fin_str, formato)
        if fin <= inicio:
            fin += timedelta(days=1)

        # Descontar refrigerio si es de 13:00 a 14:00
        descontar_refrigerio = False
        if refrigerio_inicio_str and refrigerio_fin_str:
            ri = datetime.strptime(refrigerio_inicio_str, formato).time()
            rf = datetime.strptime(refrigerio_fin_str, formato).time()
            if ri == time(13, 0) and rf == time(14, 0):
                descontar_refrigerio = True

        minutos_diurnos_total = 0
        minutos_nocturnos_total = 0

        actual = inicio
        while actual < fin:
            hora = actual.time()
            if time(6, 0) <= hora < time(22, 0):
                minutos_diurnos_total += 1
            else:
                minutos_nocturnos_total += 1
            actual += timedelta(minutes=1)

        total_minutos = minutos_diurnos_total + minutos_nocturnos_total

        # Descontar 1h de refrigerio si corresponde
        if descontar_refrigerio:
            if minutos_diurnos_total >= 60:
                minutos_diurnos_total -= 60
            else:
                restante = 60 - minutos_diurnos_total
                minutos_diurnos_total = 0
                minutos_nocturnos_total = max(0, minutos_nocturnos_total - restante)
            total_minutos -= 60

        # Normales y extras
        minutos_normales = min(total_minutos, 480)
        minutos_extras = max(0, total_minutos - 480)

        minutos_diurnos_normales = 0
        minutos_nocturnos_normales = 0
        actual = inicio
        minutos_asignados = 0
        while actual < fin and minutos_asignados < minutos_normales:
            hora = actual.time()
            if time(6, 0) <= hora < time(22, 0):
                minutos_diurnos_normales += 1
            else:
                minutos_nocturnos_normales += 1
            minutos_asignados += 1
            actual += timedelta(minutes=1)

        horas_diurnas = minutos_diurnos_normales / 60
        horas_nocturnas = minutos_nocturnos_normales / 60

        horas_extra_25 = min(minutos_extras, 120) / 60
        horas_extra_35 = max(minutos_extras - 120, 0) / 60

        horas_extra_25_nocturna = 0
        horas_extra_35_nocturna = 0

        if inicio.time() >= time(15, 0) and inicio.time() < time(20, 0):
            horas_extra_25_nocturna = horas_extra_25
            horas_extra_35_nocturna = round(horas_diurnas, 2) - horas_extra_25_nocturna 
            horas_extra_25 = 0
            horas_extra_35 = horas_extra_35 - horas_extra_35_nocturna

        if inicio.time() >= time(20, 0) and inicio.time() < time(22, 0):
            horas_extra_25_nocturna = round(horas_diurnas, 2)
            horas_extra_35_nocturna = 0
            horas_extra_25 = horas_extra_25 - horas_extra_25_nocturna
            horas_extra_35 = horas_extra_35

        total_horas = (minutos_diurnos_total + minutos_nocturnos_total) / 60

        return max(round(horas_diurnas, 2), 0), max(round(horas_nocturnas, 2), 0), \
               max(round(minutos_normales / 60, 2), 0), max(round(horas_extra_25, 2), 0), \
               max(round(horas_extra_35, 2), 0), max(round(horas_extra_25_nocturna, 2), 0), \
               max(round(horas_extra_35_nocturna, 2), 0), max(round(total_horas, 2), 0)

    except Exception as e:
        st.error(f"Error al procesar: {inicio_str} - {fin_str}. {e}")
        return [0]*8

# Función por fila
def procesar_fila(row):
    dia = str(row["DIA"]).strip().lower()
    dias_normales = ['lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes', 'sábado', 'sabado']

    resultado = calcular_horas(
        row["Hora Inicio Labores"], 
        row["Hora Término Labores"], 
        row.get("Hora Inicio Refrigerio", None),
        row.get("Hora Término Refrigerio", None)
    )

    if dia in dias_normales:
        return {
            "Horas Diurnas": resultado[0],
            "Horas Nocturnas": resultado[1],
            "Horas Normales": resultado[2],
            "Extra 25%": resultado[3],
            "Extra 35%": resultado[4],
            "Extra 25% Nocturna": resultado[5],
            "Extra 35% Nocturna": resultado[6],
            "Total Horas": resultado[7],
            "Horas Domingo/Feriado": 0,
            "Horas Extra Domingo/Feriado": 0
        }
    else:  # Domingo o feriado
        total_horas = resultado[7]
        horas_base = min(total_horas, 8)
        horas_extra = max(total_horas - 8, 0)
        return {
            "Horas Diurnas": 0,
            "Horas Nocturnas": 0,
            "Horas Normales": 0,
            "Extra 25%": 0,
            "Extra 35%": 0,
            "Extra 25% Nocturna": 0,
            "Extra 35% Nocturna": 0,
            "Total Horas": total_horas,
            "Horas Domingo/Feriado": round(horas_base, 2),
            "Horas Extra Domingo/Feriado": round(horas_extra, 2)
        }

def main():
    st.title("📊 Procesador de Horas Laborales")
    st.markdown("### Carga y procesa archivos Excel con datos de horas trabajadas")
    
    # Información sobre el formato esperado
    with st.expander("ℹ️ Formato de archivo esperado"):
        st.markdown("""
        **El archivo Excel debe contener una hoja llamada 'Horas' con las siguientes columnas:**
        - `DIA`: Día de la semana (lunes, martes, miércoles, jueves, viernes, sábado, domingo)
        - `Hora Inicio Labores`: Hora de inicio en formato HH:MM:SS
        - `Hora Término Labores`: Hora de término en formato HH:MM:SS
        - `Hora Inicio Refrigerio`: (Opcional) Hora de inicio del refrigerio
        - `Hora Término Refrigerio`: (Opcional) Hora de término del refrigerio
        
        **Cálculos realizados:**
        - Horas diurnas (06:00-22:00) y nocturnas (22:00-06:00)
        - Horas normales (hasta 8 horas) y extras
        - Sobretiempo con recargo del 25% y 35%
        - Tratamiento especial para domingos y feriados
        - Descuento automático de refrigerio (13:00-14:00)
        """)
    
    # Upload file
    uploaded_file = st.file_uploader(
        "📁 Selecciona el archivo Excel",
        type=['xlsx', 'xls'],
        help="Sube un archivo Excel con los datos de horas laborales"
    )
    
    if uploaded_file is not None:
        try:
            # Read the Excel file
            with st.spinner("📖 Leyendo archivo Excel..."):
                df = pd.read_excel(uploaded_file, sheet_name="Horas")
            
            st.success(f"✅ Archivo cargado exitosamente. {len(df)} filas encontradas.")
            
            # Display original data
            st.subheader("📋 Datos originales")
            st.dataframe(df, use_container_width=True)
            
            # Process data
            if st.button("🔄 Procesar datos", type="primary"):
                with st.spinner("⚙️ Procesando datos..."):
                    try:
                        # Apply processing to each row
                        resultados_dict = df.apply(procesar_fila, axis=1, result_type="expand")
                        
                        # Combine original data with results
                        df_final = pd.concat([df, resultados_dict], axis=1)
                        
                        st.success("✅ Datos procesados exitosamente!")
                        
                        # Display processed data
                        st.subheader("📊 Resultados calculados")
                        
                        # Show only the calculated columns for better readability
                        calculated_columns = [
                            "Horas Diurnas", "Horas Nocturnas", "Horas Normales",
                            "Extra 25%", "Extra 35%", "Extra 25% Nocturna", 
                            "Extra 35% Nocturna", "Total Horas",
                            "Horas Domingo/Feriado", "Horas Extra Domingo/Feriado"
                        ]
                        
                        # Display calculated results
                        st.dataframe(df_final[calculated_columns], use_container_width=True)
                        
                        # Summary statistics
                        st.subheader("📈 Resumen")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            total_horas_normales = df_final["Horas Normales"].sum()
                            st.metric("Total Horas Normales", f"{total_horas_normales:.2f}")
                        
                        with col2:
                            total_extra_25 = df_final["Extra 25%"].sum()
                            st.metric("Total Extra 25%", f"{total_extra_25:.2f}")
                        
                        with col3:
                            total_extra_35 = df_final["Extra 35%"].sum()
                            st.metric("Total Extra 35%", f"{total_extra_35:.2f}")
                        
                        with col4:
                            total_horas = df_final["Total Horas"].sum()
                            st.metric("Total Horas", f"{total_horas:.2f}")
                        
                        # Download processed file
                        st.subheader("💾 Descargar resultado")
                        
                        # Create Excel file in memory
                        output = io.BytesIO()
                        df_final.to_excel(output, sheet_name='Horas_Procesadas', index=False, engine='openpyxl')
                        excel_data = output.getvalue()
                        
                        st.download_button(
                            label="📥 Descargar archivo procesado",
                            data=excel_data,
                            file_name="reporte_horas_procesado.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            help="Descarga el archivo Excel con todos los cálculos realizados"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Error al procesar los datos: {str(e)}")
                        st.error("Verifica que el archivo tenga el formato correcto y las columnas requeridas.")
        
        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {str(e)}")
            st.error("Asegúrate de que el archivo tenga una hoja llamada 'Horas' con el formato correcto.")
    
    else:
        st.info("👆 Por favor, sube un archivo Excel para comenzar el procesamiento.")
    
    # Footer
    st.markdown("---")
    st.markdown("📍 **Nota**: Este procesador calcula automáticamente las horas laborales según la legislación laboral peruana, incluyendo recargos por sobretiempo y trabajo nocturno.")

if __name__ == "__main__":
    main()