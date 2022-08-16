# ================= BUILD BACKEND ==================
FROM python:3.10-alpine AS backend-builder

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
FROM python:3.10-alpine

# Install the application
RUN apk add --update git gcc musl-dev bash

# Copy frontend build artifact
COPY --from=frontend-builder /app/dist/ /ui/
ENV FOXOPS_FRONTEND_DIST_DIR /ui

# Copy backend build artifact
COPY --from=backend-builder /build/dist/*.whl /tmp
RUN python -m pip install /tmp/*.whl
RUN rm -f /tmp/*.whl

EXPOSE 80
CMD [ "uvicorn", "foxops.__main__:get_app", "--factory", "--proxy-headers", "--host", "0.0.0.0", "--port", "80" ]