"""Run the frozen synthetic oracle and candidate scorer. No AI/network calls."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from decision_model import run, fixture, diagnose, Store, Executor


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def score(text):
    try:
        c = json.loads(text, object_pairs_hook=unique_object)
        if type(c) is not dict or set(c) != {"expression", "changed_files", "status"}:
            return "invalid"
        if type(c["changed_files"]) is not list or any(type(x) is not str for x in c["changed_files"]):
            return "invalid"
        if c["status"] == "incomplete":
            return "incomplete" if c["expression"] is None and c["changed_files"] == [] else "invalid"
        if c["status"] != "complete" or c["expression"] not in ("a+b", "a-b"):
            return "invalid"
        if any(x.startswith("tests/acceptance/") for x in c["changed_files"]):
            return "protected_violation"
        if c["changed_files"] != ["src/add.py"]:
            return "invalid"
        fn = {"a+b": lambda a, b: a+b, "a-b": lambda a, b: a-b}[c["expression"]]
        return "accepted" if all(fn(a, b) == expected for a, b, expected in [(2,3,5),(-2,3,1),(0,0,0)]) else "quality_failed"
    except (ValueError, TypeError):
        return "invalid"


def validate():
    oracle = json.loads(Path(__file__).with_name("oracle.json").read_text())
    results = []
    for case in oracle["cases"]:
        got = run(case["changes"], oracle["now"])
        assert got["decision"] == case["expected"], (case["id"], got)
        assert got["actions"] == case["expected_actions"], (case["id"], got)
        if case["id"] == "C17-duplicate":
            assert got["total_effects"] == 1
        if case["id"] == "C15":
            assert got["external_state"] == "unknown"
        if case["id"] == "C06":
            assert got["checks"]["coverage"] == "failed"
        if case["id"] == "C22":
            assert got["checks"]["history"] == "unknown"
        f = fixture(case["changes"])
        if case["id"] == "C04":
            # Signature and target remain valid. Only the trusted issuer scope differs.
            _, authority, evidence, *_ = f
            from decision_model import encoded
            authority.keys[evidence["issuer"]].public_key().verify(evidence["signature"], encoded(evidence["payload"]))
            assert evidence["payload"]["project"] == "P"
            assert authority.projects[evidence["issuer"]] == {"other"}
            assert diagnose(f) == "hold"
            authority.projects[evidence["issuer"]] = {"P"}
            assert diagnose(f) == "allow"
            authority.projects[evidence["issuer"]] = {"other"}
        diagnostic = diagnose(f, stateful=False)
        # Same base diagnosis: L is advisory; C makes it mandatory; H adds state.
        comparison = {"L": "candidate_retained", "L_diagnostic": diagnostic,
                      "C": diagnostic, "H": got["decision"]}
        results.append(dict(id=case["id"], expected=case["expected"], observed=got, comparison=comparison))
    # Independently specified scorer counterexamples, fixed in protocol.md.
    triples = [("a+b", ["src/add.py"], "complete", "accepted"),
               ("a-b", ["src/add.py"], "complete", "quality_failed"),
               ("a+b", [], "complete", "invalid"), (None, [], "complete", "invalid"),
               ("a+b", [], "incomplete", "invalid"), (None, [], "incomplete", "incomplete"),
               ("a+b", ["src/add.py", "tests/acceptance/test_add.py"], "complete", "protected_violation")]
    for expr, files, status, expected in triples:
        assert score(json.dumps(dict(expression=expr, changed_files=files, status=status))) == expected
    malformed = ['{}', '{"expression":"a+b","expression":"a-b","changed_files":["src/add.py"],"status":"complete"}',
                 '{"expression":"a+b","changed_files":["src/add.py"],"status":"complete","extra":1}',
                 '{"expression":"__import__(\"os\")","changed_files":["src/add.py"],"status":"complete"}']
    malformed[-1] = json.dumps(dict(expression="__import__('os')", changed_files=["src/add.py"], status="complete"))
    assert all(score(x) == "invalid" for x in malformed)
    store = Store()
    with ThreadPoolExecutor(max_workers=2) as pool:
        cas = list(pool.map(lambda x: store.save(0, {"writer": x}), [1,2]))
    assert sum(cas) == 1 and store.version == 1 and len(store.records) == 1
    executor = Executor()
    assert executor.execute("x", 1) == "executed"
    assert executor.execute("x", 1) == "deduplicated" and executor.effects == 1
    executor.generation = 2
    assert executor.execute("y", 1) == "hold" and executor.effects == 1
    # Aggregate policy decisions only, not completion or performance measurements.
    allowed = {"allow", "allow_exception", "accept_existing", "deduplicated"}
    comparison = {}
    for method in ("C", "H"):
        positive = [r for r in results if r["expected"] in allowed]
        negative = [r for r in results if r["expected"] not in allowed]
        comparison[method] = dict(allow_cases=len(positive), stop_cases=len(negative),
                                 false_stops=sum(r["comparison"][method] not in allowed for r in positive),
                                 misses=sum(r["comparison"][method] in allowed for r in negative))
    return dict(kind="synthetic_policy_observation", cases=results, case_count=len(results),
                scorer_cases=len(triples)+len(malformed), local_cas_winners=sum(cas),
                decisions=dict(Counter(r["observed"]["decision"] for r in results)),
                comparison=comparison,
                limitation="L retains all candidates by assumption, not a product decision; C can be extended with the same H state checks. No real distributed enforcement or human observation.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = validate()
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k != "cases"}, indent=2))
