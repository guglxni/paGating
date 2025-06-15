#!/bin/bash
# run_tests.sh - Automated test runner with coverage reporting for the paGating project

set -e  # Exit on error
set -o pipefail  # Ensure pipe failures are propagated

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories and paths
PROJECT_ROOT=$(pwd)
TESTS_DIR="${PROJECT_ROOT}/tests"
COVERAGE_HTML_DIR="${TESTS_DIR}/coverage_html"
LOG_FILE="${TESTS_DIR}/test_results.log"
BENCHMARK_DIR="${PROJECT_ROOT}/benchmarks/norm_variants"

# Determine Python executable to use
# First try the system Python that has the packages installed
if command -v python3 &>/dev/null && python3 -c "import pytest" &>/dev/null; then
    PYTHON_CMD="python3"
# Otherwise use the default python (which might be from conda)
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: No Python executable found.${NC}"
    exit 1
fi

echo -e "${BLUE}==== paGating Test Runner ====${NC}"
echo "Started at: $(date)"
echo "Using Python: $(${PYTHON_CMD} --version)"
echo "Python path: $(which ${PYTHON_CMD})"
echo "Running tests with coverage tracking..."

# Ensure log directory exists
mkdir -p "${TESTS_DIR}"
mkdir -p "${BENCHMARK_DIR}"

# Step 1: Check and install dependencies if needed
check_and_install_dependency() {
    local pkg="$1"
    local pip_pkg="${2:-$1}"  # Default pip package name to the package name if not specified
    
    if ! ${PYTHON_CMD} -c "import $pkg" &>/dev/null; then
        echo -e "${YELLOW}Installing required dependency: $pip_pkg${NC}"
        ${PYTHON_CMD} -m pip install "$pip_pkg"
    fi
}

check_and_install_dependency pytest
check_and_install_dependency pytest_cov pytest-cov
check_and_install_dependency coverage
check_and_install_dependency torch
check_and_install_dependency numpy
check_and_install_dependency matplotlib

# Try to install optional dependencies
install_optional_dependency() {
    local pkg="$1"
    local pip_pkg="${2:-$1}"
    
    if ! ${PYTHON_CMD} -c "import $pkg" &>/dev/null; then
        echo -e "${YELLOW}Attempting to install optional dependency: $pip_pkg${NC}"
        ${PYTHON_CMD} -m pip install "$pip_pkg" || echo -e "${YELLOW}Optional dependency $pip_pkg could not be installed. Some tests may be skipped.${NC}"
    fi
}

install_optional_dependency coremltools
install_optional_dependency onnx
install_optional_dependency onnxruntime

# Check for tee
if ! command -v tee &>/dev/null; then
    echo -e "${YELLOW}Warning: 'tee' command not found. Will save logs directly.${NC}"
    HAS_TEE=false
else
    HAS_TEE=true
fi

# Step 2: Run the complete test suite with coverage tracking
echo -e "${BLUE}Running tests with coverage tracking...${NC}"

# Create the command to run
TEST_CMD="${PYTHON_CMD} -m pytest tests/ -v --tb=short --cov=paGating --cov-report=term-missing --cov-report=html:${COVERAGE_HTML_DIR}"

# Run the tests and collect output
if [ "$HAS_TEE" = true ]; then
    ${TEST_CMD} 2>&1 | tee "${LOG_FILE}"
    TEST_EXIT_CODE=${PIPESTATUS[0]}  # Capture the exit code of pytest, not tee
else
    ${TEST_CMD} > "${LOG_FILE}" 2>&1
    TEST_EXIT_CODE=$?
fi

# Step 3: Run the normalization integration tests specifically
echo -e "${BLUE}Running normalization integration tests...${NC}"
NORM_TEST_CMD="${PYTHON_CMD} -m pytest tests/test_norm_integration.py -v"

if [ "$HAS_TEE" = true ]; then
    ${NORM_TEST_CMD} 2>&1 | tee -a "${LOG_FILE}"
    NORM_TEST_EXIT_CODE=${PIPESTATUS[0]}
else
    ${NORM_TEST_CMD} >> "${LOG_FILE}" 2>&1
    NORM_TEST_EXIT_CODE=$?
fi

# Step 4: Run ONNX export tests if onnx is available
if ${PYTHON_CMD} -c "import onnx" &>/dev/null && ${PYTHON_CMD} -c "import onnxruntime" &>/dev/null; then
    echo -e "${BLUE}Running ONNX normalization export tests...${NC}"
    ONNX_TEST_CMD="${PYTHON_CMD} -m pytest tests/test_onnx_norm_export.py -v"
    
    if [ "$HAS_TEE" = true ]; then
        ${ONNX_TEST_CMD} 2>&1 | tee -a "${LOG_FILE}"
        ONNX_TEST_EXIT_CODE=${PIPESTATUS[0]}
    else
        ${ONNX_TEST_CMD} >> "${LOG_FILE}" 2>&1
        ONNX_TEST_EXIT_CODE=$?
    fi
else
    echo -e "${YELLOW}Skipping ONNX export tests (onnx and/or onnxruntime not installed)${NC}"
    ONNX_TEST_EXIT_CODE=0  # Don't fail if optional dependency is missing
fi

# Step 5: Run CoreML export tests if coremltools is available
if ${PYTHON_CMD} -c "import coremltools" &>/dev/null; then
    echo -e "${BLUE}Running CoreML normalization export tests...${NC}"
    COREML_TEST_CMD="${PYTHON_CMD} -m pytest tests/test_coreml_norm_export.py -v"
    
    if [ "$HAS_TEE" = true ]; then
        ${COREML_TEST_CMD} 2>&1 | tee -a "${LOG_FILE}"
        COREML_TEST_EXIT_CODE=${PIPESTATUS[0]}
    else
        ${COREML_TEST_CMD} >> "${LOG_FILE}" 2>&1
        COREML_TEST_EXIT_CODE=$?
    fi
else
    echo -e "${YELLOW}Skipping CoreML export tests (coremltools not installed)${NC}"
    COREML_TEST_EXIT_CODE=0  # Don't fail if optional dependency is missing
fi

# Step 6: Run benchmark with normalization options
echo -e "${BLUE}Running benchmark with normalization options...${NC}"
BENCHMARK_CMD="${PYTHON_CMD} experiments/benchmark_gateflow.py --device cpu --unit paGLU --use-gate-norm --pre-norm --post-norm --output-dir ${BENCHMARK_DIR}"

if [ "$HAS_TEE" = true ]; then
    ${BENCHMARK_CMD} 2>&1 | tee -a "${LOG_FILE}"
    BENCHMARK_EXIT_CODE=${PIPESTATUS[0]}
else
    ${BENCHMARK_CMD} >> "${LOG_FILE}" 2>&1
    BENCHMARK_EXIT_CODE=$?
fi

# Step 7a: Run the run_unit_tests test
echo -e "${BLUE}Running run_unit_tests tests...${NC}"
UNIT_TESTS_CMD="${PYTHON_CMD} -m pytest tests/test_run_unit_tests.py -v"

if [ "$HAS_TEE" = true ]; then
    ${UNIT_TESTS_CMD} 2>&1 | tee -a "${LOG_FILE}"
    UNIT_TESTS_EXIT_CODE=${PIPESTATUS[0]}
else
    ${UNIT_TESTS_CMD} >> "${LOG_FILE}" 2>&1
    UNIT_TESTS_EXIT_CODE=$?
fi

# Step 7: Export paGLU with all norm options to verify export pipeline
echo -e "${BLUE}Testing export of paGLU with all normalization options...${NC}"

# Determine available export methods
EXPORT_CMDS=()

# Test CoreML export if available
if ${PYTHON_CMD} -c "import coremltools" &>/dev/null; then
    EXPORT_CMDS+=("${PYTHON_CMD} coreml_export.py --unit paGLU --alpha 0.5 --use-gate-norm --pre-norm --post-norm")
fi

# Test ONNX export if available
if ${PYTHON_CMD} -c "import onnx" &>/dev/null; then
    EXPORT_CMDS+=("${PYTHON_CMD} onnx_export.py --unit paGLU --alpha 0.5 --use-gate-norm --pre-norm --post-norm")
fi

EXPORT_EXIT_CODE=0
for CMD in "${EXPORT_CMDS[@]}"; do
    echo "Running: $CMD"
    if [ "$HAS_TEE" = true ]; then
        $CMD 2>&1 | tee -a "${LOG_FILE}"
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            EXPORT_EXIT_CODE=1
        fi
    else
        $CMD >> "${LOG_FILE}" 2>&1
        if [ $? -ne 0 ]; then
            EXPORT_EXIT_CODE=1
        fi
    fi
done

# Step 8: Display results and open HTML report
echo ""
if [ ${TEST_EXIT_CODE} -eq 0 ] && [ ${NORM_TEST_EXIT_CODE} -eq 0 ] && [ ${ONNX_TEST_EXIT_CODE} -eq 0 ] && [ ${COREML_TEST_EXIT_CODE} -eq 0 ] && [ ${BENCHMARK_EXIT_CODE} -eq 0 ] && [ ${UNIT_TESTS_EXIT_CODE} -eq 0 ] && [ ${EXPORT_EXIT_CODE} -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed.${NC}"
else
    echo -e "${RED}❌ Some tests failed. See ${LOG_FILE} for details.${NC}"
    echo -e "${YELLOW}Test exit codes:${NC}"
    echo -e "  Main tests: ${TEST_EXIT_CODE}"
    echo -e "  Norm integration tests: ${NORM_TEST_EXIT_CODE}"
    echo -e "  ONNX export tests: ${ONNX_TEST_EXIT_CODE}"
    echo -e "  CoreML export tests: ${COREML_TEST_EXIT_CODE}"
    echo -e "  Benchmark: ${BENCHMARK_EXIT_CODE}"
    echo -e "  Unit tests for run_unit_tests.py: ${UNIT_TESTS_EXIT_CODE}"
    echo -e "  Export tests: ${EXPORT_EXIT_CODE}"
fi

# Display coverage summary from the log file
if [ -f "${LOG_FILE}" ]; then
    echo -e "${BLUE}Coverage Summary:${NC}"
    grep -A 10 "TOTAL" "${LOG_FILE}" | head -n 7 || true
fi

# Step 9: Open the HTML report in the default browser
echo -e "${BLUE}Coverage HTML report generated at: ${COVERAGE_HTML_DIR}/index.html${NC}"

# Determine the appropriate open command based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    OPEN_CMD="open"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v xdg-open &>/dev/null; then
        OPEN_CMD="xdg-open"
    elif command -v gnome-open &>/dev/null; then
        OPEN_CMD="gnome-open"
    else
        echo -e "${YELLOW}Could not find a suitable command to open the browser. Please open the HTML report manually.${NC}"
        OPEN_CMD=""
    fi
else
    # Unknown OS
    echo -e "${YELLOW}Unknown operating system. Please open the HTML report manually.${NC}"
    OPEN_CMD=""
fi

# Open the HTML report if a command is available
if [ -n "$OPEN_CMD" ] && [ -f "${COVERAGE_HTML_DIR}/index.html" ]; then
    echo "Opening HTML report in browser..."
    ${OPEN_CMD} "${COVERAGE_HTML_DIR}/index.html" || echo -e "${YELLOW}Failed to open browser. Please open the HTML report manually.${NC}"
fi

echo ""
echo "Test run completed at: $(date)"
echo -e "${BLUE}Test results saved to: ${LOG_FILE}${NC}"
echo -e "${BLUE}Benchmark results saved to: ${BENCHMARK_DIR}${NC}"

# Calculate final exit code (non-zero if any test failed)
FINAL_EXIT_CODE=$(( TEST_EXIT_CODE + NORM_TEST_EXIT_CODE + ONNX_TEST_EXIT_CODE + COREML_TEST_EXIT_CODE + BENCHMARK_EXIT_CODE + UNIT_TESTS_EXIT_CODE + EXPORT_EXIT_CODE ))

# Exit with the calculated exit code to indicate success/failure
exit $(( FINAL_EXIT_CODE > 0 ? 1 : 0 ))