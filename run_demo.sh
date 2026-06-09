#!/bin/bash

# Ensure we're in the right directory
cd "$(dirname "$0")"

echo "====================================================="
echo "  TracePilot: Autonomous FinOps Routing via Phoenix  "
echo "====================================================="
echo ""

# Reset the memory database for a clean demo
echo "[System] Resetting Economic Memory to naive state..."
python -m tracepilot.main reset
echo ""

# Act 1: Cold Start (Naive Routing)
echo "=== ACT 1: COLD START (Naive Routing) ==="
echo "Query: 'Find employee handbook section 7.3'"
echo "TracePilot has no memory. It will guess and likely pick the wrong tool."
echo "Press ENTER to run..."
read
python -m tracepilot.main query "Find employee handbook section 7.3"

echo ""
echo "Notice the high latency and recovery cost. The initial tool failed."
echo ""

# Audit Phase
echo "=== AUDIT PHASE ==="
echo "Background Auditor reads Phoenix telemetry traces to discover inefficiencies."
echo "Press ENTER to run auditor..."
read
python -m tracepilot.main audit

echo ""
echo "Confidence scores updated based on operational reality."
echo ""

# Act 2: Learned State (Optimized Routing)
echo "=== ACT 2: LEARNED STATE (Optimized Routing) ==="
echo "Query: 'Find employee handbook section 8.1'"
echo "TracePilot now has Economic Memory. It should route optimally."
echo "Press ENTER to run..."
read
python -m tracepilot.main query "Find employee handbook section 8.1"

echo ""
echo "Notice the low latency and zero recovery cost. The routing was optimal."
echo ""

echo "=== DEMO COMPLETE ==="
echo "Check the Arize Phoenix UI at http://localhost:6006 to see the underlying traces."
