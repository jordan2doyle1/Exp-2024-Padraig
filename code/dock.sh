#!/bin/bash
#
# Author: Jordan Doyle.
#

source log.sh
source util.sh

function check_docker_install() {
    if [[ ! "$(command -v docker)" ]]; then
        error "Docker is not installed on the host machine."
        exit 3
    fi

    if ! docker stats --no-stream > /dev/null 2>&1; then
        error "Docker deamon is not running on the host machine."
        exit 4
    fi
}

function remove_container() {
    info "Stopping container $1."
    docker stop "$1" > /dev/null
    info "Removing container $1."
    docker rm "$1" > /dev/null
}

function docker_cleanup() {
    info "Deleting existing images."
    if docker ps -a | grep -q "$1"; then
        info "Removing containers using image $1."
        containers="$(docker ps -a | grep "$1" | rev | cut -w -f 1 | rev)"
        read -ra container_array <<< "$containers"
        for container in "${container_array[@]}"; do
            remove_container "$container"
        done
    fi

    if docker image ls | grep -q "$1"; then
        info "Removing image $1."
        if ! docker image rm "$1" > /dev/null; then
            code=$?
            error "Failed to remove image $1 (Err: $code)."
            exit $((code))
        fi
    fi
}

function remove_existing_container() {      
    if docker ps -a | grep -q "$1"; then
        info "Container with the name '$1' already exists."
        remove_container "$1"
    fi
}

function docker_build() {
    info "Building docker image $1."
    docker build -t "$1" -f "$(readlink -f "$2")/Dockerfile" . 2>&1 | prepend
    code=${PIPESTATUS[0]}

    if [[ $code -ne 0 ]]; then
        error "Failed to build image $1 (Err: $code)."
        exit $((code))
    fi
}

function docker_pull() {
    if ! docker image ls | grep -q "$1"; then
        info "Pulling $1 image from docker repository."
        docker pull "$1" 2>&1 | prepend
        code=${PIPESTATUS[0]}

        if [[ $code -ne 0 ]]; then
            error "Failed to pull $1 image (Err: $code)."
            exit $((code))
        fi
    fi
}
