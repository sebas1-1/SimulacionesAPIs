# API comercial de RetroGarage

Estas rutas permiten que otro comercio consulte la oferta pública de
RetroGarage sin acceder a clientes, costos internos ni proveedores.

## Ejecución

Activa el entorno e inicia FastAPI:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Puedes probar las rutas directamente desde Postman o Swagger, sin headers
especiales.

## APIs

### 1. Catálogo de servicios

```http
GET /api/comercial/v1/servicios
GET /api/comercial/v1/servicios?buscar=aceite
```

### 2. Productos disponibles

```http
GET /api/comercial/v1/productos
GET /api/comercial/v1/productos?buscar=filtro
GET /api/comercial/v1/productos?solo_disponibles=false
```

No expone precio de costo, proveedor ni stock mínimo.

### 3. Disponibilidad de agenda

```http
GET /api/comercial/v1/agenda/disponibilidad?fecha=2026-08-03
```

La simulación utiliza dos cupos disponibles por cada hora.

### 4. Generación de cotizaciones

```http
POST /api/comercial/v1/cotizaciones
Content-Type: application/json
```

```json
{
  "servicios": [1, 3],
  "productos": [
    {
      "id_producto": 2,
      "cantidad": 2
    }
  ]
}
```

La cotización es informativa y no se almacena en la base de datos.
