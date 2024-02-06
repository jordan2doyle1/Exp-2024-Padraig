#!/bin/bash
#
# Author: Jordan Doyle.
#

# Docker settings
export docker_output="/output"
export docker_working_dir="/app"

# Global settings
export build=false	# Delete docker image and re-build from scratch.
export clean=false	# Delete results and run tests from scratch.

# Test settings
export finish_count=1

# Monkey settings
export events=50
export seeds=(7598364 508328 5420736 8377926 102074 2617534 6305440 6211883 \
					4468766 8377198)
export seed=true

# Output settings
export results_dir_name="results"
export task_log_name="cmd.log"
