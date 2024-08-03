## Endpoints

### Autenticación (/auth)

#### Registro de usuario
- **Método:** POST
- **Ruta:** `/auth/register`
- **Cuerpo:**
  ```json
  {
    "email": "usuario@ejemplo.com",
    "password": "contraseña123"
  }
  ```

#### Inicio de sesión
- **Método:** POST
- **Ruta:** `/auth/token`
- **Cuerpo:** (form-data)
  ```
  username: usuario@ejemplo.com
  password: contraseña123
  ```

#### Cambio de rol (solo para administradores)
- **Método:** POST
- **Ruta:** `/auth/change_role`
- **Encabezados:** `Authorization: Bearer <token>`
- **Cuerpo:**
  ```json
  {
    "email": "usuario@ejemplo.com",
    "new_role": "TEACHER"
  }
  ```

### Gestión de fuentes de datos (/api/datasource)

#### Subida de archivos
- **Método:** POST
- **Ruta:** `/api/datasource/upload`
- **Encabezados:** `Authorization: Bearer <token>`
- **Cuerpo:** form-data con archivos

#### Crear fuente de datos
- **Método:** POST
- **Ruta:** `/api/datasource/create`
- **Encabezados:** `Authorization: Bearer <token>`
- **Cuerpo:**
  ```json
  {
    "name": "nombre_fuente_datos",
    "session_id": "id_sesion_subida"
  }
  ```

#### Listar fuentes de datos
- **Método:** GET
- **Ruta:** `/api/datasource/list`
- **Encabezados:** `Authorization: Bearer <token>`

#### Obtener detalles de una fuente de datos
- **Método:** GET
- **Ruta:** `/api/datasource/{nombre_fuente_datos}`
- **Encabezados:** `Authorization: Bearer <token>`

### Chat (/api/chat)

#### Iniciar chat
- **Método:** POST
- **Ruta:** `/api/chat`
- **Encabezados:** `Authorization: Bearer <token>`
- **Cuerpo:**
  ```json
  {
    "message": "Hola, ¿cómo estás?",
    "datasource": "nombre_fuente_datos",
    "config": {
      "model": "gpt-4o",
      "temperature": 0.7,
      "maxTokens": 2000
    }
  }
  ```

## Ejemplos de uso

### Registro de usuario
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@ejemplo.com", "password": "contraseña123"}'
```

### Inicio de sesión
```bash
curl -X POST http://localhost:8000/auth/token \
  -F "username=usuario@ejemplo.com" \
  -F "password=contraseña123"
```

### Subida de archivos
```bash
curl -X POST http://localhost:8000/api/datasource/upload \
  -H "Authorization: Bearer <token>" \
  -F "files=@/ruta/al/archivo1.pdf" \
  -F "files=@/ruta/al/archivo2.txt"
```

### Iniciar chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hola, ¿cómo estás?",
    "datasource": "nombre_fuente_datos",
    "config": {
      "model": "gpt-4",
      "temperature": 0.7,
      "maxTokens": 2000
    }
  }'
```

## Notas adicionales
- Los roles disponibles son "ADMIN", "TEACHER" y "STUDENT".
- La respuesta del chat es un flujo de eventos (event stream) que debe ser procesado adecuadamente en el frontend.
