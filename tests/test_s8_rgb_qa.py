"""Small synthetic-file boundaries for RGB QA; no TUM data or models are read."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import qa_s8_rgb as qa


class TestS8RGBQA(unittest.TestCase):
    def payload(self, mode='RGB', size=(640, 480)):
        image = Image.new(mode, size, 0)
        out = io.BytesIO(); image.save(out, format='PNG'); return out.getvalue()

    def test_crc_full_decode_and_exact_copy_without_resaving(self):
        payload = self.payload()
        facts = qa.check_png(payload)
        self.assertEqual(facts['mode'], 'RGB')
        self.assertEqual(facts['size'], [640, 480])
        self.assertTrue(facts['png_crc_verified'] and facts['full_decode_ok'])
        digest = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'copy.png'
            self.assertEqual(qa.copy_exact(payload, path, digest), digest)
            self.assertEqual(path.read_bytes(), payload)
            with self.assertRaises(FileExistsError):
                qa.copy_exact(payload, path, digest)

    def test_bad_crc_mode_or_size_stops_the_same_sample(self):
        payload = bytearray(self.payload())
        # Corrupt the IHDR CRC; pixel bytes are otherwise unchanged.
        payload[29] ^= 1
        for bad in (bytes(payload), self.payload(mode='L'), self.payload(size=(320, 240))):
            with self.subTest(length=len(bad)), self.assertRaises(Exception):
                qa.check_png(bad)

    def test_both_outputs_must_be_fresh_and_not_nested(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); old = base / 'old'; old.mkdir()
            new = base / 'new'
            with self.assertRaisesRegex(ValueError, 'fresh'):
                qa.fresh_outputs(new, old)
            self.assertFalse(new.exists())
            broken = base / 'broken'; broken.symlink_to(base / 'missing')
            with self.assertRaisesRegex(ValueError, 'fresh'):
                qa.fresh_outputs(new, broken)
            with self.assertRaisesRegex(ValueError, 'not nested'):
                qa.fresh_outputs(new, new / 'photos')

    def test_preflight_failure_keeps_incomplete_photo_notice_without_decode(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            args = SimpleNamespace(output=base / 'qa', photo_output=base / 'photos',
                protocol=base / 'missing_protocol', manifest=base / 'missing_manifest',
                design_freeze=base / 'missing_design', data=base / 'unread_data')
            with patch.object(qa, 'check_png', side_effect=AssertionError('premature image decode')) as decoder:
                with self.assertRaises(FileNotFoundError):
                    qa.run(args)
            metadata = json.loads((args.output / 'run_metadata.json').read_text())
            self.assertEqual(metadata['status'], 'failed')
            self.assertEqual(metadata['checked_rgb_images'], 0)
            self.assertNotIn('first_rgb_decode_utc', metadata)
            self.assertFalse(metadata['depth_decoded'])
            self.assertFalse(metadata['gt_pose_values_parsed'])
            self.assertEqual(decoder.call_count, 0)
            self.assertIn('尚未完成', (args.photo_output / 'README.md').read_text())


if __name__ == '__main__':
    unittest.main()
