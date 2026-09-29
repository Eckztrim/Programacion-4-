"""
database.py
Capa de acceso a datos del gremio de aventureros.
Aquí vive todo el SQL: creación de tablas, altas/bajas/cambios, relaciones
muchos-a-muchos y consultas de reporte. main.py nunca escribe SQL.
"""
import sqlite3

DB_NAME = "gremio.db"

# Listas cerradas que también se aplican en la base con CHECK.
CLASES = ("Guerrero", "Mago", "Arquero", "Clérigo", "Pícaro", "Paladín")
TIPOS = ("Dragón", "Goblin", "No-muerto", "Demonio", "Bestia", "Gigante")


def _lista_sql(valores):
    """Convierte ('a','b') en el texto "'a','b'" para usar dentro de un CHECK."""
    return ",".join(f"'{v}'" for v in valores)


def conectar(db_name=DB_NAME):
    """Abre la conexión. Las FK de SQLite vienen APAGADAS: hay que activarlas
    en cada conexión, o los FOREIGN KEY no se aplican."""
    con = sqlite3.connect(db_name)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def crear_tablas(con):
    """Crea las 5 tablas del modelo lógico si no existen."""
    con.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS heroes (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre            TEXT    NOT NULL,
            clase             TEXT    NOT NULL CHECK (clase IN ({_lista_sql(CLASES)})),
            nivel_experiencia INTEGER NOT NULL DEFAULT 1 CHECK (nivel_experiencia >= 1)
        );

        CREATE TABLE IF NOT EXISTS misiones (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre         TEXT    NOT NULL,
            descripcion    TEXT,
            dificultad     INTEGER NOT NULL CHECK (dificultad BETWEEN 1 AND 10),
            localizacion   TEXT    NOT NULL,
            recompensa_oro INTEGER NOT NULL DEFAULT 0 CHECK (recompensa_oro >= 0)
        );

        CREATE TABLE IF NOT EXISTS monstruos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre        TEXT    NOT NULL,
            tipo          TEXT    NOT NULL CHECK (tipo IN ({_lista_sql(TIPOS)})),
            nivel_amenaza INTEGER NOT NULL CHECK (nivel_amenaza BETWEEN 1 AND 10)
        );

        CREATE TABLE IF NOT EXISTS misiones_heroes (
            mision_id INTEGER NOT NULL,
            heroe_id  INTEGER NOT NULL,
            PRIMARY KEY (mision_id, heroe_id),
            FOREIGN KEY (mision_id) REFERENCES misiones(id) ON DELETE CASCADE,
            FOREIGN KEY (heroe_id)  REFERENCES heroes(id)   ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS misiones_monstruos (
            mision_id   INTEGER NOT NULL,
            monstruo_id INTEGER NOT NULL,
            cantidad    INTEGER NOT NULL DEFAULT 1 CHECK (cantidad >= 1),
            PRIMARY KEY (mision_id, monstruo_id),
            FOREIGN KEY (mision_id)   REFERENCES misiones(id)  ON DELETE CASCADE,
            FOREIGN KEY (monstruo_id) REFERENCES monstruos(id) ON DELETE RESTRICT
        );

        CREATE INDEX IF NOT EXISTS idx_mh_heroe    ON misiones_heroes(heroe_id);
        CREATE INDEX IF NOT EXISTS idx_mm_monstruo ON misiones_monstruos(monstruo_id);
        """
    )
    con.commit()


# ---------------------------------------------------------------- HÉROES

def agregar_heroe(con, nombre, clase, nivel):
    cur = con.execute(
        "INSERT INTO heroes (nombre, clase, nivel_experiencia) VALUES (?, ?, ?)",
        (nombre, clase, nivel),
    )
    con.commit()
    return cur.lastrowid


def listar_heroes(con):
    return con.execute("SELECT * FROM heroes ORDER BY nombre COLLATE NOCASE").fetchall()


def obtener_heroe(con, heroe_id):
    return con.execute("SELECT * FROM heroes WHERE id = ?", (heroe_id,)).fetchone()


def actualizar_heroe(con, heroe_id, nombre, clase, nivel):
    cur = con.execute(
        "UPDATE heroes SET nombre = ?, clase = ?, nivel_experiencia = ? WHERE id = ?",
        (nombre, clase, nivel, heroe_id),
    )
    con.commit()
    return cur.rowcount > 0


def eliminar_heroe(con, heroe_id):
    """Sus participaciones se borran solas (ON DELETE CASCADE)."""
    cur = con.execute("DELETE FROM heroes WHERE id = ?", (heroe_id,))
    con.commit()
    return cur.rowcount > 0


# -------------------------------------------------------------- MISIONES

def agregar_mision(con, nombre, descripcion, dificultad, localizacion, oro):
    cur = con.execute(
        "INSERT INTO misiones (nombre, descripcion, dificultad, localizacion, recompensa_oro) "
        "VALUES (?, ?, ?, ?, ?)",
        (nombre, descripcion, dificultad, localizacion, oro),
    )
    con.commit()
    return cur.lastrowid


def listar_misiones(con):
    return con.execute("SELECT * FROM misiones ORDER BY id").fetchall()


def obtener_mision(con, mision_id):
    return con.execute("SELECT * FROM misiones WHERE id = ?", (mision_id,)).fetchone()


def actualizar_mision(con, mision_id, nombre, descripcion, dificultad, localizacion, oro):
    cur = con.execute(
        "UPDATE misiones SET nombre = ?, descripcion = ?, dificultad = ?, "
        "localizacion = ?, recompensa_oro = ? WHERE id = ?",
        (nombre, descripcion, dificultad, localizacion, oro, mision_id),
    )
    con.commit()
    return cur.rowcount > 0


def eliminar_mision(con, mision_id):
    """Se borran también sus héroes y monstruos asociados (CASCADE)."""
    cur = con.execute("DELETE FROM misiones WHERE id = ?", (mision_id,))
    con.commit()
    return cur.rowcount > 0


# ------------------------------------------------------------- MONSTRUOS

def agregar_monstruo(con, nombre, tipo, amenaza):
    cur = con.execute(
        "INSERT INTO monstruos (nombre, tipo, nivel_amenaza) VALUES (?, ?, ?)",
        (nombre, tipo, amenaza),
    )
    con.commit()
    return cur.lastrowid


def listar_monstruos(con):
    return con.execute("SELECT * FROM monstruos ORDER BY nombre COLLATE NOCASE").fetchall()


def obtener_monstruo(con, monstruo_id):
    return con.execute("SELECT * FROM monstruos WHERE id = ?", (monstruo_id,)).fetchone()


def actualizar_monstruo(con, monstruo_id, nombre, tipo, amenaza):
    cur = con.execute(
        "UPDATE monstruos SET nombre = ?, tipo = ?, nivel_amenaza = ? WHERE id = ?",
        (nombre, tipo, amenaza, monstruo_id),
    )
    con.commit()
    return cur.rowcount > 0


def eliminar_monstruo(con, monstruo_id):
    """Lanza sqlite3.IntegrityError si el monstruo aparece en alguna misión
    (ON DELETE RESTRICT), para no perder el historial."""
    cur = con.execute("DELETE FROM monstruos WHERE id = ?", (monstruo_id,))
    con.commit()
    return cur.rowcount > 0


# ------------------------------------------------- RELACIONES (tablas puente)

def asignar_heroe(con, mision_id, heroe_id):
    """Registra que un héroe participó en una misión.
    Lanza IntegrityError si ya estaba registrado o si algún id no existe."""
    con.execute(
        "INSERT INTO misiones_heroes (mision_id, heroe_id) VALUES (?, ?)",
        (mision_id, heroe_id),
    )
    con.commit()


def quitar_heroe(con, mision_id, heroe_id):
    cur = con.execute(
        "DELETE FROM misiones_heroes WHERE mision_id = ? AND heroe_id = ?",
        (mision_id, heroe_id),
    )
    con.commit()
    return cur.rowcount > 0


def asignar_monstruo(con, mision_id, monstruo_id, cantidad):
    """Registra un monstruo enfrentado en una misión, con su cantidad."""
    con.execute(
        "INSERT INTO misiones_monstruos (mision_id, monstruo_id, cantidad) VALUES (?, ?, ?)",
        (mision_id, monstruo_id, cantidad),
    )
    con.commit()


def quitar_monstruo(con, mision_id, monstruo_id):
    cur = con.execute(
        "DELETE FROM misiones_monstruos WHERE mision_id = ? AND monstruo_id = ?",
        (mision_id, monstruo_id),
    )
    con.commit()
    return cur.rowcount > 0


# -------------------------------------------------------------- REPORTES

def heroes_de_mision(con, mision_id):
    return con.execute(
        """SELECT h.id, h.nombre, h.clase, h.nivel_experiencia
           FROM heroes h JOIN misiones_heroes mh ON mh.heroe_id = h.id
           WHERE mh.mision_id = ? ORDER BY h.nombre""",
        (mision_id,),
    ).fetchall()


def monstruos_de_mision(con, mision_id):
    return con.execute(
        """SELECT mo.id, mo.nombre, mo.tipo, mo.nivel_amenaza, mm.cantidad
           FROM monstruos mo JOIN misiones_monstruos mm ON mm.monstruo_id = mo.id
           WHERE mm.mision_id = ? ORDER BY mo.nombre""",
        (mision_id,),
    ).fetchall()


def misiones_de_heroe(con, heroe_id):
    return con.execute(
        """SELECT m.id, m.nombre, m.localizacion, m.dificultad, m.recompensa_oro
           FROM misiones m JOIN misiones_heroes mh ON mh.mision_id = m.id
           WHERE mh.heroe_id = ? ORDER BY m.nombre""",
        (heroe_id,),
    ).fetchall()


def reporte_completo(con):
    """Héroe - misión - monstruo - cantidad (JOIN de las 5 tablas)."""
    return con.execute(
        """SELECT h.nombre AS heroe, m.nombre AS mision,
                  mo.nombre AS monstruo, mm.cantidad
           FROM heroes h
           JOIN misiones_heroes    mh ON mh.heroe_id  = h.id
           JOIN misiones           m  ON m.id         = mh.mision_id
           JOIN misiones_monstruos mm ON mm.mision_id = m.id
           JOIN monstruos          mo ON mo.id        = mm.monstruo_id
           ORDER BY h.nombre, m.nombre, mo.nombre"""
    ).fetchall()


def oro_por_heroe(con):
    """Cada héroe con nº de misiones y oro acumulado (LEFT JOIN + GROUP BY,
    para que aparezcan también los héroes sin misiones)."""
    return con.execute(
        """SELECT h.nombre, h.clase,
                  COUNT(m.id) AS misiones,
                  COALESCE(SUM(m.recompensa_oro), 0) AS oro_total
           FROM heroes h
           LEFT JOIN misiones_heroes mh ON mh.heroe_id = h.id
           LEFT JOIN misiones m         ON m.id = mh.mision_id
           GROUP BY h.id
           ORDER BY oro_total DESC, h.nombre"""
    ).fetchall()


def heroes_sin_misiones(con):
    return con.execute(
        """SELECT h.id, h.nombre, h.clase, h.nivel_experiencia
           FROM heroes h
           LEFT JOIN misiones_heroes mh ON mh.heroe_id = h.id
           WHERE mh.heroe_id IS NULL ORDER BY h.nombre"""
    ).fetchall()


# ---------------------------------------------------------- DATOS DE PRUEBA

def cargar_datos_ejemplo(con):
    """Inserta un conjunto pequeño de datos para probar los reportes."""
    heroes = [("Aragorn", "Guerrero", 12), ("Gandalf", "Mago", 20),
              ("Legolas", "Arquero", 11), ("Lía", "Clérigo", 5)]
    misiones = [
        ("Nido del Dragón", "Recuperar el tesoro robado", 9, "Montañas Rojas", 5000),
        ("Limpieza de la Cripta", "Purgar la cripta antigua", 5, "Valle Sombrío", 1200),
        ("Campamento Goblin", "Detener las emboscadas", 3, "Bosque Espeso", 400),
    ]
    monstruos = [("Smaug", "Dragón", 10), ("Esqueleto Guerrero", "No-muerto", 4),
                 ("Goblin Explorador", "Goblin", 2), ("Troll de Roca", "Gigante", 6)]
    for h in heroes:
        agregar_heroe(con, *h)
    for m in misiones:
        agregar_mision(con, *m)
    for mo in monstruos:
        agregar_monstruo(con, *mo)
    # (mision, héroe) y (mision, monstruo, cantidad); los ids son 1..n por AUTOINCREMENT
    for mision, heroe in [(1, 1), (1, 2), (1, 3), (2, 2), (2, 4), (3, 1), (3, 3)]:
        asignar_heroe(con, mision, heroe)
    for mision, monstruo, cant in [(1, 1, 1), (1, 4, 2), (2, 2, 8), (3, 3, 12)]:
        asignar_monstruo(con, mision, monstruo, cant)
