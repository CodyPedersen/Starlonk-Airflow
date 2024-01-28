repo=codypedersen
app=starlonk_airflow

env:
	zsh -c "pip3 install ./requirements.txt"

# Build with linux/amd64 for linux container compatibility
build_push:
	zsh -c " \
	export DOCKER_DEFAULT_PLATFORM=linux/amd64; \
	docker build . -t $(repo)/$(app):$(tag); \
	unset DOCKER_DEFAULT_PLATFORM; \
	docker push $(repo)/$(app):$(tag)"

push:
	zsh -c "docker push $(repo)/$(app):$(tag)"
