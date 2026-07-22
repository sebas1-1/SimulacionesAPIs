from database import obtener_conexion


try:
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("SELECT DB_NAME()")
        resultado = cursor.fetchone()

        print(f"Conexión exitosa. Base de datos: {resultado[0]}")

except Exception as error:
    print("No fue posible conectar con SQL Server")
    print(error)
    