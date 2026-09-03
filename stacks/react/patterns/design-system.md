# Pattern — design system

**Read when:** writing any component, or touching styles, colour, type, or spacing.

The project's token values live in `src/styles/theme.css` and `project.md`. This file is the
contract those values plug into.

---

## Token contract

Every visual decision resolves to a token. Components never hold a value.

```
Colour     semantic slots (base-100/200/300, base-content, primary, secondary, accent,
           neutral, success, warning, error, info) + any extra brand slot in a plain @theme
Radii      selector (pills) · field (controls) · box (cards) — three, named by role
Spacing    a 4px base ramp
Type       a closed ramp (below)
Elevation  flat by default; at most sm/md soft shadows
Focus      one ring, declared once, on every interactive element
Icons      one library, one stroke-width, imported individually
Charts     --chart-1 --chart-2 --chart-grid, per theme, validated per surface
```

### The type ramp is closed

`text-2xs … text-2xl` plus `display-1…4` (responsive web/mobile pairs) and `font-display`
for card headings. An arbitrary `text-[13px]` is off-contract, and so is a heading size the
ramp does not have. Weights stop where the vendored font stops — `font-bold` on a face
vendored at 400/500/600 renders a synthesised fake bold.

Label metrics (family, uppercase, tracking) live in one `label-mono` utility, not at call
sites. Never re-declare `uppercase` next to it; never hand-roll an eyebrow — use `Eyebrow`.

Buttons are the whole contract in one line: label face, one weight, flat size at every
variant, heights matched to the design. A `flag` variant marks an action that undoes or
abandons; it is never `primary` in another colour, and it sits at the far end of its row.

## Themes

Two DaisyUI themes, switched via `data-theme` on `<html>`, applied **before paint**.

1. **Components reference semantic slots only** — `bg-base-100`, `text-base-content`. Never
   a raw hex. Dark mode uses its own neutral surfaces, selected, never flipped.
2. **Light-only tints need a dark counterpart** — a low-alpha wash of the same hue with light
   foreground. Expose them as per-theme tokens, not fixed values.

## Restraint

The house style is spare. A screen earns its ink; nothing is on it because it *could* be.
When a choice is open, the quieter one is the answer:

- **One frame around one thing.** Nested surfaces separate with a rule and whitespace;
  `Card` is for the outermost surface only; collapsibles inside one are unbordered. A heading
  that *introduces* a page's work is not a surface.
- **A glyph beats a badge; a badge beats a sentence.** State that repeats down a list is one
  mark — tick, dash, hourglass, dot — naming itself in a `Tooltip`. Keep the badge for the
  one-off.
- **Say it once.** Chrome that repeats what the heading above it already said is deleted,
  not restyled. An exposed `Tooltip` plus an `sr-only` twin is the same words twice.
- **Terse where terseness loses nothing.** `3/15`, not "3 of 15 resolved". Prose is for the
  thing the user has to *read* to act, and there it gets the full width.
- **Metadata checked once lives behind an icon.** Leave visible the one fact the user places
  the record by.
- **An empty state and the action that fills it are one row.** Sentence left, button right;
  the action moves to the panel header the moment there is a list.
- **Long lists start collapsed, and open one at a time.**
- **A lock governs its own controls, not its neighbours'.** Anything on a locked step that
  answers to a different rule renders outside the lock and gates itself.
- **Reference is a link, work is a button — and so is upkeep.** Filled and outlined buttons
  are reserved for the action the screen exists to invite. A card wearing four outlined
  buttons has no call to action.
- **One action on a row is a glyph, not a word**, with the row's subject in its `aria-label`.
- **Whitespace over rules.** Air first, a hairline second, a border last.

Nothing that carries meaning is dropped — it is **moved**: to a tooltip, an `sr-only`
string, the row it belongs to. If a change deletes the only copy of a fact, it has gone too
far.

## Acting on a record

- **The decision belongs at the foot of the work** — a `sticky bottom-0` footer, last child
  of the container that owns the work.
- **A step's conclusion is not a second step beside it.** Offer one act at a time; the
  concluding action appears at the foot of the work it concludes, and not until there is
  work to conclude. Where the user can see the finish line but has not reached it, draw the
  action dead with the reason beside it — never live for something the server will refuse.
- **One primary per surface, and it is whatever is live now.** Upkeep on a list is an outline
  `Plus` under it. An action a record *cannot* take is not offered on it; its disabled
  control says why.
- **Permission is not intent.** An override, discard or redo arms behind an explicit red
  tick, named for what it forces, unticked on every render.
- **Say what is blocking once, at the level it is true.** Case-level in one `Alert`;
  control-level on that control's hover. Never a `title` alone — a tooltip can carry the
  consequence but never the only copy.
- **A mark means what its colour says.** Never borrow a semantic glyph for a neighbouring
  meaning.
- **Two writes behind one button are one decision.** The first is not repeated when the
  second is refused, and whether it landed is read off the record, never off component
  state.
- **Labels are instructions.** `Mark ineligible`, not `Ineligible`; and distinct from their
  neighbours.
- **Write for the user, not the engine.** No status codes, no enum values, no schema
  vocabulary. Empty and blocked states say what to do.

## Component wrappers

DaisyUI supplies the base class layer. Each component in `src/components/ui/` is a **typed
React wrapper using CVA** for variants. Raw class strings never appear in `src/features/`.
Merge incoming `className` with `cn()` so callers can adjust layout without fighting
specificity.

**Fit the component to the flow, not the flow to the inventory.** Check the existing
components first; when adapting one would clutter the UI or obscure an action, build the
purpose-built one. Keep a one-flow component in its feature; promote per the thresholds in
[refactor](../refactor.md). A new dependency still requires approval.

- **Three controls pick from a list, and the list's length decides which.** `Select` for a
  short closed set · `MultiSelect` for a handful of tags that fit as chips · a search-driven
  picker once scrolling the roster is the problem. `<select multiple>` is not one of them.
- **`Table` is for scanning short comparable values** column by column, and scrolls inside
  its own container. A "row" that is a paragraph renders as a full-width list row with its
  actions beneath. A column the user does not scan by belongs under the row (`expansion`),
  not off the screen.
- **`Modal`** for an action that interrupts · **`Drawer`** for a panel read alongside the
  page · **`ConfirmModal`** for redoing settled work, stating the **consequence**, never
  "are you sure" · **`Disclosure`/`Accordion`** for collapsing rows with scannable summaries,
  never a raw `<details>` · **`Tooltip`** for a control with no room to carry a label, and
  only that · **`Popover`** as the anchored-panel primitive, `role="dialog"`, not a menu.
- One `useModalDialog(open, onClose)` hook owns `showModal()`, focus restoration and the
  body-scroll lock. A new overlay uses it.
- **A versioned step**: the action that moves forward is primary; the one that redoes
  something is secondary and confirmed; the completed state stays on the page as an
  `Alert`, because a toast is gone by the time the user looks back.
- **Documents are named, never identified.** A bare id on the page is a defect.

## Charts

One wrapper component; features do not import the chart library. Series colours are
`--chart-1`/`--chart-2` in fixed order, each mode's steps chosen against that mode's card
surface for contrast and colour-vision separation — selected, never flipped. A persisted
chart/table toggle controls every reporting card; in chart view the `<table>` mirror stays
`sr-only` with `focus-within:not-sr-only`, because the mirror's links are the only keyboard
route into the records. The link belongs to the row, built where the value is still in hand.
Horizontal bars for long category labels; time on a line, never bars. Every chart renders
its own empty state.

**See also:** [feature](../feature.md) · [review](../review.md) · [i18n](i18n.md)
