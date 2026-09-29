# Biblioteca Personal (Python + SQLite)

Aplicación de línea de comandos para administrar una biblioteca personal. Guarda los libros (título, autor, género y estado de lectura) en una base de datos SQLite usando la biblioteca estándar `sqlite3` de Python.

## Funcionalidades

1. Agregar un libro nuevo
2. Actualizar cualquier campo de un libro (incluido el estado de lectura)
3. Eliminar un libro (con confirmación)
4. Ver el listado completo de libros
5. Buscar por título, autor o género (coincidencia parcial, sin distinguir mayúsculas)
6. Salir

## Estructura del proyecto

| Archivo | Responsabilidad |
|---|---|
| `database.py` | Acceso a datos: conexión, creación de la tabla y operaciones CRUD/búsqueda |
| `main.py` | Interfaz de consola: menú, validación de entradas y presentación de resultados |
| `biblioteca.db` | Base de datos (se crea sola en la primera ejecución) |

### Tabla `libros`

| Columna | Tipo | Restricciones |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| titulo | TEXT | NOT NULL |
| autor | TEXT | NOT NULL |
| genero | TEXT | NOT NULL |
| leido | INTEGER | NOT NULL, DEFAULT 0, CHECK (0 o 1) |






 


