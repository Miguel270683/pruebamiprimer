import pandas as pd
from datetime import datetime, timedelta, time

def convertir_a_str(hora):
    """Función para convertir hora a string si es necesario"""
    if isinstance(hora, time):
        return hora.strftime("%H:%M:%S")
    elif isinstance(hora, str):
        return hora
    return None

def calcular_horas(inicio_raw, fin_raw, refrigerio_inicio_raw=None, refrigerio_fin_raw=None):
    """Función principal de cálculo de horas laborales"""
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
        print(f"❌ Error al procesar: {inicio_str} - {fin_str}. {e}")
        return [0]*8

def procesar_fila(row):
    """Función para procesar cada fila del DataFrame"""
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