import os
from loguru import logger

from client import DBTCloud
from loader.load import load_job_definitions
from schemas import check_job_mapping_same

if __name__ == "__main__":
    absolute_path = os.path.dirname(__file__)
    example_path = "../jobs/jobs.yml"
    path = os.path.join(absolute_path, example_path)

    defined_jobs = load_job_definitions(path)

    dbt_cloud = DBTCloud(account_id=43791, api_key=os.environ.get('API_KEY'))
    cloud_jobs = dbt_cloud.get_jobs()
    tracked_jobs = {
        job.identifier: job for job in cloud_jobs if job.identifier is not None
    }

    # Use sets to find jobs for different operations
    shared_jobs = set(defined_jobs.keys()).intersection(set(tracked_jobs.keys()))
    created_jobs = set(defined_jobs.keys()) - set(tracked_jobs.keys())
    deleted_jobs = set(tracked_jobs.keys()) - set(defined_jobs.keys())

    # Update changed jobs
    logger.info("Detected {count} existing jobs.", count=len(shared_jobs))
    for identifier in shared_jobs:
        logger.info("Checking for differences in {identifier}", identifier=identifier)
        if not check_job_mapping_same(
            source_job=tracked_jobs[identifier], dest_job=defined_jobs[identifier]
        ):
            defined_jobs[identifier].id = tracked_jobs[identifier].id
            dbt_cloud.update_job(job=defined_jobs[identifier])

    # Create new jobs
    logger.info("Detected {count} new jobs.", count=len(created_jobs))
    for identifier in created_jobs:
        dbt_cloud.create_job(job=defined_jobs[identifier])

    # Remove Deleted Jobs
    logger.warning("Detected {count} deleted jobs.", count=len(deleted_jobs))
    for identifier in deleted_jobs:
        dbt_cloud.delete_job(job=tracked_jobs[identifier])
