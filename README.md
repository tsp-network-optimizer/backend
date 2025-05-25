
## Instalación dependencias
- pip install -r requirements.txt

## Ejecutar el servidor
- uvicorn app.main:app --reload
## Correr pruebas
- python -m pytest --maxfail=1 --disable-warnings -q
