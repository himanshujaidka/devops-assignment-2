# SonarQube analysis

**Project:** ACEest Fitness (`aceest-fitness`)

**Local dashboard:** http://localhost:19001/dashboard?id=aceest-fitness

**Analysis:** Completed successfully; server-reported timestamp 2026-11-23 09:48:33 +05:30. This is the timestamp reported by the local SonarQube server; check the machine clock if it differs from the actual date.

| Metric | Result |
|---|---:|
| Quality gate | Passed (`OK`) |
| Bugs | 0 |
| Vulnerabilities | 0 |
| Code smells | 1 |
| Security hotspots | 1, to review |
| Duplicated lines | 0.0% |
| Lines of code | 104 |
| Coverage | 0.0% reported; no coverage report was imported |

The code smell concerns the cognitive complexity of `create_app`. The security hotspot asks for review of CSRF protection in the Flask application; it has **not** been marked safe or remediated. Passing the quality gate is not proof that the application is free of vulnerabilities.

This analysis covered `ACEest_Fitness.py` and the test files specified by `sonar-project.properties`, not the historical Tkinter sources. The local SonarQube Python analyzer reported that it did not explicitly support Python 3.12 and analyzed using its 3.10 support. The local dashboard is available only on the machine running SonarQube, not to an external reviewer.
