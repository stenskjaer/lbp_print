import json

import docopt

from lbp_print import cli
from lbp_print import config


class TestCliConfig:

    def test_empty_config_file(self, tmpdir):
        p = tmpdir.mkdir("sub").join("hello.txt")
        p.write({})
        assert cli.load_config(p) == {}

    def test_non_empty_config_file(self, tmpdir):
        p = tmpdir.mkdir("sub").join("hello.txt")
        p.write(json.dumps({'--cache-dir': 'tmp'}))
        conf = cli.load_config(p)
        assert conf['--cache-dir'] == 'tmp'
        # assert config.cache_dir == 'tmp'


class TestSetupArgs:

    template_args = {
        '--cache-dir': '/Users/michael/.lbp_cache',
        '--config-file': '~/.lbp_print.json',
        '--help': False,
        '--local': True,
        '--output': '.',
        '--scta': False,
        '--verbosity': 'info',
        '--version': False,
        '--xslt': None,
        '--xslt-parameters': None,
        '<expression-id>': [],
        '<file>': ['/Users/michael/Documents/PhD/transcriptions/aegidius-expositio/da-199-prol/da-199-prol.xml'],
        '<recipe>': None,
        'pdf': False,
        'recipe': False,
        'tex': True
    }

    def test_setup_arguments(self):
        args = {
            '--cache-dir': '/Users/michael/.lbp_cache',
            '--config-file': '~/.lbp_print.json',
            '<recipe>': None,
        }
        cli.setup_arguments(args)
        assert config.cache_dir == '/Users/michael/.lbp_cache'
        assert args['--config-file'] == '/Users/michael/.lbp_print.json'
