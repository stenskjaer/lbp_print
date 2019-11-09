import logging

from redis import Redis
from rq import get_current_job, Queue
from rq.job import Job
from rq.exceptions import NoSuchJobError

import lbp_print.core as lbp_print
import lbp_print.config as lbp_config
from lbp_print.exceptions import SaxonError

logger = logging.getLogger()
lbp_config.cache_dir = "cache"
redis_connection = Redis(host="localhost")
q = Queue(connection=redis_connection)


def handle_job(resource: str) -> dict:
    try:
        logger.debug(f"Checking for job with the id {resource.id}")
        job = Job.fetch(resource.id, connection=redis_connection)
    except NoSuchJobError:
        logger.debug(f"No existing job. Starting one up ...")
        job = q.enqueue(
            convert_resource,
            resource,
            job_id=resource.id,
            job_timeout="1h",
            result_ttl=30,
        )
        return {"Status": f"Started processing {resource.id}"}

    status = job.meta["progress"]

    if job.result:
        response = {"Status": "Finished", "url": job.result}
        logger.debug(f"Job was finished. Result: " + job.result)
    elif job.is_failed:
        response = {"Status": "Failed. Resubmit to retry.", "error": status}
        logger.warn(f"Job failed." + status)
        job.delete()
    else:
        response = {"Status": status}
        logger.debug(f"Job running. Status: " + status)
    return response


def update_status(message, job):
    job.meta["progress"] = message
    job.save_meta()
    logger.info(message)


def convert_resource(resource: lbp_print.Resource) -> str:
    job = get_current_job()

    update_status(f"Converting {resource.id} to pdf.", job)
    try:
        filename = lbp_print.Tex(resource).process(output_format="pdf")
    except SaxonError as exc:
        update_status(str(exc), job)
        raise
    update_status(f"Successfully converted {id} to pdf.", job)

    return filename
