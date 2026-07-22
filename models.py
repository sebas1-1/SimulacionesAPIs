from datetime import date
from pydantic import BaseModel

class Cliente(BaseModel):
    identificacion: int
    nombre: str | None
    apellido: str | None
    fecha_nacimiento: date | None 