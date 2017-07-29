import json
import os

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
        '<identifier>': ['/Users/michael/Documents/PhD/transcriptions/aegidius-expositio/da-199-prol/da-199-prol.xml'],
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

    def test_arguments_expansion(self):
        args = {
            '<identifier>': '~/hello.xml',
            '<recipe>': './recipe.json',
            '--output': '~/Desktop',
            '--xslt': './test.xslt',
            '--cache-dir': '~/.lbp_cache',
            '--config-file': '~/.lbp_print.json',
        }
        expanded = os.path.expanduser('~')
        args = cli.setup_arguments(args)
        assert args['--xslt'] == os.path.join(os.getcwd(), 'test.xslt')
        assert args['<identifier>'] == os.path.join(expanded, 'hello.xml')
        assert args['--cache-dir'] == os.path.join(expanded, '.lbp_cache')
        assert args['--config-file'] == os.path.join(expanded, '.lbp_print.json')
        assert args['--output'] == os.path.join(expanded, 'Desktop')
        assert args['<recipe>'] == os.path.join(os.getcwd(), 'recipe.json')