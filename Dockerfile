FROM python:alpine as base

FROM base as builder
COPY requirements.txt /requirements.txt
RUN pip install --user -r /requirements.txt

FROM base
COPY --from=builder /root/.local /root/.local
COPY ./src /app
WORKDIR /app

# update PATH environment variable
ENV PATH=/root/.local/bin:$PATH

CMD ["fastapi", "run", "index.py"]