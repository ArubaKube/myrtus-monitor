.PHONY: build import-libs

build: import-libs
	@sh ./build_docker.sh

import-libs:
	@sh ./import_mirto_libs.sh