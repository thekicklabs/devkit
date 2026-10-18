---
name: go
description: Go services — package-by-domain, slog, wrapped errors, one config, pgx + sqlc, goose, River, the error envelope, real-Postgres tests
route: Go code
---
# Go — services

**Read when:** any task touching Go code.
**Prereq:** `../workflow.md`

stdlib `net/http` and `log/slog` · pgx v5 · sqlc · goose v3 · River on Postgres, no Redis ·
`go test` against real Postgres · golangci-lint v2.

## Layout

```
cmd/<binary>/      main: load config, wire dependencies, run a subcommand; no logic
internal/
  config/          the only package that reads the environment
  db/              sqlc output; generated, never hand-edited
  <domain>/        one package per domain: logic, sentinel errors, River args and workers
  httpapi/         GATEWAY ONLY: routes, decode, call a domain, encode, the error table
  jobs/            GATEWAY ONLY: the River client, the worker registry, the ErrorHandler
migrations/        goose SQL, embedded into the binary
queries/           sqlc input
sqlc.yaml · .golangci.yml
```

Package by domain, not by layer: unexported names keep a domain's internals inside it, and a
feature change touches one directory. A domain's job args and workers live in that domain.
`jobs/` imports every domain to register its workers, so a domain importing `jobs/` for its
args is an import cycle.

## Non-negotiables

1. **The environment is read once, in `internal/config`.** `config.Load()` parses every
   variable into a typed `Config`. A required variable has no default, for the reason in
   `../compose/AGENTS.md` Gotchas: `Load` returns one error naming every missing variable,
   and `main` exits before it opens a port. Nothing else reads the environment, tests included;
   `forbidigo` fails the lint. A new variable lands in `.env.example` in the same commit.
2. **Errors are wrapped with context and matched by identity.**
   `fmt.Errorf("load brand %s: %w", id, err)`. A domain declares its sentinels
   (`var ErrNotFound = errors.New("brand: not found")`) beside the function that returns
   them. Callers use `errors.Is` for sentinels and `errors.AsType` for typed errors, never
   `==` or `err.Error()`. The domain turns `pgx.ErrNoRows` and a `*pgconn.PgError` code into
   its own sentinel, so nothing above it imports pgx. `errorlint` enforces `%w` and `Is`.
3. **`log/slog` with key/value attributes, logged once where the error is handled.**
   `slog.ErrorContext(ctx, "submit failed", "delivery_id", id, "err", err)`. The JSON handler
   is built once in `main`. A function that returns an error does not also log it; the
   wrapped chain already carries each frame's context. No `fmt.Print*` or `log.Print*`.
4. **The caller owns the transaction.** A domain function that writes takes a `pgx.Tx` and
   never commits. The handler or worker opens it with `pgx.BeginFunc`, whose `db` argument
   is anything with `Begin`: the pool in production, the test's own `pgx.Tx` (a savepoint)
   in tests. The row change and its job insert share that transaction.
5. **SQL lives in `queries/`; `internal/db` belongs to sqlc.** `sql_package: pgx/v5`, schema
   read from `migrations/` (sqlc skips goose Down sections). Edit a query or a migration, run
   `sqlc generate`, commit both. `sqlc diff` in the gate fails a stale or hand-edited
   `internal/db`. No ORM, no query builder.
6. **Every migration has a real Down.** goose SQL with `-- +goose Up` and `-- +goose Down`,
   the Down undoing exactly what the Up did; an empty Down is a missing migration. A Go file
   in `migrations/` embeds them (`//go:embed *.sql`; a pattern cannot reach a parent
   directory), and the binary's `migrate` subcommand applies them, then River's schema
   through `rivermigrate`. Compose runs it as the one-shot service (`../compose/AGENTS.md`
   rule 2). A test migrates up, down to 0 and up again; nothing else proves the Downs work.
7. **Every River worker sets what River would otherwise default.**
   - `Timeout()` on the worker. Zero inherits the client's `JobTimeout`, 1 minute by
     default, which cancels a render or a model call mid-flight.
   - `InsertOpts()` on the args with an explicit `MaxAttempts`. The default is 25 with
     `attempt⁴`-second backoff, so a failing job is discarded about three weeks later.
   - `UniqueOpts{ByArgs: true, ByState: …}` with `river:"unique"` on the identifying args
     field. `ByState` is River's default set minus `completed`: available, pending,
     retryable, running, scheduled. A completed job lingers for `CompletedJobRetentionPeriod`
     (24 hours), and a re-insert in that window returns `UniqueSkippedAsDuplicate` with no
     error. `ByState` without `ByArgs` makes the whole kind unique.
   - The client's one `ErrorHandler` alerts when `job.Attempt >= job.MaxAttempts`. River
     discards on exactly that condition after the handler returns, so the alert fires once
     per job, not per attempt. `river.JobCancel` and shutdown skip the handler, and so does
     the rescuer when it discards a job whose process died on its last attempt.

   A job is inserted with `client.InsertTx(ctx, tx, args, nil)` on the transaction that
   changed the row: it becomes visible at commit and vanishes on rollback. Never `Insert`
   after `Commit`. River delivers at least once, so `Work` checks state before it acts, and
   passes `ctx` to every call; a worker that ignores `ctx` runs past its timeout.
8. **Handlers return `error`; one function renders it.** Every failure leaves as
   `{"error": {"code": "BRAND_NOT_FOUND", "message": "…", "details": …}}`, the envelope
   React's `ApiError` parses (`../react/patterns/data.md`, when installed). `httpapi` holds
   the one table from domain error to status and code; adding a code is a row there. An
   unmapped error is logged and rendered as 500 `INTERNAL_ERROR` with a fixed message,
   because its text can leak SQL. `details` is `null` when empty, never omitted.
   `VALIDATION_FAILED` (422) carries `[{"field", "code", "message"}]` there and never echoes
   submitted values.
9. **Every list endpoint is cursor-paginated.** `{"items": […], "next_cursor": "…"}`, with
   `next_cursor` null on the last page. Order by the sort keys then `id`, fetch `limit + 1`,
   encode the opaque cursor from the last row kept, clamp `limit` to 1..100. The `WHERE`
   mirrors the `ORDER BY`: `(created_at, id) < (@created_at, @id)` when every key sorts the
   same way, expanded into `OR`/`AND` when they mix.

## HTTP

- stdlib `http.ServeMux` method patterns (`"POST /api/brands/{id}/claims"`, `r.PathValue`);
  no router dependency.
- A body is decoded once, in the handler, through `http.MaxBytesReader` and a decoder with
  `DisallowUnknownFields`, into a request type validated before any domain call.
- Wire types live in `httpapi` with snake_case `json` tags. A `db` row is never encoded
  directly: its shape follows the schema, and the API contract must not.
- The mux is wrapped in `http.NewCrossOriginProtection().Handler`. It rejects cross-origin
  browser requests with an unsafe method, which is what protects a cookie session from CSRF.
  GET always passes, so no GET handler changes state.

## Testing

- **Real Postgres, no database mocks.** Tests run against `<db>_test`. No interface over
  `db.Queries`, no sqlmock: the SQL is the logic, and a mock only tests itself.
- **One transaction per test, rolled back.** A helper begins on the shared test pool, hands
  the `pgx.Tx` down, and rolls back in `t.Cleanup` with `context.Background()`, because
  `t.Context()` is already cancelled when cleanups run. Nothing commits; no `TRUNCATE`.
- **`TestMain` migrates through a goose `Provider` with `lock.NewPostgresSessionLocker()`.**
  `go test ./...` runs packages as parallel processes against one database.
- **External HTTP APIs are `httptest.NewServer` fakes** serving recorded fixtures. The base
  URL comes from `Config`, so the real client's encoding, auth and error mapping run.
- **Assert the job, not its effect:** `rivertest.RequireInsertedTx[*riverpgxv5.Driver]`.
  The worker gets its own test through `rivertest.NewWorker(…).Work`.
- **Assert `error.code`**, not only the status.

## Before you say done

```bash
test -z "$(gofmt -l .)" && go vet ./... && golangci-lint run && sqlc diff && go test ./...
```

`gofmt -l` exits 0 even when it lists files; `test -z` is what fails the gate. Run it inside
the stack as `docker compose exec <service> sh -c '…'` (`../compose/AGENTS.md`) and paste the
run. The lint config it relies on:

```yaml
# .golangci.yml
version: "2"
linters:
  enable: [errorlint, sloglint, forbidigo]
  settings:
    forbidigo:
      forbid:
        - pattern: ^os\.(Getenv|LookupEnv|Environ)$
          msg: read the environment only in internal/config
  exclusions:
    rules:
      - path: ^internal/config/
        linters: [forbidigo]
```
