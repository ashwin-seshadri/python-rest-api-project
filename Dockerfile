FROM python:3.13.2
WORKDIR /app
COPY requirements.txt .
RUN pip install --root-user-action=ignore --no-cache-dir --upgrade -r requirements.txt
COPY . .
RUN flask db upgrade
CMD ["guinocrn", "--bind", "0.0.0.0:80", "app:create_app()"]