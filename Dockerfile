FROM python:3.11.9-slim

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
# Install LibreOffice and essential dependencies
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-java-common \
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Set working directory
WORKDIR /app
# RUN libreoffice --headless --convert-to html:"HTML (StarWriter)" --help
# RUN unopkg add --shared -f -v ./writer2xhtml.oxt
# Copy conversion script
COPY . .
RUN pip3 install -r requirements-dev.txt

# Copy and make conversion script executable

# Create directories for input/output
RUN mkdir -p /input /output

RUN chmod +x ./scripts/convert.sh