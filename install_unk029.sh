#!/bin/bash

# Script to install unk029 package from Nexus in FastAPI environment

set -e

echo "Installing unk029 package from Nexus..."

# Extract password from .env using python
PASS=$(python3 -c "
import os
with open('.env') as f:
    for line in f:
        if line.startswith('PYPI_PASSWORD='):
            print(line.split('=',1)[1].strip().strip('\"\''))
            break
")

# Install unk029 from Nexus using uv pip
uv pip install --index-url "https://trainee:$PASS@nexus.openconsultinguk.com/repository/sandbox/simple" unk029

echo "unk029 installed successfully."

# Verify installation
uv run python -c "import unk029; print('unk029 version:', unk029.__version__)"
echo "Verification complete."