from lbp_print.core import RemoteTranscription

class TestRemoteTranscription:

    trans = RemoteTranscription('da-49-l1q1')

    def test_remote_transcription_object(self):
        assert self.trans.transcription_object.to_s() == 'http://scta.info/resource/da-49-l1q1/critical/transcription'

    def test_remote_file_download(self):
        assert self.trans.file is not None

