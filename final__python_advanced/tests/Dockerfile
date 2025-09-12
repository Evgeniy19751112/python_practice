FROM python:3.10.11-slim

COPY ./server_app /usr/share/app/
COPY ./tests /usr/share/app/
COPY ./.env_test /usr/share/app/.env
COPY ./pytest.ini /usr/share/app/

WORKDIR /usr/share

RUN groupadd -r app_grp && useradd -r -g app_grp app_usr
RUN chown -R app_usr:app_grp /usr/share/app/server_app

RUN mkdir /tmp/images &&  \
    chown -R app_usr:app_grp /tmp/images && \
    chmod -R ug+w /tmp/images

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./tests/requirements.test.txt /tmp/requirements.txt
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Обходим ошибку "ImportError: attempted relative import beyond
# top-level package"
ENV PYTHONPATH="/usr/share/app:/usr/share/app/server_app:/usr/share/app/tests"

USER app_usr

#CMD ["pytest", "./"]
CMD ["/bin/bash"]
