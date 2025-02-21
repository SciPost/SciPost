FROM python:3.11-alpine AS base

# Install basic build dependencies
RUN apk add \
    git \
    g++ make \
    nodejs npm \
    # for geopandas
    gdal-dev geos-dev 

# Create node builder
FROM base AS node_deps

# Install node packages
COPY package.json package-lock.json webpack.*.js postcss.config.js .
RUN npm install

# Run webpack on the source code
COPY --chown=scipost:scipost . .
RUN npm run webpack-dev

# Create python builder
FROM base AS python_deps

RUN mkdir -p /app
WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN python3 -m venv venv && \ 
    source ./venv/bin/activate && \
    pip install --prefer-binary --no-cache-dir  -r requirements.txt
    
# Build the final image
FROM base AS final

# Create a non-root user named 'scipost' to run the app
RUN adduser -D scipost &&\
    mkdir -p /var/log/scipost && \ 
    mkdir -p /data/scipost/static && \ 
    chown -R scipost:scipost /var/log/scipost && \
    chown -R scipost:scipost /data/scipost

USER scipost
WORKDIR /app

# Copy the app and dependencies from the previous stages
COPY --chown=scipost:scipost . /app
COPY --from=python_deps --chown=scipost:scipost /app/venv /app/venv
COPY --from=node_deps --chown=scipost:scipost ./node_modules /app/node_modules 
COPY --from=node_deps --chown=scipost:scipost ./static_bundles /app/static_bundles 
COPY --from=node_deps --chown=scipost:scipost ./webpack-stats.json /app/webpack-stats.json

