# 1. Elimina la conexión incorrecta
git remote remove origin
# 2. Añade la conexión correcta (REEMPLAZA LA URL)
git remote add origin https://github.com/CesarClaudio1424/calculadorausdusdt.git
# 3. Descarga la versión de la nube y fusiona
git pull origin main
# 4. Prepara y guarda tus cambios locales
git add .
git commit -m "Corregir conexión y subir versión final"
# 5. Sube todo a GitHub
git push --set-upstream origin main
git push