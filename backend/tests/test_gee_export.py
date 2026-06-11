import unittest

from app.gee.export import NODATA_VALUE, _clip_with_nodata


class FakeImage:
    def __init__(self):
        self.clipped_boundary = None
        self.unmask_args = None

    def clip(self, boundary):
        self.clipped_boundary = boundary
        return self

    def unmask(self, value, sameFootprint=True):
        self.unmask_args = (value, sameFootprint)
        return self


class GeeExportTests(unittest.TestCase):
    def test_clip_with_nodata_expands_footprint_for_boundary_exterior(self):
        image = FakeImage()
        boundary = object()

        result = _clip_with_nodata(image, boundary)

        self.assertIs(result, image)
        self.assertIs(image.clipped_boundary, boundary)
        self.assertEqual(image.unmask_args, (NODATA_VALUE, False))


if __name__ == "__main__":
    unittest.main()
