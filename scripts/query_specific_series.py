#!/usr/bin/env python3
"""Script para consultar series específicas y generar JSONs con los resultados"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from autodiscovery_sources.infrastructure.httpx_adapter import HttpxAdapter

# Forzar salida sin buffer
sys.stdout.reconfigure(line_buffering=True)


def query_series(series_id: str, http: HttpxAdapter) -> Optional[Dict]:
    """Consulta una serie específica desde la API."""
    url = f"https://apis.datos.gob.ar/series/api/series/?ids={series_id}"
    
    try:
        content, headers, error = http.get(url)
        if error or not content:
            print(f"  ✗ Error consultando {series_id}: {error}", flush=True)
            return None
        
        # Parse JSON
        try:
            data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            print(f"  ✗ Error parseando JSON para {series_id}: {e}", flush=True)
            return None
        
        # Verificar formato de respuesta
        if not isinstance(data, dict):
            print(f"  ✗ Formato de respuesta inesperado para {series_id}", flush=True)
            return None
        
        series_data = data.get('data', [])
        meta = data.get('meta', [])
        
        if not series_data or not isinstance(series_data, list):
            print(f"  ⚠ Serie {series_id} sin datos", flush=True)
            return None
        
        # Extraer descripción
        description = None
        if len(meta) > 1 and isinstance(meta[1], dict):
            field = meta[1].get('field', {})
            if isinstance(field, dict):
                description = field.get('description', None)
        
        # Extraer último valor
        last_data_point = series_data[-1]
        if not isinstance(last_data_point, list) or len(last_data_point) < 2:
            print(f"  ✗ Formato de datos inválido para {series_id}", flush=True)
            return None
        
        last_date = last_data_point[0]
        last_value = last_data_point[1]
        
        return {
            'series_id': series_id,
            'description': description or series_id,
            'data': series_data,  # Todos los datos de la serie
            'meta': meta,  # Metadata completa
            'last_date': last_date,
            'last_value': last_value,
            'total_points': len(series_data),
        }
        
    except Exception as e:
        print(f"  ✗ Excepción consultando {series_id}: {e}", flush=True)
        return None


def query_multiple_series(series_ids: List[str], http: HttpxAdapter) -> tuple[List[Dict], List[str]]:
    """Consulta múltiples series.
    
    Returns:
        Tuple de (series exitosas, series fallidas)
    """
    results = []
    failed = []
    total = len(series_ids)
    
    print(f"Consultando {total} series específicas...")
    print()
    
    for i, series_id in enumerate(series_ids, 1):
        print(f"[{i}/{total}] Consultando: {series_id}", flush=True)
        
        result = query_series(series_id, http)
        if result:
            results.append(result)
            print(f"  ✓ Último valor: {result['last_date']} = {result['last_value']}", flush=True)
        else:
            failed.append(series_id)
            print(f"  ✗ No se pudo obtener la serie", flush=True)
        
        # Pequeña pausa entre requests
        if i < total:
            time.sleep(0.3)
        
        print()
    
    return results, failed


def main():
    """Función principal."""
    # Series específicas a consultar (sin duplicados)
    # Nota: Algunos IDs fueron corregidos basándose en búsquedas en la API
    series_ids = [
        # 🏦 BLOQUE MONETARIO Y CAMBIARIO
        "168.1_T_CAMBI500_D_0_0_17",  # Tipo de cambio BCRA A3500 (corregido)
        "92.1_RID_0_0_32",  # Reservas internacionales BCRA (corregido)
        "300.1_AP_PAS_BASRIA_0_M_21",  # Base monetaria (corregido)
        "331.2_PASES_REDELIQ_D_MONE_0_24_19",  # LELIQs + Pases (corregido)
        "331.1_PASES_REDELIQ_M_MONE_0_24_24",  # Tasa LELIQ (corregido)
        "89.2_TS_INTELAR_0_D_20",  # BADLAR privados (corregido)
        
        # 📈 BLOQUE DE ACTIVIDAD ECONÓMICA
        # Nota: EMAE General requiere búsqueda específica
        "11.3_AGCS_2004_M_41",  # EMAE Comercio (base 2004)
        "12.3_E_2004_M_3",  # EMI (Industria Manufacturera)
        "13.2_ED_2012_T_12",  # EMI desestacionalizada
        # Nota: PIB trimestral requiere ID específico
        "183.1_BIENES_COBNES_0_M_27",  # Exportaciones de bienes (corregido)
        "166.2_I_BIENEERV_0_0_16",  # Importaciones de bienes (corregido)
        
        # 💰 BLOQUE DE PRECIOS E INGRESOS
        # Nota: IPC requiere IDs específicos del INDEC
        "447.1_TOTALTAL_0_0_5_37",  # Índice de salarios (corregido)
        # Nota: Canastas básicas requieren IDs específicos por región
        "25.1_OGP_2004_A_17",  # Índice de Precios Implícitos PIB
        "380.2_ICC_NACIONNAL_0_T_12",  # ICC (Confianza del Consumidor)
        
        # 🌎 BLOQUE DE SECTOR EXTERNO
        # Nota: Balanza comercial requiere ID específico
        "83.1_ITI_2004_A_27",  # Términos de intercambio (corregido)
        # Nota: Servicios no productivos requiere ID específico
        "167.2_E_BS_SCIOS_2004_0_13",  # Exportaciones de bienes y servicios
        "167.1_SO_EXT_IOS_2004_0_18",  # Saldo externo de bienes y servicios
        
        # 🏗️ BLOQUE DE CONSTRUCCIÓN E INDUSTRIA
        "32.2_ICP_2004_T_30",  # ISAC construcción (corregido)
        "309.1_PRODUCCIONNAL_0_M_30",  # Producción industrial manufacturera (corregido)
        "30.2_UPAB_2012_T_35",  # Capacidad instalada
        "29.3_UPT_2006_M_23",  # Utilización de capacidad instalada textil
        "11.2_VMATC_2004_T_12",  # EMAE Construcción
        
        # 💹 CONSUMO Y VENTAS
        "455.1_VENTAS_PRETES_0_M_25_98",  # Ventas en Supermercados
        "456.1_VENTAS_PRETES_0_M_25_91",  # Ventas en Mayoristas
        
        # 🌾 BLOQUE DE PRODUCCIÓN AGROPECUARIA
        "34.2_MTMAN_0_P_16",  # Producción agropecuaria (maní)
        "34.1_SGHSOR_0_P_25",  # Producción agropecuaria (sorgo)
        "40.3_PT_0_M_18",  # Faena porcina
        "40.3_AC_0_M_12",  # Faena aviar
        
        # 🏗️ BLOQUE DE INVERSIÓN Y EMPLEO
        "203.1_IBIF_0_0_4",  # IBIF total
        "205.1_IEQ_NACMAQ_0_0_14",  # IBI Nacional
        "204.1_IEQ_IMPMAQ_0_0_14",  # IBI Importado
        "324.1_F_CONSTRUCAJO__30",  # Puestos de trabajo construcción
        "324.1_M_ENSENIANZAJO__27",  # Puestos de trabajo enseñanza
        
        # ⚡ BLOQUE DE ENERGÍA Y PRODUCCIÓN INDUSTRIAL
        "307.1_GENERACIONICA_0_A_51",  # Generación eléctrica
        "305.2_ELEC_GAS_ATAL_0_19",  # Gas y agua
        "368.3_BIODISEL_PION__19",  # Producción de biodiésel
        "368.3_BIOETANOL_ION__35",  # Producción de bioetanol
        
        # 📊 BLOQUE DE INGRESO Y FINANZAS PÚBLICAS
        "166.2_INAC_BRADO_0_0_29",  # Ingreso Nacional Bruto
        "166.2_PT_ENDEETO_0_0_24",  # Préstamo o Endeudamiento Neto
        "28.1_AANBR_0_A_28",  # Ahorro nacional bruto real
    ]
    
    # Eliminar duplicados manteniendo el orden
    seen = set()
    unique_series_ids = []
    for series_id in series_ids:
        if series_id not in seen:
            seen.add(series_id)
            unique_series_ids.append(series_id)
    
    series_ids = unique_series_ids
    
    http = HttpxAdapter()
    
    print("=" * 80)
    print("Consultando series específicas del radar económico")
    print("=" * 80)
    print()
    
    # Consultar todas las series
    results, failed = query_multiple_series(series_ids, http)
    
    print()
    print("=" * 80)
    print(f"Consultas completadas: {len(results)}/{len(series_ids)} series exitosas")
    if failed:
        print(f"Series fallidas: {len(failed)}")
        print("  - " + "\n  - ".join(failed))
    print("=" * 80)
    print()
    
    # Archivo 1: JSON completo con todos los datos de cada serie
    output_file_full = Path(__file__).parent.parent / "series_data_full.json"
    with open(output_file_full, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Archivo completo guardado: {output_file_full}")
    print(f"  Total de series: {len(results)}")
    print()
    
    # Archivo 2: JSON simplificado con solo series_id, fecha y valor del último dato
    output_file_summary = Path(__file__).parent.parent / "series_last_summary.json"
    summary = []
    for result in results:
        summary.append({
            'series_id': result['series_id'],
            'description': result['description'],
            'last_date': result['last_date'],
            'last_value': result['last_value'],
        })
    
    with open(output_file_summary, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Resumen guardado: {output_file_summary}")
    print(f"  Total de series: {len(summary)}")
    print()
    
    # Mostrar resumen
    print("=" * 80)
    print("Resumen de series consultadas:")
    print("=" * 80)
    print()
    for item in summary:
        print(f"  {item['series_id']}: {item['last_date']} = {item['last_value']}")
        print(f"    {item['description'][:60]}...")
        print()
    
    return results, summary


if __name__ == "__main__":
    main()

