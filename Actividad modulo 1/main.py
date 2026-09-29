"""
main.py
Interfaz de consola del gremio de aventureros.
Muestra menús, valida lo que escribe el usuario y delega en database.py.
"""
import sqlite3
import database as db


# ---------------------------------------------------- Entrada de datos

def pedir_texto(mensaje, obligatorio=True, actual=None):
    """Pide un texto. Con `actual` (modo edición), Enter conserva el valor."""
    while True:
        sufijo = f" [{actual}]" if actual is not None else ""
        valor = input(f"{mensaje}{sufijo}: ").strip()
        if valor:
            return valor
        if actual is not None:
            return actual
        if not obligatorio:
            return ""
        print("  Este campo no puede estar vacío.")


def pedir_entero(mensaje, minimo, maximo=None, actual=None):
    """Pide un entero dentro de [minimo, maximo]. Enter conserva `actual`."""
    rango = f"{minimo}-{maximo}" if maximo is not None else f">= {minimo}"
    while True:
        sufijo = f" [{actual}]" if actual is not None else ""
        valor = input(f"{mensaje} ({rango}){sufijo}: ").strip()
        if valor == "" and actual is not None:
            return actual
        if valor.isdigit():
            n = int(valor)
            if n >= minimo and (maximo is None or n <= maximo):
                return n
        print(f"  Escribe un número entero {rango}.")


def pedir_opcion(mensaje, opciones, actual=None):
    """Pide un valor que debe estar en la lista `opciones` (sin importar mayúsculas)."""
    mapa = {o.lower(): o for o in opciones}
    while True:
        sufijo = f" [{actual}]" if actual is not None else ""
        valor = input(f"{mensaje} ({', '.join(opciones)}){sufijo}: ").strip()
        if valor == "" and actual is not None:
            return actual
        if valor.lower() in mapa:
            return mapa[valor.lower()]
        print("  Opción no válida, elige una de la lista.")


def pedir_id(mensaje):
    """Pide un id; devuelve None si no es un entero."""
    valor = input(f"{mensaje}: ").strip()
    if not valor.isdigit():
        print("  El ID debe ser un número entero.")
        return None
    return int(valor)


def confirmar(mensaje):
    return input(f"  {mensaje} (s/n): ").strip().lower() in ("s", "si", "sí")


# ---------------------------------------------------------- Presentación

def mostrar_tabla(filas, columnas):
    """columnas = [(encabezado, clave_de_la_fila, ancho), ...]"""
    if not filas:
        print("  (sin resultados)")
        return
    print()
    print(" ".join(f"{enc:<{w}}" for enc, _, w in columnas))
    print("-" * (sum(w for _, _, w in columnas) + len(columnas) - 1))
    for f in filas:
        print(" ".join(f"{str(f[k])[:w]:<{w}}" for _, k, w in columnas))
    print(f"\n  {len(filas)} registro(s)")


COL_HEROES = [("ID", "id", 4), ("Nombre", "nombre", 20), ("Clase", "clase", 10), ("Nivel", "nivel_experiencia", 6)]
COL_MISIONES = [("ID", "id", 4), ("Nombre", "nombre", 24), ("Localización", "localizacion", 16),
                ("Dif.", "dificultad", 5), ("Oro", "recompensa_oro", 8)]
COL_MONSTRUOS = [("ID", "id", 4), ("Nombre", "nombre", 22), ("Tipo", "tipo", 10), ("Amenaza", "nivel_amenaza", 8)]


# ------------------------------------------------- Submenú genérico

def submenu(titulo, acciones, con):
    """Repite un submenú numerado hasta que el usuario elige 0 (volver)."""
    while True:
        print(f"\n--- {titulo} ---")
        for i, (texto, _) in enumerate(acciones, start=1):
            print(f" {i}. {texto}")
        print(" 0. Volver")
        eleccion = input("Elige una opción: ").strip()
        if eleccion == "0":
            return
        if eleccion.isdigit() and 1 <= int(eleccion) <= len(acciones):
            try:
                acciones[int(eleccion) - 1][1](con)
            except sqlite3.IntegrityError as e:
                # Cubre FK inexistente, duplicados y ON DELETE RESTRICT.
                print(f"  No se pudo completar la operación (restricción de la base): {e}")
        else:
            print("  Opción no válida.")


# ---------------------------------------------------------------- Héroes

def heroe_agregar(con):
    nombre = pedir_texto("Nombre")
    clase = pedir_opcion("Clase", db.CLASES)
    nivel = pedir_entero("Nivel de experiencia", 1)
    print(f"  Héroe creado con ID {db.agregar_heroe(con, nombre, clase, nivel)}.")


def heroe_listar(con):
    mostrar_tabla(db.listar_heroes(con), COL_HEROES)


def heroe_actualizar(con):
    h = db.obtener_heroe(con, pedir_id("ID del héroe") or -1)
    if h is None:
        print("  No existe ese héroe.")
        return
    print("  (Enter conserva el valor actual)")
    nombre = pedir_texto("Nombre", actual=h["nombre"])
    clase = pedir_opcion("Clase", db.CLASES, actual=h["clase"])
    nivel = pedir_entero("Nivel de experiencia", 1, actual=h["nivel_experiencia"])
    db.actualizar_heroe(con, h["id"], nombre, clase, nivel)
    print("  Héroe actualizado.")


def heroe_eliminar(con):
    h = db.obtener_heroe(con, pedir_id("ID del héroe") or -1)
    if h is None:
        print("  No existe ese héroe.")
    elif confirmar(f"¿Eliminar a '{h['nombre']}' y sus participaciones?"):
        db.eliminar_heroe(con, h["id"])
        print("  Héroe eliminado.")


# -------------------------------------------------------------- Misiones

def mision_agregar(con):
    nombre = pedir_texto("Nombre")
    desc = pedir_texto("Descripción", obligatorio=False)
    dif = pedir_entero("Dificultad", 1, 10)
    loc = pedir_texto("Localización")
    oro = pedir_entero("Recompensa en oro", 0)
    print(f"  Misión creada con ID {db.agregar_mision(con, nombre, desc, dif, loc, oro)}.")


def mision_listar(con):
    mostrar_tabla(db.listar_misiones(con), COL_MISIONES)


def mision_actualizar(con):
    m = db.obtener_mision(con, pedir_id("ID de la misión") or -1)
    if m is None:
        print("  No existe esa misión.")
        return
    print("  (Enter conserva el valor actual)")
    nombre = pedir_texto("Nombre", actual=m["nombre"])
    desc = pedir_texto("Descripción", actual=m["descripcion"] or "")
    dif = pedir_entero("Dificultad", 1, 10, actual=m["dificultad"])
    loc = pedir_texto("Localización", actual=m["localizacion"])
    oro = pedir_entero("Recompensa en oro", 0, actual=m["recompensa_oro"])
    db.actualizar_mision(con, m["id"], nombre, desc, dif, loc, oro)
    print("  Misión actualizada.")


def mision_eliminar(con):
    m = db.obtener_mision(con, pedir_id("ID de la misión") or -1)
    if m is None:
        print("  No existe esa misión.")
    elif confirmar(f"¿Eliminar '{m['nombre']}' con sus héroes y monstruos asociados?"):
        db.eliminar_mision(con, m["id"])
        print("  Misión eliminada.")


# ------------------------------------------------------------ Monstruos

def monstruo_agregar(con):
    nombre = pedir_texto("Nombre")
    tipo = pedir_opcion("Tipo", db.TIPOS)
    amenaza = pedir_entero("Nivel de amenaza", 1, 10)
    print(f"  Monstruo creado con ID {db.agregar_monstruo(con, nombre, tipo, amenaza)}.")


def monstruo_listar(con):
    mostrar_tabla(db.listar_monstruos(con), COL_MONSTRUOS)


def monstruo_actualizar(con):
    mo = db.obtener_monstruo(con, pedir_id("ID del monstruo") or -1)
    if mo is None:
        print("  No existe ese monstruo.")
        return
    print("  (Enter conserva el valor actual)")
    nombre = pedir_texto("Nombre", actual=mo["nombre"])
    tipo = pedir_opcion("Tipo", db.TIPOS, actual=mo["tipo"])
    amenaza = pedir_entero("Nivel de amenaza", 1, 10, actual=mo["nivel_amenaza"])
    db.actualizar_monstruo(con, mo["id"], nombre, tipo, amenaza)
    print("  Monstruo actualizado.")


def monstruo_eliminar(con):
    mo = db.obtener_monstruo(con, pedir_id("ID del monstruo") or -1)
    if mo is None:
        print("  No existe ese monstruo.")
    elif confirmar(f"¿Eliminar a '{mo['nombre']}'?"):
        db.eliminar_monstruo(con, mo["id"])  # RESTRICT si aparece en misiones
        print("  Monstruo eliminado.")


# ----------------------------------------- Relaciones (tablas puente)

def rel_asignar_heroe(con):
    mision, heroe = pedir_id("ID de la misión"), pedir_id("ID del héroe")
    if mision is None or heroe is None:
        return
    db.asignar_heroe(con, mision, heroe)
    print("  Héroe registrado en la misión.")


def rel_quitar_heroe(con):
    mision, heroe = pedir_id("ID de la misión"), pedir_id("ID del héroe")
    if mision is None or heroe is None:
        return
    print("  Héroe quitado de la misión." if db.quitar_heroe(con, mision, heroe)
          else "  Ese héroe no participaba en esa misión.")


def rel_asignar_monstruo(con):
    mision, monstruo = pedir_id("ID de la misión"), pedir_id("ID del monstruo")
    if mision is None or monstruo is None:
        return
    cantidad = pedir_entero("Cantidad", 1)
    db.asignar_monstruo(con, mision, monstruo, cantidad)
    print("  Monstruo registrado en la misión.")


def rel_quitar_monstruo(con):
    mision, monstruo = pedir_id("ID de la misión"), pedir_id("ID del monstruo")
    if mision is None or monstruo is None:
        return
    print("  Monstruo quitado de la misión." if db.quitar_monstruo(con, mision, monstruo)
          else "  Ese monstruo no estaba en esa misión.")


# --------------------------------------------------------------- Reportes

def rep_completo(con):
    mostrar_tabla(db.reporte_completo(con), [
        ("Héroe", "heroe", 16), ("Misión", "mision", 24),
        ("Monstruo", "monstruo", 22), ("Cant.", "cantidad", 6)])


def rep_detalle_mision(con):
    mision_id = pedir_id("ID de la misión")
    m = db.obtener_mision(con, mision_id) if mision_id is not None else None
    if m is None:
        print("  No existe esa misión.")
        return
    print(f"\n  {m['nombre']} | {m['localizacion']} | dificultad {m['dificultad']} "
          f"| {m['recompensa_oro']} monedas de oro")
    if m["descripcion"]:
        print(f"  {m['descripcion']}")
    print("\n  Héroes participantes:")
    mostrar_tabla(db.heroes_de_mision(con, m["id"]), COL_HEROES)
    print("\n  Monstruos enfrentados:")
    mostrar_tabla(db.monstruos_de_mision(con, m["id"]), COL_MONSTRUOS + [("Cant.", "cantidad", 6)])


def rep_misiones_de_heroe(con):
    heroe_id = pedir_id("ID del héroe")
    h = db.obtener_heroe(con, heroe_id) if heroe_id is not None else None
    if h is None:
        print("  No existe ese héroe.")
        return
    print(f"\n  Misiones de {h['nombre']} ({h['clase']}, nivel {h['nivel_experiencia']}):")
    mostrar_tabla(db.misiones_de_heroe(con, h["id"]), COL_MISIONES)


def rep_oro(con):
    mostrar_tabla(db.oro_por_heroe(con), [
        ("Héroe", "nombre", 20), ("Clase", "clase", 10),
        ("Misiones", "misiones", 9), ("Oro total", "oro_total", 10)])


def rep_sin_misiones(con):
    mostrar_tabla(db.heroes_sin_misiones(con), COL_HEROES)


# ------------------------------------------------------ Programa principal

MENU = """
======== GREMIO DE AVENTUREROS ========
 1. Héroes
 2. Misiones
 3. Monstruos
 4. Participantes y enemigos de una misión
 5. Consultas y reportes
 6. Cargar datos de ejemplo
 0. Salir
======================================="""


def cargar_ejemplo(con):
    if db.listar_heroes(con) or db.listar_misiones(con) or db.listar_monstruos(con):
        print("  La base ya tiene datos; no se cargó el ejemplo para no mezclarlos.")
        return
    db.cargar_datos_ejemplo(con)
    print("  Datos de ejemplo cargados.")


def main():
    con = db.conectar()
    db.crear_tablas(con)
    try:
        while True:
            print(MENU)
            op = input("Elige una opción: ").strip()
            if op == "0":
                print("¡Hasta pronto!")
                break
            elif op == "1":
                submenu("Héroes", [("Agregar héroe", heroe_agregar), ("Listar héroes", heroe_listar),
                                   ("Actualizar héroe", heroe_actualizar), ("Eliminar héroe", heroe_eliminar)], con)
            elif op == "2":
                submenu("Misiones", [("Agregar misión", mision_agregar), ("Listar misiones", mision_listar),
                                     ("Actualizar misión", mision_actualizar), ("Eliminar misión", mision_eliminar)], con)
            elif op == "3":
                submenu("Monstruos", [("Agregar monstruo", monstruo_agregar), ("Listar monstruos", monstruo_listar),
                                      ("Actualizar monstruo", monstruo_actualizar), ("Eliminar monstruo", monstruo_eliminar)], con)
            elif op == "4":
                submenu("Participantes y enemigos", [
                    ("Registrar héroe en una misión", rel_asignar_heroe),
                    ("Quitar héroe de una misión", rel_quitar_heroe),
                    ("Registrar monstruo en una misión", rel_asignar_monstruo),
                    ("Quitar monstruo de una misión", rel_quitar_monstruo)], con)
            elif op == "5":
                submenu("Consultas y reportes", [
                    ("Reporte completo (héroe - misión - monstruo)", rep_completo),
                    ("Detalle de una misión", rep_detalle_mision),
                    ("Misiones de un héroe", rep_misiones_de_heroe),
                    ("Oro acumulado por héroe", rep_oro),
                    ("Héroes sin misiones", rep_sin_misiones)], con)
            elif op == "6":
                cargar_ejemplo(con)
            else:
                print("  Opción no válida.")
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma interrumpido. ¡Hasta pronto!")
    finally:
        con.close()


if __name__ == "__main__":
    main()
