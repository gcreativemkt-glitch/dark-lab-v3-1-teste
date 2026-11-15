import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from storage import Store

class SnapshotTests(unittest.TestCase):
    def test_new_snapshot_does_not_invent_growth(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch('storage.LOCAL_DB', Path(folder) / 'test.db'):
                db = Store()
                video = {'video_id': 'video_001', 'views': 1000}
                self.assertEqual(db.observed_video_growth([video]), {})
                db.save_video_snapshots([video])
                self.assertEqual(db.observed_video_growth([video]), {})

    def test_growth_requires_prior_date(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch('storage.LOCAL_DB', Path(folder) / 'test.db'):
                db = Store()
                old_day = (datetime.now(timezone.utc).date() - timedelta(days=2)).isoformat()
                with db._connect() as conn:
                    conn.execute('INSERT INTO video_snapshots(video_id,recorded_on,views) VALUES(?,?,?)',
                                 ('video_002', old_day, 1500))
                values = db.observed_video_growth([{'video_id': 'video_002', 'views': 2500}])
                self.assertEqual(values['video_002'], 500.0)

if __name__ == '__main__':
    unittest.main()
