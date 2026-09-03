# Pattern — forms and validation

**Read when:** touching any form.
**Prereq:** [state](state.md)

React Hook Form + Zod via `@hookform/resolvers`. Every field gets a schema.

---

## Schemas

One Zod schema per form (or per section of a multi-step form), in `schemas.ts`. They mirror
the backend's — **the backend is the authority**; it validates the same payload again on
submit, and its blockers are what the review screen shows. These exist so a mistake is caught
next to the field that caused it.

Field names are the **wire names**, because that is what is stored: a form's values object
*is* the payload.

Shared limits (long-text lengths) come from `lib/constants.ts` in both the Zod schema and
the input's `maxLength`, so validation, enforcement and the counter agree.

## `FormField` is the only wrapper

Every control goes through it: label + required mark + control slot + hint + error. No
feature renders a bare `<label>` next to a bare `<input>` — that's how the a11y association
and the error styling drift.

```tsx
<FormField label={t('company.name')} required error={errors.companyName?.message}>
  {(field) => <Input {...field} {...register('companyName')} />}
</FormField>
```

A hint that qualifies *whether the field applies at all* goes under the label
(`hintPlacement="label"`); advice on the answer goes under the control.

## Multi-step forms

A section component declares its resolver, empty values and fields; a `useSectionForm`
hook owns the autosave subscription and an imperative `submit(): Promise<boolean>`.

- **`defaultValues`, not `values`.** The draft query refetches, and RHF's `values` prop would
  reset the form mid-sentence each time. Render a section only once its draft has loaded.
- **Section identity is a semantic key**, ordered by a manifest the server returns — never an
  ordinal, never a second step array in the SPA.
- Where a rule needs runtime data (every item in a server-defined set must be ticked), build
  the resolver once the data has loaded — split into a fetching outer and a form-holding
  inner component, because `useForm` must be called before any early return. **Until the
  data is known the section reads as incomplete.** Failing open renders a green submit the
  server then rejects.

## Autosave

- **Focus-out triggers autosave.** Typing updates queued values; leaving a control flushes
  them — no write while the user is still composing a value.
- **Keyed by section**, so a long-form mode rendering every section at once files values
  under the right one.
- **Queued saves are written sequentially.** Each returns the next `lockVersion`; two
  concurrent requests both send the old one and the second gets a 409.
- **Navigation calls `flush()`.**
- **Never feed `isSaving` to the footer button's `saving` prop.** The mousedown on the
  button is what blurs the field and starts the focus-out save — the button goes disabled
  between mousedown and mouseup, the browser drops the click, and the step needs a second
  press. Pass a flag the click handler owns; the status badge reports background saves.

The conflict check is the client's `lockVersion`, echoed from the previous read. A second tab
that saved in between has bumped it, so this tab's next save gets a 409 instead of
overwriting.

## Repeating rows

`useFieldArray` behind one `RowGrid` primitive. **Never mint row ids by hand** — a
module-level counter is shared between mounted grids and restarts on remount, and React
re-keys surviving rows onto removed rows' inputs.

## Mirrored business rules

A gate or a lock the UI shows is **data-driven**: counts come from the data, editability
comes from the record. Never hardcode a count or an id — a test that hardcodes one
reproduces the bug it should catch. Show the reason: a disabled button with no explanation
generates support tickets. When the server returns a 422 with its complete blocker list,
render **that** in preference to the local gate, each entry linking to its field.

## Derived values

A value the server derives (a percentage from two amounts, a region from a selection) is
not a field. Accepting both lets someone declare one next to figures that say another.

**See also:** [state](state.md) · [data](data.md) · [i18n](i18n.md) · [testing](../testing.md)
