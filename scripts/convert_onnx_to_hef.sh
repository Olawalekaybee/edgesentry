#!/usr/bin/env bash
# ONNX → HEF conversion (v1 pipeline, kept here for completeness).
#
# Compiles an ONNX model to a Hailo Executable Format (.hef) file using the
# Hailo Dataflow Compiler. This is the documented pipeline from the Pi5 Edge AI
# Security Monitor — reproduce or import it here so the repo is self-contained.
#
# Prereqs: Hailo Dataflow Compiler + a calibration image set.
set -euo pipefail

ONNX="${1:?usage: convert_onnx_to_hef.sh <model.onnx> <calib_dir>}"
CALIB="${2:?provide a calibration image directory}"
OUT="${ONNX%.onnx}.hef"

echo "Parsing ${ONNX}…"
# hailo parser onnx "${ONNX}" --hw-arch hailo8l
echo "Optimizing with calibration set ${CALIB}…"
# hailo optimize <har> --calib-set-path "${CALIB}"
echo "Compiling to ${OUT}…"
# hailo compiler <optimized_har> --hw-arch hailo8l
echo "TODO: paste your exact v1 Hailo DFC commands above. Output: ${OUT}"
