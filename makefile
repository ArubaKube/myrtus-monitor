.PHONY: build import-libs

import-libs:
	@mkdir -p libs/mirto-lib
	@cp -r ../development-environment/mirto-lib/ ./libs/mirto-lib/
	@uv pip install ./libs/mirto-lib/

build: import-libs
	@docker build -f docker/Dockerfile -t ghcr.io/arubakube/myrtus-monitor .