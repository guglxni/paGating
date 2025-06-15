#!/usr/bin/env bash

# --- Configuration ---
VALID_UNITS=("paGLU" "paGTU" "paSwishU" "paReGLU" "paGELU" "paMishU" "paSiLU" "paGRU")
LOG_DIR="logs"
VERIFY_SCRIPT="./verify_pagating.sh"

# --- Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m' # For warnings or info
NC='\033[0m' # No Color

# --- Check if verify script exists and is executable ---
if [[ ! -f "$VERIFY_SCRIPT" ]]; then
  echo -e "${RED}❌ Error: Verification script '$VERIFY_SCRIPT' not found.${NC}"
  exit 1
fi
if [[ ! -x "$VERIFY_SCRIPT" ]]; then
  echo -e "${RED}❌ Error: Verification script '$VERIFY_SCRIPT' is not executable.${NC}"
  echo -e "${YELLOW}Run: chmod +x $VERIFY_SCRIPT${NC}"
  exit 1
fi

# --- Create Log Directory ---
mkdir -p "$LOG_DIR"
echo -e "📝 Log directory ensured: $LOG_DIR"

# --- Array to Store Failure Status (0=Success, 1=Failure) ---
declare -a failure_flags # Use a simple indexed array
unit_count=${#VALID_UNITS[@]}
for (( i=0; i<$unit_count; i++ )); do
  failure_flags[$i]=0 # Initialize all to success
done

# --- Main Loop ---
echo ""
echo "🚀 Starting verification for all paGating units..."
echo "=================================================="

processed_count=0
unit_index=0

for unit in "${VALID_UNITS[@]}"; do
  processed_count=$((processed_count + 1))
  LOG_FILE="${LOG_DIR}/verify_${unit}.log"
  
  echo -e "\n[${processed_count}/${unit_count}] Verifying unit: ${YELLOW}${unit}${NC} (Log: ${LOG_FILE})"
  
  # Run the verification script for the current unit, redirecting stdout and stderr
  "$VERIFY_SCRIPT" --unit "$unit" &> "$LOG_FILE"
  
  # Check the exit status of the verification script
  exit_status=$?
  
  if [[ $exit_status -eq 0 ]]; then
    echo -e "${GREEN}✅ Success:${NC} Verification passed for ${unit}."
    # failure_flags[$unit_index] remains 0
  else
    echo -e "${RED}❌ Failure:${NC} Verification failed for ${unit}. Check log: ${LOG_FILE}"
    failure_flags[$unit_index]=1 # Mark as failed
  fi
  echo "--------------------------------------------------"
  unit_index=$((unit_index + 1))
done

# --- Final Summary ---
echo ""
echo "🏁 Verification Summary 🏁"
echo "=================================================="
printf "%-10s | %-6s\n" "Unit" "Status"
echo "-----------|---------"
overall_success=1
unit_index=0
for unit in "${VALID_UNITS[@]}"; do
  status_flag=${failure_flags[$unit_index]}
  if [[ $status_flag -eq 0 ]]; then
    printf "%-10s | ${GREEN}%-6s${NC}\n" "$unit" "PASS"
  else
    printf "%-10s | ${RED}%-6s${NC}\n" "$unit" "FAIL"
    overall_success=0 # Mark overall as failed if any unit fails
  fi
  unit_index=$((unit_index + 1))
done
echo "=================================================="

if [[ $overall_success -eq 1 ]]; then
  echo -e "${GREEN}✅ All units verified successfully.${NC}"
  exit 0
else
  echo -e "${RED}❌ Some units failed verification. Please check the logs in the '$LOG_DIR' directory.${NC}"
  exit 1 # Exit with non-zero status if any unit failed
fi 