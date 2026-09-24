# submit lanes

Agent-agnostic submission. The module defines capability needs, not the
operator's harness. Whatever drives the browser or desktop must satisfy
the lane contract below; house paths (Legends Chrome Kit tabs, Shell Kit
surfaces) are instances, not the interface.

## Capability interface

- `read-page`: open the live notice or portal page and quote terms.
- `fill-form`: complete fields from the business profile + drafts only.
- `upload-file`: attach named files, confirm receipt per file.
- `submit-once`: exactly one send per authorization. No retries without
  a fresh receipt check.
- `print-pack`: produce a print-ready package (coversheet, forms, order
  of pages) when the channel is mail or in-person.

## Authorization gates (every submission)

1. Name the exact opportunity, channel, credential owner, and payload.
2. Get Benjamin's GO for that send. One GO covers one send, not a season.
3. After: record what was sent, where, when, plus receipt (confirmation
   page, email ack, tracking number). Receipt or it did not happen.

## Channel table

| Channel | Agent does | Human does |
|---|---|---|
| API post | build payload, post, store response | nothing (after GO) |
| Portal upload | fill, attach, submit once, capture confirmation | owns the login if non-delegable |
| Email | compose + attach + send from authorized box | nothing (after GO) |
| Mail / in-person | print-pack, checklist, envelope order | sign, post, hand over |
| Gated login | prepare everything to one-click state | the click itself |

## Proof rules

Glass or receipt before claiming anything. Tool ack alone is not done.
Failed or ambiguous sends stop the lane: preserve evidence, report, await
direction. Never double-submit to fix uncertainty.
