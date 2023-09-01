# app/Dockerfile

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

EXPOSE 8553

COPY . /app

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8553", "--server.address=0.0.0.0"]