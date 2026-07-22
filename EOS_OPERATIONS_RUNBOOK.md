# EOS Operations Runbook

**Status:** current · **Audience:** the founder, at activation time · **Nature:** step-by-step for the founder-controlled activation lifecycle.

> **No real nonce appears in this runbook.** Wherever a nonce is required, generate a fresh high-entropy value yourself and substitute it for the placeholder `<FRESH_NONCE>`. The historical retired nonce is permanently rejected (`ACTIVATION_NONCE_RETIRED`) and must never be reused. Each step below is a **separate founder gate**; none is executed by this document.

---

## 0. Preconditions (verify before starting)

- `main` is green on required checks (`Validate Terraform`, `GitGuardian`).
- The Model B compatibility chain validates on the current `main`.
- Mission #26 has: exactly **1** authorization event that is **structurally superseded**, **0** attempts, **0** consumptions.
- The `outputs/eos-activation-readiness/` snapshot validates (`scripts/engineering-os/validate-activation-readiness ...`).

If the current authorization is the superseded (pre-identity-separation) one, activation proceeds by issuing a **replacement** authorization (below). The model supports this without rewriting history.

---

## 1. `/eos authorize-baseline <FRESH_NONCE>`

Post on **issue #26**:

```
/eos authorize-baseline <FRESH_NONCE>
```

**Nonce rules:** fresh, high-entropy, ≥ 32 chars, charset `[A-Za-z0-9._:-]`, never previously used; **must not equal the retired nonce**.

**Expected success:** a `test_integrity.baseline.authorized` event is appended, binding historical baseline identity, active-execution identity (the live checkout), and a valid Model B compatibility proof.

**Validate:** authenticate the event (hash recomputes, schema/chain valid); confirm exactly one usable authorization; confirm the compatibility proof validates against `main`.

**Expected failure states (fail closed, no event appended):**
- `ACTIVATION_NONCE_RETIRED` — you reused a retired/prior nonce.
- `COMPATIBILITY_CHAIN_*` — the chain does not validate (e.g., the invariant surface drifted, an undeclared merge parent, a range gap).
- `ACTIVATION_COMMIT_MISMATCH` / `ACTIVATION_TREE_MISMATCH` — the default branch advanced past the authorized execution identity.

---

## 2. `/eos attempt-baseline <SAME_NONCE>`

Post on **issue #26** using the **same** nonce:

```
/eos attempt-baseline <FRESH_NONCE>
```

**Expected success:** a `test_integrity.baseline.consumption_attempted` event, `consumption_result: attempted`, `post_consumption_state: locked`.

**Validate:** authenticate the attempted-consumption event and its workflow/run provenance.

**Expected failure states:**
- `ACTIVATION_AUTHORIZATION_REQUIRED` — no usable authorization.
- `ACTIVATION_ATTEMPT_REPLAY` — an attempt/consumption already exists.
- provenance mismatch — the checkout/run changed between authorization and attempt.

---

## 3. `/eos consume-baseline <SAME_NONCE>`

Post on **issue #26** using the **same** nonce:

```
/eos consume-baseline <FRESH_NONCE>
```

**Expected success:** a `test_integrity.baseline.consumed` event, `consumption_result: activated`, `post_consumption_state: active`. Single-use lockout is now permanent.

**Validate:** authenticate the consumed event; confirm baseline activation; confirm lockout by attempting any reuse (must fail closed):
- a second `authorize-baseline` → replay/authority failure,
- reuse of any prior nonce → `ACTIVATION_NONCE_RETIRED`,
- a second attempt/consume → replay failure.

**Expected failure states:**
- `ACTIVATION_ATTEMPT_REQUIRED` — no authenticated attempt exists.
- `ACTIVATION_CONSUMPTION_REPLAY` — already consumed.

---

## 4. Test Integrity activation verification

After consumption, confirm production Test Integrity passes on `main`:
- Trigger / observe the Test Integrity check on the default branch.
- **Expected:** `allowed: true` — the corpus-wide pre-activation ambiguity clears once the baseline is active.
- If it still denies, do **not** suppress it. Investigate: the canonical findings must be resolved through the activated baseline, not by exclusion.

---

## 5. Deployment (separate founder gate)

Deployment is **not** part of activation and is not exercised by the EOS. Deployment record `5528959623` remains `inactive` (accidental API-audit artifact; preserve it). Any deployment is a separate, explicit founder decision.

---

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `ACTIVATION_NONCE_RETIRED` | reused the retired or a prior nonce | generate a brand-new nonce |
| `COMPATIBILITY_CHAIN_PARENT_UNDECLARED` | a merge parent outside the range is not a declared pre-baseline ancestor | inspect the range; the builder declares verified pre-baseline parents |
| `COMPATIBILITY_INVARIANT_VIOLATED` | the baseline generator/analyzer surface changed in-range | the invariant surface is prohibited from change; a real change requires a new reviewed baseline (founder decision) |
| `ACTIVATION_COMMIT_MISMATCH` | `main` advanced after authorization | re-authorize against the current head |
| Test Integrity still denies after consume | findings not resolved through the baseline | investigate; never suppress or exclude |

All rejections are fail-closed: no event is appended, no nonce is consumed, no partial state is left.
