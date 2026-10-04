# API Documentation

All API endpoints are prefixed with `/api/v1/`.

## General
### GET `/api/v1/health`
**Description:** Infrastructure verification mechanism to check backend and database connectivity.
**Auth Required:** No

**Response (200 OK):**
```json
{
    "status": "ok",
    "service": "canteen-backend",
    "database": "connected"
}
```

## Error Handling
Standard error format for the API:
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message"
    }
}
```
