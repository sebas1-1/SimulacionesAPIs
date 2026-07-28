from fastapi import FastAPI, HTTPException
from database import obtener_conexion
from models import Cliente, RepuestoSocio, PolizaSocio, GruaSocio, VehiculoAlquilerSocio
from routers.comercial import router as comercial_router
from fastapi.middleware.cors import CORSMiddleware
from datetime import date


app = FastAPI(
        title="Retro Garage Simulations API",
        description="API for Retro Garage clients management and simulations.",
        version="1.0.0"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(comercial_router)




@app.get("/clientes/{identificacion}", response_model=Cliente)
def buscar_cliente(identificacion: int):
    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(
                """
                SELECT identificacion, nombre, apellido, fecha_nacimiento
                FROM TSE
                WHERE identificacion = ?
                """,
                (identificacion,),
            )
            resultado = cursor.fetchone()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar la base de datos",
        ) from error

    if resultado is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return Cliente(
        identificacion=resultado[0],
        nombre=resultado[1],
        apellido=resultado[2],
        fecha_nacimiento=resultado[3],
    )

@app.get(
    "/socios/proveedores/repuestos",
    response_model=list[RepuestoSocio],
)
def buscar_catalogo_repuestos(buscar: str):
    termino = buscar.strip().upper()

    if not termino:
        return []

    patron = f"%{termino}%"

    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(
                """
                SELECT
                    id_repuesto,
                    proveedor,
                    codigo,
                    nombre,
                    marca,
                    precio,
                    existencia,
                    tiempo_entrega_dias
                FROM socios_repuestos
                WHERE activo = 1
                  AND (
                      UPPER(codigo) LIKE ?
                      OR UPPER(nombre) LIKE ?
                      OR UPPER(ISNULL(marca, '')) LIKE ?
                  )
                ORDER BY nombre ASC, codigo ASC, precio ASC
                """,
                patron,
                patron,
                patron,
            )
            filas = cursor.fetchall()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error al buscar el catálogo de proveedores",
        ) from error

    return [
        RepuestoSocio(
            id_repuesto=fila[0],
            proveedor=fila[1],
            codigo=fila[2],
            nombre=fila[3],
            marca=fila[4],
            precio=float(fila[5]),
            existencia=fila[6],
            tiempo_entrega_dias=fila[7],
        )
        for fila in filas
    ]


@app.get("/socios/proveedores/repuestos/{codigo}",response_model=list[RepuestoSocio],
)
def buscar_repuestos_proveedores(codigo: str):
    codigo_limpio = codigo.strip().upper()

    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()

            cursor.execute(
                """
                SELECT
                    id_repuesto,
                    proveedor,
                    codigo,
                    nombre,
                    marca,
                    precio,
                    existencia,
                    tiempo_entrega_dias
                FROM socios_repuestos
                WHERE codigo = ?
                  AND activo = 1
                ORDER BY precio ASC
                """,
                codigo_limpio,
            )

            filas = cursor.fetchall()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar los repuestos de proveedores",
        ) from error

    if not filas:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron ofertas para ese repuesto",
        )

    return [
        RepuestoSocio(
            id_repuesto=fila[0],
            proveedor=fila[1],
            codigo=fila[2],
            nombre=fila[3],
            marca=fila[4],
            precio=float(fila[5]),
            existencia=fila[6],
            tiempo_entrega_dias=fila[7],
        )
        for fila in filas
    ]

@app.get("/socios/aseguradoras/polizas/{placa}",response_model=PolizaSocio,)

def buscar_poliza_por_placa(placa: str):
    placa_limpia = placa.strip().replace("-", "").upper()

    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()

            cursor.execute(
                """
                SELECT TOP 1
                    id_poliza,
                    aseguradora,
                    numero_poliza,
                    placa,
                    identificacion_cliente,
                    tipo_cobertura,
                    deducible,
                    fecha_inicio,
                    fecha_vencimiento,
                    activa
                FROM socios_polizas
                WHERE placa = ?
                ORDER BY fecha_vencimiento DESC
                """,
                placa_limpia,
            )

            fila = cursor.fetchone()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar la póliza",
        ) from error

    if fila is None:
        raise HTTPException(
            status_code=404,
            detail="No se encontró una póliza para esa placa",
        )

    hoy = date.today()

    vigente = (
        bool(fila[9])
        and fila[7] <= hoy
        and fila[8] >= hoy
    )

    return PolizaSocio(
        id_poliza=fila[0],
        aseguradora=fila[1],
        numero_poliza=fila[2],
        placa=fila[3],
        identificacion_cliente=fila[4],
        tipo_cobertura=fila[5],
        deducible=float(fila[6]),
        fecha_inicio=fila[7],
        fecha_vencimiento=fila[8],
        activa=bool(fila[9]),
        vigente=vigente,
    )

@app.get("/socios/gruas/disponibles",response_model=list[GruaSocio],)
def consultar_gruas_disponibles(provincia: str | None = None):
    consulta = """
        SELECT
            id_grua,
            empresa,
            placa,
            tipo_grua,
            provincia,
            canton,
            telefono,
            capacidad_toneladas,
            tarifa_base,
            tiempo_estimado_minutos,
            disponible
        FROM socios_gruas
        WHERE disponible = 1
    """

    parametros = []

    if provincia:
        consulta += " AND provincia = ?"
        parametros.append(provincia.strip())

    consulta += " ORDER BY tiempo_estimado_minutos ASC, tarifa_base ASC"

    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(consulta, parametros)
            filas = cursor.fetchall()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar las grúas disponibles",
        ) from error

    return [
        GruaSocio(
            id_grua=fila[0],
            empresa=fila[1],
            placa=fila[2],
            tipo_grua=fila[3],
            provincia=fila[4],
            canton=fila[5],
            telefono=fila[6],
            capacidad_toneladas=float(fila[7]),
            tarifa_base=float(fila[8]),
            tiempo_estimado_minutos=fila[9],
            disponible=bool(fila[10]),
        )
        for fila in filas
    ]

@app.get("/socios/alquileres/disponibles",response_model=list[VehiculoAlquilerSocio],)
def consultar_vehiculos_alquiler(categoria: str | None = None):
    consulta = """
        SELECT
            id_vehiculo,
            empresa,
            placa,
            marca,
            modelo,
            anio,
            categoria,
            transmision,
            cantidad_pasajeros,
            tarifa_diaria,
            deposito,
            disponible
        FROM socios_vehiculos_alquiler
        WHERE disponible = 1
    """

    parametros = []

    if categoria:
        consulta += " AND categoria = ?"
        parametros.append(categoria.strip())

    consulta += " ORDER BY tarifa_diaria ASC"

    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(consulta, parametros)
            filas = cursor.fetchall()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar los vehículos de alquiler",
        ) from error

    return [
        VehiculoAlquilerSocio(
            id_vehiculo=fila[0],
            empresa=fila[1],
            placa=fila[2],
            marca=fila[3],
            modelo=fila[4],
            anio=fila[5],
            categoria=fila[6],
            transmision=fila[7],
            cantidad_pasajeros=fila[8],
            tarifa_diaria=float(fila[9]),
            deposito=float(fila[10]),
            disponible=bool(fila[11]),
        )
        for fila in filas
    ]
