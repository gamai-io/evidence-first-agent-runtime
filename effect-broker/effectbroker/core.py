import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from .signing import HmacSigner

SCHEMA = "effect-broker/0.1"
LAB_KEY = b"effect-broker-lab-key-not-for-production"


class BrokerError(Exception):
    code = "E_BROKER"


class PolicyDenied(BrokerError):
    code = "E_POLICY"


class ScopeMismatch(BrokerError):
    code = "E_SCOPE"


class GrantInvalid(BrokerError):
    code = "E_GRANT"


class NoEffect(BrokerError):
    code = "E_NO_EFFECT"


class Replay(BrokerError):
    code = "E_REPLAY"


class Stale(BrokerError):
    code = "E_STALE"


def canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(obj: Any) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()


def digest_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@dataclass(frozen=True)
class Intent:
    task_id: str
    action: str
    target: str
    scope: str
    expected: Any
    deadline_s: float = 5.0
    idempotency_key: str = ""
    claimed_at: Optional[float] = None

    def body(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "action": self.action,
            "target": self.target,
            "scope": self.scope,
            "expected": self.expected,
            "deadline_s": self.deadline_s,
            "idempotency_key": self.idempotency_key,
        }

    def hash(self) -> str:
        return digest(self.body())


@dataclass(frozen=True)
class Grant:
    grant_id: str
    intent_hash: str
    expires_at: float
    sig: str

    def token(self) -> Dict[str, Any]:
        return {"grant_id": self.grant_id, "intent_hash": self.intent_hash, "expires_at": self.expires_at, "sig": self.sig}


@dataclass(frozen=True)
class Effect:
    effect_id: str
    intent_hash: str
    nonce: str
    result: Dict[str, Any]
    executed_at: float
    sig: str

    def token(self) -> Dict[str, Any]:
        return {
            "effect_id": self.effect_id,
            "intent_hash": self.intent_hash,
            "nonce": self.nonce,
            "result": self.result,
            "executed_at": self.executed_at,
            "sig": self.sig,
        }


@dataclass(frozen=True)
class CommitToken:
    token_id: str
    intent_hash: str
    effect_id: str
    nonce: str
    probe: Dict[str, Any]
    verdict: str
    issued_at: float
    expires_at: float
    sig: str

    def token(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "intent_hash": self.intent_hash,
            "effect_id": self.effect_id,
            "nonce": self.nonce,
            "probe": self.probe,
            "verdict": self.verdict,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "sig": self.sig,
        }


@dataclass
class Policy:
    actions: Dict[str, Any] = field(default_factory=dict)
    ttl_s: float = 30.0
    token_ttl_s: float = 3600.0
    max_deadline_s: float = 60.0


def verdict_for(claim_status: str, truth_ok: bool, verifiable: bool = True) -> str:
    if not verifiable:
        return "unverifiable"
    if claim_status == "success":
        return "pass" if truth_ok else "false_success"
    if claim_status in ("failure", "partial"):
        return "true_failure" if not truth_ok else "false_failure"
    return "unverifiable"


class Broker:
    def __init__(
        self,
        adapters: Dict[str, Any],
        policy: Optional[Policy] = None,
        key: bytes = LAB_KEY,
        signer: Any = None,
        now: Optional[Callable[[], float]] = None,
        evidence=None,
    ):
        self.adapters = adapters
        self.policy = policy or Policy()
        self.signer = signer or HmacSigner(key)
        self.now = now or time.time
        self.evidence = evidence
        self._grants: Dict[str, Dict[str, Any]] = {}
        self._effects: Dict[str, Dict[str, Any]] = {}
        self._tokens: Dict[str, Dict[str, Any]] = {}
        self._idem: Dict[str, str] = {}
        self._used_tokens: set = set()

    def _sign(self, body: Dict[str, Any]) -> str:
        return self.signer.sign(canon(dict(body, alg=self.signer.alg)))

    def _verify(self, body: Dict[str, Any], sig: str) -> bool:
        return self.signer.verify(canon(dict(body, alg=self.signer.alg)), sig)

    def _record(self, kind: str, **fields) -> None:
        if self.evidence is not None:
            self.evidence.append({"schema": SCHEMA, "kind": kind, "alg": self.signer.alg, **fields})

    def authorize(self, intent: Intent) -> Grant:
        if intent.action not in self.adapters:
            raise PolicyDenied("action not allowed: %s" % intent.action)
        if intent.deadline_s <= 0 or intent.deadline_s > self.policy.max_deadline_s:
            raise PolicyDenied("deadline out of policy bounds: %s" % intent.deadline_s)
        adapter = self.adapters[intent.action]
        if not adapter.scope_ok(intent.target, intent.scope):
            raise ScopeMismatch("target outside scope: %s" % intent.target)
        grant_id = "g_" + uuid.uuid4().hex[:20]
        expires_at = self.now() + self.policy.ttl_s
        body = {"grant_id": grant_id, "intent_hash": intent.hash(), "expires_at": expires_at}
        grant = Grant(grant_id=grant_id, intent_hash=body["intent_hash"], expires_at=expires_at, sig=self._sign(body))
        self._grants[grant_id] = {"intent": intent, "used": False, "body": body, "sig": grant.sig}
        self._record("grant", grant_id=grant_id, intent_hash=grant.intent_hash, action=intent.action, target=intent.target)
        return grant

    def _grant_state(self, grant: Grant) -> Dict[str, Any]:
        state = self._grants.get(grant.grant_id)
        if state is None:
            raise GrantInvalid("unknown grant")
        if not self._verify(state["body"], grant.sig):
            raise GrantInvalid("grant signature mismatch")
        if grant.intent_hash != state["intent"].hash():
            raise GrantInvalid("grant bound to another intent")
        if self.now() > state["body"]["expires_at"]:
            raise GrantInvalid("grant expired")
        if state["used"]:
            raise GrantInvalid("grant already used")
        return state

    def execute(self, grant: Grant, payload: Dict[str, Any]) -> Effect:
        state = self._grant_state(grant)
        intent = state["intent"]
        if intent.idempotency_key and intent.idempotency_key in self._idem:
            return self._effects[self._idem[intent.idempotency_key]]["effect"]
        adapter = self.adapters[intent.action]
        result = adapter.execute(intent, payload)
        nonce = "n_" + uuid.uuid4().hex[:24]
        effect_id = "e_" + uuid.uuid4().hex[:20]
        executed_at = self.now()
        body = {"effect_id": effect_id, "intent_hash": intent.hash(), "nonce": nonce, "result": result, "executed_at": executed_at}
        effect = Effect(effect_id=effect_id, intent_hash=body["intent_hash"], nonce=nonce, result=result, executed_at=executed_at, sig=self._sign(body))
        state["used"] = True
        self._effects[effect_id] = {"intent": intent, "effect": effect, "effect_body": body, "grant": grant}
        if intent.idempotency_key:
            self._idem[intent.idempotency_key] = effect_id
        self._record("effect", effect_id=effect_id, intent_hash=effect.intent_hash, nonce=nonce, action=intent.action, target=intent.target)
        return effect

    def probe(self, intent: Intent, effect: Optional[Effect] = None) -> Dict[str, Any]:
        adapter = self.adapters[intent.action]
        return adapter.probe(intent, effect)

    def commit(self, effect: Effect, claim_status: str = "success") -> Dict[str, Any]:
        state = self._effects.get(effect.effect_id)
        if state is None:
            raise NoEffect("unknown effect")
        if not self._verify(state["effect_body"], effect.sig):
            raise GrantInvalid("effect signature mismatch")
        intent = state["intent"]
        probe = self.probe(intent, effect)
        claimed_at = intent.claimed_at if intent.claimed_at is not None else self.now()
        late = claimed_at > effect.executed_at + intent.deadline_s
        verdict = verdict_for(claim_status, probe.get("ok", False), verifiable=not late)
        mismatch = None
        if verdict == "false_success":
            mismatch = probe.get("mismatch") or "M1"
        if late:
            mismatch = "M3"
        if verdict != "pass":
            self._record("verdict", effect_id=effect.effect_id, verdict=verdict, mismatch=mismatch, probe=probe)
            return {"verdict": verdict, "token": None, "probe": probe, "mismatch": mismatch}
        issued_at = self.now()
        token_id = "t_" + uuid.uuid4().hex[:20]
        expires_at = issued_at + self.policy.token_ttl_s
        body = {
            "token_id": token_id,
            "intent_hash": intent.hash(),
            "effect_id": effect.effect_id,
            "nonce": effect.nonce,
            "probe": probe,
            "verdict": verdict,
            "issued_at": issued_at,
            "expires_at": expires_at,
        }
        token = CommitToken(
            token_id=token_id,
            intent_hash=body["intent_hash"],
            effect_id=effect.effect_id,
            nonce=effect.nonce,
            probe=probe,
            verdict=verdict,
            issued_at=issued_at,
            expires_at=expires_at,
            sig=self._sign(body),
        )
        self._tokens[token_id] = {"intent": intent, "effect": effect, "token": token, "body": body}
        self._record("commit", token_id=token_id, effect_id=effect.effect_id, verdict=verdict, probe_sha256=probe.get("sha256"), mismatch=None)
        return {"verdict": verdict, "token": token, "probe": probe, "mismatch": None}

    def verify(self, token: CommitToken) -> Dict[str, Any]:
        state = self._tokens.get(token.token_id)
        if state is None:
            raise GrantInvalid("unknown commit token")
        body = {
            "token_id": token.token_id,
            "intent_hash": token.intent_hash,
            "effect_id": token.effect_id,
            "nonce": token.nonce,
            "probe": token.probe,
            "verdict": token.verdict,
            "issued_at": token.issued_at,
            "expires_at": token.expires_at,
        }
        if not self._verify(body, token.sig):
            raise GrantInvalid("commit token signature mismatch")
        if self.now() > token.expires_at:
            raise Stale("commit token expired")
        if token.token_id in self._used_tokens:
            raise Replay("commit token already verified")
        probe_now = self.probe(state["intent"], state["effect"])
        if probe_now.get("sha256") != token.probe.get("sha256") or not probe_now.get("ok", False):
            self._record("toctou", token_id=token.token_id, expected=token.probe.get("sha256"), observed=probe_now.get("sha256"))
            raise Stale("effect changed after commit (TOCTOU)")
        self._used_tokens.add(token.token_id)
        self._record("verify", token_id=token.token_id, verdict=token.verdict)
        return {"ok": True, "verdict": token.verdict, "probe": probe_now}

    def audit_claim(self, intent: Intent, claim_status: str = "success", effect: Optional[Effect] = None) -> Dict[str, Any]:
        probe = self.probe(intent, effect)
        claimed_at = intent.claimed_at if intent.claimed_at is not None else self.now()
        executed_at = effect.executed_at if effect is not None else self.now()
        late = claimed_at > executed_at + intent.deadline_s
        verdict = verdict_for(claim_status, probe.get("ok", False), verifiable=not late)
        mismatch = None
        if late:
            mismatch = "M3"
        elif verdict == "false_success":
            mismatch = probe.get("mismatch") or "M1"
        self._record("audit", intent_hash=intent.hash(), verdict=verdict, mismatch=mismatch, probe=probe)
        return {"verdict": verdict, "probe": probe, "mismatch": mismatch}
