# Login as teste2

Logs in with the second test user credentials and returns the access token.

## Command

```bash
curl -s -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"email": "teste2@teste2.com", "password": "123456"}'
```

## Description

Logs in with the second test user and returns the JWT access token. Use the returned token in Authorization header:
```
Authorization: Bearer <token>
```
