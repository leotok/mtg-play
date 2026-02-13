#!/bin/bash

# Script to add all cards from the decklist to deck ID 3
API_BASE="http://localhost:8000/api/v1"
DECK_ID=3

# Login and get token
echo "Logging in..."
TOKEN=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"email": "player@example.com", "password": "GameOn2024!"}' \
  "$API_BASE/login" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Failed to get token"
    exit 1
fi

echo "Token acquired: ${TOKEN:0:20}..."

# Card list with their Scryfall IDs (you'll need to look these up)
# For now, let's add some basic lands that should exist

# Basic lands
echo "Adding basic lands..."
curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"card_scryfall_id": "f84e964b-9a0d-4a26-9c73-7bf620959b0", "quantity": 1}' \
  "$API_BASE/decks/$DECK_ID/cards" > /dev/null

curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"card_scryfall_id": "538274b1-7c67-4362-8e13-5bd155a6fb01", "quantity": 1}' \
  "$API_BASE/decks/$DECK_ID/cards" > /dev/null

curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"card_scryfall_id": "de8d7f43-179c-4082-b3c4-6650b93a384", "quantity": 1}' \
  "$API_BASE/decks/$DECK_ID/cards" > /dev/null

curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"card_scryfall_id": "61d9e407-4f71-4914-a7d6-5d5b8ebee2b", "quantity": 1}' \
  "$API_BASE/decks/$DECK_ID/cards" > /dev/null

curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"card_scryfall_id": "4e3a41e5-1942-4c3e-8e2b-aa7b72e4c6c", "quantity": 2}' \
  "$API_BASE/decks/$DECK_ID/cards" > /dev/null

echo "Basic lands added. Checking deck..."

# Check the deck
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_BASE/decks/$DECK_ID" | python3 -m json.tool

echo ""
echo "To add more cards, you need to:"
echo "1. Find the Scryfall ID for each card"
echo "2. Use the add card endpoint with the correct format"
echo ""
echo "Example for a single card:"
echo "curl -X POST -H \"Content-Type: application/json\" -H \"Authorization: Bearer \$TOKEN\" \\"
echo "  -d '{\"card_scryfall_id\": \"<SCRYFALL_ID>\", \"quantity\": 1}' \\"
echo "  \"\$API_BASE/decks/\$DECK_ID/cards\""
