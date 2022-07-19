# ================= BUILD ==================
FROM python:3.10-alpine AS builder

# Install the build system
RUN apk add --update git
RUN python -m pip install -U pip wheel
RUN python -m pip install build

# Copy the source code
COPY ./ /build

# Build the application
WORKDIR /build
RUN python -m build --wheel .


# =============== PRODUCTION ===============
FROM python:3.10-alpine

# Copy the build artifact
COPY --from=builder /build/dist/*.whl /tmp

# Install the application
RUN apk add --update git gcc musl-dev bash
RUN python -m pip install /tmp/*.whl
RUN rm -f /tmp/*.whl

ENTRYPOINT [ "foxops" ]