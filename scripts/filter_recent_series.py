#!/usr/bin/env python3
"""Script para filtrar series con time_end o time_start en 2025 o posterior"""

import json
import sys
from pathlib import Path
from datetime import datetime


def filter_recent_series(input_file: str, output_file: str, min_year: int = 2025):
    """Filtra series cuyo time_end o time_start estén en min_year o posterior."""
    
    # Leer el JSON de entrada
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: Archivo no encontrado: {input_file}")
        return
    
    print(f"Leyendo archivo: {input_file}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total de series en el archivo: {len(data)}")
    print()
    
    # Filtrar series
    min_date = f"{min_year}-01-01"
    filtered_series = []
    
    for series in data:
        time_start = series.get('time_start', '')
        time_end = series.get('time_end', '')
        
        # Verificar si time_end o time_start están en 2025 o posterior
        if time_end and time_end >= min_date:
            filtered_series.append(series)
        elif time_start and time_start >= min_date:
            filtered_series.append(series)
    
    print(f"Series con time_end o time_start >= {min_year}: {len(filtered_series)}")
    print()
    
    # Guardar en archivo de salida
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_series, f, indent=2, ensure_ascii=False)
    
    print(f"Resultados guardados en: {output_file}")
    print()
    
    # Mostrar algunas estadísticas
    print("=" * 80)
    print("Estadísticas:")
    print("=" * 80)
    
    # Agrupar por año de time_end
    by_year = {}
    for series in filtered_series:
        time_end = series.get('time_end', '')
        if time_end:
            year = time_end.split('-')[0]
            by_year[year] = by_year.get(year, 0) + 1
    
    print("\nDistribución por año de time_end:")
    for year in sorted(by_year.keys(), reverse=True):
        print(f"  {year}: {by_year[year]} series")
    
    # Mostrar primeras 10 series
    print()
    print("Primeras 10 series filtradas:")
    print("-" * 80)
    for i, series in enumerate(filtered_series[:10], 1):
        print(f"{i}. ID: {series['id']}")
        print(f"   Descripción: {series['description']}")
        print(f"   Período: {series.get('time_start', 'N/A')} - {series.get('time_end', 'N/A')}")
        print()
    
    return filtered_series


if __name__ == "__main__":
    input_file = "series_ids_extracted.json"
    output_file = "series_recent_2025.json"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    if len(sys.argv) > 3:
        min_year = int(sys.argv[3])
    else:
        min_year = 2025
    
    filter_recent_series(input_file, output_file, min_year)

