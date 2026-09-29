"""
main.py
Interfaz de consola de la biblioteca personal.
Muestra el menú, pide datos al usuario y delega el trabajo a database.py.
"""
import database as db


# ---------- Utilidades de entrada/salida ----------

def pedir_texto(mensaje, obligatorio=True, actual=None):
    """
    Pide un texto por consola.
    - obligatorio=True: repite hasta que el usuario escriba algo.
    - actual: si se indica (modo edición), Enter conserva el valor actual.
    """
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


def pedir_estado(actual=None):
    """Pide el estado de lectura (s/n). En edición, Enter conserva el actual."""
    sufijo = ""
    if actual is not None:
        sufijo = f" [{'s' if actual else 'n'}]"
    while True:
        r = input(f"¿Ya lo leíste? (s/n){sufijo}: ").strip().lower()
        if r in ("s", "si", "sí"):
            return True
        if r in ("n", "no"):
            return False
        if r == "" and actual is not None:
            return bool(actual)
        print("  Responde 's' o 'n'.")


def pedir_id(mensaje="ID del libro"):
    """Pide un id numérico; devuelve None si el valor no es un entero."""
    valor = input(f"{mensaje}: ").strip()
    if not valor.isdigit():
        print("  El ID debe ser un número entero.")
        return None
    return int(valor)


def mostrar_libros(libros):
    """Imprime una lista de libros en formato de tabla."""
    if not libros:
        print("  (sin resultados)")
        return
    print(f"\n{'ID':<4} {'Título':<30} {'Autor':<22} {'Género':<15} Estado")
    print("-" * 82)
    for l in libros:
        estado = "Leído" if l["leido"] else "No leído"
        print(f"{l['id']:<4} {l['titulo'][:29]:<30} {l['autor'][:21]:<22} "
              f"{l['genero'][:14]:<15} {estado}")
    print(f"\nTotal: {len(libros)} libro(s)")


# ---------- Opciones del menú ----------

def opcion_agregar(con):
    print("\n--- Agregar libro ---")
    titulo = pedir_texto("Título")
    autor = pedir_texto("Autor")
    genero = pedir_texto("Género")
    leido = pedir_estado()
    nuevo_id = db.agregar_libro(con, titulo, autor, genero, leido)
    print(f"  Libro agregado con ID {nuevo_id}.")


def opcion_actualizar(con):
    print("\n--- Actualizar libro ---")
    libro_id = pedir_id()
    if libro_id is None:
        return
    libro = db.obtener_libro(con, libro_id)
    if libro is None:
        print("  No existe un libro con ese ID.")
        return
    print("  (Enter para conservar el valor actual)")
    titulo = pedir_texto("Título", actual=libro["titulo"])
    autor = pedir_texto("Autor", actual=libro["autor"])
    genero = pedir_texto("Género", actual=libro["genero"])
    leido = pedir_estado(actual=libro["leido"])
    db.actualizar_libro(con, libro_id, titulo, autor, genero, leido)
    print("  Libro actualizado.")


def opcion_eliminar(con):
    print("\n--- Eliminar libro ---")
    libro_id = pedir_id()
    if libro_id is None:
        return
    libro = db.obtener_libro(con, libro_id)
    if libro is None:
        print("  No existe un libro con ese ID.")
        return
    confirmar = input(f"  ¿Eliminar '{libro['titulo']}'? (s/n): ").strip().lower()
    if confirmar in ("s", "si", "sí"):
        db.eliminar_libro(con, libro_id)
        print("  Libro eliminado.")
    else:
        print("  Operación cancelada.")


def opcion_listar(con):
    print("\n--- Listado de libros ---")
    mostrar_libros(db.listar_libros(con))


def opcion_buscar(con):
    print("\n--- Buscar libros ---")
    print("  1. Por título\n  2. Por autor\n  3. Por género")
    campos = {"1": "titulo", "2": "autor", "3": "genero"}
    eleccion = input("Buscar por: ").strip()
    if eleccion not in campos:
        print("  Opción no válida.")
        return
    texto = pedir_texto("Texto a buscar")
    mostrar_libros(db.buscar_libros(con, campos[eleccion], texto))


# ---------- Programa principal ----------

MENU = """
========== BIBLIOTECA PERSONAL ==========
 1. Agregar libro
 2. Actualizar libro
 3. Eliminar libro
 4. Ver listado de libros
 5. Buscar libros
 6. Salir
=========================================="""


def main():
    con = db.conectar()
    db.crear_tabla(con)
    acciones = {
        "1": opcion_agregar,
        "2": opcion_actualizar,
        "3": opcion_eliminar,
        "4": opcion_listar,
        "5": opcion_buscar,
    }
    try:
        while True:
            print(MENU)
            opcion = input("Elige una opción: ").strip()
            if opcion == "6":
                print("¡Hasta pronto!")
                break
            accion = acciones.get(opcion)
            if accion:
                accion(con)
            else:
                print("  Opción no válida. Elige un número del 1 al 6.")
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma interrumpido. ¡Hasta pronto!")
    finally:
        con.close()  # se cierra la conexión pase lo que pase


if __name__ == "__main__":
    main()
