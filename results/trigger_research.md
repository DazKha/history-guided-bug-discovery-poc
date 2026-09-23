# Trigger-synthesis research

## Question

Given a plausible or correct failure mechanism, what techniques help construct concrete executable conditions that reach the mechanism and expose a meaningful observable?

## Findings

| Method | Mechanism | Problem solved | Runtime / effort | Hidden knowledge required? | Repository-level fit | Hypothesis-driven? | Expected benefit | Main risk | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| Structured trigger planning | Separates preconditions, input, state, environment, sequence, observable, and evidence before code generation | Prevents a correct mechanism from collapsing into one weak example | Low runtime; one extra LLM call; low implementation effort | No, if dimensions are selected from visible evidence | High for Python API/file/state bugs | Yes | Better reachability and clearer failure analysis | Planner can produce plausible but unsupported setup | Issue2Test; ReProAgent |
| Bounded candidate diversification | Generates a small set of meaningfully different realizations for one frozen hypothesis | Addresses unstable concrete trigger shape | 3–5 test generations per hypothesis; linear execution cost | No | High | Yes | Raises chance that one candidate reaches the relevant state | Extra executions may look like quality improvement unless normalized | Issue2Test’s candidate/refinement loop; fuzzing seed diversity |
| Property-based structured input | Generates values from constrained strategies and shrinks failing examples | Covers boundaries and preserves input validity | Low-to-medium; library integration and strategy design | No | Medium-high when the API accepts structured values | Yes | More boundary coverage and smaller counterexamples | Generic random values can miss environment/sequence bugs; oracle remains hard | Hypothesis documentation; QuickCheck/FuzzChick |
| Grammar/input fuzzing | Mutates or generates syntactically valid structured inputs | Avoids invalid-input noise and explores parser/state boundaries | Medium-high; usually a fuzz harness and many executions | No | Medium; strongest for parsers and file formats | Sometimes | More valid input combinations | Overkill for a small repository PoC and can obscure semantic oracle | OSS-Fuzz/OSS-Fuzz-gen |
| Coverage-guided fuzzing | Retains inputs that reach new paths/edges and mutates them | Finds deeper paths than blind random generation | High; instrumentation and long runs | No | Medium; target-specific harness work | Weakly | Better path/state reachability | Coverage is not the same as triggering the hypothesized semantic fault | AFL/OSS-Fuzz literature |
| Environment perturbation | Enumerates locale, encoding, timezone, filesystem, ordering, retry, or concurrency assumptions | Reaches bugs hidden behind implicit runtime conditions | Low-medium per dimension; potentially expensive cross-product | No, when dimension is hypothesis-supported | High for environment-sensitive functional bugs | Yes | Directly exercises preconditions absent from direct tests | Target-specific dimension selection can leak if not evidence-grounded | ReProAgent test-plan discussion; current failure taxonomy |
| Metamorphic testing | Applies a transformation with a known relation between executions | Provides an oracle when exact output is unknown | Medium; relation design plus multiple runs | No, if relation follows docs/spec | Medium; useful for invariants and transformations | Yes | Strengthens observable construction | Relation may be false for stateful/side-effectful APIs | Metamorphic testing survey |
| Differential testing | Compares independent implementations or versions | Detects semantic disagreement without a full oracle | Medium-high; needs trustworthy comparator | No hidden target facts, but needs another implementation | Low-medium for this single target/revision | Sometimes | Strong failure signal where a reference exists | No suitable independent implementation in current PoC; fixed revision is evaluator-only | Differential-testing literature |
| Symbolic/concolic generation | Solves path constraints to reach a branch/state | Constructs inputs for hard path predicates | High setup and runtime; solver/tool integration | No | Low for this small Python repository | Yes | Strong reachability for numeric/path constraints | Path explosion, dynamic Python/environment complexity | KLEE/CUTE/concolic literature |
| Search-based testing | Optimizes a fitness function such as branch distance or state reachability | Searches input/sequence spaces systematically | Medium-high; requires instrumentation and fitness design | No | Medium, but not smallest intervention | Yes | Useful when a measurable target predicate exists | Fitness may optimize coverage without semantic failure | Search-based test-data-generation surveys |
| LLM execution-feedback refinement | Revises setup/path mechanics using syntax, import, trace, and output feedback | Converts plausible tests into runnable/relevant tests | One to two bounded extra calls | No if feedback is generation-visible only | High | Yes | Fixes mechanical and path-construction errors | Can overfit observed failures or weaken the oracle | Issue2Test; ReProAgent |
| Candidate self-critique/diversity constraints | Checks whether candidates differ in state/path/observable before execution | Removes redundant near-duplicates | Low; one deterministic filter or review call | No | High | Yes | Makes an N-candidate budget useful rather than repetitive | LLM may rationalize diversity without real path difference | ReProAgent triadic review; fuzzing seed scheduling |

## Comparison

| Approach | Trigger diversity | Target-specific grounding | Execution cost | Engineering effort | Leakage risk | Generality | Fit for current PoC |
|---|---|---|---|---|---|---|---|
| Structured planner + N=4 candidates | High | High | Medium | Low | Low | High | **Best** |
| Property-based testing | High for inputs | Medium | Medium | Medium | Low | Medium-high | Secondary |
| Coverage-guided fuzzing | High | Medium-high after harnessing | High | High | Low | Medium | Too large |
| Environment enumeration | Medium | High when supported | Medium | Low-medium | Low | High | Add as a planner dimension |
| Metamorphic testing | Medium | High if a relation exists | Medium | Medium | Low | Medium | Useful selectively |
| Differential testing | Medium | Requires reference | Medium-high | Medium-high | Low | Low-medium | No current reference |
| Symbolic/concolic | Targeted | High | High | High | Low | Medium | Not justified |
| Search-based testing | High | Requires fitness | High | High | Low | Medium | Not justified |
| Bounded execution feedback | Medium | High | Medium | Low-medium | Low | High | **Add at most two iterations** |

## Selection rationale

The smallest technically justified intervention is a structured trigger planner followed by four meaningfully diverse candidate tests, with a cheap deterministic diversity filter and bounded mechanical feedback. It directly addresses the observed `TRIGGER_TOO_WEAK`, `TRIGGER_WRONG_SHAPE`, P2P, and F2F outcomes without changing historical memory or evaluator semantics. It also permits hypothesis-level freezing, so Experiment 3 can ask whether trigger construction improves conditional on the same mechanism.

The planner is generic: it does not contain an encoding rule, a PySnooper path, or a target-specific environmental prescription. It may mention an environment dimension only when that dimension is present in the frozen hypothesis and visible target evidence. Fixed source, issue/fix text, hidden regression tests, evaluator truth, and changed-file metadata remain outside generation.

## Sources

- Issue2Test: https://arxiv.org/abs/2503.16320
- ReProAgent repository and staged workflow: https://github.com/iSEngLab/ReProAgent
- Hypothesis documentation: https://hypothesis.readthedocs.io/en/latest/
- Hypothesis shrinking guide: https://github.com/HypothesisWorks/hypothesis/blob/master/guides/strategies-that-shrink.rst
- OSS-Fuzz LLM target generation: https://google.github.io/oss-fuzz/research/llms/target_generation/
- LLM-generated fuzz drivers: https://arxiv.org/abs/2307.12469
- Metamorphic testing survey: https://eprints.whiterose.ac.uk/id/eprint/110335/
- Search-based test data generation: https://groups.csail.mit.edu/EVO-DesignOpt/gecco2011Proceedings/proceedings/p1859.pdf
- Coverage-guided property testing: https://doi.org/10.1145/3360607

