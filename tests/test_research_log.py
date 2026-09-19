import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from research_log import append_event


class ResearchLogTests(unittest.TestCase):
    def test_backfill_records_real_time_source_and_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            args=dict(action='测试历史补记',outcome='测试',occurred_at='2026-09-05T13:48:03+00:00',
                      time_source='run metadata',event_id='test-only',root=root)
            self.assertTrue(append_event(**args))
            before=(root/'research_events.jsonl').read_bytes()
            self.assertFalse(append_event(**args))
            self.assertEqual(before,(root/'research_events.jsonl').read_bytes())
            row=json.loads(before)
            self.assertTrue(row['occurred_local'].startswith('2026-09-05T21:48:03'))
            self.assertEqual(row['time_source'],'run metadata')
            self.assertIn('测试历史补记',(root/'RESEARCH_LOG.md').read_text())

    def test_naive_time_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                append_event('test','test',occurred_at='2026-09-05T13:00:00',root=Path(tmp))
