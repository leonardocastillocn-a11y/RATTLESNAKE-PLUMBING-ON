import sqlite3
import pandas as pd
import os

DB_PATH = "database/erp_local.db"

def init_db():
    """Inicializa la base de datos SQLite local."""
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Tabla de Proyectos / Obras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            presupuesto_total REAL DEFAULT 0,
            estado TEXT DEFAULT 'activo',
            fecha_inicio DATE DEFAULT CURRENT_DATE
        )
    ''')

    # 2. Tabla de Requisiciones de Campo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requisiciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER,
            insumo TEXT NOT NULL,
            cantidad REAL NOT NULL,
            unidad TEXT NOT NULL,
            observaciones TEXT,
            estatus TEXT DEFAULT 'pendiente',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
        )
    ''')

    conn.commit()
    conn.close()

def obtener_proyectos():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM proyectos ORDER BY id DESC", conn)
    conn.close()
    return df

def guardar_proyecto(codigo, nombre, presupuesto):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO proyectos (codigo, nombre, presupuesto_total) VALUES (?, ?, ?)",
        (codigo, nombre, presupuesto)
    )
    conn.commit()
    conn.close()

def guardar_requisicion(proyecto_id, insumo, cantidad, unidad, observaciones):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO requisiciones (proyecto_id, insumo, cantidad, unidad, observaciones) VALUES (?, ?, ?, ?, ?)",
        (proyecto_id, insumo, cantidad, unidad, observaciones)
    )
    conn.commit()
    conn.close()
