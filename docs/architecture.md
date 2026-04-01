# Architecture

## Current scope

This first Python implementation mirrors the current Power Apps pattern:

- one request with one uploaded document
- one ordered list of approvers
- only the active approver can act
- approve advances to the next step
- reject ends the request
- requester can cancel while the request is open
- email notifications are emitted from the backend
- audit records are written for workflow events

## Core models

- `SignatureRequest`: the parent request record
- `RequestDocument`: uploaded source file and future working/final file versions
- `ApprovalStep`: ordered approval chain
- `AuditLog`: immutable event history

## Planned next layers

- PDF conversion pipeline for Word or Excel uploads
- signature image capture and storage
- visible PDF stamping after each approval
- reminder scheduling and timeout handling in Celery
- role-based permissions for requesters, approvers, and admins
- reporting and search filters similar to the current Power Apps gallery views
