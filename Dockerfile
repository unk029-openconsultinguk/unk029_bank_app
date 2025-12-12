# Use a multi-stage build to reduce the size of the final image.
#   This example is optimized to reduce final image size rather than for simplicity.
# Using a -slim image also greatly reduces image size.
# It is possible to use -alpine images instead to further reduce image size, but this comes
# with several important caveats.
#   - Alpine images use MUSL rather than GLIBC (as used in the default Debian-based images).
#   - Most Python packages that require C code are tested against GLIBC, so there could be
#     subtle errors when using MUSL.
#   - These Python packages usually only provide binary wheels for GLIBC, so the packages
#     will need to be recompiled fully within the container images, increasing build times.
FROM python:3.12-slim-bookworm AS python_builder

# Pin uv to a specific version to make container builds reproducible.
ENV UV_VERSION=0.8.8
ENV UV_PYTHON_DOWNLOADS=never

# Set ENV variables that make Python more friendly to running inside a container.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

# By default, pip caches copies of downloaded packages from PyPI. These are not useful within
# a contain image, so disable this to reduce the size of images.
ENV PIP_NO_CACHE_DIR=1
ENV WORKDIR=/src

WORKDIR ${WORKDIR}

# Install any system dependencies required to build wheels, such as C compilers or system packages
# For example:
#RUN apt-get update && apt-get install -y \
#    gcc \
#    && rm -rf /var/lib/apt/lists/*

# Install uv into the global environment to isolate it from the venv it creates.
RUN pip install "uv==${UV_VERSION}"

# Pre-download/compile wheel dependencies into a virtual environment.
# Doing this in a multi-stage build allows omitting compile dependencies from the final image.
# This must be the same path that is used in the final image as the virtual environment has
# absolute symlinks in it.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# Accept build args for Nexus authentication
ARG PYPI_HOST
ARG PYPI_USER
ARG PYPI_PASSWORD

# Copy in project dependency specification.
COPY pyproject.toml uv.lock ./

# Copy requirements-nexus.txt
COPY requirements-nexus.txt ./

# Copy in only bank_app source (unk029 comes from Nexus as a package)
COPY src/bank_app ./src/bank_app

# Install dependencies from Nexus and only bank_app locally
# Tell uv not to install the local project to ensure unk029 is pulled from Nexus.
RUN UV_EXTRA_INDEX_URL="https://${PYPI_USER}:${PYPI_PASSWORD}@${PYPI_HOST}/simple/" \
  uv sync --no-default-groups --no-install-project

# Copy in only bank_app source (unk029 comes from Nexus as a package)
COPY src/bank_app ./src/bank_app

## Final Image
# The image used in the final image MUST match exactly to the python_builder image.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

ENV HOME=/home/user
ENV APP_HOME=${HOME}/apps

# Create the home directory for the new user.
RUN mkdir -p ${HOME}

# Create the user so the program doesn't run as root. This increases security of the container.
RUN groupadd -r user && \
    useradd -r -g user -d ${HOME} -s /sbin/nologin -c "Container image user" user

# Setup application install directory.
RUN mkdir ${APP_HOME}

# If you use Docker Compose volumes, you might need to create the directories in the image,
# otherwise when Docker Compose creates them they are owned by the root user and are inaccessible
# by the non-root user. See https://github.com/docker/compose/issues/3270

WORKDIR ${APP_HOME}

# Copy and activate pre-built virtual environment.
COPY --from=python_builder ${UV_PROJECT_ENVIRONMENT} ${UV_PROJECT_ENVIRONMENT}
ENV PATH="${UV_PROJECT_ENVIRONMENT}/bin:${PATH}"

# Copy source files
COPY src src

# Add src to PYTHONPATH so bank_app module can be imported
ENV PYTHONPATH="${APP_HOME}/src:${PYTHONPATH}"

# Give access to the entire home folder to the new user so that files and folders can be written
# there. Some packages such as matplotlib, want to write to the home folder.
RUN chown -R user:user ${HOME}

# Run the FastAPI application using uvicorn
# Override CMD below for multi-service support
ENV SERVICE=fastapi
CMD ["sh", "-c", "case \"$SERVICE\" in \
  mcp_server) uvicorn bank_app.mcpserver:app --host 0.0.0.0 --port 8002 ;; \
  fastapi) uvicorn bank_app.api:app --host 0.0.0.0 --port 8001 ;; \
  dev_ui) adk web --host 0.0.0.0 --port 8003 --url_prefix /dev-ui ./src/bank_app ;; \
  *) echo \"Unknown service: $SERVICE\" && exit 1 ;; \
esac"]

USER user



