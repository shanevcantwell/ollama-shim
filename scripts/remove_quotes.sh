#!/bin/bash
sed -i '1s/^\"\"\"//' pyproject.toml
sed -i '$s/\"\"\"$//' pyproject.toml
