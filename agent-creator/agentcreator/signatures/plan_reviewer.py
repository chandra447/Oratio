"""PlanReviewer Signature - Reviews and critiques agent architecture plan"""

import dspy


class PlanReviewerSignature(dspy.Signature):
    """You are a senior AI architect conducting a thorough review of an agent architecture plan. This is review iteration {review_iteration}.

Your task is to critically evaluate the plan against the original requirements and provide constructive feedback.

Evaluate the plan on these criteria:

1. **Requirements Alignment**: Does the plan address all requirements? Are there any gaps?

2. **Completeness**: Are all necessary components included (agent structure, tools, reasoning, error handling)?

3. **Technical Soundness**: Is the architecture feasible? Are the tools and integrations appropriate?

4. **Personality Implementation**: Is the personality properly integrated into the design?

5. **Scalability & Maintainability**: Is the design extensible and well-structured?

For each criterion, identify:
- **Strengths**: What is done well
- **Weaknesses**: What needs improvement
- **Suggestions**: Specific actionable improvements
- **Missing Elements**: What is completely absent but needed

Based on your evaluation, decide whether to approve the plan (approved: true) or request revisions (approved: false).

Be thorough but constructive. If this is iteration 2 or 3, be more lenient if the plan is mostly good.

Output a JSON object with your review."""

    plan: str = dspy.InputField(desc="Agent architecture plan to review")
    requirements: str = dspy.InputField(desc="Original requirements for validation")
    review_iteration: str = dspy.InputField(desc="Current review iteration number")
    
    approved: bool = dspy.OutputField(desc="Boolean indicating if the plan is approved (true) or needs revision (false)")
    review: str = dspy.OutputField(
        desc="Review feedback in JSON format with fields: strengths (list), weaknesses (list), suggestions (list), missing_elements (list). Do NOT include 'approved' in this JSON - it's a separate field."
    )
