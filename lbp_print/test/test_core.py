import os
import shutil

import pytest

from lbp_print.core import LocalResource, RemoteResource, UrlResource, Tex
from lbp_print import config


class TestUrlResource:

    url = "https://raw.githubusercontent.com/scta-texts/da-49/master/da-49-l1q1/da-49-l1q1.xml"
    res = UrlResource(url)

    def test_successfull_download_to_file(self):
        assert self.res.file is not None
        assert os.path.isfile(self.res.file)

    def test_identified_schema_info(self):
        assert self.res.get_schema_info().get("version") == "1.0.0"
        assert self.res.get_schema_info().get("type") == "critical"

    def test_identified_xslt_exists(self):
        assert os.path.isfile(self.res.xslt)

    def test_resource_id_exists(self):
        assert type(self.res.id) == str


class TestRemoteResource:

    res = RemoteResource("da-49-l1q1")

    def test_remote_file_download(self):
        assert self.res.file is not None
        assert os.path.isfile(self.res.file)

    def test_identified_schema_info(self):
        assert self.res.get_schema_info().get("version") == "1.0.0"
        assert self.res.get_schema_info().get("type") == "critical"

    def test_identified_xslt_exists(self):
        assert os.path.isfile(self.res.xslt)

    def test_resource_id_exists(self):
        assert type(self.res.id) == str


class TestCache:
    path = os.path.join(config.module_dir, "test", "assets", "da-49-l1q1.xml")
    res = LocalResource(path)

    @pytest.fixture
    def cache_settings(self):
        config.cache_dir = os.path.join(os.path.curdir, "cache")
        yield
        shutil.rmtree(config.cache_dir)

    def test_store_in_cache_after_processing(self, cache_settings):
        Tex(self.res).process(output_format="tex")
        assert os.path.isfile(os.path.join(config.cache_dir, self.res.digest + ".tex"))
