# Work Order Documents

The `Document` entity is how files — technician photos, customer signatures,
scanned receipts — are attached to a work order on Corrigo Enterprise. The
SDK exposes `attach_document` and `list_documents` on
`WorkOrderResource` so callers don't have to construct the JSON envelope by
hand.

## Discovery Context

The required-field set for `Document` is not documented on Corrigo's
developer portal. This was discovered after exhausting the following dead
ends:

| Approach | Result |
|---|---|
| `POST /base/Document` with `{Title, ActorTypeId:"WO", ActorId, Blob}` only | `[400] EMPTY_INPUT_PARAMETER` |
| Adding `DocType` as a string (e.g. `"Picture"`) | `[400] DocType is a required field` (still rejected — `DocType` is a typed FK, not a string) |
| Adding `DocType: {Id: 3}` | `[400] StorageTypeId is a required field` |
| `QueryBuilder("StorageType")` to enumerate valid values | `[400] ENTITY_NOT_FOUND: no such entityType as 'StorageType'` |
| `QueryBuilder("DocType")` to enumerate valid values | `[400] ENTITY_NOT_FOUND: no such entityType as 'DocType'` |
| Inspecting existing `Document` rows | Reveals `StorageTypeId="Cloud"` and `DocType.Id ∈ {1, 3}` in real data |
| Multipart `POST /base/Document` | Not supported on Enterprise (multipart is CorrigoPro Direct's `/api/attachments`) |

The working envelope embeds the file as base64 in the JSON body and includes
**`StorageTypeId`**, **`DocType.Id`**, and **`MimeType`** alongside the
`ActorTypeId="WO"` / `ActorId=<wo_id>` link to the work order.

## Entity Structure

```json
{
  "Id": 456679,
  "Title": "evidence.png",
  "Description": null,
  "ActorTypeId": "WO",
  "ActorId": 174218,
  "StorageTypeId": "Cloud",
  "DocType": {"Id": 3, "DisplayAs": "Picture"},
  "MimeType": "image/png",
  "IsPublic": true,
  "StartDate": "2026-05-15T18:42:00+00:00",
  "DocUrl": "https://enterpriseam.s3.amazonaws.com/12345/abcd/evidence.png"
}
```

## DocType is Derived from MimeType

Corrigo **ignores** any `DocType.Id` sent in the `POST /base/Document`
request body and infers the stored value from `MimeType` server-side.
Observed on staging (2026-05-15):

| Sent `MimeType` | Stored `DocType.Id` | Display |
|---|---|---|
| `image/png` (and other `image/*`) | `3` | Picture |
| `application/pdf` | `32` | PDF |

The SDK still sends `DocType: {"Id": 3}` because the field is required by
server-side validation, but the value is decorative — Corrigo overwrites
it. The helper therefore does **not** expose a `doc_type` parameter; pass
the correct `mime_type` and Corrigo will categorise the document
correctly in the UI.

**Signatures.** The `DocType.Id=1` "Signature" rows visible in existing
Corrigo data are created through other paths (legacy SOAP clients, the
mobile app signature pad, etc.) — not through `POST /base/Document`. This
endpoint cannot produce a Signature record. If you need signature
ergonomics, file a separate issue.

The `DocType` table itself is not queryable through the Corrigo REST API
(`QueryBuilder("DocType")` returns `ENTITY_NOT_FOUND`), so the full list
of MIME → DocType mappings can only be observed by uploading samples and
reading back what was stored.

## Attaching a Document

### From bytes

```python
result = client.work_orders.attach_document(
    work_order_id=174218,
    file=open("photo.png", "rb").read(),
    filename="photo.png",
    mime_type="image/png",
)
# result: {"EntitySpecifier": {"EntityType": "Document", "Id": 456679}}
```

### From a path

When `file` is a `str` or `pathlib.Path`, filename and MIME type are
inferred automatically:

```python
from pathlib import Path

result = client.work_orders.attach_document(
    work_order_id=174218,
    file=Path("evidence/photo.png"),
)
```

### Private documents

`is_public` defaults to `True`, matching the typical
technician-uploaded-photo case. Pass `is_public=False` for internal-only
documents:

```python
client.work_orders.attach_document(
    work_order_id=174218,
    file=invoice_pdf_bytes,
    filename="vendor-invoice.pdf",
    mime_type="application/pdf",
    is_public=False,
)
```

## Listing Documents

```python
docs = client.work_orders.list_documents(work_order_id=174218)
for d in docs:
    print(d["Title"], d["MimeType"], d["DocUrl"])
```

`DocUrl` is a permanent, publicly-addressable S3 URL (unlike CorrigoPro
Direct's 15-minute signed link). Fetch the binary directly:

```python
import httpx

content = httpx.get(docs[0]["DocUrl"]).content
```

## Limits and Validation

- **Size:** 20 MB per file. The SDK rejects oversize payloads client-side
  with a `ValueError` before any HTTP call is made — base64 inflates the
  request by ~33%, and Corrigo's server-side error path is opaque.
- **MIME type:** required, either explicit via `mime_type=` or inferred
  from the filename via `mimetypes.guess_type`. An unguessable filename
  raises `ValueError` rather than silently defaulting to
  `application/octet-stream` — Corrigo derives `DocType` from this value
  and a wrong MIME also miscategorises the document in the UI.
- **Filename:** required when `file` is `bytes`; derived from `Path.name`
  when `file` is a path. Always surfaces in the Corrigo UI as the
  document's name.

## Raw API

```
POST /api/v1/base/Document
Content-Type: application/json

{
  "Entity": {
    "Title": "evidence.png",
    "ActorTypeId": "WO",
    "ActorId": 174218,
    "StorageTypeId": "Cloud",
    "DocType": {"Id": 3},        // required but ignored — Corrigo derives DocType from MimeType
    "MimeType": "image/png",
    "IsPublic": true,
    "StartDate": "2026-05-15T18:42:00+00:00",
    "Blob": {
      "FileName": "evidence.png",
      "Body": "<base64-encoded file bytes>"
    }
  }
}
```

Response:

```json
{"EntitySpecifier": {"EntityType": "Document", "Id": 456679}}
```

For queries, `DocType` is a scalar property and must be selected with
dotted paths — bare `DocType` returns
`ERROR_CODE_1003: scalar property must be the last in property path`:

```python
QueryBuilder("Document").select(
    "Id", "Title", "MimeType", "DocUrl",
    "DocType.Id", "DocType.DisplayAs",   # dotted, not bare
)
```

## Documents vs CorrigoPro Direct Attachments

CorrigoPro Direct (a separate Corrigo product) exposes
`POST /api/attachments` as a multipart endpoint with 15-minute signed
download URLs. That API does not work on Corrigo Enterprise. The 20 MB
ceiling is the only thing the two products share.

## References

- Developer portal: <https://developer.corrigo.com/reference/entities>
- Corrigo SOAP forum thread (partial public source for `ActorTypeId` /
  `Blob` shape): <https://developer-soap.corrigo.com/discuss/5cd5b80bf631cd000e1c3d38>
- CorrigoPro Direct attachments (different product, 20 MB ceiling
  reference): <https://developer.corrigopro.com/docs/working-with-attachments>
