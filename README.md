##Build docker
docker build -t backend_tutoria .

##Run

docker run -p 8000:8000 backend_tutoria

## Endpoints

### Autenticación (/auth)

### User Registration
- **Method:** POST
- **Route:** `/auth/register`
- **Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "role": "STUDENT"
  }
  ```
- **Note:** Available roles are "ADMIN", "TEACHER", and "STUDENT".

### User Login
- **Method:** POST
- **Route:** `/auth/token`
- **Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
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
- **Ruta:** `/datasource/upload`
- **Encabezados:** `Authorization: Bearer <token>`
- **Cuerpo:** form-data con archivos

#### Crear fuente de datos
- **Método:** POST
- **Ruta:** `/datasource/upload`
Multipart formdata con forma:
{
  "files": [
    (binary data of file 1),
    (binary data of file 2),
    ...
  ],
  "datasource_name": "name_of_your_datasource"

}

### Upload Files and Create Data Source
- **Method:** POST
- **Route:** `/datasource/upload`
- **Headers:** `Authorization: Bearer <token>`
- **Body:** Multipart form-data
  ```
  files: (binary data of PDF files)
  datasource_name: "name_of_your_datasource"
  ```
- **Note:** Only PDF files are accepted.

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
      "model": "gpt-3.5-turbo-16k",
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

### Login Example
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
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
