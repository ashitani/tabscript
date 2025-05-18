from tabscript.parser.builder.score import ScoreBuilder

def test_section_parsing():
    lines = [
        '$title="test"',
        '$section="A"',
        '4-2 4-4 3-2',
        '$section="B"',
        '5-2 5-4 4-2',
    ]
    builder = ScoreBuilder()
    score = builder.parse_lines(lines)
    assert len(score.sections) == 2
    assert score.sections[0].name == "A"
    assert score.sections[1].name == "B"
    assert len(score.sections[0].columns) == 1
    assert len(score.sections[1].columns) == 1
    assert len(score.sections[0].columns[0].bars) == 1
    assert len(score.sections[1].columns[0].bars) == 1
    # 内容も確認
    assert score.sections[0].columns[0].bars[0].notes[0].string == 4
    assert score.sections[1].columns[0].bars[0].notes[0].string == 5 