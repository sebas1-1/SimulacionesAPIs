from fastapi import FastAPI, HTTPException
from database import obtener_conexion
from models import Cliente

app = FastAPI(
    title="Retro Garage Simulations API",
    description="API for Retro Garage clients management and simulations.",
    version="1.0.0",
)

@app.get("/")
def inicio():
    return {"message": "Welcome to the Retro Garage Simulations API!"}

@app.get("/clientes/{identificacion}", response_model=Cliente)
def buscar_cliente(identificacion: int):
    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(
                "SELECT identificacion, nombre, apellido, fecha_nacimiento FROM TSE WHERE identificacion = ?",
                (identificacion,),
            )
            resultado = cursor.fetchone()

            if resultado:
                cliente = Cliente(
                    identificacion=resultado[0],
                    nombre=resultado[1],
                    apellido=resultado[2],
                    fecha_nacimiento=resultado[3],
                )
                return cliente
            else:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))