import os

from lbp_print.core import Tex, LocalTranscription, RemoteTranscription

class TestTexProcessing:

    local = LocalTranscription(os.path.join('lbp_print', 'test', 'assets', 'da-49-l1q1.xml'))
    remote = RemoteTranscription('da-49-l1q1')

    def test_create_tex_file_from_local(self):
        """Make sure that the return value of the tex compilation is a tex file."""
        assert os.path.splitext(Tex(self.local, output_format='tex').process())[1] == '.tex'

    def test_create_tex_file_from_remote(self):
        """Make sure that the return value of the tex compilation is a tex file."""
        assert os.path.splitext(Tex(self.remote, output_format='tex').process())[1] == '.tex'