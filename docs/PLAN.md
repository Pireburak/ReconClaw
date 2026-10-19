# ReconClaw Plan

Planned work only. Nothing here exists yet. When a phase is built, document it in `lat.md/` and tick it here.

**Rules:** one step at a time, verify each step before the next, no skipped step, no non-working part.

| Phase | Name | Status |
|---|---|---|
| S | Staging environment | Planned |

---

## Phase S: Staging environment

**Why:** ReconClaw handles OAuth logins, PayTR payments and a background scheduler. These must be testable without touching production data or real customers.

**Today:** only local and production exist (see `lat.md/devops-and-environments.md`).

| Step | Do | Done when |
|---|---|---|
| S1 | Add `.env.staging.example` with its own `DOMAIN`, `PUBLIC_URL` and a separate `RECONCLAW_DB` path | A staging instance starts with no production values |
| S2 | Add `docker-compose.staging.yml` (override) with its own data volume and project name | `docker compose` for staging and production can run side by side without sharing a volume |
| S3 | Set `ALLOW_PRIVATE_TARGETS=false` and `REQUIRE_TARGET_VERIFICATION=true` | A private-IP scan is rejected on staging |
| S4 | Keep `PAYTR_TEST_MODE=true` and use test merchant credentials | A test payment completes and no real charge is made |
| S5 | Register separate OAuth apps with the staging callback URL | Google, GitHub, Microsoft and Apple login each succeed on staging |
| S6 | Use a test webhook URL for monitors; keep `SCHEDULER_ENABLED=true` | A monitor run on staging posts only to the test channel |
| S7 | Add a short deploy and rollback note to `docs/YAYIN.md` | A second person can deploy staging from the note alone |
| S8 | Document staging in `lat.md/devops-and-environments.md` and run `lat check` | Graph matches the repository |

**UX:** show a visible "STAGING" label (text, not color alone) in the top bar so it is never mistaken for production. Follow `docs/UX.md` sections 1 and 4.
