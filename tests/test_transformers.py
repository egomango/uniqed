from unittest import TestCase
import numpy as np
from uniqed.transformers.transformers import TimeDelayEmbedder, TransformYTrue, invertit, _make_result_df


class TestTimeDelayEmbedder(TestCase):
    def gen_data(self, n=100):
        return np.random.rand(n)

    def test_fit(self):
        x = self.gen_data()
        TimeDelayEmbedder().fit(x)

    def test_transform(self):
        x = self.gen_data()
        TimeDelayEmbedder().fit(x).transform(x)

    def test_fit_transform(self):
        x = self.gen_data()
        TimeDelayEmbedder().fit(x)

    def test__embedding(self):
        n = 100
        x = self.gen_data()
        d = 3
        tau = 1
        N = n - (d-1)*tau
        shape = [N, d]

        X = TimeDelayEmbedder()._embedding(x, d=d, tau=tau)
        is_eq = np.isclose(shape, X.shape)
        self.assertTrue(np.all(is_eq))


class TestTransformYTrue(TestCase):
    def test_fit(self):
        t = np.zeros(100)
        TransformYTrue().fit(t)

    def test_transform(self):
        t = np.zeros(100)
        TransformYTrue().fit(t).transform(t)

    def test_fit_transform(self):
        t = np.zeros(100)
        TransformYTrue().fit_transform(t)

    def test__transform_y_true(self):
        t = np.zeros(100)
        x = TransformYTrue().fit(t)._transform_y_true(t)

    def test__get_faketime_axis(self):
        n = 5
        t= np.arange(n)
        x = np.zeros(n)
        d = 3
        tau = 1
        fake_t = t[1:-1]
        fake_t_calc = TransformYTrue().fit(x)._get_faketime_axis(d, tau)
        is_eq = np.isclose(fake_t, fake_t_calc)
        self.assertTrue(np.all(is_eq))

    def test_invertit(self):
        x = np.arange(1, 111)
        y = invertit(x, True)
        is_eq = np.isclose(x, 1/y)
        self.assertTrue(np.all(is_eq))


    def test_invertit2(self):
        x = np.arange(1, 111)
        y = invertit(x, False)
        is_eq = np.isclose(x, y)
        self.assertTrue(np.all(is_eq))

    def test__make_result_df(self):
        x = np.arange(1, 111)
        inv_it = True
        prefix = ""

        _make_result_df(x, x, x, inv_it, prefix)


def test_odd_window_is_stamped_at_ceil_of_half_window():
    # d=2, tau=1: window 1, centre 0.5. Issue #1: was truncated to 0; now rounds to 1,
    # so the score is stamped no earlier than the last sample it needed.
    from uniqed.transformers.transformers import TransformYTrue

    x = np.arange(10)
    axis = TransformYTrue(d=2, tau=1).fit(x)._get_faketime_axis(2, 1)
    assert axis[0] == 1
    assert axis[-1] == 9
    axis = TransformYTrue(d=4, tau=1).fit(x)._get_faketime_axis(4, 1)  # window 3, centre 1.5 -> 2
    assert axis[0] == 2
    axis = TransformYTrue(d=3, tau=1).fit(x)._get_faketime_axis(3, 1)  # even window unchanged
    assert axis[0] == 1
