# Define custom function directory
ARG FUNCTION_DIR="/function"

FROM python:3.11 as build-image

# Include global arg in this stage of the build
ARG FUNCTION_DIR

RUN mkdir -p ${FUNCTION_DIR}

# Copy function code
COPY requirements.txt ${FUNCTION_DIR}
COPY app.py ${FUNCTION_DIR}
COPY utils ${FUNCTION_DIR}/utils
COPY config ${FUNCTION_DIR}/config

# Install the function's dependencies
RUN pip install --upgrade pip \
	&& pip install --no-cache-dir --target ${FUNCTION_DIR} -r ${FUNCTION_DIR}/requirements.txt \
	&& pip install --no-cache-dir --target ${FUNCTION_DIR} awslambdaric

# Copy into another image with only the necessary parts to reduce disk size. Smaller size should improve lambda load time performance
FROM python:3.11-slim-bookworm

# Include global arg in this stage of the build
ARG FUNCTION_DIR

RUN mkdir -p ${FUNCTION_DIR}

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

# Set runtime interface client as default command for the container runtime
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]

# Pass the name of the function handler as an argument to the runtime
CMD [ "app.lambda_handler" ]