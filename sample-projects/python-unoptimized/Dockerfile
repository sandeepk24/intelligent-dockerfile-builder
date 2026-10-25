FROM python:latest
ADD . /app
WORKDIR /app
RUN pip install -r requirements.txt
COPY .env .
USER root
EXPOSE 8000
CMD python app/main.py
