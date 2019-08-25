import logging

import lbp_print.core
import lbp_print.config


# Setup logging according to configuration
logger = logging.getLogger("lbp_print")
logger.setLevel(lbp_print.config.log_level)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("[%(asctime)s] %(name)s - %(levelname)s - %(message)s")

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

