#!/bin/bash
mkdir -p libs/mirto-lib
cp -r ../development-environment/mirto-lib/ ./libs/mirto-lib/
uv pip install ./libs/mirto-lib/
