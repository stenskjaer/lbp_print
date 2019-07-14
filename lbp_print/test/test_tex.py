import os
import tempfile

from lbp_print.core import Tex, LocalResource, RemoteResource


class TestWhiteSpaceCleanup:

    local = LocalResource(os.path.join("lbp_print", "test", "assets", "da-49-l1q1.xml"))

    def clean(self, content: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w+") as fh:
            fh.writelines(content)
            fh.seek(0)
            Tex(self.local).whitespace_cleanup(fh.name)
            return fh.read()

    def test_whitespace_cleanup(self):
        assert self.clean("test { test") == "test{test"
        assert self.clean("test }") == "test}"
        assert self.clean(" . , ? ! : ;") == ".,?!:;"
        assert self.clean(" \\edtext{}") == "\\edtext{}"
        assert self.clean("}\\edtext{test}") == "} \\edtext{test}"
        assert self.clean("test      ") == "test "
        assert self.clean("} .") == "}."
        assert self.clean("          ") == ""
        assert self.clean("test   %") == "test%"
        assert self.clean("test ( test") == "test (test"
        assert self.clean("test )") == "test)"
        assert self.clean("test_name and\\ more") == "test\\_name and\\ more"
        assert self.clean('test "and"') == "test \\enquote{and}"


class TestTexProcessing:

    local = LocalResource(os.path.join("lbp_print", "test", "assets", "da-49-l1q1.xml"))
    remote = RemoteResource("da-49-l1q1")

    def test_create_tex_file_from_local(self):
        """Make sure that the return value of the tex compilation is a tex file."""
        output_file = Tex(self.local).process(output_format="tex")
        assert os.path.splitext(output_file)[1] == ".tex"

    def test_create_tex_file_from_remote(self):
        """Make sure that the return value of the tex compilation is a tex file."""
        output_file = Tex(self.local).process(output_format="tex")
        assert os.path.splitext(output_file)[1] == ".tex"
