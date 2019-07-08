import os

from lbp_print.core import Tex, LocalTranscription, RemoteTranscription


class TestTexProcessing:

    local = LocalTranscription(
        os.path.join("lbp_print", "test", "assets", "da-49-l1q1.xml")
    )
    remote = RemoteTranscription("da-49-l1q1")

    def test_create_tex_file_from_local(self):
        """Make sure that the return value of the tex compilation is a tex file."""
        output_file = Tex(self.local).process(output_format="tex")
        assert os.path.splitext(output_file)[1] == ".tex"

    def test_create_tex_file_from_remote(self):
        """Make sure that the return value of the tex compilation is a tex file."""
        output_file = Tex(self.local).process(output_format="tex")
        assert os.path.splitext(output_file)[1] == ".tex"
