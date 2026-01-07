# 🔒 Guía para Eliminar Secretos del Repositorio Git

GitHub detectó secretos en tu commit y bloqueó el push. Sigue estos pasos para corregirlo.

## ⚠️ IMPORTANTE

Los archivos sensibles que debes eliminar del historial:
- `credentials.json` - Contiene Client ID y Client Secret de Google OAuth
- `token.json` - Contiene tokens de acceso de Google
- `tests/token.json` - Token de prueba
- `.env` - Variables de entorno con secretos
- `ultron_memory.db` - Base de datos (puede contener datos sensibles)
- `__pycache__/` - Archivos compilados de Python (no necesarios)

## 📋 Pasos para Corregir

### Paso 1: Eliminar archivos sensibles del índice de Git

Ejecuta estos comandos en PowerShell (en la carpeta del bot):

```powershell
cd "J:\Automatizaciones\Bot Barberia Kevin\Bot barberia Kevin"

# Eliminar archivos sensibles del índice (se mantienen localmente)
git rm --cached credentials.json
git rm --cached token.json
git rm --cached tests/token.json
git rm --cached .env
git rm --cached ultron_memory.db

# Eliminar archivos de caché de Python
git rm -r --cached __pycache__
git rm -r --cached services/__pycache__
```

### Paso 2: Agregar el .gitignore

```powershell
# Agregar el .gitignore al índice
git add .gitignore
```

### Paso 3: Verificar que los archivos sensibles ya no estén en el índice

```powershell
# Ver el estado actual
git status
```

Deberías ver que los archivos sensibles aparecen como "deleted" pero NO deberían aparecer en "Changes to be committed" a menos que sea para eliminarlos.

### Paso 4: Crear un nuevo commit sin los archivos sensibles

```powershell
# Hacer commit de los cambios (eliminación de archivos sensibles + .gitignore)
git commit --amend -m "Primer Deploy render - Sin archivos sensibles"
```

O si prefieres un commit nuevo:

```powershell
git commit -m "Eliminar archivos sensibles y agregar .gitignore"
```

### Paso 5: Verificar que no haya secretos

```powershell
# Ver qué archivos se van a subir
git ls-files
```

Verifica que NO aparezcan:
- ❌ credentials.json
- ❌ token.json
- ❌ tests/token.json
- ❌ .env
- ❌ ultron_memory.db
- ❌ __pycache__/

### Paso 6: Subir al repositorio

```powershell
# Si usaste --amend, necesitarás forzar el push (solo esta vez)
git push -f origin main
```

⚠️ **Nota**: Usa `-f` solo si estás seguro de que quieres reescribir el historial. Si prefieres no forzar, puedes hacer un commit nuevo y luego push normal.

## 🔄 Alternativa: Commit Nuevo (Más Seguro)

Si prefieres no modificar el commit anterior:

```powershell
# Paso 1-3: Igual que arriba
git rm --cached credentials.json token.json tests/token.json .env ultron_memory.db
git rm -r --cached __pycache__ services/__pycache__
git add .gitignore

# Paso 4: Commit nuevo
git commit -m "Eliminar archivos sensibles y agregar .gitignore"

# Paso 5: Push normal (sin -f)
git push origin main
```

## ✅ Verificación Final

Después del push, verifica en GitHub que:

1. ✅ El archivo `.gitignore` esté presente
2. ✅ Los archivos `credentials.json`, `token.json`, `.env`, `ultron_memory.db` NO estén en el repositorio
3. ✅ GitHub no muestre más errores de secretos detectados

## 🛡️ Prevención Futura

Para evitar esto en el futuro:

1. **Siempre verifica antes de commitear**:
   ```powershell
   git status
   git diff --cached
   ```

2. **Usa el .gitignore** - Ya está configurado, solo asegúrate de que esté en la raíz del repositorio

3. **Nunca hagas commit de**:
   - Archivos `.env`
   - `credentials.json` o `client_secret_*.json`
   - `token.json`
   - Bases de datos `.db`
   - Archivos `__pycache__/`

## 🆘 Si GitHub Aún Detecta Secretos

Si después de estos pasos GitHub sigue detectando secretos, es porque están en el historial de commits anteriores. En ese caso:

1. Ve a la URL que GitHub te proporcionó en el error
2. O usa `git filter-branch` o `git filter-repo` para limpiar el historial completo
3. O contacta a GitHub para que revoquen los secretos expuestos

## 📝 Notas Importantes

- Los archivos **NO se eliminan de tu computadora**, solo del repositorio Git
- Los archivos seguirán funcionando localmente
- Para producción (Render), usa variables de entorno en lugar de archivos
