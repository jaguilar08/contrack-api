FROM python:3.10-slim

# create the app user
RUN addgroup --system app && adduser --system --group app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

ENV PYTHONPATH=/app

# aws credentials
ENV AWS_ACCESS_KEY_ID="AKIAZMSSGKTAI2D2XG2Q"
ENV AWS_SECRET_ACCESS_KEY="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"

# chown all the files to the app user
RUN chown -R app:app $HOME

# change to the app user
# Switch to a non-root user, which is recommended by Heroku.
USER app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

