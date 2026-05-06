# References

## Primary Algorithmic References

**Edmonds, J., & Karp, R. M. (1972).**
Theoretical improvements in algorithmic efficiency for network flow problems.
*Journal of the ACM, 19*(2), 248–264.
https://doi.org/10.1145/321694.321699

> The seminal paper introducing the BFS-based augmenting path selection that gives Edmonds-Karp its polynomial-time guarantee of O(VE²), resolving the exponential worst-case behaviour of the original Ford-Fulkerson method.

---

**Ford, L. R., & Fulkerson, D. R. (1956).**
Maximal flow through a network.
*Canadian Journal of Mathematics, 8*, 399–404.
https://doi.org/10.4153/CJM-1956-045-5

> The foundational paper proving the Max-Flow Min-Cut Theorem and introducing the augmenting path framework that all subsequent maximum flow algorithms build upon.

---

**Ford, L. R., & Fulkerson, D. R. (1962).**
*Flows in Networks.*
Princeton University Press.

> The definitive textbook treatment of network flow theory, covering the mathematical foundations used in this project.

---

## Network Flow Textbooks

**Ahuja, R. K., Magnanti, T. L., & Orlin, J. B. (1993).**
*Network Flows: Theory, Algorithms, and Applications.*
Prentice-Hall.

> The standard graduate-level reference for network optimization. Chapter 6 covers maximum flow algorithms in detail, including proofs of correctness and complexity analyses for Edmonds-Karp.

---

**Korte, B., & Vygen, J. (2018).**
*Combinatorial Optimization: Theory and Algorithms* (6th ed.).
Springer.

> Chapters 8–9 cover network flow and the min-cut max-flow theorem with formal proofs.

---

## Python and NetworkX

**Hagberg, A., Swart, P., & Chult, D. (2008).**
Exploring network structure, dynamics, and function using NetworkX.
*Proceedings of the 7th Python in Science Conference (SciPy 2008)*, 11–15.
https://conference.scipy.org/proceedings/scipy2008/paper_2/

> The original paper presenting the NetworkX library used in this project.

---

**NetworkX Developers. (2024).**
*NetworkX 3.x Documentation — Flow algorithms.*
https://networkx.org/documentation/stable/reference/algorithms/flow.html

> Official documentation for `nx.maximum_flow()` and `nx.minimum_cut()`, including algorithm selection and parameter reference.

---

## MIS and Information Infrastructure Management

**Laudon, K. C., & Laudon, J. P. (2022).**
*Management Information Systems: Managing the Digital Firm* (17th ed.).
Pearson.

> Chapter 5 (IT Infrastructure) provides the MIS framework within which campus network design decisions are situated. The discussion of infrastructure as a strategic asset motivates the managerial interpretation in this project.

---

**Goldratt, E. M. (1984).**
*The Goal: A Process of Ongoing Improvement.*
North River Press.

> Introduced Theory of Constraints (TOC), the management philosophy that frames bottleneck analysis as the primary lever for system-level improvement — directly applicable to the min-cut interpretation in this project.

---

**Weill, P., & Ross, J. W. (2004).**
*IT Governance: How Top Performers Manage IT Decision Rights for Superior Results.*
Harvard Business School Press.

> Provides the IT governance framework within which infrastructure investment prioritization decisions (such as those recommended in the Managerial Interpretation section) are made.

---

## Campus Network Planning

**Cisco Systems. (2023).**
*Campus LAN and Wireless LAN Solution Design Guide.*
https://www.cisco.com/c/en/us/td/docs/solutions/Enterprise/Campus/

> Industry reference for campus network capacity planning, including transceiver specifications used to set the edge capacities in the hypothetical dataset (1 GbE, 2.5 GbE, 10 GbE).

---

**Marmara University. (2024).**
*Kurumsal Bilgi — Marmara Üniversitesi Hakkında.*
https://www.marmara.edu.tr/universite/hakkimizda

> Institutional source for student and staff population figures cited in the Real-World Problem Context section.

---

## Data Visualization

**Hunter, J. D. (2007).**
Matplotlib: A 2D graphics environment.
*Computing in Science & Engineering, 9*(3), 90–95.
https://doi.org/10.1109/MCSE.2007.55

> The foundational paper for Matplotlib, the visualization library used to generate `results/network_visualization.png`.

---

*All URLs verified as of June 2025.*
