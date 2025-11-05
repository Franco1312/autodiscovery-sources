#!/usr/bin/env python3
"""Script temporal para extraer IDs y descripciones de series de la API de datos.gob.ar"""

import json
import sys
import time
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from autodiscovery_sources.infrastructure.httpx_adapter import HttpxAdapter


def extract_series_ids(base_url: str, limit: int = 1000):
    """Extrae IDs y descripciones de todas las series de la API usando paginación."""
    http = HttpxAdapter()
    
    all_results = []
    start = 0
    total_count = None
    page = 1
    
    print(f"Consultando API con paginación (limit={limit})")
    print(f"URL base: {base_url}")
    print()
    print("=" * 80)
    print()
    
    while True:
        # Construir URL con paginación
        if '?' in base_url:
            url = f"{base_url}&limit={limit}&start={start}"
        else:
            url = f"{base_url}?limit={limit}&start={start}"
        
        print(f"[Página {page}] Consultando: start={start}, limit={limit}")
        print(f"  URL: {url}")
        
        # GET request
        content, headers, error = http.get(url)
        if error or not content:
            print(f"  ✗ Error: {error}")
            break
        
        # Parse JSON
        try:
            data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            print(f"  ✗ Error parseando JSON: {e}")
            break
        
        # Extraer datos
        series_data = data.get('data', [])
        count = data.get('count', 0)
        
        # Guardar total_count en la primera página
        if total_count is None:
            total_count = count
            print(f"  ✓ Total de series en la API: {count}")
        
        print(f"  ✓ Series en esta página: {len(series_data)}")
        
        # Si no hay más datos, salir
        if not series_data:
            print(f"  ✓ No hay más series. Fin de la paginación.")
            break
        
        # Procesar series de esta página
        page_results = []
        for item in series_data:
            field = item.get('field', {})
            dataset = item.get('dataset', {})
            
            series_id = field.get('id', '')
            description = field.get('description', '')
            title = field.get('title', '')
            frequency = field.get('frequency', '')
            units = field.get('units', '')
            time_start = field.get('time_index_start', '')
            time_end = field.get('time_index_end', '')
            
            dataset_title = dataset.get('title', '')
            source = dataset.get('source', '')
            
            result = {
                'id': series_id,
                'description': description,
                'title': title,
                'frequency': frequency,
                'units': units,
                'time_start': time_start,
                'time_end': time_end,
                'dataset_title': dataset_title,
                'source': source,
            }
            
            page_results.append(result)
            all_results.append(result)
        
        print(f"  ✓ Total acumulado: {len(all_results)} series")
        print()
        
        # Si ya obtuvimos todas las series, salir
        if len(all_results) >= total_count:
            print(f"  ✓ Todas las series obtenidas ({len(all_results)}/{total_count})")
            break
        
        # Si la página tiene menos series que el limit, es la última página
        if len(series_data) < limit:
            print(f"  ✓ Última página (menos de {limit} resultados)")
            break
        
        # Preparar para la siguiente página
        start += limit
        page += 1
        
        # Pequeña pausa entre requests
        time.sleep(0.5)
    
    print()
    print("=" * 80)
    print(f"Paginación completada")
    print(f"Total de series extraídas: {len(all_results)}")
    print("=" * 80)
    print()
    
    # Guardar en JSON
    output_file = Path(__file__).parent.parent / "series_ids_extracted.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"Resultados guardados en: {output_file}")
    print(f"Total de series extraídas: {len(all_results)}")
    
    return all_results


if __name__ == "__main__":
    base_url = "https://apis.datos.gob.ar/series/api/search/?dataset_theme=Actividad&sort_by=relevance&sort=desc"
    limit = 1000
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    if len(sys.argv) > 2:
        limit = int(sys.argv[2])
    
    extract_series_ids(base_url, limit)

