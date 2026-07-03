"""
SIA-T: Pipeline de Carga y Sincronización de Calificaciones, Asistencia y Pensiones
Este script simula o ejecuta la inserción y actualización masiva de los registros
de la institución escolar hacia la base de datos de réplica analítica.
"""

import sys
import os
from datetime import datetime

# Añadir el directorio raíz del backend al path de Python para permitir imports relativos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.database import SessionLocal, engine

def cargar_datos_academicos(datos_estudiantes: list):
    """
    Sincroniza notas, asistencia y estado de pensiones de estudiantes para un periodo específico.
    Calcula automáticamente 'nota_final' antes de la inserción o actualización.
    """
    db = SessionLocal()
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando carga ETL de registros académicos...")
        
        cargados_notas = 0
        cargados_asistencia = 0
        cargados_pensiones = 0
        
        for data in datos_estudiantes:
            est_id = data["estudiante_id"]
            per_id = data["periodo_id"]
            
            # 1. Procesar y calcular Notas
            n_libro = data["nota_libro"]
            n_cuaderno = data["nota_cuaderno"]
            n_examen = data["nota_examen"]
            conducta_val = data["conducta"]
            
            # Regla de Negocio: nota_final es el promedio simple de las 3 notas académicas principales
            nota_final_val = round((n_libro + n_cuaderno + n_examen) / 3, 2)
            
            # En un entorno real con SQL y SQLAlchemy u ORM, se ejecutaría un query UPSERT:
            # db.execute(insert(notas).values(...).on_conflict_do_update(...))
            # Para fines demostrativos del pipeline ETL, se imprime la lógica consolidada:
            cargados_notas += 1
            
            # 2. Procesar Asistencia
            inasist_val = data["inasistencias"]
            cargados_asistencia += 1
            
            # 3. Procesar Pensiones
            estado_p_val = data["estado_pension"]
            cargados_pensiones += 1
            
            print(f" -> Sincronizado Estudiante ID: {est_id} | Nota Final: {nota_final_val} | Inasistencias: {inasist_val} | Pensión: {estado_p_val}")
            
        db.commit()
        print("\n=== PIPELINE DE CARGA COMPLETADO CON ÉXITO ===")
        print(f"Total Notas cargadas/actualizadas: {cargados_notas}")
        print(f"Total Registros de asistencia cargados: {cargados_asistencia}")
        print(f"Total Estados de pensión sincronizados: {cargados_pensiones}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"=== ERROR CRÍTICO EN PIPELINE ETL DE CARGA ===")
        print(f"Detalle: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Datos de ejemplo para simular la ejecución del pipeline de carga
    datos_ejemplo = [
        {
            "estudiante_id": 1,
            "periodo_id": 1,
            "nota_libro": 11.0,
            "nota_cuaderno": 12.5,
            "nota_examen": 10.0,
            "conducta": 14.0,
            "inasistencias": 3,
            "estado_pension": "al_dia"
        },
        {
            "estudiante_id": 2,
            "periodo_id": 1,
            "nota_libro": 9.5,
            "nota_cuaderno": 10.0,
            "nota_examen": 8.0,
            "conducta": 11.0,
            "inasistencias": 5,
            "estado_pension": "deuda"
        },
        {
            "estudiante_id": 3,
            "periodo_id": 1,
            "nota_libro": 15.0,
            "nota_cuaderno": 16.0,
            "nota_examen": 14.5,
            "conducta": 18.0,
            "inasistencias": 0,
            "estado_pension": "al_dia"
        }
    ]
    
    cargar_datos_academicos(datos_ejemplo)
