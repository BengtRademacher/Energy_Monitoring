from __future__ import annotations

import unittest

from config import CONFIG
from tab_additional_info_optional import _find_boxplot_logo_path, _find_iso_logo_path
from utils import find_image_path


class LogoAssetTests(unittest.TestCase):
    def test_config_defaults_use_replacement_logos(self) -> None:
        self.assertEqual(CONFIG["LOGO_IFW_BASENAME"], "logo_firma")
        self.assertEqual(CONFIG["LOGO_FX_BASENAME"], "logo_f\u00f6rderung")

    def test_configured_logos_exist(self) -> None:
        self.assertIsNotNone(find_image_path(CONFIG["LOGO_IFW_BASENAME"]))
        self.assertIsNotNone(find_image_path(CONFIG["LOGO_FX_BASENAME"]))

    def test_optional_tab_replacement_logos_exist(self) -> None:
        self.assertIsNotNone(_find_iso_logo_path())
        self.assertIsNotNone(_find_boxplot_logo_path())


if __name__ == "__main__":
    unittest.main()
