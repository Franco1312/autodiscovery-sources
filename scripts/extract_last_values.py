#!/usr/bin/env python3
"""Script para extraer el último valor de cada serie desde la API de datos.gob.ar"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

# Forzar salida sin buffer para ver logs en tiempo real
sys.stdout.reconfigure(line_buffering=True)

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from autodiscovery_sources.infrastructure.httpx_adapter import HttpxAdapter


def get_series_last_value(series_id: str, http: HttpxAdapter) -> Optional[Dict]:
    """Obtiene el último valor de una serie desde la API.
    
    Formato de respuesta esperado:
    {
        "data": [["fecha", valor], ...],
        "count": N,
        "meta": [
            {"frequency": "...", "start_date": "...", "end_date": "..."},
            {"field": {"description": "...", ...}, ...}
        ],
        "params": {...}
    }
    """
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
            print(f"  ✗ Formato de respuesta inesperado para {series_id}")
            return None
        
        series_data = data.get('data', [])
        meta = data.get('meta', [])
        
        if not series_data or not isinstance(series_data, list):
            print(f"  ⚠ Serie {series_id} sin datos", flush=True)
            return None
        
        # El último valor es el último elemento del array data
        last_data_point = series_data[-1]
        if not isinstance(last_data_point, list) or len(last_data_point) < 2:
            print(f"  ✗ Formato de datos inválido para {series_id}")
            return None
        
        last_date = last_data_point[0]
        last_value = last_data_point[1]
        
        # Extraer descripción de meta[1]['field']['description']
        description = None
        if len(meta) > 1 and isinstance(meta[1], dict):
            field = meta[1].get('field', {})
            if isinstance(field, dict):
                description = field.get('description', None)
        
        # Si no hay descripción en meta, usar el ID como fallback
        if not description:
            description = series_id
        
        return {
            'series_id': series_id,
            'description': description,
            'last_date': last_date,
            'last_value': last_value,
            'total_points': len(series_data),
        }
        
    except Exception as e:
        print(f"  ✗ Excepción consultando {series_id}: {e}", flush=True)
        return None


def get_multiple_series_last_values_batch(series_ids: List[str], http: HttpxAdapter, batch_size: int = 10) -> List[Dict]:
    """Obtiene los últimos valores de múltiples series, procesando en lotes.
    
    La API acepta múltiples IDs separados por coma, pero parece que solo
    devuelve datos de la primera serie. Por ahora procesamos en lotes
    para optimizar el tiempo.
    """
    results = []
    total = len(series_ids)
    
    print(f"Procesando {total} series en lotes de {batch_size}...")
    print()
    
    # Procesar en lotes
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch = series_ids[batch_start:batch_end]
        batch_num = (batch_start // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        print(f"[Lote {batch_num}/{total_batches}] Procesando {len(batch)} series (IDs {batch_start+1}-{batch_end}/{total})", flush=True)
        
        # Intentar procesar el lote completo primero
        ids_param = ",".join(batch)
        url = f"https://apis.datos.gob.ar/series/api/series/?ids={ids_param}"
        
        try:
            content, headers, error = http.get(url)
            if error or not content:
                print(f"  ✗ Error en lote: {error}", flush=True)
                # Fallback: procesar individualmente
                for series_id in batch:
                    result = get_series_last_value(series_id, http)
                    if result:
                        results.append(result)
                    time.sleep(0.1)
                continue
            
            data = json.loads(content.decode('utf-8'))
            
            # La API parece devolver solo la primera serie en data
            # pero podemos intentar extraer todas desde meta
            if isinstance(data, dict):
                series_data = data.get('data', [])
                meta = data.get('meta', [])
                params = data.get('params', {})
                identifiers = params.get('identifiers', [])
                
                # La API parece devolver solo la primera serie en data
                # Procesar todas individualmente desde el lote para asegurar que obtenemos todas
                # Pero primero intentar extraer la primera del lote completo
                if len(identifiers) > 0 and len(series_data) > 0:
                    # Procesar la primera desde la respuesta del lote
                    first_id = identifiers[0].get('id', batch[0])
                    last_point = series_data[-1]
                    if isinstance(last_point, list) and len(last_point) >= 2:
                        description = None
                        if len(meta) > 1 and isinstance(meta[1], dict):
                            field = meta[1].get('field', {})
                            if isinstance(field, dict):
                                description = field.get('description', first_id)
                        
                        results.append({
                            'series_id': first_id,
                            'description': description or first_id,
                            'last_date': last_point[0],
                            'last_value': last_point[1],
                            'total_points': len(series_data),
                        })
                    
                    # Procesar las demás del lote individualmente (más rápido)
                    for remaining_id_dict in identifiers[1:]:
                        remaining_id = remaining_id_dict.get('id')
                        if remaining_id:
                            result = get_series_last_value(remaining_id, http)
                            if result:
                                results.append(result)
                            time.sleep(0.05)  # Pausa más corta dentro del lote
                elif len(identifiers) == 1:
                    # Solo una serie, procesar normalmente
                    if series_data:
                        last_point = series_data[-1]
                        if isinstance(last_point, list) and len(last_point) >= 2:
                            description = None
                            if len(meta) > 1 and isinstance(meta[1], dict):
                                field = meta[1].get('field', {})
                                if isinstance(field, dict):
                                    description = field.get('description', batch[0])
                            
                            results.append({
                                'series_id': batch[0],
                                'description': description or batch[0],
                                'last_date': last_point[0],
                                'last_value': last_point[1],
                                'total_points': len(series_data),
                            })
        
        except Exception as e:
            print(f"  ✗ Excepción en lote: {e}", flush=True)
            # Fallback: procesar individualmente
            for series_id in batch:
                result = get_series_last_value(series_id, http)
                if result:
                    results.append(result)
                time.sleep(0.1)
        
        # Mostrar progreso
        print(f"  ✓ Procesadas {len(results)} series hasta ahora", flush=True)
        print()
        
        # Pequeña pausa entre lotes
        if batch_end < total:
            time.sleep(0.5)
    
    return results


def extract_last_values(input_file: str, output_file: str):
    """Extrae los últimos valores de todas las series del JSON."""
    http = HttpxAdapter()
    
    # Leer el JSON de entrada
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: Archivo no encontrado: {input_file}")
        return
    
    print(f"Leyendo archivo: {input_file}")
    with open(input_path, 'r', encoding='utf-8') as f:
        series_list = json.load(f)
    
    print(f"Total de series en el archivo: {len(series_list)}")
    print()
    
    # Extraer IDs de series
    series_ids = [series.get('id', '') for series in series_list if series.get('id')]
    
    print(f"Series IDs encontrados: {len(series_ids)}")
    print()
    
    # Obtener últimos valores
    print("Consultando API de datos.gob.ar...")
    print("=" * 80)
    print()
    
    # Procesar en lotes pequeños (10) para maximizar velocidad sin sobrecargar la API
    results = get_multiple_series_last_values_batch(series_ids, http, batch_size=10)
    
    print()
    print("=" * 80)
    print(f"Procesamiento completado: {len(results)} series procesadas exitosamente")
    print("=" * 80)
    print()
    
    # Guardar resultados
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Resultados guardados en: {output_file}")
    print()
    
    # Mostrar algunas estadísticas
    print("Primeras 10 series procesadas:")
    print("-" * 80)
    for i, result in enumerate(results[:10], 1):
        print(f"{i}. ID: {result['series_id']}")
        print(f"   Descripción: {result['description']}")
        print(f"   Última fecha: {result['last_date']}")
        print(f"   Último valor: {result['last_value']}")
        print()
    
    return results


if __name__ == "__main__":
    input_file = "series_recent_2025.json"
    output_file = "series_last_values.json"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    extract_last_values(input_file, output_file)

