# React — Review

**Read when:** reviewing a frontend diff, after the generic `code-review` skill checklist.

---

## Blocking

- [ ] **Raw hex in a component?** Semantic slots only — [design system](patterns/design-system.md)
- [ ] **Raw DaisyUI class strings outside `src/components/ui/`?**
- [ ] **Dark theme unchecked?**
- [ ] **A user-facing literal in a component, or an API error code without a translation?** — [i18n](patterns/i18n.md)
- [ ] **Screen switching off component state instead of a route?** — [routing](patterns/routing.md)
- [ ] **Server data copied into `useState`?** — [state](patterns/state.md)
- [ ] **Hardcoded domain data in a component** instead of MSW seed — [data](patterns/data.md)
- [ ] **Form field without a Zod rule, or a control outside `FormField`?** — [forms](patterns/forms.md)
- [ ] **A mirrored business rule changed without a test, or hardcoded to an id?** — [forms](patterns/forms.md)
- [ ] **Token in `localStorage`, or PII in a log/analytics call?** — [security](security.md)
- [ ] **Branching on `response.status` instead of `error.code`?** — [data](patterns/data.md)
- [ ] **A primitive rebuilt that already exists in `src/components/ui/`?**

## Should fix

- [ ] Loading, error, or empty state missing on a query-backed view — [data](patterns/data.md)
- [ ] Two successive steps drawn with separate submits on one screen, or an action offered
      on a record that cannot take it — [design system](patterns/design-system.md)
- [ ] No test for a new primitive or a new flow — [testing](testing.md)
- [ ] Snapshot test added
- [ ] Query key too broad on invalidate — [performance](performance.md)
- [ ] Whole-store Zustand selector instead of a narrow one
- [ ] JS-driven responsiveness; `window.innerWidth` anywhere
- [ ] Missing label, focus ring, landmark, or accessible name on an icon-only button
- [ ] `import * as` from `lucide-react`
- [ ] Heavy dependency pulled into the main bundle instead of a lazy route — [performance](performance.md)
- [ ] `className` composing appearance where a CVA variant belongs — [refactor](refactor.md)
- [ ] Off-ramp type size or weight outside the ramp — [design system](patterns/design-system.md)
- [ ] Response not parsed at the `api.ts` boundary
- [ ] Date/number formatted by hand instead of `Intl.*` — [i18n](patterns/i18n.md)

## Worth asking about

- [ ] A component built that the "not building" list excludes — does a flow genuinely need it?
- [ ] A new dependency — check `npm run build` output for what it cost

**See also:** [refactor](refactor.md) · [security](security.md)
