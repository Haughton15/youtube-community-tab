# Usar una imagen base de Python
FROM python:3.9-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar el archivo de dependencias y el código fuente
COPY ./youtube-community-tab /app

# Instalar dependencias
RUN pip install -e .

# Exponer el puerto (si se ejecuta como servicio)
EXPOSE 8000

# Comando predeterminado
CMD ["python", "main.py"]
