import unittest
from datetime import datetime,timezone,timedelta
from analytics import age_days, rank_outliers, title_keywords, revenue_range, niche_summary

class AnalysisTests(unittest.TestCase):
    def test_outlier_ratio_uses_same_sample_median(self):
        videos=[{'title':str(i),'views':v,'published_at':'2026-01-01T00:00:00Z'} for i,v in enumerate([100,200,500])]
        ranked=rank_outliers(videos)
        self.assertEqual(ranked[0]['outlier_ratio'],2.5)

    def test_revenue(self):
        self.assertEqual(revenue_range(100000,2,0.5),(50,200))

    def test_keywords(self):
        self.assertEqual(title_keywords([{'title':'Rainy Medieval Tavern Music'},{'title':'Rainy medieval castle'}])[0],('rainy',2))

    def test_niche_empty(self):
        self.assertEqual(niche_summary([])['sample_size'],0)

    def test_age_is_positive(self):
        self.assertGreaterEqual(age_days(datetime.now(timezone.utc).isoformat()),1)

if __name__=='__main__': unittest.main()
