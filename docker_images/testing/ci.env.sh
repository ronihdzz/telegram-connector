#!/bin/bash
echo "📦 Running ci.env.sh..."

if [ "$CI" = "true" ]; then
  echo "✅ CI detected, overriding variables with GitHub Actions values..."

  # Here you can associate environment variables with GitHub Actions values
  # Available variables in GitHub Actions:
  # - GITHUB_DATABASE_POSTGRESQL  ==> connects to PostgreSQL database running in github actions
  # - GITHUB_DATABASE_MONGODB  ==> connects to MongoDB database running in github actions 
  # - GITHUB_DATABASE_REDIS  ==> connects to Redis database running in github actions
  # Example:
  # export POSTGRESQL_URL="${GITHUB_DATABASE_POSTGRESQL:-$POSTGRESQL_URL}"
  # export MONGODB_URL="${GITHUB_DATABASE_MONGODB:-$MONGODB_URL}"
  # export REDIS_URL="${GITHUB_DATABASE_REDIS:-$REDIS_URL}"

  # Add environment variable associations with GitHub Actions values here
  # -----------------------------------------------------------------
  export POSTGRESQL_URL="${GITHUB_DATABASE_POSTGRESQL:-$POSTGRESQL_URL}"
  export MONGO_URL="${GITHUB_DATABASE_MONGODB:-$MONGO_URL}"
  export REDIS_URL="${GITHUB_DATABASE_REDIS:-$REDIS_URL}"










  echo "🔐 POSTGRESQL_URL=${POSTGRESQL_URL}"
  echo "🔐 MONGO_URL=${MONGO_URL}"
  echo "🔐 REDIS_URL=${REDIS_URL}"
else
  echo "🧪 Local mode: using local environment variables"
fi

echo "🎬 Variables ready. Continuing with tests..."