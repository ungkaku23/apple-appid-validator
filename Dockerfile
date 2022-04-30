FROM python:3.10.4
ADD requirements.txt /requirements.txt
ADD index.py /index.py
ADD okteto-stack.yaml /okteto-stack.yaml
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["python3", "index.py"]