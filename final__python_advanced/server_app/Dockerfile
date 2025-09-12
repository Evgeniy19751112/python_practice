FROM python:3.10.11-slim

WORKDIR /usr/share/server_app

RUN groupadd -r app_grp && useradd -r -g app_grp app_usr
RUN chown -R app_usr:app_grp /usr/share/server_app

RUN mkdir /usr/share/images &&  \
    chown -R app_usr:app_grp /usr/share/images && \
    chmod -R ug+w /usr/share/images

RUN mkdir /var/log/app &&  \
    chown -R app_usr:app_grp /var/log/app && \
    chmod -R ug+w /var/log/app

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Обходим ошибку "ImportError: attempted relative import beyond
# top-level package"
ENV PYTHONPATH="/usr/share:/usr/share/server_app"

USER app_usr

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
