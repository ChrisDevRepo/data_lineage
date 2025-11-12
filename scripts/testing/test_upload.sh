#!/bin/bash

# Upload files
echo "Uploading Parquet files..."
RESPONSE=$(curl -X POST "http://localhost:8000/api/upload-parquet?incremental=false" \
  -F "files=@.build/temp/part-00000-163999fc-8981-440d-8ccd-8a762427b50a-c000.snappy.parquet" \
  -F "files=@.build/temp/part-00000-987ade22-ace3-473f-a6b8-22dd9c2e0bba-c000.snappy.parquet" \
  -F "files=@.build/temp/part-00000-e4447ab7-3304-48c6-9d99-e1ee7b3e649b-c000.snappy.parquet" \
  -F "files=@.build/temp/part-00000-49de9afd-76ab-4385-83a7-92ac8c14c3d6-c000.snappy.parquet" \
  -F "files=@.build/temp/part-00000-e3366b2c-9942-41d4-94b7-e23354d0b4ea-c000.snappy.parquet" \
  -s 2>&1)

JOB_ID=$(echo "$RESPONSE" | grep -oP 'job_id":"[^"]+' | cut -d'"' -f3)

if [ -z "$JOB_ID" ]; then
  echo "Failed to get job ID. Response:"
  echo "$RESPONSE"
  exit 1
fi

echo "Job ID: $JOB_ID"
echo "Waiting for job to complete..."

# Poll job status
for i in {1..90}; do
  sleep 2
  JOB_DATA=$(curl -s "http://localhost:8000/api/job/$JOB_ID")
  STATUS=$(echo "$JOB_DATA" | jq -r '.status // empty')

  if [ "$STATUS" = "completed" ]; then
    echo ""
    echo "✅ Job completed!"
    echo "$JOB_DATA" | jq '{status, progress, completed_at, result: {total_objects, total_stored_procedures, sp_with_inputs_outputs}}'
    exit 0
  elif [ "$STATUS" = "failed" ]; then
    echo ""
    echo "❌ Job failed!"
    echo "$JOB_DATA" | jq '.error'
    exit 1
  fi

  printf "\rStatus: $STATUS (attempt $i/90)"
done

echo ""
echo "⏱️ Timeout waiting for job"
