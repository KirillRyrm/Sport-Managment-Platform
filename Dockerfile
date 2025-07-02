FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc python3-dev netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN python manage.py collectstatic --noinput


CMD ["gunicorn", "sportmanagment.wsgi:application", "--bind", "0.0.0.0:8000"]


#CMD ["python", "manage.py", "runserver", "localhost:8000"]

