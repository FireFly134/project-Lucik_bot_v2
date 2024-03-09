FROM python:3.11-alpine

ENV PYTHONFAULTHANDLER=1 \
     PYTHONUNBUFFERED=1 \
     PYTHONDONTWRITEBYTECODE=1

WORKDIR /usr/local/app

RUN pip install pipenv
COPY ./Pipfile* ./

RUN pipenv install --system --dev --deploy

COPY . .

CMD ["python3", "main_bot.py"]
