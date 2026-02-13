#!/bin/bash

echo "Testing simple import endpoint..."

# Test the endpoint directly
curl -s -X POST -H "Content-Type: application/json" \
  -d '{
    "name": "Test Deck",
    "commander": "Edgar Markov",
    "cards": ["Blood Artist"],
    "is_public": false
  }' \
  http://localhost:8000/api/v1/decks/simple-import

echo ""
echo "If this returns 405 Method Not Allowed, the endpoint is not registered."
echo "If it returns 200, the endpoint is working."
