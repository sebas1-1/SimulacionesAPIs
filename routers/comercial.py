from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status

from database import obtener_conexion
from public_models import (
    CotizacionRespuesta,
    CotizacionSolicitud,
    DetalleCotizacion,
    EspacioAgenda,
    ProductoPublico,
    ServicioPublico,
)


router = APIRouter(
    prefix="/api/comercial/v1",
    tags=["API comercial"],
)

CAPACIDAD_CITAS_POR_HORA = 2
IVA_PORCENTAJE = Decimal("13")


def _estado_stock(stock_actual: int, stock_minimo: int) -> str:
    if stock_actual <= 0:
        return "AGOTADO"
    if stock_actual <= stock_minimo:
        return "STOCK BAJO"
    return "DISPONIBLE"


@router.get("/servicios", response_model=list[ServicioPublico])
def consultar_catalogo_servicios(
    buscar: str | None = Query(default=None, max_length=100),
):
    consulta = """
        SELECT
            s.id_servicio,
            c.nombre AS categoria,
            s.nombre,
            s.precio_base
        FROM servicios s
        INNER JOIN categorias c ON c.id_categoria = s.id_categoria
        WHERE s.activo = 1
    """
    parametros: list[str] = []

    if buscar and buscar.strip():
        consulta += " AND (s.nombre LIKE ? OR c.nombre LIKE ?)"
        patron = f"%{buscar.strip()}%"
        parametros.extend([patron, patron])

    consulta += " ORDER BY c.nombre, s.nombre"

    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(consulta, *parametros)
            filas = cursor.fetchall()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar el catálogo de servicios",
        ) from error

    return [
        ServicioPublico(
            id_servicio=fila[0],
            categoria=fila[1],
            nombre=fila[2],
            precio_base=float(fila[3]),
        )
        for fila in filas
    ]


@router.get("/productos", response_model=list[ProductoPublico])
def consultar_productos_disponibles(
    buscar: str | None = Query(default=None, max_length=100),
    solo_disponibles: bool = True,
):
    consulta = """
        SELECT
            p.id_producto,
            c.nombre AS categoria,
            p.nombre,
            p.codigo_item,
            p.precio_venta,
            p.stock_actual,
            p.stock_minimo,
            p.unidad_medida
        FROM productos p
        INNER JOIN categorias c ON c.id_categoria = p.id_categoria
        WHERE p.activo = 1
    """
    parametros: list[str] = []

    if solo_disponibles:
        consulta += " AND p.stock_actual > 0"

    if buscar and buscar.strip():
        consulta += """
            AND (
                p.nombre LIKE ?
                OR p.codigo_item LIKE ?
                OR c.nombre LIKE ?
            )
        """
        patron = f"%{buscar.strip()}%"
        parametros.extend([patron, patron, patron])

    consulta += " ORDER BY c.nombre, p.nombre"

    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(consulta, *parametros)
            filas = cursor.fetchall()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar los productos disponibles",
        ) from error

    return [
        ProductoPublico(
            id_producto=fila[0],
            categoria=fila[1],
            nombre=fila[2],
            codigo=fila[3],
            precio_venta=float(fila[4]),
            stock_disponible=fila[5],
            unidad_medida=fila[7],
            estado_stock=_estado_stock(fila[5], fila[6]),
        )
        for fila in filas
    ]


@router.get("/agenda/disponibilidad", response_model=list[EspacioAgenda])
def consultar_disponibilidad_agenda(fecha: date):
    hoy = date.today()

    if fecha < hoy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha no puede ser anterior a hoy",
        )

    # El taller no ofrece citas los domingos.
    if fecha.weekday() == 6:
        return []

    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(
                """
                SELECT DATEPART(HOUR, hora) AS hora, COUNT(*) AS reservadas
                FROM citas
                WHERE fecha = ?
                  AND estado <> 'CANCELADA'
                GROUP BY DATEPART(HOUR, hora)
                """,
                fecha,
            )
            reservadas_por_hora = {
                int(fila[0]): int(fila[1]) for fila in cursor.fetchall()
            }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar la disponibilidad de la agenda",
        ) from error

    espacios: list[EspacioAgenda] = []

    # Citas de una hora: 08:00 es la primera y 16:00 la última.
    for hora in range(8, 17):
        reservadas = reservadas_por_hora.get(hora, 0)
        disponibles = max(CAPACIDAD_CITAS_POR_HORA - reservadas, 0)
        espacios.append(
            EspacioAgenda(
                fecha=fecha,
                hora=f"{hora:02d}:00",
                cupos_totales=CAPACIDAD_CITAS_POR_HORA,
                cupos_disponibles=disponibles,
                disponible=disponibles > 0,
            )
        )

    return espacios


@router.post("/cotizaciones", response_model=CotizacionRespuesta)
def generar_cotizacion(solicitud: CotizacionSolicitud):
    cantidades_productos: dict[int, int] = {}
    for producto in solicitud.productos:
        cantidades_productos[producto.id_producto] = (
            cantidades_productos.get(producto.id_producto, 0)
            + producto.cantidad
        )

    ids_servicios = sorted(set(solicitud.servicios))
    ids_productos = sorted(cantidades_productos)

    if not ids_servicios and not ids_productos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cotización debe incluir servicios o productos",
        )

    filas_servicios = []
    filas_productos = []

    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()

            if ids_servicios:
                marcadores = ",".join("?" for _ in ids_servicios)
                cursor.execute(
                    f"""
                    SELECT id_servicio, nombre, precio_base
                    FROM servicios
                    WHERE activo = 1
                      AND id_servicio IN ({marcadores})
                    """,
                    *ids_servicios,
                )
                filas_servicios = cursor.fetchall()

            if ids_productos:
                marcadores = ",".join("?" for _ in ids_productos)
                cursor.execute(
                    f"""
                    SELECT
                        id_producto,
                        codigo_item,
                        nombre,
                        precio_venta,
                        stock_actual
                    FROM productos
                    WHERE activo = 1
                      AND id_producto IN ({marcadores})
                    """,
                    *ids_productos,
                )
                filas_productos = cursor.fetchall()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error al generar la cotización",
        ) from error

    servicios_encontrados = {int(fila[0]) for fila in filas_servicios}
    productos_encontrados = {int(fila[0]) for fila in filas_productos}
    servicios_faltantes = sorted(set(ids_servicios) - servicios_encontrados)
    productos_faltantes = sorted(set(ids_productos) - productos_encontrados)

    if servicios_faltantes or productos_faltantes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "mensaje": "Hay elementos inexistentes o inactivos",
                "servicios": servicios_faltantes,
                "productos": productos_faltantes,
            },
        )

    detalles: list[DetalleCotizacion] = []
    subtotal = Decimal("0")

    for fila in filas_servicios:
        precio = Decimal(fila[2])
        subtotal_item = precio
        subtotal += subtotal_item
        detalles.append(
            DetalleCotizacion(
                tipo="SERVICIO",
                id_item=fila[0],
                descripcion=fila[1],
                cantidad=1,
                precio_unitario=float(precio),
                subtotal=float(subtotal_item),
            )
        )

    for fila in filas_productos:
        cantidad = cantidades_productos[int(fila[0])]
        precio = Decimal(fila[3])
        subtotal_item = precio * cantidad
        subtotal += subtotal_item
        detalles.append(
            DetalleCotizacion(
                tipo="PRODUCTO",
                id_item=fila[0],
                codigo=fila[1],
                descripcion=fila[2],
                cantidad=cantidad,
                precio_unitario=float(precio),
                subtotal=float(subtotal_item),
                stock_suficiente=cantidad <= int(fila[4]),
            )
        )

    porcentaje = IVA_PORCENTAJE
    impuesto = (subtotal * porcentaje / Decimal("100")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    total = subtotal + impuesto

    return CotizacionRespuesta(
        id_cotizacion=str(uuid4()),
        generada_en=datetime.now(timezone.utc),
        moneda="CRC",
        detalles=detalles,
        subtotal=float(subtotal),
        impuesto_porcentaje=float(porcentaje),
        impuesto=float(impuesto),
        total=float(total),
    )
