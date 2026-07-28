from datetime import date, datetime

from pydantic import BaseModel, Field


class ServicioPublico(BaseModel):
    id_servicio: int
    categoria: str
    nombre: str
    precio_base: float


class ProductoPublico(BaseModel):
    id_producto: int
    categoria: str
    nombre: str
    codigo: str
    precio_venta: float
    stock_disponible: int
    unidad_medida: str
    estado_stock: str


class EspacioAgenda(BaseModel):
    fecha: date
    hora: str
    cupos_totales: int
    cupos_disponibles: int
    disponible: bool


class ProductoCotizacionSolicitud(BaseModel):
    id_producto: int
    cantidad: int = Field(gt=0, le=1000)


class CotizacionSolicitud(BaseModel):
    servicios: list[int] = Field(default_factory=list)
    productos: list[ProductoCotizacionSolicitud] = Field(default_factory=list)


class DetalleCotizacion(BaseModel):
    tipo: str
    id_item: int
    codigo: str | None = None
    descripcion: str
    cantidad: int
    precio_unitario: float
    subtotal: float
    stock_suficiente: bool | None = None


class CotizacionRespuesta(BaseModel):
    id_cotizacion: str
    generada_en: datetime
    moneda: str
    detalles: list[DetalleCotizacion]
    subtotal: float
    impuesto_porcentaje: float
    impuesto: float
    total: float
