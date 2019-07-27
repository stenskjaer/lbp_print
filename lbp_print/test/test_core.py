import os

from lbp_print.core import RemoteResource, UrlResource


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


class TestRemoteResource:

    trans = RemoteResource("da-49-l1q1")

    def test_remote_transcription_object(self):
        assert (
            self.trans.transcription_object.to_s()
            == "http://scta.info/resource/da-49-l1q1/critical/transcription"
        )

    def test_remote_file_download(self):
        assert self.trans.file is not None
