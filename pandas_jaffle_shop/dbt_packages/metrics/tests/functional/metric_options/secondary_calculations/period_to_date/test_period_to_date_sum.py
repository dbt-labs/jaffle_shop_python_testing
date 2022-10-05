from struct import pack
import os
import pytest
from dbt.tests.util import run_dbt

# our file contents
from tests.functional.fixtures import (
    fact_orders_source_csv,
    fact_orders_sql,
    fact_orders_yml,
)

# models/period_to_date_sum.sql
period_to_date_sum_sql = """
select *
from 
{{ metrics.calculate(metric('period_to_date_sum'), 
    grain='month',
    secondary_calculations=[
        metrics.period_to_date(aggregate="sum", period="year", alias="this_year_sum"),
        metrics.period_to_date(aggregate="max", period="year"),
        metrics.period_to_date(aggregate="sum", period="year"),
        metrics.period_to_date(aggregate="average", period="year"),
    ]
    )
}}
"""

# models/period_to_date_sum.yml
period_to_date_sum_yml = """
version: 2 
models:
  - name: period_to_date_sum
    tests: 
      - dbt_utils.equality:
          compare_model: ref('period_to_date_sum__expected')
metrics:
  - name: period_to_date_sum
    model: ref('fact_orders')
    label: sum value
    timestamp: order_date
    time_grains: [day, week, month]
    type: sum
    sql: customer_id
    dimensions:
      - had_discount
      - order_country
"""

# seeds/period_to_date_sum__expected.csv
if os.getenv('dbt_target') == 'postgres':
    period_to_date_sum__expected_csv = """
date_month,date_year,period_to_date_sum,period_to_date_sum_this_year_sum,period_to_date_sum_max_for_year,period_to_date_sum_sum_for_year,period_to_date_sum_average_for_year
2022-01-01,2022-01-01,18,18,18,18,18.0000000000000000
2022-02-01,2022-01-01,6,24,18,24,12.0000000000000000
""".lstrip()

# seeds/period_to_date_sum__expected.csv
if os.getenv('dbt_target') == 'redshift':
    period_to_date_sum__expected_csv = """
date_month,date_year,period_to_date_sum,period_to_date_sum_this_year_sum,period_to_date_sum_max_for_year,period_to_date_sum_sum_for_year,period_to_date_sum_average_for_year
2022-01-01,2022-01-01,18,18,18,18,18.0000000000000000
2022-02-01,2022-01-01,6,24,18,24,12.0000000000000000
""".lstrip()

# seeds/period_to_date_sum__expected.csv
if os.getenv('dbt_target') == 'snowflake':
    period_to_date_sum__expected_csv = """
date_month,date_year,period_to_date_sum,period_to_date_sum_this_year_sum,period_to_date_sum_max_for_year,period_to_date_sum_sum_for_year,period_to_date_sum_average_for_year
2022-01-01,2022-01-01,18,18,18,18,18.000000
2022-02-01,2022-01-01,6,24,18,24,12.000000
""".lstrip()

# seeds/period_to_date_sum__expected.csv
if os.getenv('dbt_target') == 'bigquery':
    period_to_date_sum__expected_csv = """
date_month,date_year,period_to_date_sum,period_to_date_sum_this_year_sum,period_to_date_sum_max_for_year,period_to_date_sum_sum_for_year,period_to_date_sum_average_for_year
2022-01-01,2022-01-01,18,18,18,18,18.0000000000000000
2022-02-01,2022-01-01,6,24,18,24,12.0000000000000000
""".lstrip()

# seeds/period_to_date_sum__expected.yml
if os.getenv('dbt_target') == 'bigquery':
    period_to_date_sum__expected_yml = """
version: 2
seeds:
  - name: period_to_date_sum__expected
    config:
      column_types:
        date_month: date
        date_year: date
        period_to_date_sum: INT64
        period_to_date_sum_this_year_min: INT64
        period_to_date_sum_max_for_year: INT64
        period_to_date_sum_sum_for_year: INT64
        period_to_date_sum_average_for_year: FLOAT64
""".lstrip()
else: 
    period_to_date_sum__expected_yml = """"""
    

class TestPeriodToDateSum:

    # configuration in dbt_project.yml
    # setting bigquery as table to get around query complexity 
    # resource constraints with compunding views
    if os.getenv('dbt_target') == 'bigquery':
        @pytest.fixture(scope="class")
        def project_config_update(self):
            return {
            "name": "example",
            "models": {"+materialized": "table"}
            }
    else: 
        @pytest.fixture(scope="class")
        def project_config_update(self):
            return {
            "name": "example",
            "models": {"+materialized": "view"}
            }  

    # install current repo as package
    @pytest.fixture(scope="class")
    def packages(self):
        return {
            "packages": [
                {"local": os.getcwd()}
                ]
        }

    # everything that goes in the "seeds" directory
    @pytest.fixture(scope="class")
    def seeds(self):
        return {
            "fact_orders_source.csv": fact_orders_source_csv,
            "period_to_date_sum__expected.csv": period_to_date_sum__expected_csv,
            "period_to_date_sum__expected.yml": period_to_date_sum__expected_yml
        }

    # everything that goes in the "models" directory
    @pytest.fixture(scope="class")
    def models(self):
        return {
            "fact_orders.sql": fact_orders_sql,
            "fact_orders.yml": fact_orders_yml,
            "period_to_date_sum.sql": period_to_date_sum_sql,
            "period_to_date_sum.yml": period_to_date_sum_yml
        }

    def test_build_completion(self,project,):
        # running deps to install package
        results = run_dbt(["deps"])

        # seed seeds
        results = run_dbt(["seed"])
        assert len(results) == 2

        # initial run
        results = run_dbt(["run"])
        assert len(results) == 3

        # test tests
        results = run_dbt(["test"]) # expect passing test
        assert len(results) == 1

        # # # validate that the results include pass
        result_statuses = sorted(r.status for r in results)
        assert result_statuses == ["pass"]