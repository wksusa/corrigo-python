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

## Valid DocumentType Values

| `DocType.Id` | Member | Use |
|---|---|---|
| `1` | `DocumentType.SIGNATURE` | Customer or technician signature |
| `3` | `DocumentType.PICTURE` | Photo / image attachment |

Other integer IDs may exist on a given tenant (e.g. an `InvoicePrintout`
type configured for a specific customer). Pass a bare `int` to bypass the
enum:

```python
client.work_orders.attach_document(..., doc_type=7)
```

The `DocType` table is not queryable through the Corrigo REST API — to
discover tenant-specific IDs, inspect existing `Document` rows on the
tenant in question.

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

### Signatures

```python
client.work_orders.attach_document(
    work_order_id=174218,
    file=signature_png_bytes,
    filename="signature.png",
    mime_type="image/png",
    doc_type=DocumentType.SIGNATURE,
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
  `application/octet-stream` — the wrong MIME shows up in the Corrigo UI
  and is worse than failing loudly.
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
    "DocType": {"Id": 3},
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
