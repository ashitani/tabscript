import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--show-debug",
        action="store_true",
        default=False,
        help="enable debug output for failed tests"
    )

@pytest.fixture
def debug_on_failure(request):
    """テスト失敗時のみデバッグ出力を有効にする"""
    def _debug_on_failure(score):
        if request.node.rep_setup.failed or request.node.rep_call.failed:
            print("\nDebug output for failed test:")
            print("Score structure:")
            for section in score.sections:
                print(f"\nSection: {section.name}")
                for column in section.columns:
                    for bar in column.bars:
                        print("\nBar:")
                        for note in bar.notes:
                            print(f"  Note: string={note.string}, fret={note.fret}, "
                                  f"duration={note.duration}, step={note.step}, "
                                  f"chord={note.chord}")
    return _debug_on_failure

# テストの実行状態を記録するためのフック
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep) 