# partner_request
`partner_request` is the public inbound app for expressions of interest from potential retail partners.

## Purpose

The app exists to receive simple external contact data from stores or retailers who are interested in selling SwedeSweets products. It functions as a controlled “inbox” for leads coming from the public website.

This is **not** an internal onboarding engine and **not** a workflow for creating accounts or stores.

## Responsibilities

The app is responsible for:

- displaying a public form
- validating and normalizing input through Django forms
- storing partner requests in the database
- giving admins a simple interface to read, search, filter, and mark requests as processed

## Non-responsibilities

The app is **not** responsible for:

- creating `User`
- creating `Store`
- approving or rejecting partners in the business-domain sense
- assigning permissions
- triggering account onboarding or password flows

If a partner request leads to a business relationship, that happens manually outside this app, for example by an admin later creating a store and account in the system’s internal models.

## Design Principles

### 1. Clear boundary between external input and internal truth
`PartnerRequest` represents external, untrusted, public input.  
`Store` and `User` represent internal, trusted state.

These should not be directly coupled within this app.

### 2. Simplicity over workflow
For the current business, there is no need for a state machine for approval or rejection.  
It is enough to distinguish between:

- new / unprocessed
- processed

This is expressed through `is_processed` and `processed_at`.

### 3. Forms as a boundary
HTTP input should be validated in `forms.py`, not written directly from `request.POST` into the model.  
This makes validation, error handling, and normalization clearer and safer.

### 4. Admin without side effects
The admin interface is used for review and follow-up, not provisioning.  
Admin actions in this app should therefore remain small and local, for example marking a request as processed.

## Data Model

A `PartnerRequest` contains only contact and context data, for example:

- contact person
- store name
- email
- phone
- address
- message
- created timestamp
- processed status
- internal admin notes

This is enough to support manual follow-up without introducing unnecessary complexity.

## Practical Usage

Typical flow:

1. A store submits the form on the website
2. The request is stored in the database
3. An admin sees it in Django admin
4. The admin contacts the store or ignores it
5. The admin marks the request as processed
6. If a business relationship begins, the account and store are created separately in internal apps

## Future Development

If needed, the app could later be extended with things like:

- spam protection / rate limiting / honeypot
- email notification to admins
- additional review statuses such as `contacted` or `archived`

But such additions should only be made when they reflect a real workflow in the business.
