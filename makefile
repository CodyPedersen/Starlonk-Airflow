env:
	zsh -c "pip3 install ./requirements.txt"
    
build_image_m1:
	zsh -c " \
	export DOCKER_DEFAULT_PLATFORM=linux/amd64; \
	docker build . -t codypedersen/starlonk_airflow:$(tag); \
	unset DOCKER_DEFAULT_PLATFORM \
	echo $(tag)"

push:
	zsh -c "docker push codypedersen/starlonk_airflow:$(tag)"

deploy:
	#To do - set deploy file to update var

test:
	@echo "$(tag)"
