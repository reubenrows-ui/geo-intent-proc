import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, Conflict
import logging

# Configure logging to provide more detailed output
logging.basicConfig(level=logging.INFO)
logging.getLogger("google.cloud").setLevel(logging.DEBUG)

def create_bigquery_dataset(project_id: str, dataset_id: str, location: str = "US"):
    """
    Creates a new BigQuery dataset if it does not already exist.

    Args:
        project_id (str): The Google Cloud project ID.
        dataset_id (str): The ID of the dataset to create.
        location (str): The geographic location for the dataset (e.g., 'US', 'EU').
                        This cannot be changed after creation.
    """
    try:
        logging.info(f"Connecting to BigQuery client for project '{project_id}'...")
        client = bigquery.Client(project=project_id)

        # Construct a full Dataset object
        dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")
        dataset.location = location

        logging.info(f"Attempting to create dataset '{dataset_id}' in location '{location}'...")
        dataset = client.create_dataset(dataset, timeout=30)
        logging.info(f"Successfully created dataset '{dataset.dataset_id}'.")
    except Conflict:
        logging.info(f"Dataset '{dataset_id}' already exists. Skipping creation.")
    except Exception as e:
        logging.error(f"An error occurred while creating the dataset: {e}")
        raise


def write_table_from_query(project_id: str, dataset_id: str, table_id: str, query: str, overwrite: bool = True):
    """
    Executes a SQL query and writes the results to a new or existing BigQuery table.

    Args:
        project_id (str): The Google Cloud project ID.
        dataset_id (str): The ID of the target dataset.
        table_id (str): The ID of the target table.
        query (str): The SQL query to execute.
        overwrite (bool): If True, the table will be overwritten (truncated). If False,
                          the results will be appended to the table.
    """
    try:
        logging.info(f"Connecting to BigQuery client for project '{project_id}'...")
        client = bigquery.Client(project=project_id)

        # Define the fully qualified destination table ID
        table_ref = client.dataset(dataset_id).table(table_id)
        
        # Determine the write disposition based on the 'overwrite' parameter
        if overwrite:
            write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
            logging.info(f"Setting job disposition to WRITE_TRUNCATE (overwrite).")
        else:
            write_disposition = bigquery.WriteDisposition.WRITE_APPEND
            logging.info(f"Setting job disposition to WRITE_APPEND (append).")

        # Configure the query job to save results to the specified table
        job_config = bigquery.QueryJobConfig(
            destination=table_ref,
            write_disposition=write_disposition
        )

        logging.info(f"Starting query job to populate table '{table_id}'...")
        # Start the query and wait for it to complete
        job = client.query(query, job_config=job_config)
        
        logging.info(f"Waiting for job {job.job_id} to complete...")
        job.result()  # Waits for the job to finish

        logging.info(f"Job {job.job_id} completed. Table populated successfully.")
        table = client.get_table(table_ref)
        logging.info(
            f"Table '{table.table_id}' now contains {table.num_rows} rows."
        )

    except NotFound:
        logging.error(f"Dataset '{dataset_id}' not found. Please create the dataset first.")
        raise
    except Exception as e:
        logging.error(f"An error occurred during the table creation from query: {e}")
        raise


def run_query(project_id: str, query: str) -> pd.DataFrame:
    """
    Executes a SQL query and returns the results as a Pandas DataFrame.

    Args:
        project_id (str): The Google Cloud project ID.
        query (str): The SQL query to execute.

    Returns:
        pd.DataFrame: A DataFrame containing the query results.
    """
    try:
        logging.info(f"Connecting to BigQuery client for project '{project_id}'...")
        client = bigquery.Client(project=project_id)

        logging.info("Starting query job...")
        # Start the query and wait for it to complete
        job = client.query(query)

        logging.info(f"Waiting for job {job.job_id} to complete...")
        results = job.result()  # Waits for the job to finish

        logging.info(f"Job {job.job_id} completed. Fetching results as a DataFrame...")
        df = results.to_dataframe()
        logging.info(f"Query returned {len(df)} rows.")
        return df

    except Exception as e:
        logging.error(f"An error occurred while running the query: {e}")
        raise


def import_parquet_file(project_id: str, dataset_id: str, table_id: str, parquet_file_path: str, overwrite: bool = True):
    """
    Loads data from a local Parquet file into a BigQuery table.
    The table will be created if it does not exist.

    Args:
        project_id (str): The Google Cloud project ID.
        dataset_id (str): The ID of the target dataset.
        table_id (str): The ID of the target table.
        parquet_file_path (str): The local path to the Parquet file.
        overwrite (bool): If True, the table will be overwritten (truncated). If False,
                          the results will be appended to the table.
    """
    if not os.path.exists(parquet_file_path):
        logging.error(f"Parquet file not found at path: {parquet_file_path}")
        raise FileNotFoundError(f"File not found: {parquet_file_path}")

    try:
        logging.info(f"Connecting to BigQuery client for project '{project_id}'...")
        client = bigquery.Client(project=project_id)
        
        # Define the fully qualified destination table ID
        table_ref = client.dataset(dataset_id).table(table_id)

        # Determine the write disposition based on the 'overwrite' parameter
        if overwrite:
            write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
            logging.info(f"Setting job disposition to WRITE_TRUNCATE (overwrite).")
        else:
            write_disposition = bigquery.WriteDisposition.WRITE_APPEND
            logging.info(f"Setting job disposition to WRITE_APPEND (append).")

        # Configure the load job for a Parquet file
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=write_disposition
        )

        logging.info(f"Opening local Parquet file from '{parquet_file_path}'...")
        with open(parquet_file_path, "rb") as source_file:
            logging.info(f"Starting load job for table '{table_id}'...")
            job = client.load_table_from_file(
                source_file,
                table_ref,
                location="US",  # Must match the dataset location
                job_config=job_config
            )

        # Wait for the job to complete
        logging.info(f"Waiting for job {job.job_id} to complete...")
        job.result()

        logging.info(f"Job {job.job_id} completed. Data loaded successfully.")
        table = client.get_table(table_ref)
        logging.info(
            f"Loaded {table.num_rows} rows and {len(table.schema)} columns to table '{table_id}'."
        )

    except NotFound:
        logging.error(f"Dataset '{dataset_id}' not found. Please create the dataset first.")
        raise
    except Exception as e:
        logging.error(f"An error occurred during the table load job: {e}")
        raise

def import_csv_file(project_id: str, dataset_id: str, table_id: str, csv_file_path: str, overwrite: bool = True):
    """
    Loads data from a local CSV file into a BigQuery table.
    The table will be created with an autodetected schema if it does not exist.

    Args:
        project_id (str): The Google Cloud project ID.
        dataset_id (str): The ID of the target dataset.
        table_id (str): The ID of the target table.
        csv_file_path (str): The local path to the CSV file.
        overwrite (bool): If True, the table will be overwritten (truncated). If False,
                          the results will be appended to the table.
    """
    if not os.path.exists(csv_file_path):
        logging.error(f"CSV file not found at path: {csv_file_path}")
        raise FileNotFoundError(f"File not found: {csv_file_path}")

    try:
        logging.info(f"Connecting to BigQuery client for project '{project_id}'...")
        client = bigquery.Client(project=project_id)
        
        # Define the fully qualified destination table ID
        table_ref = client.dataset(dataset_id).table(table_id)

        # Determine the write disposition based on the 'overwrite' parameter
        if overwrite:
            write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
            logging.info(f"Setting job disposition to WRITE_TRUNCATE (overwrite).")
        else:
            write_disposition = bigquery.WriteDisposition.WRITE_APPEND
            logging.info(f"Setting job disposition to WRITE_APPEND (append).")

        # Configure the load job for a CSV file with auto-detection
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1, # Skips the header row
            autodetect=True,
            write_disposition=write_disposition
        )

        logging.info(f"Opening local CSV file from '{csv_file_path}'...")
        with open(csv_file_path, "rb") as source_file:
            logging.info(f"Starting load job for table '{table_id}'...")
            job = client.load_table_from_file(
                source_file,
                table_ref,
                location="US",  # Must match the dataset location
                job_config=job_config
            )

        # Wait for the job to complete
        logging.info(f"Waiting for job {job.job_id} to complete...")
        job.result()

        logging.info(f"Job {job.job_id} completed. Data loaded successfully.")
        table = client.get_table(table_ref)
        logging.info(
            f"Loaded {table.num_rows} rows and {len(table.schema)} columns to table '{table_id}'."
        )

    except NotFound:
        logging.error(f"Dataset '{dataset_id}' not found. Please create the dataset first.")
        raise
    except Exception as e:
        logging.error(f"An error occurred during the table load job: {e}")
        raise

def import_json_file(project_id: str, dataset_id: str, table_id: str, json_file_path: str, overwrite: bool = True):
    """
    Loads data from a local JSON file (newline-delimited) into a BigQuery table.
    The table will be created with an autodetected schema if it does not exist.

    Args:
        project_id (str): The Google Cloud project ID.
        dataset_id (str): The ID of the target dataset.
        table_id (str): The ID of the target table.
        json_file_path (str): The local path to the JSON file.
        overwrite (bool): If True, the table will be overwritten (truncated). If False,
                          the results will be appended to the table.
    """
    if not os.path.exists(json_file_path):
        logging.error(f"JSON file not found at path: {json_file_path}")
        raise FileNotFoundError(f"File not found: {json_file_path}")

    try:
        logging.info(f"Connecting to BigQuery client for project '{project_id}'...")
        client = bigquery.Client(project=project_id)
        
        # Define the fully qualified destination table ID
        table_ref = client.dataset(dataset_id).table(table_id)

        # Determine the write disposition based on the 'overwrite' parameter
        if overwrite:
            write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
            logging.info(f"Setting job disposition to WRITE_TRUNCATE (overwrite).")
        else:
            write_disposition = bigquery.WriteDisposition.WRITE_APPEND
            logging.info(f"Setting job disposition to WRITE_APPEND (append).")

        # Configure the load job for a JSON file
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True,
            write_disposition=write_disposition
        )

        logging.info(f"Opening local JSON file from '{json_file_path}'...")
        with open(json_file_path, "rb") as source_file:
            logging.info(f"Starting load job for table '{table_id}'...")
            job = client.load_table_from_file(
                source_file,
                table_ref,
                location="US",  # Must match the dataset location
                job_config=job_config
            )

        # Wait for the job to complete
        logging.info(f"Waiting for job {job.job_id} to complete...")
        job.result()

        logging.info(f"Job {job.job_id} completed. Data loaded successfully.")
        table = client.get_table(table_ref)
        logging.info(
            f"Loaded {table.num_rows} rows and {len(table.schema)} columns to table '{table_id}'."
        )

    except NotFound:
        logging.error(f"Dataset '{dataset_id}' not found. Please create the dataset first.")
        raise
    except Exception as e:
        logging.error(f"An error occurred during the table load job: {e}")
        raise
