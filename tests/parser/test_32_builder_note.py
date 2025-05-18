import unittest
from tabscript.parser.note_builder import NoteBuilder

class TestNoteBuilder(unittest.TestCase):
    def setUp(self):
        self.note_builder = NoteBuilder()

    def test_triplet_groups(self):
        # テスト用の入力文字列
        input_str = "[ 4-2 4-4 3-2 ]3 [ 4-2 4-4 3-2 ]3 [ 4-2 4-4 3-2 ]3 [ 4-2 4-4 3-2 ]3"
        # 三連グループごとに分割
        triplet_strs = [s.strip() for s in input_str.split(']3') if s.strip()]
        self.assertEqual(len(triplet_strs), 4, "三連グループが4つあるはず")
        triplet_groups = []
        for tstr in triplet_strs:
            tstr = tstr.lstrip('[').strip()
            notes = self.note_builder.parse_triplet(tstr)
            triplet = self.note_builder.build_triplet(notes, None)
            triplet_groups.append(triplet)
        self.assertEqual(len(triplet_groups), 4, "三連グループが4つ生成されているはずです")
        for triplet in triplet_groups:
            self.assertTrue(triplet.is_triplet)
            self.assertEqual(len(triplet.triplet_notes), 3)
            self.assertEqual(triplet.triplet_notes[0].fret, '2')
            self.assertEqual(triplet.triplet_notes[0].string, 4)
            self.assertEqual(triplet.triplet_notes[1].fret, '4')
            self.assertEqual(triplet.triplet_notes[1].string, 4)
            self.assertEqual(triplet.triplet_notes[2].fret, '2')
            self.assertEqual(triplet.triplet_notes[2].string, 3)

if __name__ == '__main__':
    unittest.main()
    