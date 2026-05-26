FROM python:3

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY server.py server.py
COPY opts.py opts.py
COPY auth.py auth.py
COPY capitals.txt capitals.txt
COPY constants.py constants.py
COPY keys/ keys/
COPY client.py client.py
COPY main.py main.py

CMD [ "python3", "server.py"]
