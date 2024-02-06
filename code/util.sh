#!/bin/bash
#
# Author: Jordan Doyle.
#

source log.sh
source setting.sh

function wait_for_emulator_bootup() {
    log_update=true
    wait_counter=0

    while true; do
        if adb shell getprop sys.boot_completed > /dev/null 2>&1; then
            if $log_update; then
                info "Emulator booting up."
                log_update=false
            fi

            if adb shell getprop init.svc.bootanim | grep -q "stopped"; then
                info "Emulator finished booting."
                break
            fi
        fi

        sleep 1
        wait_counter=$((wait_counter+1))

        if [[ $wait_counter -eq 300 ]]; then
            error "Emulator failed to boot. Timed out (5m)."
            exit 3
        fi
    done
}

function launch_emulator() {
    info "Launching the Android Emulator."
    nohup emulator -avd "$1" -wipe-data -no-audio -no-window > "$2" 2>&1 &
    info "Waiting for emulator to start."
    wait_for_emulator_bootup
    info "Waiting 10 seconds, some servers are a bit slow."
    sleep 10
}

function grant_app_permissions() {
    info "Granting permissions to $1."
    permissions=$(aapt d permissions "$2")
    while read -r line; do
        if grep -q "uses-permission: name=" <<< "$line"; then
            permission=$(cut -d'=' -f2 <<< "$line")
            info "Granting permission $permission."
            adb shell pm grant "$1" "$permission" &> /dev/null
            code=$? 

            if [[ $code -ne 0 ]]; then
                warn "Could not grant permission $permission."
            fi
        fi
    done <<< "$permissions"
}

function prepend() { 
    while read -r line; do
        printf "\t-> %s\n" "$line"
    done; 
}

function check_output_exists() {
    if [[ -z "$output" ]]; then
        error "Output directory has not been provided."
        exit 4
    fi 

    if [[ ! -d $output ]]; then
        error "Output directory '$output' does not exist."
        exit 5
    fi
}

function log_execution_time() {
    date_command='date'
    if [[ $OSTYPE == darwin* ]]; then
        date_command='gdate'
    fi

    local time
    time=$($date_command -d@$SECONDS -u +%H:%M:%S)
    info "Execution time: $time."
}

function check_apk_exists() {
    if [[ -z "$apk" ]]; then
        error "APK file has not been provided."
        exit 6
    fi

    if [[ ! -f "$apk" ]] || [[ "$apk" != *.apk ]]; then
        error "APK file ($apk) does not exist."
        exit 7
    fi
}

function format_app_title() {
    sed 's/\([a-z]*\)_[0-9]*/\u\1 /g; s/ $//' <<< "$1"
}

function check_task_exists() {
    if [[ -z "$task" ]]; then
        error "Task has not been provided."
        exit 8
    fi

    if [[ ! -f "$task" ]]; then
        error "Task '$task' executable does not exist."
        exit 9
    fi
}

function get_input_apk() {
    local app_name
    app_name=$(basename "$2" .apk)

    local app_title
    app_title=$(format_app_title "$app_name")

    local iapk
    iapk="$output/$results_dir_name/$app_name/instrument/$app_name.apk"

    local return
    return=$1

    if [ -f "$iapk" ]; then
        info "Using instrumented APK for $app_title."
        eval "$return"="$iapk"
    else
        warn "Using original APK for $app_title."
        eval "$return"="$2"
    fi
}
