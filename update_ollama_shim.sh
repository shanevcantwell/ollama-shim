"#!/bin/bash

# Create backup of original file
cp ollama_shim.py ollama_shim.bak

cat > ollama_shim_new.py << 'EOF'
# [The complete content shown above]
EOF

# Verify the new file before replacing
echo "Verification: Compare ollama_shim.py and ollama_shim_new.py"
diff -u ollama_shim.py ollama_shim_new.py

# If you approve, run this to replace:
# mv ollama_shim.py ollama_shim.old && mv ollama_shim_new.py ollama_shim.py
"