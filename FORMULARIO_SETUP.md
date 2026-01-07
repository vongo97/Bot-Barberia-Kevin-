# 📝 Formulario Interactivo de Setup

## Descripción

El comando `/setup` ahora incluye un formulario interactivo que guía al dueño paso a paso para capturar información completa de su barbería.

## Flujo del Formulario

### Paso 1: Nombre de Barbería (Obligatorio)
- El bot pregunta: "¿Cuál es el nombre de tu barbería?"
- **Validación**: Mínimo 2 caracteres, máximo 100 caracteres
- **Ejemplo**: "Barbería El Estilo"

### Paso 2: Teléfono (Opcional)
- El bot pregunta: "¿Cuál es tu número de teléfono? (Opcional)"
- **Opciones**: 
  - Escribir el teléfono (ej: +57 300 123 4567)
  - Escribir "omitir" para saltar
- **Validación**: Debe contener al menos 7 dígitos

### Paso 3: Dirección (Opcional)
- El bot pregunta: "¿Cuál es la dirección de tu barbería? (Opcional)"
- **Opciones**:
  - Escribir la dirección completa
  - Escribir "omitir" para saltar
- **Ejemplo**: "Calle 123 #45-67, Bogotá"

### Finalización
- El bot muestra un resumen de la información registrada
- Guarda todos los datos en la base de datos
- Indica el siguiente paso: conectar Google Calendar

## Comandos Disponibles

### Durante el Formulario:
- `/cancel` - Cancela el proceso de setup en cualquier momento

### Después del Setup:
- `/info` - Ver información completa del dueño (solo admin)
- `/whoami` - Ver quién es el dueño del bot

## Datos Capturados

### Automáticos (de Telegram):
- ✅ ID de Telegram
- ✅ Nombre del dueño
- ✅ Usuario de Telegram (@username)

### Del Formulario:
- ✅ Nombre de barbería (obligatorio)
- 📞 Teléfono (opcional)
- 📍 Dirección (opcional)

## Base de Datos

Los datos se guardan en la tabla `bot_info`:
- `barberia_name` - Nombre de la barbería
- `owner_phone` - Teléfono del dueño
- `owner_address` - Dirección de la barbería (nuevo campo)

### Migración Automática

El sistema detecta automáticamente si la columna `owner_address` existe y la agrega si es necesario. Las bases de datos antiguas seguirán funcionando sin problemas.

## Ejemplo de Uso

```
Usuario: /setup
Bot: 👋 ¡Hola, Juan!
     Vamos a configurar tu bot de barbería paso a paso.
     📝 Paso 1 de 3
     ¿Cuál es el nombre de tu barbería?

Usuario: Barbería El Estilo
Bot: ✅ Nombre guardado: Barbería El Estilo
     📝 Paso 2 de 3
     ¿Cuál es tu número de teléfono? (Opcional)

Usuario: +57 300 123 4567
Bot: ✅ Teléfono guardado.
     📝 Paso 3 de 3
     ¿Cuál es la dirección de tu barbería? (Opcional)

Usuario: Calle 123 #45-67, Bogotá
Bot: ✅ ¡Perfecto, Juan!
     Información registrada:
     👤 Dueño: Juan
     💈 Barbería: Barbería El Estilo
     📞 Teléfono: +57 300 123 4567
     📍 Dirección: Calle 123 #45-67, Bogotá
     🎉 ¡Ya eres el administrador de este bot!
     El siguiente paso es conectar tu Google Calendar.
     Escribe /connect para hacerlo.
```

## Validaciones

### Nombre de Barbería:
- ❌ No puede estar vacío
- ❌ Mínimo 2 caracteres
- ❌ Máximo 100 caracteres

### Teléfono:
- ✅ Opcional (puede omitirse)
- ❌ Si se proporciona, debe tener al menos 7 dígitos
- ✅ Acepta formatos: +57 300 123 4567, 3001234567, etc.

### Dirección:
- ✅ Opcional (puede omitirse)
- ✅ Sin restricciones de formato

## Compatibilidad

- ✅ Compatible con bots ya configurados (no afecta datos existentes)
- ✅ Migración automática de base de datos (agrega columna `owner_address` si no existe)
- ✅ El script `list_bots.py` muestra la nueva información

## Mejoras Implementadas

1. **Experiencia de Usuario**: Formulario guiado paso a paso
2. **Validación**: Verificación de datos antes de guardar
3. **Flexibilidad**: Campos opcionales pueden omitirse
4. **Información Completa**: Captura todos los datos necesarios desde el inicio
5. **Cancelación**: Permite cancelar en cualquier momento con `/cancel`
