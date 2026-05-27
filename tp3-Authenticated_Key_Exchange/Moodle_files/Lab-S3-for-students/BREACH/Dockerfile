FROM python:3

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY server.py server.py
COPY cert.pem cert.pem
COPY key.pem key.pem

COPY oracle.py oracle.py
COPY entrypoint.sh entrypoint.sh

EXPOSE 5000 5001

RUN chmod +x entrypoint.sh

CMD [ "./entrypoint.sh"]