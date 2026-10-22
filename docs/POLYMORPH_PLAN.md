# Polymorphic / immune runtime — research plan

Status: research plan, not a security guarantee. Defensive use only.

## 1. Šta je urađeno

Pregledan je VastVM lab (`76.71.171.67:40337`, Ubuntu 22.04, 10 vCPU,
32 GB RAM, GTX 1660 SUPER 6 GB) i lokalni `gamai-labs`. Korišteno je 5
istraživačkih agenata:

1. inventar laba (`/opt/p2`–`/opt/p5`, immune, proofgate, PROTEAN, phone, APK, llama.cpp),
2. defensive polimorfizam / mutacija / imunitet,
3. slojevi izvan LLM-a i deterministic routera + fuzije,
4. GAMA Lang / GAMA OS effect-typed dizajn,
5. adversarial review plana i granice tvrdnji.

## 2. Nalaz: šta lab stvarno ima

| Sloj | Dokazano | Slabost |
|---|---|---|
| seccomp | 48 dozvoljenih syscall-a, 0 izvan allowlist-e, socket/ptrace/mount EPERM | Docker control plane trenutno ne radi (client 29 / daemon 24 API mismatch) |
| gVisor | checkpoint 23 ms, restore 124 ms, stanje očuvano | n=1, nema p95/failure rate |
| Firecracker | snapshot resume ~6 ms, fork 2 VM | 2 orphan VM-a još rade; nema config/report za snapshot creation |
| Kata | pod boot 7 s, guest kernel 6.18 | nema mrežu (`cls_flower`/`act_*` nedostaju) |
| GPU | dvije CUDA alokacije se ne izoluju; B OOM | nema MIG na GTX 1660 SUPER; nema VRAM izolacije |
| eBPF | 36 fork / 16 exec / 3 open; cgroup atribucija | nema `syscalls:*` tracepointa; uprobe-only |
| proofgate | 10 confirmed / 2 refuted / 0 unverified; 16 testova | nije spojen na harness; evidence može biti caller-supplied |
| agent-immunity | ASR 100% → 0%; 9 antitijela | simulirani LLM; 10% false denial u jednoj postavci |
| PROTEAN | genome+HMAC lease+substrate ladder+evidence+antibody | lease se ne veže na proof/report; ključ je na istom hostu |
| telefon | 7/7 deterministic skillova; llama.cpp 92.7 tok/s | bridge mrtav; OCR tap 12/25; nema goal_done |
| reprodukcija | pojedinačni skripti rade | nema clean-contract provision za p2–p5; disk 84% |

## 3. Teza

Polimorfizam napada **prepoznavač**. Ne treba se takmičiti u prepoznavanju
mutacija; treba ograničiti **šta program smije**. Mutacija tada postaje
generator testova, ne prijetnja.

Tri invarijante:

1. **Capability invarijanta** — mutant ne dobija novu efektnu moć. Ako traži
   novi syscall, mrežu, exec ili fajl, lease ga odbija.
2. **Effect invarijanta** — dva program su ista klasa ako imaju isti efektni
   potpis i isti ugovor; sintaksa, imena i algoritam smiju varirati.
3. **Evidence invarijanta** — tvrdnja "urađeno" bez vanjskog dokaza ostaje
   `unverified`, nikad `confirmed`.

Zato termin **"benigni polimorfni agent"** mijenjamo u **"substrate diversity /
moving-target defense"**; "polymorphic virus" ne koristimo javno.

## 4. Šta graditi

### Track A — `polymorph/` (najmanji falsifikacijski eksperiment)

```
polymorph/
  mutators/       # samo benigni, semantics-preserving operatori
  corpus/         # 200 benignih seedova, split po operatoru
  runtime/        # PROTEAN adapter, trace, normalizer
  oracles/        # effect subset, output predicate, proofgate
  bench/          # seed x mutant x substrate
  ETHICS.md       # zabranjeni oblici (C2, persistence, evasion)
```

Prvi commit: E1 samo — 20 benignih + 40 zlonamjernih varijanti istog zadatka;
40/40 zlonamjernih mora biti odbijeno **prije izvršenja**, 20/20 benignih
proći, 0 capability gain, <20 ms.

### Track B — lease-bound proof chain

Spojiti PROTEAN lease (`lease_id`, `genome_hash`, `cmd_sha`, `expiry`,
`nonce`) i proofgate report u jedan potpisan bundle. Verifier provjerava:
hash, potpis, lease nije istekao, `cmd_sha` odgovara tvrdnji, `out_sha`
odgovara evidence liniji. Replay se odbija po `nonce`/`audience`.

### Track C — GAMA Lang / GAMA OS MVP

7 modula: `effects`, `genome`, `lease`, `typecheck`, `host`, `evidence`,
`cbr`. Plan IR prije pune sintakse:

```json
{"plan":"p1","steps":[
 {"op":"fs.read","args":{"path":"/in/a.csv"},"out":"v1"},
 {"op":"model.infer","args":{"model":"sha256:...","seed":7},"out":"v2"},
 {"op":"fs.write","args":{"path":"/out/a.json"},"out":"w3"},
 {"op":"prove","args":{"claim":"sha256_eq(v2,/out/a.json)","witnesses":["w3"]}}
]}
```

Pravila: efektni red je tip; `Proven<T>` je obavezan za vanjske akcije;
`Advisory` (CBR/antitijela) nikad nije `Cap`; runtime ne mijenja genom;
backend se bira deterministicno, a ako izabrani backend nije dostupan — deny,
bez tihog downgrade-a.

## 5. Slojevi i fuzije (prioritet)

| Prioritet | Sloj | Šta stvarno garantuje | Ne tvrditi |
|---|---|---|---|
| 1 | capability lease + effect typing | mutant ne prelazi lease | nije formalna verifikacija |
| 2 | lease-bound proof chain | tvrdnja vezana za izvršenje | ne dokazuje istinitost izvora |
| 3 | eBPF + seccomp + FS/net diff | nezavisna opservacija | nije potpuna (io_uring, vDSO, TLS) |
| 4 | SMT plan preflight | redoslijed u **modelu** | ne garantuje stvarni sistem |
| 5 | conformal abstention | marginalna pokrivenost pod exchangeability | ne pod shiftom |
| 6 | substrate diversity / N-version | hvata environment coupling | nije security boundary |
| 7 | CBR + repair | ubrzava, pamti | nije autoritet; može se otrovati |
| 8 | mechanism design / dual control | ekonomska i ljudska kontrola | nije tehnička izolacija |

Najveće nove fuzije: **effect-typed GAMA Lang + lease**, **lease + proofgate**,
**taint + sink declassification**, **deterministic router + SMT preflight**,
**substrate equivalence matrix**, **CBR + verifier**.

## 6. 14-dnevni plan (1 inženjer, <$2/dan)

| Dan | Deliverable | Gate |
|---|---|---|
| 1 | threat model, 100 benign + 50 holdout (drugi model), env manifest, snapshot | hashes pinned |
| 2 | fix Docker API; 4-substrate matrix; downgrade test | nema tihog fallbacka |
| 3–4 | E1: substrate divergence + fingerprint | ako >2% divergencije, "equivalence" se briše |
| 5–6 | E2: TOCTOU (symlink, PATH, 302, env) + openat2/memfd | 0/200 verified mismatch |
| 7–8 | E3: immunity holdout (60 payloada, 6 encodinga, 5 kanala) | ASR <10%, FDR <5% ili immunity postaje filter |
| 9 | E4: mutation oracle (100 equivalent + 100 malicious) | false-kill/survive <10% |
| 10 | E5: CBR/antibody poisoning + promotion gate | nema top-1 izvršenja bez reviewa |
| 11 | E6: conformal coverage (i.i.d. / shift) | tvrdnja samo ako prođe |
| 12 | eBPF/gVisor blind-spot + GPU prefix-cache test | nema multi-tenant tvrdnje |
| 13 | cut list + key custody/nonce + go/no-go | eksplicitni cutovi |
| 14 | clean reproduction svih brojeva + REVIEW.md | svaki broj reproducible |

## 7. Prva 3 eksperimenta (odmah)

1. **Docker + repeats**: `systemctl restart docker`; 20× gVisor checkpoint/restore
   i 20× Firecracker resume; p50/p95/failure rate.
2. **E1 mutation widening**: 60 varijanti; 40 zlonamjernih dodaje `net`, `exec`,
   symlink ili manifest drift; mjeri 0 egress, 0 spawn, 40/40 deny.
3. **Lease-bound proof**: jedan PROTEAN run → proofgate report + lease bundle;
   tamper claim/lease → verifier mora vratiti false.

## 8. Granica tvrdnji

Ne tvrditi: "sandbox = safe", "substrate equivalence", "proof-carrying
execution", "0% ASR generalno", "conformal guarantee" bez E6, "multi-tenant
safe", "GPU izolacija", "benigni polimorfni" kao security pojam.

Tvrditi samo: "na našem korpusu, mutant koji traži novu efektnu moć je odbijen;
dokazi su tamper-evident; izmjereni su p50/p95; generalizacija na adaptivnog
napadača nije dokazana."
