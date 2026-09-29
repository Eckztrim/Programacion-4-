"""
database.py
Capa de acceso a datos: todo lo que toca SQLite vive aquí.
El resto del programa (main.py) nunca escribe SQL directamente.
"""
import sqlite3

DB_NAME = "biblioteca.db"

# Campos por los que se puede buscar o actualizar. Se usa como "lista blanca":
# los nombres de columna NO se pueden parametrizar con "?", así que solo se
# insertan en el SQL si están en esta lista (evita inyección SQL).
CAMPOS_TEXTO = ("titulo", "autor", "genero")


def conectar(db_name=DB_NAME):
    """Abre la conexión y activa el acceso a columnas por nombre."""
    conexion = sqlite3.connect(db_name)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tabla(conexion):
    """Crea la tabla libros si todavía no existe."""
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS libros (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo  TEXT    NOT NULL,
            autor   TEXT    NOT NULL,
            genero  TEXT    NOT NULL,
            leido   INTEGER NOT NULL DEFAULT 0 CHECK (leido IN (0, 1))
        )
        """
    )
    conexion.commit()


def agregar_libro(conexion, titulo, autor, genero, leido):
    """Inserta un libro y devuelve el id generado."""
    cursor = conexion.execute(
        "INSERT INTO libros (titulo, autor, genero, leido) VALUES (?, ?, ?, ?)",
        (titulo, autor, genero, int(leido)),
    )
    conexion.commit()
    return cursor.lastrowid


def obtener_libro(conexion, libro_id):
    """Devuelve un libro por id, o None si no existe."""
    return conexion.execute(
        "SELECT * FROM libros WHERE id = ?", (libro_id,)
    ).fetchone()


def listar_libros(conexion):
    """Devuelve todos los libros ordenados por título."""
    return conexion.execute(
        "SELECT * FROM libros ORDER BY titulo COLLATE NOCASE"
    ).fetchall()


def actualizar_libro(conexion, libro_id, titulo, autor, genero, leido):
    """Actualiza todos los campos de un libro. Devuelve True si existía."""
    cursor = conexion.execute(
        "UPDATE libros SET titulo = ?, autor = ?, genero = ?, leido = ? WHERE id = ?",
        (titulo, autor, genero, int(leido), libro_id),
    )
    conexion.commit()
    return cursor.rowcount > 0


def eliminar_libro(conexion, libro_id):
    """Elimina un libro por id. Devuelve True si se eliminó algo."""
    cursor = conexion.execute("DELETE FROM libros WHERE id = ?", (libro_id,))
    conexion.commit()
    return cursor.rowcount > 0


def buscar_libros(conexion, campo, texto):
    """
    Busca libros cuyo `campo` contenga `texto` (sin distinguir mayúsculas).
    `campo` debe ser 'titulo', 'autor' o 'genero'.
    """
    if campo not in CAMPOS_TEXTO:
        raise ValueError(f"Campo de búsqueda no válido: {campo}")
    # El nombre de la columna sale de la lista blanca; el valor va parametrizado.
    sql = f"SELECT * FROM libros WHERE {campo} LIKE ? ORDER BY titulo COLLATE NOCASE"
    return conexion.execute(sql, (f"%{texto}%",)).fetchall()
