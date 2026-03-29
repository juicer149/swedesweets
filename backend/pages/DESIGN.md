# Pages App — Design Notes

## Purpose

The `pages` app is responsible for rendering static and semi-static pages.

Examples:
- homepage
- about page
- contact page

This app contains **no business logic, no persistence, and no domain models**.

---

## Responsibilities

- Map URLs → views → templates
- Present content to the user
- Act as a thin presentation layer

---

## Non-responsibilities

This app does NOT handle:

- business rules (domain layer)
- database models (catalog / ordering)
- authentication logic (accounts)

---

## Design Principles

- Keep it minimal
- No unnecessary files or abstractions
- No Django models unless strictly needed
- Templates should be simple and readable

---

## Philosophy

This app follows a **“thin adapter”** approach:

    HTTP request → view → template → response

Nothing more.

---

## When to extend

Only introduce more complexity if needed:

- Add models → only if content becomes dynamic (e.g. CMS)
- Add forms → for contact page (future)
- Add styling → via static CSS (not inline)

---

## Summary

The `pages` app exists to:

> render content, nothing else
