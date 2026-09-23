from scripts.re_evaluate_experiment2 import classify_revision_result, classify_pair, verified_f2p


def record():
    return {
        "status": "TEST",
        "hypothesis": "FileWriter should preserve non-ASCII output and not raise UnicodeEncodeError under an ASCII locale.",
        "potential_failure": "UnicodeEncodeError while writing the trace",
        "oracle": {
            "expected_behavior": "The public call returns and the UTF-8 trace contains the value.",
            "target_evidence": "pysnooper/tracer.py FileWriter.write uses implicit encoding.",
        },
    }


def test_target_exception_can_be_meaningful_f2p():
    rec = record()
    buggy = "pysnooper/tracer.py:134: UnicodeEncodeError: ascii codec can't encode"
    fixed = ". 1 passed"
    b = classify_revision_result(rec, buggy, 1)
    f = classify_revision_result(rec, fixed, 0)
    assert b["failure_type"] == "TARGET_EXCEPTION"
    assert f["state"] == "PASS"
    assert classify_pair(b, f, rec) == "EXCEPTION_F2P"
    assert verified_f2p(b, f, rec, same_test=True)


def test_unrelated_exception_is_mechanical():
    rec = record()
    buggy = "E   ImportError: cannot import generated fixture"
    result = classify_revision_result(rec, buggy, 1)
    assert result["state"] == "MECHANICAL_FAILURE"


def test_unsupported_oracle_cannot_be_f2p():
    rec = record()
    rec["oracle"]["target_evidence"] = ""
    buggy = "pysnooper/tracer.py:134: UnicodeEncodeError"
    fixed = ". 1 passed"
    b = classify_revision_result(rec, buggy, 1)
    f = classify_revision_result(rec, fixed, 0)
    assert classify_pair(b, f, rec) == "UNSUPPORTED_ORACLE"
    assert not verified_f2p(b, f, rec, same_test=True)
