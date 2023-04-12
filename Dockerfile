# ================= BUILD BACKEND ==================
FROM python:3.11-alpine AS backend-builder

# Install the build system
RUN apk add --update git
RUN python -m pip install -U pip wheel
RUN python -m pip install build

# Copy the source code
COPY ./ /build

# Build the application
WORKDIR /build
RUN python -m build --wheel .

# ================= BUILD FRONTEND ==================
FROM node:lts-alpine as frontend-builder

# Copy the source code
ENV PATH /app/node_modules/.bin:$PATH
COPY ./ui /app

# Build the application
WORKDIR /app
RUN npm install
RUN npm run build

# =============== PRODUCTION ===============
FROM python:3.11-alpine

# Install the application
RUN apk add --update git gcc musl-dev bash

# Copy frontend build artifact
COPY --from=frontend-builder /app/dist/ /ui/
ENV FOXOPS_FRONTEND_DIST_DIR /ui

# Copy backend build artifact
COPY --from=backend-builder /build/dist/*.whl /tmp
RUN python -m pip install /tmp/*.whl
RUN rm -f /tmp/*.whl

# Add the application user
RUN addgroup --system foxops --gid 2102 \
    && adduser --system foxops --ingroup foxops --uid 2102 --home /home/foxops
USER foxops
WORKDIR /home/foxops

# Copy database migrations into the image, so that they can be applied
COPY ./alembic.ini alembic.ini
COPY ./alembic/versions alembic/versions
COPY ./alembic/env.py alembic/env.py

EXPOSE 8000
CMD [ "uvicorn", "foxops.__main__:create_app", "--factory", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000" ]
