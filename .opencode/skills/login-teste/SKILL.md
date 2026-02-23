# Login as teste

Logs in with the test user credentials and returns the access token.

## Command

```bash
curl -s -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"email": "teste@teste.com", "password": "123456"}'
```

## Description

Logs in with the test user and returns the JWT access token. Use the returned token in Authorization header:
```
Authorization: Bearer <token>
```
