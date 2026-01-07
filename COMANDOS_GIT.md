# 🚀 Comandos para Corregir el Repositorio

Ejecuta estos comandos en PowerShell, uno por uno, en la carpeta del bot:

```powershell
# 1. Ir a la carpeta del proyecto
cd "J:\Automatizaciones\Bot Barberia Kevin\Bot barberia Kevin"

# 2. Eliminar archivos sensibles del índice de Git
git rm --cached credentials.json
git rm --cached token.json
git rm --cached tests/token.json
git rm --cached .env
git rm --cached ultron_memory.db

# 3. Eliminar archivos de caché
git rm -r --cached __pycache__
git rm -r --cached services/__pycache__

# 4. Agregar .gitignore
git add .gitignore

# 5. Verificar estado
git status

# 6. Crear nuevo commit (reemplaza el anterior)
git commit --amend -m "Primer Deploy render - Sin archivos sensibles"

# 7. Subir al repositorio (forzar porque modificamos el commit)
git push -f origin main
```

## ⚠️ Importante

- Los archivos **NO se eliminan de tu computadora**, solo del repositorio
- El `-f` en el push es necesario porque modificamos el commit anterior
- Después de esto, GitHub debería aceptar el push

## ✅ Verificación

Después del push, verifica en GitHub que los archivos sensibles ya no estén en el repositorio.
