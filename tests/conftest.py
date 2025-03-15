import pytest
from tabscript.models import Score, Section, Bar, Note, Column

def pytest_addoption(parser):
    """pytestのコマンドラインオプションを追加"""
    parser.addoption(
        "--debug-level",
        action="store",
        default="0",
        help="デバッグレベルを指定: 0=無効, 1=基本, 2=詳細, 3=全情報"
    )

@pytest.fixture
def debug_level(request):
    """デバッグレベルを取得するフィクスチャ"""
    return int(request.config.getoption("--debug-level"))

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

@pytest.fixture
def sample_score():
    """サンプルスコアを作成"""
    score = Score(title="Test Score", tuning="guitar", beat="4/4")
    
    # セクション1
    section1 = Section(name="Section 1")
    
    # 小節を作成
    bar1 = Bar()
    bar1.notes.append(Note(string=1, fret="0", duration="4"))
    bar1.notes.append(Note(string=2, fret="2", duration="4"))
    
    bar2 = Bar()
    bar2.notes.append(Note(string=3, fret="3", duration="4"))
    bar2.notes.append(Note(string=4, fret="0", duration="4"))
    
    # 繰り返し記号付きの小節
    bar3 = Bar(is_repeat_start=True)
    bar3.notes.append(Note(string=5, fret="5", duration="4"))
    bar3.notes.append(Note(string=6, fret="7", duration="4"))
    
    bar4 = Bar(is_repeat_end=True)
    bar4.notes.append(Note(string=6, fret="5", duration="4"))
    bar4.notes.append(Note(string=5, fret="3", duration="4"))
    
    # n番カッコ付きの小節
    bar5 = Bar(volta_number=1)
    bar5.notes.append(Note(string=4, fret="2", duration="4"))
    bar5.notes.append(Note(string=3, fret="0", duration="4"))
    
    # Columnを作成
    column1 = Column(bars=[bar1, bar2])
    column2 = Column(bars=[bar3, bar4, bar5])
    
    # セクションにColumnを追加
    section1.columns.append(column1)
    section1.columns.append(column2)
    
    # スコアにセクションを追加
    score.sections.append(section1)
    
    return score 