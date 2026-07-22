from datetime import date
from pydantic import BaseModel

# Modelo de la tabla cliente
class Cliente(BaseModel):
    identificacion: int
    nombre: str | None
    apellido: str | None
    fecha_nacimiento: date | None 

# Modelo de la tabla repuesto_socio
class RepuestoSocio(BaseModel):
    id_repuesto: int
    proveedor: str
    codigo: str
    nombre: str
    marca: str | None
    precio: float
    existencia: int
    tiempo_entrega_dias: int

# Modelo de la tabla poliza_socio
class PolizaSocio(BaseModel):
    id_poliza: int
    aseguradora: str
    numero_poliza: str
    placa: str
    identificacion_cliente: str
    tipo_cobertura: str
    deducible: float
    fecha_inicio: date
    fecha_vencimiento: date
    activa: bool
    vigente: bool

# Modelo de la tabla grua_socio
class GruaSocio(BaseModel):
    id_grua: int
    empresa: str
    placa: str
    tipo_grua: str
    provincia: str
    canton: str
    telefono: str
    capacidad_toneladas: float
    tarifa_base: float
    tiempo_estimado_minutos: int
    disponible: bool
    
# Modelo de la tabla vehiculo_alquiler_socio
class VehiculoAlquilerSocio(BaseModel):
    id_vehiculo: int
    empresa: str
    placa: str
    marca: str
    modelo: str
    anio: int
    categoria: str
    transmision: str
    cantidad_pasajeros: int
    tarifa_diaria: float
    deposito: float
    disponible: bool