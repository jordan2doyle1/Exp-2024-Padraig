#!/bin/bash
#
# Author: Jordan Doyle.
#

function format_caller() {
	echo "$(rev <<< "$2" | cut -d "/" -f1 | rev):$1"
}

function debug() {
	# Splitting is intentional, ignore warning.
	# shellcheck disable=SC2046
	echo "[DEBUG] ($(format_caller $(caller))) - $*"
}

function info() {
	# Splitting is intentional, ignore warning.
	# shellcheck disable=SC2046
	echo "[INFO] ($(format_caller $(caller))) - $*"
}

function warn() {
	# Splitting is intentional, ignore warning.
	# shellcheck disable=SC2046
	echo "[WARN] ($(format_caller $(caller))) - $*" >&2
}

function error() {
	# Splitting is intentional, ignore warning.
	# shellcheck disable=SC2046
	echo "[ERROR] ($(format_caller $(caller))) - $*" >&2
}
