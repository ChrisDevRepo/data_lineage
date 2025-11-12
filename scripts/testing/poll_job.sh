#!/bin/bash
JOB_ID="$1"

for i in {1..60}; do
  sleep 3
  JOB_DATA=$(curl -s "http://localhost:8000/api/job/$JOB_ID")
  STATUS=$(echo "$JOB_DATA" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null || echo "unknown")

  if [ "$STATUS" = "completed" ]; then
    echo ""
    echo "✅ Job completed!"
    echo "$JOB_DATA" | python3 -m json.tool
    exit 0
  elif [ "$STATUS" = "failed" ]; then
    echo ""
    echo "❌ Job failed!"
    echo "$JOB_DATA" | python3 -m json.tool
    exit 1
  fi

  printf "\rStatus: $STATUS (attempt $i/60)"
done

echo ""
echo "⏱️ Timeout waiting for job"
exit 2
