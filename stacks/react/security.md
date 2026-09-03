# React — Security

**Read when:** touching auth, uploads, or anything rendering personal data.

**The client is not a security boundary.** Every rule here is UX on top of a backend control.
If a check exists only here, it doesn't exist.

---

## Auth

- Session in an `httpOnly` cookie, same-origin. **Never a token in `localStorage`** — any
  XSS reads it, and it survives the tab.
- `<ProtectedRoute>` guards every authenticated route — [routing](patterns/routing.md). A
  hidden nav item is not a guard.
- A 401 from any request clears auth state and redirects to `/login?next=…`. One interceptor
  in `lib/api.ts`, not per-hook handling.
- Log out clears the Query cache (`queryClient.clear()`). Otherwise the next user on that
  device sees the previous one's data.

## Trust nothing over the wire

Parse every response with its Zod schema at the `api.ts` boundary — [data](patterns/data.md).
A malformed or hostile payload fails there, loudly, once.

- Never `dangerouslySetInnerHTML` with server or user content. Rich text is a conversation
  about sanitisation, not a quick fix.
- Never build a URL for `window.open`/`<a href>` from unvalidated response data.

## Uploads

- Validate type and size client-side **for the error message**. The server validates for real.
- Show the constraint before the user picks the file, not after the upload fails.
- Render the original filename as text — never as HTML, never as a link target.
- Downloads come from the API; don't cache a URL in a store.

## Personal data

- **Nothing personal in `console.log`, analytics, or error-reporting payloads.** Scrub before
  sending anywhere.
- Don't put PII in a URL — it lands in history and referrers.
- Error boundaries show a message and a retry, never a raw error object.

## The rules the UI mirrors — and does not own

Any gate, lock or permission the screen renders is read from data the API returns, and the
API enforces it. The UI renders these so the user understands the state; a disabled button
is a hint, not the control. Consent is collected by a checkbox and recorded server-side.

**See also:** [data](patterns/data.md) · [forms](patterns/forms.md)
