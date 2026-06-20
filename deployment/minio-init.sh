#!/bin/sh
set -eu

: "${MINIO_ENDPOINT:=http://minio:9000}"
: "${MINIO_ACCESS_KEY:=change-me-local}"
: "${MINIO_SECRET_KEY:=change-me-local}"
: "${MINIO_BUCKET:=yahaha-game}"

until mc alias set local "$MINIO_ENDPOINT" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"; do
  echo "Waiting for MinIO at ${MINIO_ENDPOINT}..."
  sleep 2
done

mc mb --ignore-existing "local/${MINIO_BUCKET}"

cat > /tmp/published-readonly-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": ["*"]
      },
      "Action": ["s3:GetObject"],
      "Resource": [
        "arn:aws:s3:::${MINIO_BUCKET}/published/*",
        "arn:aws:s3:::${MINIO_BUCKET}/avatars/*"
      ]
    }
  ]
}
EOF

mc anonymous set-json /tmp/published-readonly-policy.json "local/${MINIO_BUCKET}"
mc anonymous get "local/${MINIO_BUCKET}/published" || true
mc anonymous get "local/${MINIO_BUCKET}/avatars" || true
