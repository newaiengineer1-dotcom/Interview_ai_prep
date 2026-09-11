# Test Data

Use the included `sample_cv.txt` and `sample_jd.txt` to validate the application.

Expected behavior:
1. The app should identify Solar PV, BESS, energy yield, grid connection and due diligence as supported skills.
2. It must NOT invent a project capacity, employer, client, revenue, certification or specific project result.
3. A likely question is similar in intent to: "How would you review an energy yield assessment from a lender perspective?"
4. If the user answers with an invented project capacity, the analyzer should flag the unsupported claim.
5. The improved answer must remain within the evidence in the synthetic CV.
