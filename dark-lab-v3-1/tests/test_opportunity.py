import io
import json
import unittest
import zipfile
from datetime import datetime, timezone, timedelta
from opportunity_engine import evaluate_opportunity, build_production_plan
from production_pack import make_production_zip

NOW = datetime.now(timezone.utc)


def data(n_channels=10, n_videos=30, young=5):
    channels = [
        {
            'channel_id': f'UC{c:022d}',
            'published_at': (NOW - timedelta(days=130 if c < young else 800)).isoformat(),
            'subscribers': 6000 if c < young else 100000,
        }
        for c in range(n_channels)
    ]
    vids = []
    for v in range(n_videos):
        channel = channels[v % n_channels]
        vids.append({
            'video_id': f'video_{v}', 'channel_id': channel['channel_id'],
            'channel_title': f'Canal {v % n_channels}',
            'views': 50000 if v % n_channels < young else 3000,
            'published_at': (NOW - timedelta(days=10 + v)).isoformat(),
            'title': f'Rainy night ambient calm mix {v}',
            'url': f'https://www.youtube.com/watch?v=video_{v}',
        })
    return vids, channels


class OpportunityTests(unittest.TestCase):
    def test_empty_cannot_be_ocean_blue(self):
        result = evaluate_opportunity('ambient', [], [])
        self.assertEqual(result['status'], 'Dados insuficientes')
        self.assertFalse(result['evidence_ok'])
        self.assertLessEqual(result['score'], 49)
        self.assertIsNone(result['observed_growth_vpd'])

    def test_only_one_viral_channel_is_not_open(self):
        vids, channels = data(n_channels=10, n_videos=30, young=1)
        result = evaluate_opportunity('ambient', vids, channels, methods=2)
        self.assertTrue(result['evidence_ok'])
        self.assertLess(result['young_breakout_channels'], 3)
        self.assertNotEqual(result['status'], 'Sinais de abertura (na amostra)')

    def test_several_young_channels_can_be_indicated(self):
        vids, channels = data()
        result = evaluate_opportunity('rain ambient', vids, channels, methods=2)
        self.assertTrue(result['evidence_ok'])
        self.assertGreaterEqual(result['young_breakout_channels'], 3)
        self.assertEqual(result['status'], 'Sinais de abertura (na amostra)')
        self.assertEqual(result['methods'], 2)
        self.assertEqual(result['observed_video_count'], 0)

    def test_separate_growth_observations_from_lifetime_average(self):
        vids, channels = data()
        result = evaluate_opportunity('ambient', vids, channels, {'video_0': 100, 'video_1': 300}, methods=2)
        self.assertEqual(result['observed_growth_vpd'], 200)
        self.assertNotEqual(result['observed_growth_vpd'], result['median_vpd_lifetime'])

    def test_plan_requires_evidence_and_correct_niche(self):
        vids, channels = data()
        valid = evaluate_opportunity('ambient', vids, channels, methods=2)
        with self.assertRaises(ValueError):
            build_production_plan('different', valid, vids)
        with self.assertRaises(ValueError):
            build_production_plan('ambient', evaluate_opportunity('ambient', [], []), vids)

    def test_pilot_contains_different_tracks_and_zip(self):
        vids, channels = data()
        query = 'rainy night ambient'
        report = evaluate_opportunity(query, vids, channels, methods=2)
        plans = build_production_plan(query, report, vids, count=2, target_minutes=30)
        self.assertEqual(len(plans), 2)
        self.assertNotEqual(plans[0]['cover_prompt'], plans[1]['cover_prompt'])
        self.assertEqual(len(plans[0]['tracks']), 8)
        self.assertEqual(len(set(t['style'] for t in plans[0]['tracks'])), 8)
        self.assertNotIn('3 Hours', plans[0]['title'])
        packed = make_production_zip(query, report, plans)
        with zipfile.ZipFile(io.BytesIO(packed)) as archive:
            self.assertIn('00_LEIA_PRIMEIRO.md', archive.namelist())
            self.assertIn('video_01/BRIEFING_E_PROMPTS.md', archive.namelist())
            d = json.loads(archive.read('01_RELATORIO_E_PLANO.json'))
            self.assertEqual(d['research']['query'], query)
            self.assertEqual(len(d['plan']), 2)


if __name__ == '__main__':
    unittest.main()
