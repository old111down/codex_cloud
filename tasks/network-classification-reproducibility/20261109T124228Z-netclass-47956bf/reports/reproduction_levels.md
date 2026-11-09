# Reproduction levels and evidence scope

These are local audit conventions, not an external certification.

| Level | Required evidence | What it does not establish |
| --- | --- | --- |
| R0 | Verified association/static inspection, or no successful algorithm execution | An installation, failed command or unrun model is not an algorithm success |
| R1 | Independent environment and a successful bounded component/smoke test | Synthetic inputs, random weights, a metric probe or generated P4 text do not reproduce paper results |
| R2 | Core algorithm executed on identified available real data with inspectable outputs | Does not establish original sampling, split, full evaluation, deployment or comparable performance |
| R3 | Original processing/evaluation restored with paper-metric comparison, declared tolerances and repeated-run protocol | Does not automatically cover every deployment/hardware claim |
| R4 | Independently validated complete claimed use cases and required deployment/hardware with comparable resource/performance results | Never assigned without actual required hardware observations |

Levels are scoped by component. Mousika overall remainsR1 although a UNIV prefix component ran on real derived data; Lens main model remainsR0 although its original metric/split functions haveR1 diagnostics. No R3/R4 is established in this run.

A is public code coverage, B is executable behavior, C is paper-result reproduction. Exit0 alone is insufficient: an empty CSV or Disabled controller is not algorithm success. P4 text/table generation, compiler execution, software packet simulation and physical-switch measurements are separate layers.

The common archive statuses Verified / Partially Verified / Failed / Unknown always carry a scope. A verified fact that code is missing is not a failed experiment; a verified public upload is not verified paper accuracy. Compatibility and algorithm patches remain separate from original-code results.
