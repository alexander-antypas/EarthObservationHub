FROM python:3
RUN mkdir /app
WORKDIR /app
COPY app/requirements.txt /app/requirements.txt
COPY app /app
RUN python -m pip install --upgrade pip
RUN pip --no-cache-dir install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["app.py"]
#CMD ["python","./app.py"]