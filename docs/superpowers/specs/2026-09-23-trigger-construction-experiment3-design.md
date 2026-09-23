# Experiment 3 Trigger Construction Design

## Goal

Test whether freezing a structured-history bug mechanism and diversifying the trigger plan improves conversion from mechanism-matched hypotheses to verified buggy/fixed evidence.

## Research basis

The literature and engineering evidence point to a separation between diagnosis and reproduction. Issue2Test and ReProAgent explicitly separate issue/root-cause understanding from trigger/setup/assertion planning and use bounded execution feedback. Hypothesis demonstrates that structured input strategies make meaningful variation and shrinking practical. Coverage-guided fuzzing shows why reaching a relevant state matters beyond merely naming a path. Metamorphic and differential testing are useful when a stable relation or independent implementation oracle exists, but neither is a general fit for this single-revision Python target without adding assumptions.

Sources consulted:

- Issue2Test: https://arxiv.org/abs/2503.16320
- ReProAgent: https://github.com/iSEngLab/ReProAgent
- Hypothesis documentation: https://hypothesis.readthedocs.io/en/latest/
- Hypothesis shrinking guide: https://github.com/HypothesisWorks/hypothesis/blob/master/guides/strategies-that-shrink.rst
- OSS-Fuzz LLM target generation: https://google.github.io/oss-fuzz/research/llms/target_generation/
- Fuzzing with LLM-generated drivers: https://arxiv.org/abs/2307.12469
- Metamorphic testing survey: https://eprints.whiterose.ac.uk/id/eprint/110335/
- Search-based test data generation: https://groups.csail.mit.edu/EVO-DesignOpt/gecco2011Proceedings/proceedings/p1859.pdf

## Selected intervention

The primary intervention is a generic, bounded Trigger Planner:

```text
frozen grounded hypothesis
  -> 4 structured trigger candidates
  -> cheap schema/relevance/diversity filter
  -> one executable pytest per retained trigger
  -> unchanged existing evaluator
```

The planner may use only the hypothesis, historical evidence already visible to structured condition C, and the existing target context. It must select trigger dimensions supported by that material. It cannot see fixed source, the target issue, a diff, a regression test, benchmark truth, or evaluator labels.

Each trigger records `trigger_type`, `preconditions`, `input_mutation`, `state_setup`, `environment_setup`, `action_sequence`, `observable`, `why_this_may_expose_the_mechanism`, `target_evidence`, and `confidence`. Trigger types are limited to INPUT, STATE, SEQUENCE, CONCURRENCY, and RETRY. A candidate that merely swaps Unicode characters without changing the exercised state is not diverse.

The first run freezes each hypothesis before trigger generation. No mechanism regeneration is allowed per trigger. A maximum of two bounded execution-feedback revisions is available only for syntax/import/fixture/setup/path issues; it cannot change the expected behavior, oracle, or hidden-test target.

## Experimental arms

### Experiment 3A: natural end-to-end

- C1: existing structured-history prompt, one direct test per hypothesis.
- C2: the same structured-history hypothesis stage, followed by four planned triggers and one test per retained trigger.
- Five hypotheses per arm, same model, temperature, context, history, evaluator, and repair budget.

### Experiment 3B: conditional trigger test

Use only previously stored C hypotheses whose hidden evaluator label is mechanism-matched. The stored hypothesis text and oracle are immutable. C1 generates one direct test; C2 generates four planned triggers and one test per retained trigger. The truth label is evaluator-only and never part of the generation input.

The primary comparison is C1 versus C2 within each experiment. The existing evaluator semantics remain unchanged. Each test is hashed and run unchanged on buggy and fixed revisions.

## Budget accounting

Report both hypothesis-normalized and execution-normalized quantities. C2 has four candidate executions per hypothesis by design; therefore it is not sufficient to compare total F2P counts. The report includes generated tests, executions, LLM calls, prompt/completion tokens, wall time, F2P per hypothesis, F2P per executed test, executions per verified F2P, calls/tokens per verified F2P, and time to first verified F2P.

If the stored conditional sample permits it, a C1 budget-matched arm generates independent direct tests until it consumes the same execution count as C2. If it cannot be run without changing the frozen hypothesis or exceeding the model budget, the report states that limitation explicitly.

## Leakage and invariants

Frozen across C1/C2: target revision, target context, structured historical memory, hypothesis prompt, model/configuration, evaluator, oracle policy, environment, test execution timeout, and repair budget. Fixed checkout and evaluator truth remain evaluator-only. The trigger planner is generic and contains no PySnooper-specific rule; environmental dimensions are considered only when supported by the hypothesis and target evidence.

## Success and failure analysis

Verified F2P remains the current criterion: unchanged test, meaningful semantic failure on buggy, fixed pass, and supported pre-execution oracle. Metrics add trigger executability, activation, mechanism-to-failure/F2P, diversity yield, unique failure modes, executions per F2P, LLM calls/tokens per F2P, and time to first F2P. Existing taxonomy is retained and refined at trigger/test level.

