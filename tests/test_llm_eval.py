from evals.llm_eval import assert_all_passed, run_all_evals


def test_llm_eval_suite_passes() -> None:
    results = run_all_evals()

    assert_all_passed(results)
