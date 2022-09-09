FROM python:3.9

COPY requirements.txt .

RUN apt-get update && apt-get install -y cmake

RUN pip install pip --upgrade
RUN pip install -r requirements.txt

COPY app.py .

CMD ["python", "app.py"]