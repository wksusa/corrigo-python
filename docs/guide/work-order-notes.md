# Work Order Notes (WoNote)

Work order notes (`WoNote`) are standalone text annotations on a work order,
separate from the action log entries produced by status transitions. They are
the correct mechanism for adding technician updates, parts orders, or observations
without changing the work order status.

## Discovery Context

This was discovered after exhausting the following dead ends:

| Approach | Result |
|---|---|
| `POST /base/WorkOrderNote` | `[400] There are no such entityType as 'WorkOrderNote'` |
| `POST /base/ActionLogRecord` | `[400] There are no such entityType as 'ActionLogRecord'` |
| `POST /base/WoActionLog` | `[400] Create operation is not supported by WoActionLog entity` |
| `PUT /base/WorkOrder/{id}` | `[405]` (staging blocks PUT on WorkOrder) |
| `PATCH /base/WorkOrder/{id}` | `[405]` (same) |
| `WoAddNoteCommand`, `WoNoteCommand`, `WoCommentCommand` (5 variants) | All `COMMAND_NOT_FOUND` |
| `POST /base/Note` | `[400] ActorId is a required field` (different entity — customer-level notes) |

The correct endpoint is `POST /base/WoNote`.

## Entity Structure

```json
{
  "Id": 206686,
  "WorkOrderId": 183445,
  "NoteTypeId": "Completion",
  "Body": "Replaced compressor, system running normally.",
  "CreatedDate": "2026-03-10T06:15:04",
  "CreatedBy": {
    "Id": 1280,
    "TypeId": "Employee"
  }
}
```

## Valid NoteTypeId Values

| Value | Description | Limit |
|---|---|---|
| `"Public"` | Visible to all parties (store, technician, facilities team) | Unlimited |
| `"Private"` | Internal only | Unlimited |
| `"Completion"` | Technician's final completion summary | **One per work order** |

## Creating a Note

```python
result = client.work_orders.add_note(
    work_order_id=183445,
    body="Ordered replacement compressor, ETA 3 business days.",
    note_type="Public",   # default
)
# result: {"EntitySpecifier": {"EntityType": "WoNote", "Id": 206687}}
```

### Attribution for Service Accounts

Corrigo commands run as the service account (no impersonation param). Prefix
the body to attribute notes to the originating technician:

```python
body = f"Via Nova ({tech_name}): {tech_message}"
client.work_orders.add_note(work_order_id, body, note_type="Public")
```

## Raw API

```
POST /api/v1/base/WoNote
Content-Type: application/json

{
  "Entity": {
    "WorkOrderId": 183445,
    "Body": "Via Nova (Jesus Archila): Ordered parts, ETA 3 days.",
    "NoteTypeId": "Public"
  }
}
```

Response:
```json
{"EntitySpecifier": {"EntityType": "WoNote", "Id": 206687}}
```

## Notes vs Action Log Entries

| Feature | WoNote | ActionLogRecord |
|---|---|---|
| Created via | `POST /base/WoNote` | Status transition commands (start, complete, hold, etc.) |
| Standalone? | Yes | No — always tied to a status change |
| Read via | `GET /base/WoNote/{id}` or `QueryBuilder("WoNote")` | `WorkOrder.ActionLogRecords` field |
| Queryable? | Yes (`QueryBuilder("WoNote")`) | Via WO ActionLogRecords only |

## References

- Developer docs: https://developer.corrigo.com/reference/endpoint
- Sample entities: https://developer.corrigo.com/reference/sample-entities
- Swagger: https://az-am-ent-f8.corrigo.com/api/swagger/ui/index
- CorrigoService API: https://securecontent.corrigo.com/docs/HelpCE921/html/1ff85626-3e88-4000-a8e6-466cfeb8edf8.htm
