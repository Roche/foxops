FROM python:3.10-alpine AS builder

# Install the build system
RUN apk add --update git gcc musl-dev
RUN python -m pip install -U pip wheel
RUN python -m pip install build

# Copy the source code
COPY ./ /build

# Build the application
WORKDIR /build
RUN python -m build --wheel .


# =============== PRODUCTION ===============
FROM builder AS production

# Copy the build artifact
COPY --from=builder /build/dist/*.whl /tmp

# Install the application
RUN python -m pip install /tmp/*.whl

ENTRYPOINT [ "foxops" ]