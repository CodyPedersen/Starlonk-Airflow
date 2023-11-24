env:
	zsh -c "pip3 install ./requirements.txt"
    
build_push:
	zsh -c " \
	export DOCKER_DEFAULT_PLATFORM=linux/amd64; \
	docker build . -t codypedersen/starlonk_airflow:$(tag); \
	unset DOCKER_DEFAULT_PLATFORM; \
	docker push codypedersen/starlonk_airflow:$(tag)"

push:
	zsh -c "docker push codypedersen/starlonk_airflow:$(tag)"

deploy:
	#To do - set deploy file to update var

test:
	@echo "$(tag)"
