#!/bin/bash
#
# Author: Jordan Doyle.
#

source log.sh

function check_acv_installation() {
    if ! acv -h | grep -q "acv"; then
        error "ACVTool is not configured correctly or not installed."
        exit 3
    fi
}

function acv_instrument() {
	local app_name
    app_name=$(basename "$1" .apk)

    acv_apk="$2/acv_$app_name.apk"
    instrument_log="$2/acv_instrument.log"
    pickle="$2/acv_$app_name.pickle"

    if [[ ! -f "$instrument_log" ]] || [[ ! -f "$acv_apk" ]] || \
            [[ ! -f "$pickle" ]]; then
        info "Instrumenting APK with ACV."
        acv instrument -f "$1" | tee "$instrument_log" | prepend
        code=${PIPESTATUS[0]}

        if [[ $code -ne 0 ]]; then
            error "Failed to instrument APK with ACV (Err: $code)."
            exit $((code))
        fi

        iapk=$(grep "apk instrumented: " < "$instrument_log" \
                | cut -d: -f2 \
                | tr -d '[:blank:]' \
             )
        info "ACV instrumented APK file at $iapk."
        info "Moving ACV APK to output directory."
        mv "$iapk" "$acv_apk"

        ipickle=$(grep "pickle file saved: " < "$instrument_log" \
               | cut -d: -f2 \
               | tr -d '[:blank:]' \
            )
        info "ACV pickle file at $ipickle."
        info "Moving ACV pickle file to output directory."
        mv "$ipickle" "$pickle"
    fi

    package=$(grep "package name: " < "$instrument_log" \
                | cut -d: -f2 \
                | tr -d '[:blank:]' \
             )
    info "Package of instrumented APK is '$package'."

    if [[ ! -f "$acv_apk" ]] || [[ ! -f "$pickle" ]]; then
        error "The ACV instrumented APK or pickle file does not exist."
        exit 4
    fi
}

function acv_install() {
	info "Installing ACV instrumented APK $1."
	acv install "$1" | prepend
	code=${PIPESTATUS[0]}

	if [[ $code -ne 0 ]]; then
	    error "Failed to install ACV instrumented APK $1 (Err: $code)."
	    exit $((code))
	fi
}

function acv_start() {
	start_log="$2/acv_start_$3.log"
	info "Starting ACV coverage for package $1."
	nohup acv start "$1" >> start_log 2>&1 &
	start_pid=$!
	info "Waiting 3 seconds for the app to start."
	sleep 3
}

function acv_stop() {
	info "Stopping ACV coverage for package $1."
	acv stop "$1" | prepend
	code=${PIPESTATUS[0]}

	if [[ $code -ne 0 ]]; then
	    error "Failed to stop ACV coverage for package $1 (Err: $code)"
	    exit $((code))
	fi
}

function acv_report() {
	report_log="$1/report_$2.log"
	info "Retrieving coverage report for the package $3."
	acv report "$3" -p "$4" | tee "$report_log" | prepend
	code=${PIPESTATUS[0]}

	if [[ $code -ne 0 ]]; then
	    error "ACV report generation failed for package $3 (Err: $code)"
	    exit $((code))
	fi

	report=$(tac < "$report_log" \
            | grep -m 1 "report saved: " \
            | cut -d: -f2 \
            | tr -d '[:blank:]' \
        )
	info "Report for test $2 with package $3 at '$report'."
	info "Moving report to $1."
	mv "$report" "$1/report_$2" 2>&1 | prepend
	code=${PIPESTATUS[0]}

	if [[ $code -ne 0 ]]; then
	    error "Failed to move report to the output directory (Err $code)."
	    exit $((code))
	fi
}

function move_acv_report() {
	report=$(grep "report saved: " < "$3" \
            | cut -d: -f2 \
            | tr -d '[:blank:]' \
        )
	info "Report for test $2 at '$report'."
	info "Moving report to output directory."
	mv "$report" "$1/report_$2" 2>&1 | prepend
	code=${PIPESTATUS[0]}

	if [[ $code -ne 0 ]]; then
	    error "Failed to move report to the output directory (Err $code)."
	    exit $((code))
	fi
}
