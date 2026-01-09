#!/bin/bash
# Manual API Tests for PetInsure360 Backend
# Run this script with the backend server running on port 3002

BASE_URL="http://localhost:3002"
RESULTS_FILE="/tmp/petinsure360_test_results.txt"

echo "PetInsure360 Backend API Tests" > $RESULTS_FILE
echo "===============================" >> $RESULTS_FILE
echo "Test Date: $(date)" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE

test_count=0
pass_count=0
fail_count=0

# Function to run test and report result
run_test() {
    local test_name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=$5

    test_count=$((test_count + 1))
    echo "Test $test_count: $test_name" >> $RESULTS_FILE

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X $method -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint" 2>&1)
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" == "$expected_status" ]; then
        echo "  PASS - Status: $http_code" >> $RESULTS_FILE
        pass_count=$((pass_count + 1))
    else
        echo "  FAIL - Expected: $expected_status, Got: $http_code" >> $RESULTS_FILE
        echo "  Response: $body" >> $RESULTS_FILE
        fail_count=$((fail_count + 1))
    fi
    echo "" >> $RESULTS_FILE
}

echo "Running Tests..." >> $RESULTS_FILE
echo "" >> $RESULTS_FILE

# Health Check Tests
echo "=== Health Check Tests ===" >> $RESULTS_FILE
run_test "Root endpoint health check" "GET" "/" "" "200"
run_test "Health endpoint check" "GET" "/health" "" "200"

# Customer API Tests
echo "=== Customer API Tests ===" >> $RESULTS_FILE
run_test "Get demo customer by email" "GET" "/api/customers/lookup?email=demo@demologin.com" "" "200"
run_test "Get customer by ID" "GET" "/api/customers/DEMO-001" "" "200"
run_test "Get non-existent customer" "GET" "/api/customers/INVALID-ID" "" "404"

# Pets API Tests
echo "=== Pets API Tests ===" >> $RESULTS_FILE
run_test "Get pets for customer" "GET" "/api/pets/customer/DEMO-001" "" "200"
run_test "Get pet by ID" "GET" "/api/pets/PET-DEMO-001" "" "200"
run_test "Get non-existent pet" "GET" "/api/pets/INVALID-PET-ID" "" "404"

# Policies API Tests
echo "=== Policies API Tests ===" >> $RESULTS_FILE
run_test "Get policies for customer" "GET" "/api/policies/customer/DEMO-001" "" "200"
run_test "Get policies for pet" "GET" "/api/policies/pet/PET-DEMO-001" "" "200"
run_test "Get available plans" "GET" "/api/policies/plans/available" "" "200"
run_test "Validate policy for pet" "GET" "/api/policies/validate/POL-DEMO-001/PET-DEMO-001" "" "200"

# Claims API Tests
echo "=== Claims API Tests ===" >> $RESULTS_FILE
run_test "Get claims for customer" "GET" "/api/claims/customer/DEMO-001" "" "200"

# Insights API Tests
echo "=== Insights API Tests ===" >> $RESULTS_FILE
run_test "Get summary statistics" "GET" "/api/insights/summary" "" "200"
run_test "Get KPIs" "GET" "/api/insights/kpis" "" "200"
run_test "Get customers list" "GET" "/api/insights/customers" "" "200"
run_test "Get customer 360 view" "GET" "/api/insights/customers/DEMO-001" "" "200"
run_test "Get claims analytics" "GET" "/api/insights/claims" "" "200"
run_test "Get provider performance" "GET" "/api/insights/providers" "" "200"
run_test "Get risk scores" "GET" "/api/insights/risks" "" "200"
run_test "Get cross-sell opportunities" "GET" "/api/insights/cross-sell" "" "200"
run_test "Get customer segments" "GET" "/api/insights/segments" "" "200"

# Pipeline API Tests
echo "=== Pipeline API Tests ===" >> $RESULTS_FILE
run_test "Get pipeline status" "GET" "/api/pipeline/status" "" "200"
run_test "Get pipeline flow" "GET" "/api/pipeline/flow" "" "200"
run_test "Get pending claims" "GET" "/api/pipeline/pending" "" "200"
run_test "Get pipeline metrics" "GET" "/api/pipeline/metrics" "" "200"
run_test "Get fraud scenarios" "GET" "/api/pipeline/fraud-scenarios" "" "200"

echo "===============================" >> $RESULTS_FILE
echo "Test Summary" >> $RESULTS_FILE
echo "Total Tests: $test_count" >> $RESULTS_FILE
echo "Passed: $pass_count" >> $RESULTS_FILE
echo "Failed: $fail_count" >> $RESULTS_FILE
echo "Success Rate: $(awk "BEGIN {printf \"%.2f%%\", ($pass_count/$test_count)*100}")" >> $RESULTS_FILE
echo "===============================" >> $RESULTS_FILE

cat $RESULTS_FILE
