
1. Which strategy won, and on what dimension?

The Structured Prompting technique performed the best overall. It achieved the highest accuracy score (2.90/3) and the highest judge score (25.0/25). Additionally, it was the only strategy that consistently returned null for j10, the deliberately unspecified-years scenario. This demonstrated not only strong extraction performance but also better handling of missing information and edge cases.

2. What surprised you?

Two findings were particularly surprising.

First, zero-shot prompting performed worse than expected on edge cases but better than expected on straightforward examples. For snippets j01-j03 and j08-j09, it consistently achieved perfect scores (3/3). However, its weaknesses became apparent when handling fuzzy numerical expressions such as "around 6 years" or "about three years", as well as the null case (j10).

Second, chain-of-thought prompting was not consistently better than structured prompting, despite producing more detailed and verbose responses. The step-by-step reasoning appeared to help in cases such as j07, but it did not translate into a clear overall performance advantage. This suggests that additional reasoning does not necessarily improve extraction accuracy when the task primarily requires structured information retrieval.

3. Which strategy would you reach for first in your capstone domain?

I would choose structured, role-based prompting without hesitation. My capstone project focuses on entity extraction, where explicit output schemas and clearly defined roles reduce ambiguity and improve consistency. Structured prompting makes the required output format explicit rather than relying on the model to infer expectations from natural-language instructions. Furthermore, the 100% parse rate is essential for a production-style pipeline that feeds downstream validation and processing stages.

4. If you had another day, what would you try next?

Given more time, I would expand the evaluation using more ambiguous snippets. The current dataset contains only one genuinely difficult edge case (j10). A second test set containing 5-10 additional ambiguous examples would provide a stronger assessment of robustness. Examples could include cases where years of experience are implied rather than stated directly, salary figures are confused with experience levels, overlapping date ranges exist, or contradictory employment histories appear within the same text. Testing on these challenging scenarios would better reveal differences between prompting strategies and provide a more realistic measure of performance in real-world extraction tasks.