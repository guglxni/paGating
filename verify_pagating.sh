#!/usr/bin/env bash

# Stop script on any error
set -e

# --- Default Values ---
INPUT_DIM=64
HIDDEN_DIM=64
ALPHA=0.5
UNIT_NAME=""
VALID_UNITS=("paGLU" "paGTU" "paSwishU" "paReGLU" "paGELU" "paMishU" "paSiLU" "paGRU")

# --- Usage Function ---
usage() {
  cat <<EOF
Usage: $0 --unit <unit_name> [options]

Runs verification steps for a specified paGating unit.

Required Arguments:
  --unit <unit_name>    The paGating unit to verify.
                        Valid options: ${VALID_UNITS[*]}

Optional Arguments:
  --input-dim <int>     Input dimension for export scripts (default: $INPUT_DIM)
  --hidden-dim <int>    Hidden dimension for export scripts (default: $HIDDEN_DIM)
                        (Note: Used as output dim for non-RNN units in export)
  --alpha <float>       Static alpha value for export scripts (default: $ALPHA)
  --help                Display this help message and exit.
EOF
  exit 1
}

# --- Argument Parsing ---
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --unit)
      UNIT_NAME="$2"
      shift # past argument
      shift # past value
      ;;
    --input-dim)
      INPUT_DIM="$2"
      shift # past argument
      shift # past value
      ;;
    --hidden-dim)
      HIDDEN_DIM="$2"
      shift # past argument
      shift # past value
      ;;
    --alpha)
      ALPHA="$2"
      shift # past argument
      shift # past value
      ;;
    --help)
      usage
      ;;
    *)    # unknown option
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

# --- Validate Unit Name ---
is_valid=0
if [[ -n "$UNIT_NAME" ]]; then
  for valid_unit in "${VALID_UNITS[@]}"; do
    if [[ "$UNIT_NAME" == "$valid_unit" ]]; then
      is_valid=1
      break
    fi
  done
fi

if [[ $is_valid -eq 0 ]]; then
  echo "❌ Invalid or missing unit name."
  echo "Valid options: ${VALID_UNITS[*]}"
  exit 1
fi

echo "🚀 Starting verification for unit: $UNIT_NAME"
echo "   Input Dim: $INPUT_DIM"
echo "   Hidden Dim: $HIDDEN_DIM"
echo "   Alpha: $ALPHA"

# --- Create Output Directory ---
mkdir -p build/models
echo "Ensured output directory exists: build/models"

# --- Step 1: Run Example Training Script ---
echo ""
echo "==> Step 1: Running Example Training Script"
# Convert unit name to lowercase for example script filename convention
LC_UNIT_NAME=$(echo "$UNIT_NAME" | tr '[:upper:]' '[:lower:]')
EXAMPLE_SCRIPT="examples/train_${LC_UNIT_NAME}_example.py"
if [[ -f "$EXAMPLE_SCRIPT" ]]; then
    echo "Running: python $EXAMPLE_SCRIPT"
    python "$EXAMPLE_SCRIPT"
    echo "✅ Example script completed."
else
    echo "⚠️ Warning: Example script not found at $EXAMPLE_SCRIPT. Skipping."
    # Consider exiting here if the example script MUST exist for verification
    # exit 1 
fi


# --- Step 2: Run Experiment Pipeline (Sweep + Transformer) ---
echo ""
echo "==> Step 2: Running Experiment Pipeline (Sweep + Transformer)"
echo "Running: python scripts/run_experiment_pipeline.py --units $UNIT_NAME --include_transformer"
python scripts/run_experiment_pipeline.py --units "$UNIT_NAME" --include_transformer
echo "✅ Experiment pipeline completed." # Note: This might report success even if sub-scripts had issues logged above.

# --- Step 3: Export to CoreML ---
echo ""
echo "==> Step 3: Exporting to CoreML"
COREML_OUTPUT="build/models/${UNIT_NAME}_alpha${ALPHA}.mlpackage"
echo "Running: python scripts/coreml_export.py --unit $UNIT_NAME --input-dim $INPUT_DIM --hidden-dim $HIDDEN_DIM --alpha $ALPHA --output $COREML_OUTPUT"
python scripts/coreml_export.py --unit "$UNIT_NAME" --input-dim "$INPUT_DIM" --hidden-dim "$HIDDEN_DIM" --alpha "$ALPHA" --output "$COREML_OUTPUT"
echo "✅ CoreML export completed."

# --- Step 4: Export to ONNX and Verify ---
echo ""
echo "==> Step 4: Exporting to ONNX and Verifying"
ONNX_OUTPUT="build/models/${UNIT_NAME}_alpha${ALPHA}.onnx"
echo "Running: python scripts/onnx_export.py --unit $UNIT_NAME --input-dim $INPUT_DIM --hidden-dim $HIDDEN_DIM --alpha $ALPHA --verify --output $ONNX_OUTPUT"
python scripts/onnx_export.py --unit "$UNIT_NAME" --input-dim "$INPUT_DIM" --hidden-dim "$HIDDEN_DIM" --alpha "$ALPHA" --verify --output "$ONNX_OUTPUT"
echo "✅ ONNX export and verification completed."

# --- Completion ---
echo ""
echo "✅ All verification steps completed for $UNIT_NAME."

exit 0 