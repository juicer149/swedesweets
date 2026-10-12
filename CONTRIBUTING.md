# Working on SwedeSweets

How the project is worked on day to day: setup, the everyday commands,
branches, migrations, translations and deploys. How the code is organised
is in [ARCHITECTURE.md](ARCHITECTURE.md); what is planned next is in
[docs/roadmap.md](docs/roadmap.md).

## Setup

```sh
cp .env.example .env      # local settings: DJANGO_DEBUG=1 and friends
make setup                # venv, dependencies, migrate, static files
make seed                 # demo products, customers, batches and orders
make run                  # http://localhost:8000
```

`make` reads `.env` for every command. Running `manage.py` by hand does not:
load it first in that terminal, or Django starts as production and asks for
a secret key.

```sh
set -a; . ./.env; set +a
.venv/bin/python manage.py <command>
```

## Everyday commands

| Command | What it does |
| --- | --- |
| `make run` | Development server |
| `make test` | The whole test suite (the gate before any merge) |
| `make lint` | Ruff |
| `make migrate` | Apply migrations |
| `make check-migrations` | "No changes detected" when every model change has its migration |
| `make i18n` | Update and compile the French translations |
| `make reset-demo` | Wipe and seed the demo data again |
| `make help` | Everything else |

## Branches and merging

- One topic per branch, named in English, kebab-case
  (`product-variants-orders`, `ops-product-variants`).
- `main` is what runs in production: Railway deploys every push to it.
- A branch is merged only with the whole suite green (`make test`), and
  fast-forward only, so `main` stays a straight line:

  ```sh
  git checkout main
  git merge --ff-only <branch>
  git push
  git branch -d <branch>
  git push origin --delete <branch>
  ```

- If `--ff-only` refuses, the branch is behind `main`: rebase it on `main`
  (`git rebase main`, then `git push --force-with-lease`) and merge again.

## Migrations

- A migration that has reached `main` has run in production. It is never
  edited, renamed or deleted afterwards; a change is a new migration.
- A migration only on an unmerged branch may still be rewritten or dropped:
  first migrate back below it locally
  (`manage.py migrate <app> <previous>`), then change it.
- Data migrations use the historical models (`apps.get_model`), never
  imports from the app, so they keep working as the code changes. They
  check their result and stop with a clear message rather than leave data
  half done.
- PostgreSQL will not alter a table in the transaction that just updated
  its rows' foreign keys: fill a new column in one migration, make it
  required in the next.
- Before merging: `make migrate`, then `make check-migrations`.

## Translations

The site is in English and French. Customer-facing text is marked for
translation; ops is English only. After changing such text:

```sh
make i18n                         # updates and compiles locale/fr
git add locale/
git commit -m "Compile translations"
```

## Personal files

Notes and scratch files that are yours alone are never committed. Name them
`<name>.local.<ext>` (`docs/todos.local.md`) or keep them in a `local/`
folder; `.gitignore` leaves both out.

## Deploys

Railway deploys `main`. The start command runs `manage.py migrate` first, so
a deploy applies new migrations on its own; the deploy log shows each one
(`Applying products.0008_productvariant... OK`). A migration that stops
changes nothing (each runs in one transaction) and the log says why.
