"""Synthetic local model of R1-R8. NOT a Hub service or security boundary.

Checks/approvals are synthetic signed fixtures. Only signature verification is
cryptographic; clocks, roles, persistence and executor are injected local models.
"""
from copy import deepcopy
import json
import threading
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class Authority:
    def __init__(self):
        self.keys = {name: Ed25519PrivateKey.generate() for name in ("checker", "owner", "delegate")}
        self.roles = {"checker": {"evidence"}, "owner": {"approval", "exception", "delegation"}, "delegate": {"approval"}}
        # Trusted issuer registry, independent of claims in the signed payload.
        self.projects = {name: {"P"} for name in self.keys}

    def sign(self, payload, issuer):
        return {"payload": deepcopy(payload), "issuer": issuer,
                "signature": self.keys[issuer].sign(encoded(payload))}

    def verify(self, envelope, kind, target):
        try:
            issuer, p = envelope["issuer"], envelope["payload"]
            self.keys[issuer].public_key().verify(envelope["signature"], encoded(p))
            return (kind in self.roles[issuer] and p["kind"] == kind
                    and p["format"] == "local-fixture-1" and p["project"] == "P"
                    and p["project"] in self.projects[issuer]
                    and all(p[k] == v for k, v in target.items()))
        except (InvalidSignature, KeyError, TypeError, ValueError):
            return False


class Store:
    """In-memory compare-and-swap. No real Git or distributed durability."""
    def __init__(self, available=True):
        self.version = 0
        self.available = available
        self.records = []
        self.lock = threading.Lock()

    def save(self, expected, record):
        with self.lock:
            if not self.available or self.version != expected:
                return False
            self.records.append(deepcopy(record))
            self.version += 1
            return True


class Executor:
    def __init__(self, generation=1, revoked=False):
        self.generation = generation
        self.revoked = revoked
        self.commands = set()
        self.effects = 0

    def execute(self, command, generation):
        if self.revoked or generation != self.generation:
            return "hold"
        if command in self.commands:
            return "deduplicated"
        self.commands.add(command)
        self.effects += 1
        return "executed"


def fixture(changes):
    s = dict(candidate="A", policy="P1", environment="E", if_db="V", requirements="Q",
             approval_expiry=200, approval="present", clock_known=True,
             revocation_known=True, revoked=False, consumer_known=True,
             execution_slots=1, review_slots=1, generation=1, save_ok=True,
             response="new", coverage="passed", unit="passed", history="passed")
    s.update(changes)
    a = Authority()
    a.projects["checker"] = {s.get("issuer_project", "P")}
    base = dict(format="local-fixture-1", project="P", candidate="A", policy="P1",
                environment="E", if_db="V", requirements="Q")
    checks = {name: s[name] for name in ("unit", "coverage", "history")}
    checks.pop(s.get("missing_check"), None)
    if s.get("tamper"):
        checks["unit"] = "failed"
    evidence = a.sign(dict(base, kind="evidence", checks=checks), "checker")
    if s.get("tamper"):
        evidence["payload"]["checks"]["unit"] = "passed"  # after signing
    approval = a.sign(dict(base, kind="approval", expiry=s["approval_expiry"], action="submit"),
                      "delegate" if s.get("delegated") else "owner")
    exception = None
    if s.get("exception"):
        exception = a.sign(dict(base, kind="exception", condition=s["exception"],
                               expiry=s.get("exception_expiry", 200), revoked=s.get("exception_revoked", False),
                               owner="synthetic-owner", residual="synthetic unresolved issue",
                               resolution="recheck before expiry", action="submit"), "owner")
    delegation = a.sign(dict(base, kind="delegation", delegate="delegate", action="submit",
                             organization="O", parent_organization="O", parent_project="P",
                             delegated_project=s.get("delegate_project", "P"),
                             expiry=200, parent_expiry=s.get("parent_expiry", 200),
                             parent_revoked=s.get("parent_revoked", False),
                             redelegated=s.get("redelegated", False)), "owner")
    return s, a, evidence, approval, exception, delegation


def diagnose(f, now=100, stateful=True):
    s, a, evidence, approval, exception, delegation = f
    # Stateless comparison deliberately fixes freshness to the original subject.
    target = {k: (s[k] if stateful else v) for k, v in
              dict(candidate="A", policy="P1", environment="E", if_db="V", requirements="Q").items()}
    if not a.verify(evidence, "evidence", target):
        return "hold"
    if s["approval"] != "present" or not a.verify(approval, "approval", target) or approval["payload"]["action"] != "submit":
        return "hold"
    if not stateful:
        return "allow" if all(evidence["payload"]["checks"].get(k) == "passed"
                              for k in ("unit", "coverage", "history")) else "hold"
    if not s["clock_known"] or not s["revocation_known"] or s["revoked"] or now >= approval["payload"]["expiry"]:
        return "hold"
    if approval["issuer"] == "delegate":
        if not a.verify(delegation, "delegation", target):
            return "hold"
        d = delegation["payload"]
        if (d["parent_revoked"] or d["redelegated"] or d["delegated_project"] != d["parent_project"]
                or d["organization"] != d["parent_organization"] or d["action"] != "submit"
                or d["delegate"] != approval["issuer"] or d["expiry"] > d["parent_expiry"]
                or now >= min(d["expiry"], d["parent_expiry"])):
            return "hold"
    checks = evidence["payload"]["checks"]
    unmet = {k for k in ("unit", "coverage", "history") if checks.get(k) != "passed"}
    outcome = "allow"
    if unmet:
        if not exception or not a.verify(exception, "exception", target):
            return "hold"
        e = exception["payload"]
        condition = e["condition"]
        eligible = (condition == "coverage" and checks.get(condition) == "failed") or (condition == "history" and checks.get(condition) == "unknown")
        if (not eligible or unmet != {condition} or e["revoked"] or now >= e["expiry"]
                or not all(e.get(k) for k in ("owner", "residual", "resolution")) or e["action"] != "submit"):
            return "hold"
        outcome = "allow_exception"
    if not s["consumer_known"] or s["generation"] != 1:
        return "hold"
    return outcome


def run(changes, now=100):
    f = fixture(changes)
    s = f[0]
    actions = dict(new_effects=0, dispatches=0, new_runs=0, imports=0, cancel_requests=0)
    store = Store(s["save_ok"])
    executor = Executor(revoked=s.get("effect_revoked", False))
    if s.get("duplicate"):
        executor.execute("command-1", 1)
    initial_effects = executor.effects
    result = diagnose(f, now)
    if result != "hold":
        if s.get("cancel_requested") and s.get("late_result"):
            result = "quarantine"
        elif s.get("effect_revoked"):
            result = "cancel_unknown" if s.get("running") else "hold"
            actions["cancel_requests"] = int(s.get("running", False))
        elif s["response"] == "unknown":
            result = "hold"
        elif s["execution_slots"] <= 0 or s["review_slots"] <= 0:
            result = "hold"
        elif not store.save(0, {"decision": result, "command": "command-1"}):
            result = "hold"
        elif s["response"] == "completed":
            result = "accept_existing"
            actions["imports"] = 1
        elif s.get("duplicate"):
            result = executor.execute("command-1", s["generation"])
        else:
            effect = executor.execute("command-1", s["generation"])
            if effect == "executed":
                actions.update(dispatches=1, new_runs=1)
            else:
                result = effect
    actions["new_effects"] = executor.effects - initial_effects
    return dict(decision=result, actions=actions, total_effects=executor.effects,
                external_state="unknown" if s["response"] == "unknown" or result == "cancel_unknown" else "modeled",
                checks=deepcopy(f[2]["payload"]["checks"]), stored=len(store.records))
